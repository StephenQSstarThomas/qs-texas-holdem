"""
玩家类实现
Player class for Texas Hold'em poker game
"""

from typing import List, Optional
from enum import Enum
from .card import Card


class PlayerStatus(Enum):
    """玩家状态枚举"""
    ACTIVE = "active"           # 活跃状态
    FOLDED = "folded"          # 已弃牌
    ALL_IN = "all_in"          # 全押
    SITTING_OUT = "sitting_out" # 离座


class PlayerAction(Enum):
    """玩家动作枚举"""
    FOLD = "fold"       # 弃牌
    CHECK = "check"     # 过牌
    CALL = "call"       # 跟注
    RAISE = "raise"     # 加注
    ALL_IN = "all_in"   # 全押


class Player:
    """玩家类"""
    
    def __init__(self, name: str, chips: int, position: int = 0):
        """
        初始化玩家
        
        Args:
            name: 玩家姓名
            chips: 初始筹码数量
            position: 座位位置 (0-5)
        """
        self.name = name
        self.chips = chips
        self.position = position
        
        # 游戏状态
        self.hole_cards: List[Card] = []  # 底牌
        self.status = PlayerStatus.SITTING_OUT
        self.current_bet = 0              # 当前轮次下注金额
        self.total_bet = 0                # 本手牌总下注金额
        self.last_action: Optional[PlayerAction] = None
        
        # 统计数据
        self.hands_played = 0
        self.hands_won = 0
        self.total_winnings = 0
    
    def sit_in(self):
        """玩家入座参与游戏"""
        if self.chips > 0:
            self.status = PlayerStatus.ACTIVE
    
    def sit_out(self):
        """玩家离座"""
        self.status = PlayerStatus.SITTING_OUT
        self.fold()
    
    def deal_hole_cards(self, cards: List[Card]):
        """
        发底牌给玩家
        
        Args:
            cards: 两张底牌
        """
        if len(cards) != 2:
            raise ValueError("德州扑克每位玩家必须有2张底牌")
        self.hole_cards = cards
    
    def fold(self):
        """弃牌"""
        if self.status != PlayerStatus.SITTING_OUT:
            self.status = PlayerStatus.FOLDED
            self.last_action = PlayerAction.FOLD
    
    def check(self) -> bool:
        """
        过牌
        
        Returns:
            是否成功过牌
        """
        if self.current_bet == 0 and self.status == PlayerStatus.ACTIVE:
            self.last_action = PlayerAction.CHECK
            return True
        return False
    
    def call(self, amount: int) -> int:
        """
        跟注
        
        Args:
            amount: 需要跟注的金额
            
        Returns:
            实际跟注金额
        """
        if self.status != PlayerStatus.ACTIVE:
            return 0
        
        # 计算需要补足的金额
        call_amount = amount - self.current_bet
        
        if call_amount <= 0:
            return 0
        
        # 如果筹码不足，则全押
        if call_amount >= self.chips:
            actual_bet = self.chips
            self.chips = 0
            self.current_bet += actual_bet
            self.total_bet += actual_bet
            self.status = PlayerStatus.ALL_IN
            self.last_action = PlayerAction.ALL_IN
            return actual_bet
        
        # 正常跟注
        self.chips -= call_amount
        self.current_bet += call_amount
        self.total_bet += call_amount
        self.last_action = PlayerAction.CALL
        return call_amount
    
    def raise_bet(self, total_amount: int) -> int:
        """
        加注
        
        Args:
            total_amount: 本轮总下注金额
            
        Returns:
            实际加注金额
        """
        if self.status != PlayerStatus.ACTIVE:
            return 0
        
        raise_amount = total_amount - self.current_bet
        
        if raise_amount <= 0:
            return 0
        
        # 如果筹码不足，则全押
        if raise_amount >= self.chips:
            actual_bet = self.chips
            self.chips = 0
            self.current_bet += actual_bet
            self.total_bet += actual_bet
            self.status = PlayerStatus.ALL_IN
            self.last_action = PlayerAction.ALL_IN
            return actual_bet
        
        # 正常加注
        self.chips -= raise_amount
        self.current_bet += raise_amount
        self.total_bet += raise_amount
        self.last_action = PlayerAction.RAISE
        return raise_amount
    
    def all_in(self) -> int:
        """
        全押
        
        Returns:
            全押金额
        """
        if self.status != PlayerStatus.ACTIVE or self.chips == 0:
            return 0
        
        all_in_amount = self.chips
        self.chips = 0
        self.current_bet += all_in_amount
        self.total_bet += all_in_amount
        self.status = PlayerStatus.ALL_IN
        self.last_action = PlayerAction.ALL_IN
        return all_in_amount
    
    def new_betting_round(self):
        """开始新的下注轮次"""
        self.current_bet = 0
        self.last_action = None
        if self.status == PlayerStatus.FOLDED:
            return
        if self.status == PlayerStatus.ALL_IN:
            return
        if self.chips > 0:
            self.status = PlayerStatus.ACTIVE
    
    def new_hand(self):
        """开始新手牌"""
        self.hole_cards = []
        self.current_bet = 0
        self.total_bet = 0
        self.last_action = None
        if self.chips > 0:
            self.status = PlayerStatus.ACTIVE
        else:
            self.status = PlayerStatus.SITTING_OUT
    
    def win_chips(self, amount: int):
        """赢得筹码"""
        self.chips += amount
        self.total_winnings += amount
        self.hands_won += 1
    
    def post_blind(self, amount: int) -> int:
        """
        下盲注
        
        Args:
            amount: 盲注金额
            
        Returns:
            实际下注金额
        """
        if self.chips <= amount:
            # 筹码不足，全押
            actual_amount = self.chips
            self.chips = 0
            self.current_bet = actual_amount
            self.total_bet = actual_amount
            self.status = PlayerStatus.ALL_IN
            return actual_amount
        
        self.chips -= amount
        self.current_bet = amount
        self.total_bet = amount
        return amount
    
    def can_act(self) -> bool:
        """检查玩家是否可以行动"""
        return self.status == PlayerStatus.ACTIVE
    
    def is_in_hand(self) -> bool:
        """检查玩家是否还在这手牌中"""
        return self.status in [PlayerStatus.ACTIVE, PlayerStatus.ALL_IN]
    
    def get_win_rate(self) -> float:
        """计算胜率"""
        if self.hands_played == 0:
            return 0.0
        return self.hands_won / self.hands_played
    
    def __str__(self) -> str:
        """返回玩家信息字符串"""
        return f"{self.name} (筹码: {self.chips}, 状态: {self.status.value})"
    
    def __repr__(self) -> str:
        """返回玩家详细信息"""
        return f"Player(name='{self.name}', chips={self.chips}, position={self.position})"


if __name__ == "__main__":
    # 测试代码
    player = Player("Alice", 1000, 0)
    print(f"新玩家: {player}")
    
    player.sit_in()
    print(f"入座后: {player}")
    
    # 测试下注
    blind_amount = player.post_blind(50)
    print(f"下盲注 {blind_amount}, 剩余筹码: {player.chips}")
    
    # 测试跟注
    call_amount = player.call(100)
    print(f"跟注 {call_amount}, 当前下注: {player.current_bet}")
    
    # 测试加注
    raise_amount = player.raise_bet(200)
    print(f"加注 {raise_amount}, 当前下注: {player.current_bet}")
    
    print(f"最终状态: {player}")