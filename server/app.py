"""
FastAPI + WebSocket 后端，用于将现有 Python 牌局引擎(game.Game) 暴露给前端网页 UI。

消息协定(JSON)：
  前端 → 后端：
    - {"type":"join", "player":"Alice"}
    - {"type":"start_hand"}
    - {"type":"action", "action":"fold|check|call|raise|all_in", "amount": int}
  后端 → 前端：
    - {"type":"state", "state": <Game.get_game_state()>}
    - {"type":"message", "text": str}

运行：
  uvicorn server.app:app --reload --port 8000
"""

from __future__ import annotations

from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from game.game_engine import Game, GameMode, GamePhase
from game.player import Player, PlayerAction, PlayerStatus


app = FastAPI(title="Texas Hold'em WebSocket Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, data: Dict[str, Any]):
        for ws in list(self.active):
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(ws)


manager = ConnectionManager()


class GameService:
    def __init__(self):
        self.game = Game(mode=GameMode.CASH_GAME, small_blind=10, big_blind=20)
        # 默认两名玩家，前端 join 时可追加
        self.ensure_default_players()

    def ensure_default_players(self):
        if len(self.game.players) < 2:
            # Player(name, chips, position)
            self.game.add_player(Player("Alice", 1000, 0))
            self.game.add_player(Player("Bob", 1000, 1))

    def state(self) -> Dict[str, Any]:
        if not self.game.players:
            return {"status": "waiting_for_players"}
            
        # 获取基础状态
        base_state = self.game.get_game_state()
        
        # 获取当前玩家，确保是可以行动的玩家
        current = self.game.get_current_player()
        current_player_position = current.position if current else None
        
        # 二次验证：如果当前玩家无法行动，尝试修复
        if current and not current.can_act():
            print(f"⚠️  当前玩家 {current.name} 无法行动 (状态: {current.status.value})，尝试跳到下一个玩家")
            # 强制移动到下一个活跃玩家
            active_players = [i for i, p in enumerate(self.game.players) if p.can_act()]
            if active_players:
                self.game.current_player_index = active_players[0]
                current = self.game.get_current_player()
                current_player_position = current.position if current else None
                print(f"✅ 已切换到玩家 {current.name if current else 'None'}")
        
        # 构建玩家数据，只对当前玩家显示底牌
        players_data = []
        for p in self.game.players:
            player_state = {
                "id": p.position,
                "name": p.name,
                "chips": p.chips,
                "status": p.status.value,
                "current_bet": p.current_bet,
                "last_action": p.last_action.value if p.last_action else None,
                "hole_cards": [str(card) for card in p.hole_cards] if p.hole_cards and p.position == current_player_position else (["🂠", "🂠"] if p.hole_cards else [])
            }
            players_data.append(player_state)
        
        # 计算需要跟注的金额
        to_call = 0
        valid_actions = []
        if current:
            to_call = max(0, self.game.current_bet - current.current_bet)
            try:
                acts = self.game.get_valid_actions(current)
                valid_actions = [a.value for a in acts]
            except Exception:
                valid_actions = []
        
        # 构建完整状态
        return {
            "status": "ok",
            "game_phase": self.game.phase.value,
            "pot_size": self.game.pot.get_total_pot(),
            "community_cards": [str(card) for card in self.game.community_cards],
            "players": players_data,
            "current_player_index": self.game.current_player_index,
            "dealer_position": self.game.dealer_position,
            "small_blind": self.game.small_blind,
            "big_blind": self.game.big_blind,
            "current_bet": self.game.current_bet,
            "min_raise": self.game.min_raise,
            "to_call": to_call,
            "valid_actions": valid_actions,
            "phase": base_state.get("phase", "waiting")
        }

    def start_hand(self):
        if self.game.can_start_game():
            self.game.start_new_hand()

    def new_game(self, *, small_blind: int = 10, big_blind: int = 20, players: list[dict] | None = None):
        # 重建 Game 并加入玩家
        self.game = Game(mode=GameMode.CASH_GAME, small_blind=small_blind, big_blind=big_blind)
        players = players or [{"name": "Alice", "chips": 1000}, {"name": "Bob", "chips": 1000}]
        for idx, p in enumerate(players):
            name = str(p.get("name", f"P{idx+1}"))[:16]
            chips = int(p.get("chips", 1000))
            # Player(name, chips, position)
            self.game.add_player(Player(name, chips, idx))
        if self.game.can_start_game():
            self.game.start_new_hand()

    def add_player(self, name: str, chips: int = 1000):
        if not any(p.name == name for p in self.game.players):
            self.game.add_player(Player(name, chips, len(self.game.players)))

    def action(self, action: str, amount: int = 0) -> bool:
        current = self.game.get_current_player()
        if not current or not current.can_act():
            return False
        mapping = {
            "fold": PlayerAction.FOLD,
            "check": PlayerAction.CHECK,
            "call": PlayerAction.CALL,
            "raise": PlayerAction.RAISE,
            "all_in": PlayerAction.ALL_IN,
        }
        if action not in mapping:
            return False
        return self.game.player_action(current, mapping[action], amount)


service = GameService()

# ---- Static files (serve /web) ----
BASE_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = BASE_DIR / "web"
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")


@app.get("/")
def index():
    """Redirect to /web if available, otherwise show a simple message."""
    if WEB_DIR.exists():
        return RedirectResponse(url="/web/index.html")
    return {"message": "Server running. Place frontend in /web or open web/index.html via a static server."}


@app.get("/favicon.ico")
def favicon():
    ico = WEB_DIR / "favicon.ico"
    if ico.exists():
        return FileResponse(str(ico))
    return RedirectResponse(url="/web/index.html")


@app.get("/api/state")
def http_state():
    return {"type": "state", "state": service.state()}


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    await websocket.send_json({"type": "state", "state": service.state()})
    try:
        while True:
            msg = await websocket.receive_json()
            mtype = msg.get("type")
            if mtype == "join":
                name = (msg.get("player") or "Guest").strip() or "Guest"
                service.add_player(name)
                await manager.broadcast({"type": "state", "state": service.state()})
            elif mtype == "start_hand":
                service.start_hand()
                await manager.broadcast({"type": "state", "state": service.state()})
            elif mtype == "new_game":
                cfg = msg.get("config", {}) or {}
                service.new_game(
                    small_blind=int(cfg.get("small_blind", 10)),
                    big_blind=int(cfg.get("big_blind", 20)),
                    players=cfg.get("players") or []
                )
                await manager.broadcast({"type": "state", "state": service.state(), "new_game": True})
            elif mtype == "action":
                action_type = msg.get("action", "")
                amount = int(msg.get("amount", 0))
                current_player = service.game.get_current_player()
                print(f"🎯 处理动作: {action_type}, 金额: {amount}, 当前玩家: {current_player.name if current_player else 'None'}")
                
                # 特别记录弃牌动作
                if action_type == "fold":
                    print(f"🔴 玩家 {current_player.name if current_player else 'None'} 尝试弃牌")
                    print(f"💡 玩家状态: {current_player.status.value if current_player else 'None'}")
                    print(f"💰 玩家筹码: {current_player.chips if current_player else 'None'}")
                    print(f"📊 玩家当前下注: {current_player.current_bet if current_player else 'None'}")
                    valid_actions = service.game.get_valid_actions(current_player) if current_player else []
                    print(f"✅ 有效动作: {[a.value for a in valid_actions]}")
                
                ok = service.action(action_type, amount)
                print(f"📊 动作执行结果: {ok}")
                done = service.game.is_hand_complete()
                
                new_current_player = service.game.get_current_player()
                print(f"📊 动作结果: ok={ok}, hand_complete={done}, 游戏阶段={service.game.phase.value}")
                print(f"👤 下一位行动玩家: {new_current_player.name if new_current_player else 'None'}")
                
                # 显示所有玩家状态
                active_players = [p for p in service.game.players if p.can_act()]
                folded_players = [p for p in service.game.players if p.status.value == 'folded']
                print(f"🟢 可行动玩家: {[p.name for p in active_players]}")
                print(f"🔴 已弃牌玩家: {[p.name for p in folded_players]}")
                
                # 检查是否有玩家筹码耗尽
                players_with_chips = [p for p in service.game.players if p.chips > 0]
                game_over = len(players_with_chips) < 2
                
                print(f"💰 有筹码的玩家: {len(players_with_chips)}, game_over={game_over}")
                
                # 先广播状态更新
                await manager.broadcast({
                    "type": "state", 
                    "state": service.state(), 
                    "ok": ok, 
                    "hand_complete": done,
                    "game_over": game_over
                })
                
                # 如果一手结束，等待一会儿再询问
                if done:
                    print(f"⏰ 一手结束，等待1.5秒后显示对话框...")
                    import asyncio
                    await asyncio.sleep(1.5)  # 让玩家看到结果
                    
                    if game_over:
                        print(f"🏁 游戏结束，发送 ask_restart_or_exit 消息")
                        await manager.broadcast({"type": "ask_restart_or_exit"})
                    else:
                        print(f"🔄 继续游戏，发送 ask_continue 消息")
                        await manager.broadcast({"type": "ask_continue"})
            elif mtype == "continue_game":
                # 继续下一轮
                try:
                    service.start_hand()
                    await manager.broadcast({"type": "state", "state": service.state(), "hand_started": True})
                except Exception as e:
                    await manager.broadcast({"type": "message", "text": f"无法开启下一手: {e}"})
            elif mtype == "ask_restart_or_exit":
                # 询问重新开始或退出
                await manager.broadcast({"type": "ask_restart_or_exit"})
            elif mtype == "restart_game":
                # 重置所有玩家筹码并开始新游戏
                initial_chips = 1000
                for player in service.game.players:
                    player.chips = initial_chips  # 重置为初始筹码
                    player.status = PlayerStatus.SITTING_OUT
                    player.hole_cards = []
                    player.current_bet = 0
                    player.total_bet = 0
                    player.last_action = None
                    player.sit_in()  # 重新入座
                
                # 重置游戏状态
                service.game.phase = GamePhase.WAITING
                service.game.community_cards = []
                service.game.pot.reset()
                service.game.current_bet = 0
                service.game.min_raise = service.game.big_blind
                
                try:
                    service.start_hand()
                    await manager.broadcast({"type": "state", "state": service.state(), "game_restarted": True})
                except Exception as e:
                    await manager.broadcast({"type": "message", "text": f"重启游戏失败: {e}"})
            elif mtype == "exit_game":
                # 退出游戏
                await manager.broadcast({"type": "game_exit"})
                # 这里可以添加服务器关闭逻辑，但通常不建议从客户端关闭服务器
            elif mtype == "check_current_player":
                print("🔍 检查当前玩家状态")
                current = service.game.get_current_player()
                if current:
                    print(f"📍 当前玩家: {current.name}, 状态: {current.status.value}, 可行动: {current.can_act()}")
                    if not current.can_act():
                        print("⚡ 强制跳转到下一个活跃玩家")
                        active_players = [i for i, p in enumerate(service.game.players) if p.can_act()]
                        if active_players:
                            service.game.current_player_index = active_players[0]
                            new_current = service.game.get_current_player()
                            print(f"✅ 已切换到: {new_current.name if new_current else 'None'}")
                
                # 重新广播状态
                await manager.broadcast({"type": "state", "state": service.state()})
            else:
                await websocket.send_json({"type": "message", "text": "Unknown message"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        try:
            await websocket.send_json({"type": "message", "text": f"Server error: {e}"})
        except Exception:
            pass


