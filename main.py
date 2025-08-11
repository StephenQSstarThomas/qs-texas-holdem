"""
德州扑克游戏主入口
Texas Hold'em Poker Game Main Entry Point
"""

import sys
import json
from typing import List
from game import Game, Player, PlayerAction, GameMode, GamePhase


class TexasHoldemCLI:
    """德州扑克命令行界面"""
    
    def __init__(self):
        """初始化CLI游戏"""
        self.game: Game = None
        self.config = self.load_config()
    
    def load_config(self) -> dict:
        """加载游戏配置"""
        default_config = {
            "small_blind": 10,
            "big_blind": 20,
            "default_chips": 1000,
            "game_mode": "cash_game"
        }
        
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            # 创建默认配置文件
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def save_config(self):
        """保存游戏配置"""
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def display_welcome(self):
        """显示欢迎信息"""
        print("=" * 50)
        print("🃏 欢迎来到德州扑克游戏! 🃏")
        print("=" * 50)
        print("游戏规则:")
        print("- 支持2-6人游戏")
        print("- 每位玩家获得2张底牌")
        print("- 5张公共牌分三轮发出 (翻牌3张, 转牌1张, 河牌1张)")
        print("- 用7张牌中的最佳5张组成最大牌型")
        print("=" * 50)
    
    def setup_game(self):
        """设置游戏"""
        print("\n🎮 游戏设置")
        
        # 选择游戏模式
        mode_choice = input("选择游戏模式 (1: 现金游戏, 2: 锦标赛) [1]: ").strip()
        if mode_choice == "2":
            game_mode = GameMode.TOURNAMENT
        else:
            game_mode = GameMode.CASH_GAME
        
        # 设置盲注
        try:
            small_blind = int(input(f"小盲注 [{self.config['small_blind']}]: ") or self.config['small_blind'])
            big_blind = int(input(f"大盲注 [{self.config['big_blind']}]: ") or self.config['big_blind'])
        except ValueError:
            small_blind = self.config['small_blind']
            big_blind = self.config['big_blind']
        
        # 创建游戏实例
        self.game = Game(game_mode, small_blind, big_blind)
        
        # 添加玩家
        self.setup_players()
        
        print(f"\n✅ 游戏设置完成!")
        print(f"模式: {game_mode.value}")
        print(f"盲注: {small_blind}/{big_blind}")
        print(f"玩家数量: {len(self.game.players)}")
    
    def setup_players(self):
        """设置玩家"""
        print("\n👥 添加玩家")
        
        while len(self.game.players) < 6:
            if len(self.game.players) >= 2:
                continue_input = input(f"当前有 {len(self.game.players)} 位玩家，是否继续添加? (y/n) [n]: ").strip().lower()
                if continue_input != 'y':
                    break
            
            player_name = input(f"输入玩家 {len(self.game.players) + 1} 的姓名: ").strip()
            if not player_name:
                break
            
            try:
                chips = int(input(f"输入 {player_name} 的初始筹码 [{self.config['default_chips']}]: ") 
                           or self.config['default_chips'])
            except ValueError:
                chips = self.config['default_chips']
            
            player = Player(player_name, chips)
            if self.game.add_player(player):
                print(f"✅ {player_name} 已加入游戏 (筹码: {chips})")
            else:
                print(f"❌ 无法添加玩家 {player_name}")
    
    def display_game_state(self):
        """显示游戏状态"""
        print("\n" + "=" * 60)
        print(f"🎯 第 {self.game.hand_number} 手牌 - {self.game.phase.value.upper()}")
        print("=" * 60)
        
        # 显示公共牌
        if self.game.community_cards:
            cards_str = " ".join(str(card) for card in self.game.community_cards)
            print(f"🃏 公共牌: {cards_str}")
        else:
            print("🃏 公共牌: 尚未发出")
        
        # 显示奖池
        print(f"💰 奖池: {self.game.pot.get_total_pot()} 筹码")
        print(f"📊 当前下注: {self.game.current_bet}")
        
        # 显示玩家状态
        print("\n👥 玩家状态:")
        for i, player in enumerate(self.game.players):
            status_icon = "🎯" if i == self.game.current_player_index else "  "
            dealer_icon = "🔘" if i == self.game.dealer_position else "  "
            
            print(f"{status_icon}{dealer_icon} {player.name:10} | "
                  f"筹码: {player.chips:6} | "
                  f"下注: {player.current_bet:4} | "
                  f"状态: {player.status.value:10}")
            
            # 显示底牌 (仅在摊牌阶段或游戏结束时)
            if (self.game.phase in [GamePhase.SHOWDOWN, GamePhase.HAND_COMPLETE] 
                and player.hole_cards and player.is_in_hand()):
                cards_str = " ".join(str(card) for card in player.hole_cards)
                print(f"    底牌: {cards_str}")
        
        print("-" * 60)
    
    def get_player_action(self, player: Player) -> tuple:
        """获取玩家动作"""
        valid_actions = self.game.get_valid_actions(player)
        
        print(f"\n🎯 {player.name} 的回合")
        print(f"可用筹码: {player.chips}")
        print(f"当前下注: {player.current_bet}")
        print(f"需要跟注: {max(0, self.game.current_bet - player.current_bet)}")
        
        # 显示底牌
        if player.hole_cards:
            cards_str = " ".join(str(card) for card in player.hole_cards)
            print(f"底牌: {cards_str}")
        
        # 显示可选动作
        print("\n可选动作:")
        action_map = {}
        for i, action in enumerate(valid_actions, 1):
            action_names = {
                PlayerAction.FOLD: "弃牌",
                PlayerAction.CHECK: "过牌",
                PlayerAction.CALL: f"跟注 ({self.game.current_bet - player.current_bet})",
                PlayerAction.RAISE: "加注",
                PlayerAction.ALL_IN: f"全押 ({player.chips})"
            }
            print(f"{i}. {action_names[action]}")
            action_map[str(i)] = action
        
        # 获取玩家选择
        while True:
            choice = input("请选择动作 (输入数字): ").strip()
            if choice in action_map:
                selected_action = action_map[choice]
                
                # 如果是加注，需要输入金额
                if selected_action == PlayerAction.RAISE:
                    min_raise = self.game.current_bet + self.game.min_raise
                    max_raise = player.chips + player.current_bet
                    
                    try:
                        amount = int(input(f"输入加注到的总金额 ({min_raise}-{max_raise}): "))
                        if min_raise <= amount <= max_raise:
                            return selected_action, amount
                        else:
                            print(f"❌ 金额必须在 {min_raise}-{max_raise} 之间")
                    except ValueError:
                        print("❌ 请输入有效数字")
                else:
                    return selected_action, 0
            else:
                print("❌ 无效选择，请重新输入")
    
    def play_hand(self):
        """进行一手牌"""
        self.game.start_new_hand()
        
        while not self.game.is_hand_complete():
            self.display_game_state()
            
            current_player = self.game.get_current_player()
            if current_player and current_player.can_act():
                action, amount = self.get_player_action(current_player)
                
                if self.game.player_action(current_player, action, amount):
                    action_names = {
                        PlayerAction.FOLD: "弃牌",
                        PlayerAction.CHECK: "过牌",
                        PlayerAction.CALL: "跟注",
                        PlayerAction.RAISE: f"加注到 {amount}",
                        PlayerAction.ALL_IN: "全押"
                    }
                    print(f"✅ {current_player.name} {action_names[action]}")
                else:
                    print(f"❌ 动作执行失败")
            else:
                # 自动进入下一阶段
                break
        
        # 显示最终结果
        self.display_final_result()
    
    def display_final_result(self):
        """显示最终结果"""
        self.display_game_state()
        
        print("\n🏆 手牌结果:")
        
        # 显示获胜者
        active_players = [p for p in self.game.players if p.is_in_hand()]
        if len(active_players) == 1:
            winner = active_players[0]
            print(f"🎉 {winner.name} 获胜! (其他玩家弃牌)")
        else:
            # 显示所有玩家的最终牌型
            from game.hand_evaluator import HandEvaluator
            
            print("\n各玩家最终牌型:")
            player_results = []
            
            for player in active_players:
                all_cards = player.hole_cards + self.game.community_cards
                hand_result = HandEvaluator.evaluate_hand(all_cards)
                player_results.append((player, hand_result))
                print(f"{player.name}: {hand_result}")
            
            # 找出获胜者
            best_hand = max(result[1] for result in player_results)
            winners = [player for player, result in player_results if result == best_hand]
            
            if len(winners) == 1:
                print(f"\n🎉 {winners[0].name} 获胜!")
            else:
                winner_names = ", ".join(p.name for p in winners)
                print(f"\n🤝 平局! 获胜者: {winner_names}")
        
        input("\n按回车键继续...")
    
    def run(self):
        """运行游戏主循环"""
        self.display_welcome()
        self.setup_game()
        
        if not self.game.can_start_game():
            print("❌ 玩家数量不足，无法开始游戏")
            return
        
        try:
            while True:
                # 检查是否还有足够玩家继续游戏
                active_players = [p for p in self.game.players if p.chips > 0]
                if len(active_players) < 2:
                    print("\n🎯 游戏结束! 玩家数量不足")
                    break
                
                # 进行一手牌
                self.play_hand()
                
                # 询问是否继续
                continue_game = input("\n是否继续下一手牌? (y/n) [y]: ").strip().lower()
                if continue_game == 'n':
                    break
        
        except KeyboardInterrupt:
            print("\n\n游戏被中断")
        except Exception as e:
            print(f"\n游戏出现错误: {e}")
        
        finally:
            self.display_final_stats()
    
    def display_final_stats(self):
        """显示最终统计"""
        print("\n" + "=" * 50)
        print("📊 游戏统计")
        print("=" * 50)
        
        for player in self.game.players:
            win_rate = player.get_win_rate() * 100 if player.hands_played > 0 else 0
            print(f"{player.name:15} | "
                  f"最终筹码: {player.chips:6} | "
                  f"盈亏: {player.total_winnings:+6} | "
                  f"胜率: {win_rate:5.1f}%")
        
        print("\n感谢游戏! 🎉")


def main():
    """主函数"""
    try:
        cli = TexasHoldemCLI()
        cli.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()