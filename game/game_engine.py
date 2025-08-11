"""
游戏引擎主控制类实现
Main game engine for Texas Hold'em poker
"""

from typing import List, Optional, Dict, Tuple
from enum import Enum
import random

from .card import Card, Deck
from .player import Player, PlayerStatus, PlayerAction
from .hand_evaluator import HandEvaluator, HandResult
from .pot import Pot


class GamePhase(Enum):
    """游戏阶段枚举"""
    WAITING = "waiting"           # 等待开始
    PRE_FLOP = "pre_flop"        # 翻牌前
    FLOP = "flop"                # 翻牌
    TURN = "turn"                # 转牌
    RIVER = "river"              # 河牌
    SHOWDOWN = "showdown"        # 摊牌
    HAND_COMPLETE = "hand_complete"  # 手牌结束


class GameMode(Enum):
    """游戏模式枚举"""
    CASH_GAME = "cash_game"      # 现金游戏
    TOURNAMENT = "tournament"     # 锦标赛


class Game:
    """德州扑克游戏主控制类"""
    
    def __init__(self, mode: GameMode = GameMode.CASH_GAME, 
                 small_blind: int = 10, big_blind: int = 20):
        """
        初始化游戏
        
        Args:
            mode: 游戏模式
            small_blind: 小盲注
            big_blind: 大盲注
        """
        self.mode = mode
        self.small_blind = small_blind
        self.big_blind = big_blind
        
        # 游戏状态
        self.phase = GamePhase.WAITING
        self.hand_number = 0
        self.players: List[Player] = []
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pot = Pot()
        
        # 位置信息
        self.dealer_position = 0
        self.current_player_index = 0
        self.last_raiser_index = -1
        
        # 下注信息
        self.current_bet = 0
        self.min_raise = self.big_blind
        
        # 游戏历史
        self.hand_history: List[Dict] = []
    
    def add_player(self, player: Player) -> bool:
        """
        添加玩家到游戏
        
        Args:
            player: 要添加的玩家
            
        Returns:
            是否成功添加
        """
        if len(self.players) >= 6:
            return False
        
        if any(p.name == player.name for p in self.players):
            return False
        
        player.position = len(self.players)
        self.players.append(player)
        player.sit_in()
        return True
    
    def remove_player(self, player_name: str) -> bool:
        """
        移除玩家
        
        Args:
            player_name: 玩家姓名
            
        Returns:
            是否成功移除
        """
        for i, player in enumerate(self.players):
            if player.name == player_name:
                self.players.pop(i)
                # 重新分配位置
                for j, p in enumerate(self.players):
                    p.position = j
                return True
        return False
    
    def can_start_game(self) -> bool:
        """检查是否可以开始游戏"""
        active_players = [p for p in self.players if p.chips > 0]
        return len(active_players) >= 2
    
    def start_new_hand(self):
        """开始新的一手牌"""
        if not self.can_start_game():
            raise ValueError("玩家数量不足，无法开始游戏")
        
        # 初始化新手牌
        self.hand_number += 1
        self.phase = GamePhase.PRE_FLOP
        self.community_cards = []
        self.pot.reset()
        self.current_bet = 0
        self.min_raise = self.big_blind
        self.last_raiser_index = -1
        
        # 重置玩家状态
        for player in self.players:
            player.new_hand()
            player.hands_played += 1
        
        # 移动庄家位置
        self._move_dealer_button()
        
        # 重新洗牌发牌
        self.deck.reset()
        self.deck.shuffle()
        
        # 发底牌
        self._deal_hole_cards()
        
        # 下盲注
        self._post_blinds()
        
        # 设置第一个行动玩家
        self._set_first_player_to_act()
    
    def _move_dealer_button(self):
        """移动庄家按钮"""
        active_players = [i for i, p in enumerate(self.players) if p.chips > 0]
        if not active_players:
            return
        
        # 找到下一个有筹码的玩家作为庄家
        current_dealer = self.dealer_position
        for _ in range(len(self.players)):
            current_dealer = (current_dealer + 1) % len(self.players)
            if current_dealer in active_players:
                self.dealer_position = current_dealer
                break
    
    def _deal_hole_cards(self):
        """发底牌"""
        active_players = [p for p in self.players if p.chips > 0]
        
        # 每位玩家发2张牌
        for _ in range(2):
            for player in active_players:
                card = self.deck.deal_card()
                if card:
                    if not player.hole_cards:
                        player.hole_cards = []
                    player.hole_cards.append(card)
    
    def _get_small_blind_position(self) -> int:
        """获取小盲注位置"""
        active_players = [i for i, p in enumerate(self.players) if p.chips > 0]
        if len(active_players) < 2:
            return 0
        
        dealer_idx = self.dealer_position
        if len(active_players) == 2:
            # 两人游戏，庄家是小盲
            return dealer_idx
        else:
            # 多人游戏，庄家左侧是小盲
            dealer_pos_in_active = active_players.index(dealer_idx) if dealer_idx in active_players else 0
            return active_players[(dealer_pos_in_active + 1) % len(active_players)]
    
    def _get_big_blind_position(self) -> int:
        """获取大盲注位置"""
        active_players = [i for i, p in enumerate(self.players) if p.chips > 0]
        if len(active_players) < 2:
            return 1
        
        dealer_idx = self.dealer_position
        if len(active_players) == 2:
            # 两人游戏，非庄家是大盲
            dealer_pos_in_active = active_players.index(dealer_idx) if dealer_idx in active_players else 0
            return active_players[(dealer_pos_in_active + 1) % len(active_players)]
        else:
            # 多人游戏，庄家左侧第二个是大盲
            dealer_pos_in_active = active_players.index(dealer_idx) if dealer_idx in active_players else 0
            return active_players[(dealer_pos_in_active + 2) % len(active_players)]

    def _post_blinds(self):
        """下盲注"""
        active_players = [i for i, p in enumerate(self.players) if p.chips > 0]
        if len(active_players) < 2:
            return
        
        # 获取小盲和大盲位置
        small_blind_idx = self._get_small_blind_position()
        big_blind_idx = self._get_big_blind_position()
        
        # 下小盲注
        small_blind_amount = self.players[small_blind_idx].post_blind(self.small_blind)
        self.pot.add_bet(self.players[small_blind_idx], small_blind_amount)
        
        # 下大盲注
        big_blind_amount = self.players[big_blind_idx].post_blind(self.big_blind)
        self.pot.add_bet(self.players[big_blind_idx], big_blind_amount)
        
        self.current_bet = self.big_blind
    
    def _set_first_player_to_act(self):
        """设置第一个行动的玩家"""
        active_players = [i for i, p in enumerate(self.players) 
                         if p.can_act()]
        
        if not active_players:
            return
        
        if self.phase == GamePhase.PRE_FLOP:
            # 翻牌前：大盲注左侧的玩家先行动 (Under the Gun)
            if len(self.players) == 2:
                # 两人游戏：庄家(小盲)先行动
                self.current_player_index = self.dealer_position
            else:
                # 多人游戏：找到大盲注位置，然后是左侧第一个活跃玩家
                big_blind_pos = self._get_big_blind_position()
                # 从大盲注下一位开始找第一个可以行动的玩家
                for i in range(1, len(self.players)):
                    next_pos = (big_blind_pos + i) % len(self.players)
                    if next_pos in active_players:
                        self.current_player_index = next_pos
                        break
        else:
            # 翻牌后：小盲注先行动，如果小盲注已弃牌则下一个活跃玩家
            if len(self.players) == 2:
                # 两人游戏：非庄家先行动
                non_dealer = (self.dealer_position + 1) % len(self.players)
                if non_dealer in active_players:
                    self.current_player_index = non_dealer
                else:
                    self.current_player_index = self.dealer_position
            else:
                # 多人游戏：从小盲注开始找第一个活跃玩家
                small_blind_pos = self._get_small_blind_position()
                found = False
                for i in range(len(self.players)):
                    check_pos = (small_blind_pos + i) % len(self.players)
                    if check_pos in active_players:
                        self.current_player_index = check_pos
                        found = True
                        break
                if not found and active_players:
                    self.current_player_index = active_players[0]
    
    def get_current_player(self) -> Optional[Player]:
        """获取当前行动的玩家"""
        if 0 <= self.current_player_index < len(self.players):
            current_player = self.players[self.current_player_index]
            # 如果当前玩家无法行动，自动跳到下一个可以行动的玩家
            if not current_player.can_act():
                self._move_to_next_active_player()
                if 0 <= self.current_player_index < len(self.players):
                    return self.players[self.current_player_index]
            else:
                return current_player
        return None
    
    def get_valid_actions(self, player: Player) -> List[PlayerAction]:
        """
        获取玩家的有效动作
        
        Args:
            player: 玩家
            
        Returns:
            有效动作列表
        """
        if not player.can_act():
            return []
        
        # 弃牌总是可用的（除非玩家已经弃牌或坐出）
        actions = [PlayerAction.FOLD]
        
        # 检查是否可以过牌
        if player.current_bet == self.current_bet:
            actions.append(PlayerAction.CHECK)
        else:
            # 可以跟注
            call_amount = self.current_bet - player.current_bet
            if call_amount <= player.chips:
                actions.append(PlayerAction.CALL)
        
        # 检查是否可以加注
        min_raise_amount = self.current_bet + self.min_raise
        if player.chips >= min_raise_amount - player.current_bet:
            actions.append(PlayerAction.RAISE)
        
        # 总是可以全押
        if player.chips > 0:
            actions.append(PlayerAction.ALL_IN)
        
        return actions
    
    def player_action(self, player: Player, action: PlayerAction, 
                     amount: int = 0) -> bool:
        """
        处理玩家动作
        
        Args:
            player: 玩家
            action: 动作
            amount: 金额 (用于加注)
            
        Returns:
            是否成功执行动作
        """
        if not player.can_act() or player != self.get_current_player():
            return False
        
        valid_actions = self.get_valid_actions(player)
        if action not in valid_actions:
            return False
        
        if action == PlayerAction.FOLD:
            player.fold()
        
        elif action == PlayerAction.CHECK:
            if player.current_bet != self.current_bet:
                return False
            player.last_action = PlayerAction.CHECK
        
        elif action == PlayerAction.CALL:
            call_amount = self.current_bet - player.current_bet
            actual_amount = player.call(self.current_bet)
            self.pot.add_bet(player, actual_amount)
        
        elif action == PlayerAction.RAISE:
            if amount < self.current_bet + self.min_raise:
                return False
            
            bet_amount = amount - player.current_bet
            actual_amount = player.raise_bet(amount)
            self.pot.add_bet(player, actual_amount)
            
            # 更新当前下注和最小加注
            self.current_bet = player.current_bet
            self.min_raise = amount - (self.current_bet - actual_amount)
            self.last_raiser_index = self.current_player_index
        
        elif action == PlayerAction.ALL_IN:
            actual_amount = player.all_in()
            self.pot.add_bet(player, actual_amount)
            
            # 如果全押金额超过当前下注，更新下注信息
            if player.current_bet > self.current_bet:
                old_bet = self.current_bet
                self.current_bet = player.current_bet
                self.min_raise = player.current_bet - old_bet
                self.last_raiser_index = self.current_player_index
        
        # 移动到下一个玩家
        self._next_player()
        
        # 检查是否只剩一个玩家在手牌中
        players_in_hand = [p for p in self.players if p.is_in_hand()]
        if len(players_in_hand) <= 1:
            self._handle_single_winner()
            return True
        
        # 检查是否需要进入下一阶段
        if self._is_betting_round_complete():
            self._advance_to_next_phase()
        
        return True
    
    def _move_to_next_active_player(self):
        """移动到下一个可以行动的玩家（不检查下注轮完成）"""
        active_players = [i for i, p in enumerate(self.players) 
                         if p.can_act()]
        
        if not active_players:
            return
        
        # 从当前玩家位置开始，顺时针找下一个可以行动的玩家
        start_pos = self.current_player_index
        for i in range(1, len(self.players) + 1):  # +1 确保检查所有玩家
            next_pos = (start_pos + i) % len(self.players)
            if next_pos in active_players:
                self.current_player_index = next_pos
                return
        
        # 如果没找到，设置为第一个活跃玩家
        if active_players:
            self.current_player_index = active_players[0]

    def _next_player(self):
        """移动到下一个可以行动的玩家"""
        self._move_to_next_active_player()
    
    def _is_betting_round_complete(self) -> bool:
        """检查当前下注轮是否完成"""
        active_players = [p for p in self.players if p.can_act()]
        all_in_players = [p for p in self.players if p.status == PlayerStatus.ALL_IN]
        
        if len(active_players) <= 1:
            return True
        
        # 检查所有活跃玩家是否都已行动
        for player in active_players:
            if player.last_action is None:
                return False
        
        # 检查所有在手牌中的玩家下注是否相等（除了全押玩家）
        in_hand_players = [p for p in self.players if p.is_in_hand()]
        if len(in_hand_players) <= 1:
            return True
            
        max_bet = max(p.current_bet for p in in_hand_players)
        
        for player in in_hand_players:
            # 全押玩家可以下注少于最高下注
            if player.status == PlayerStatus.ALL_IN:
                continue
            # 活跃玩家必须匹配最高下注
            if player.current_bet != max_bet:
                return False
        
        return True
    
    def _advance_to_next_phase(self):
        """进入下一个游戏阶段"""
        # 重置玩家下注轮状态
        for player in self.players:
            player.new_betting_round()
        
        self.current_bet = 0
        self.min_raise = self.big_blind
        
        if self.phase == GamePhase.PRE_FLOP:
            self._deal_flop()
            self.phase = GamePhase.FLOP
        elif self.phase == GamePhase.FLOP:
            self._deal_turn()
            self.phase = GamePhase.TURN
        elif self.phase == GamePhase.TURN:
            self._deal_river()
            self.phase = GamePhase.RIVER
        elif self.phase == GamePhase.RIVER:
            self._showdown()
            # _showdown() 内部已经设置了 GamePhase.HAND_COMPLETE，不需要再设置
        
        # 设置下一轮的第一个行动玩家
        if self.phase in [GamePhase.FLOP, GamePhase.TURN, GamePhase.RIVER]:
            self._set_first_player_to_act()
    
    def _deal_flop(self):
        """发翻牌 (3张公共牌)"""
        # 烧掉一张牌
        self.deck.deal_card()
        # 发3张公共牌
        self.community_cards.extend(self.deck.deal_cards(3))
    
    def _deal_turn(self):
        """发转牌 (第4张公共牌)"""
        # 烧掉一张牌
        self.deck.deal_card()
        # 发1张公共牌
        self.community_cards.extend(self.deck.deal_cards(1))
    
    def _deal_river(self):
        """发河牌 (第5张公共牌)"""
        # 烧掉一张牌
        self.deck.deal_card()
        # 发1张公共牌
        self.community_cards.extend(self.deck.deal_cards(1))
    
    def _showdown(self):
        """摊牌阶段"""
        active_players = [p for p in self.players if p.is_in_hand()]
        
        if len(active_players) == 0:
            # 所有玩家都弃牌了，奖池归最后一个弃牌的玩家
            # 这种情况在德州扑克中通常不会发生，但为了代码健壮性处理
            self.phase = GamePhase.HAND_COMPLETE
            return
        elif len(active_players) == 1:
            # 只有一个玩家，直接获胜
            winner = active_players[0]
            winner.win_chips(self.pot.get_total_pot())
            self.phase = GamePhase.HAND_COMPLETE
            return
        
        # 评估每个玩家的牌型
        player_hands = {}
        for player in active_players:
            all_cards = player.hole_cards + self.community_cards
            hand_result = HandEvaluator.evaluate_hand(all_cards)
            player_hands[player] = hand_result
        
        # 找出获胜者并分配奖金
        winners = self._determine_winners(player_hands)
        
        # 简化奖金分配：平分奖池给获胜者
        if winners:
            total_pot = self.pot.get_total_pot()
            amount_per_winner = total_pot // len(winners)
            remainder = total_pot % len(winners)
            
            for i, winner in enumerate(winners):
                amount = amount_per_winner
                # 余数给前几个获胜者
                if i < remainder:
                    amount += 1
                winner.win_chips(amount)
        
        self.phase = GamePhase.HAND_COMPLETE
    
    def _handle_single_winner(self):
        """处理只有一个玩家剩余的情况"""
        players_in_hand = [p for p in self.players if p.is_in_hand()]
        if len(players_in_hand) == 1:
            winner = players_in_hand[0]
            winner.win_chips(self.pot.get_total_pot())
        # 无论是否有获胜者，都结束这手牌
        self.phase = GamePhase.HAND_COMPLETE
    
    def _determine_winners(self, player_hands: Dict[Player, HandResult]) -> List[Player]:
        """
        确定获胜者
        
        Args:
            player_hands: 玩家手牌字典
            
        Returns:
            获胜者列表
        """
        if not player_hands:
            return []
        
        # 找到最好的牌型
        best_hand = max(player_hands.values())
        
        # 找到所有拥有最好牌型的玩家
        winners = [player for player, hand in player_hands.items() 
                  if hand == best_hand]
        
        return winners
    
    def get_game_state(self) -> Dict:
        """获取游戏状态信息"""
        return {
            'phase': self.phase.value,
            'hand_number': self.hand_number,
            'community_cards': [str(card) for card in self.community_cards],
            'pot_size': self.pot.get_total_pot(),
            'current_bet': self.current_bet,
            'dealer_position': self.dealer_position,
            'current_player': self.get_current_player().name if self.get_current_player() else None,
            'players': [
                {
                    'name': p.name,
                    'chips': p.chips,
                    'status': p.status.value,
                    'current_bet': p.current_bet,
                    'hole_cards': [str(card) for card in p.hole_cards] if p.hole_cards else []
                }
                for p in self.players
            ]
        }
    
    def is_hand_complete(self) -> bool:
        """检查当前手牌是否完成"""
        return self.phase == GamePhase.HAND_COMPLETE


if __name__ == "__main__":
    # 测试代码
    game = Game()
    
    # 添加玩家
    players = [
        Player("Alice", 1000, 0),
        Player("Bob", 1000, 1),
        Player("Charlie", 1000, 2)
    ]
    
    for player in players:
        game.add_player(player)
    
    print("游戏初始化完成")
    print(f"玩家数量: {len(game.players)}")
    
    # 开始新手牌
    if game.can_start_game():
        game.start_new_hand()
        print(f"\n开始第 {game.hand_number} 手牌")
        print(f"游戏阶段: {game.phase.value}")
        print(f"奖池: {game.pot.get_total_pot()}")
        print(f"当前下注: {game.current_bet}")
        print(f"当前玩家: {game.get_current_player().name}")
        
        # 显示玩家状态
        for player in game.players:
            print(f"{player.name}: 筹码={player.chips}, 当前下注={player.current_bet}")