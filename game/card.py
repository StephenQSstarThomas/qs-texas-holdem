"""
扑克牌相关类实现
Card and Deck classes for Texas Hold'em poker game
"""

import random
from enum import Enum
from typing import List, Optional


class Suit(Enum):
    """扑克牌花色枚举"""
    HEARTS = "♥"      # 红桃
    DIAMONDS = "♦"    # 方块  
    CLUBS = "♣"       # 梅花
    SPADES = "♠"      # 黑桃


class Rank(Enum):
    """扑克牌点数枚举"""
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14
    
    @property
    def symbol(self) -> str:
        """返回牌面符号"""
        symbols = {
            2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 
            10: "10", 11: "J", 12: "Q", 13: "K", 14: "A"
        }
        return symbols[self.value]


class Card:
    """扑克牌类"""
    
    def __init__(self, suit: Suit, rank: Rank):
        """
        初始化扑克牌
        
        Args:
            suit: 花色
            rank: 点数
        """
        self.suit = suit
        self.rank = rank
    
    def __str__(self) -> str:
        """返回牌的字符串表示"""
        return f"{self.rank.symbol}{self.suit.value}"
    
    def __repr__(self) -> str:
        """返回牌的详细表示"""
        return f"Card({self.suit.name}, {self.rank.name})"
    
    def __eq__(self, other) -> bool:
        """比较两张牌是否相等"""
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank
    
    def __lt__(self, other) -> bool:
        """比较牌的大小"""
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank.value < other.rank.value
    
    def __hash__(self) -> int:
        """返回牌的哈希值"""
        return hash((self.suit, self.rank))


class Deck:
    """牌堆类"""
    
    def __init__(self):
        """初始化标准52张牌的牌堆"""
        self.cards: List[Card] = []
        self.reset()
    
    def reset(self):
        """重置牌堆为标准52张牌"""
        self.cards = []
        for suit in Suit:
            for rank in Rank:
                self.cards.append(Card(suit, rank))
    
    def shuffle(self):
        """洗牌 - 使用Fisher-Yates算法"""
        random.shuffle(self.cards)
    
    def deal_card(self) -> Optional[Card]:
        """
        发一张牌
        
        Returns:
            发出的牌，如果牌堆为空则返回None
        """
        if not self.cards:
            return None
        return self.cards.pop()
    
    def deal_cards(self, count: int) -> List[Card]:
        """
        发多张牌
        
        Args:
            count: 要发的牌数
            
        Returns:
            发出的牌列表
        """
        dealt_cards = []
        for _ in range(count):
            card = self.deal_card()
            if card is None:
                break
            dealt_cards.append(card)
        return dealt_cards
    
    def cards_remaining(self) -> int:
        """返回牌堆中剩余的牌数"""
        return len(self.cards)
    
    def is_empty(self) -> bool:
        """检查牌堆是否为空"""
        return len(self.cards) == 0
    
    def __len__(self) -> int:
        """返回牌堆中的牌数"""
        return len(self.cards)
    
    def __str__(self) -> str:
        """返回牌堆的字符串表示"""
        return f"Deck with {len(self.cards)} cards"


if __name__ == "__main__":
    # 测试代码
    deck = Deck()
    print(f"新牌堆: {deck}")
    
    deck.shuffle()
    print("洗牌完成")
    
    # 发5张牌测试
    hand = deck.deal_cards(5)
    print(f"发出的5张牌: {[str(card) for card in hand]}")
    print(f"剩余牌数: {deck.cards_remaining()}")