"""
牌型评估器实现
Hand evaluator for Texas Hold'em poker game
"""

from typing import List, Tuple, Dict
from enum import Enum
from .card import Card, Rank, Suit
from collections import Counter


class HandRank(Enum):
    """牌型等级枚举 (数值越大等级越高)"""
    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10
    
    @property
    def name_zh(self) -> str:
        """返回中文名称"""
        names = {
            1: "高牌", 2: "一对", 3: "两对", 4: "三条", 5: "顺子",
            6: "同花", 7: "葫芦", 8: "四条", 9: "同花顺", 10: "皇家同花顺"
        }
        return names[self.value]


class HandResult:
    """牌型结果类"""
    
    def __init__(self, hand_rank: HandRank, cards: List[Card], 
                 rank_values: List[int], description: str = ""):
        """
        初始化牌型结果
        
        Args:
            hand_rank: 牌型等级
            cards: 组成牌型的5张牌
            rank_values: 用于比较的数值列表 (按重要性排序)
            description: 牌型描述
        """
        self.hand_rank = hand_rank
        self.cards = cards
        self.rank_values = rank_values
        self.description = description or hand_rank.name_zh
    
    def __lt__(self, other) -> bool:
        """比较牌型大小"""
        if not isinstance(other, HandResult):
            return NotImplemented
        
        # 首先比较牌型等级
        if self.hand_rank.value != other.hand_rank.value:
            return self.hand_rank.value < other.hand_rank.value
        
        # 牌型相同时比较具体数值
        for i, (a, b) in enumerate(zip(self.rank_values, other.rank_values)):
            if a != b:
                return a < b
        
        return False  # 完全相同
    
    def __eq__(self, other) -> bool:
        """判断牌型是否相等"""
        if not isinstance(other, HandResult):
            return False
        return (self.hand_rank == other.hand_rank and 
                self.rank_values == other.rank_values)
    
    def __str__(self) -> str:
        """返回牌型描述"""
        cards_str = " ".join(str(card) for card in self.cards)
        return f"{self.description}: {cards_str}"


class HandEvaluator:
    """牌型评估器"""
    
    @staticmethod
    def evaluate_hand(cards: List[Card]) -> HandResult:
        """
        评估7张牌中的最佳5张牌组合
        
        Args:
            cards: 7张牌 (2张底牌 + 5张公共牌)
            
        Returns:
            最佳牌型结果
        """
        if len(cards) != 7:
            raise ValueError("德州扑克评估需要7张牌")
        
        best_hand = None
        
        # 从7张牌中选择5张牌的所有组合 (C(7,5) = 21种)
        from itertools import combinations
        for five_cards in combinations(cards, 5):
            hand_result = HandEvaluator._evaluate_five_cards(list(five_cards))
            if best_hand is None or hand_result > best_hand:
                best_hand = hand_result
        
        return best_hand
    
    @staticmethod
    def _evaluate_five_cards(cards: List[Card]) -> HandResult:
        """
        评估5张牌的牌型
        
        Args:
            cards: 5张牌
            
        Returns:
            牌型结果
        """
        if len(cards) != 5:
            raise ValueError("评估需要正好5张牌")
        
        # 按点数排序
        sorted_cards = sorted(cards, key=lambda x: x.rank.value, reverse=True)
        
        # 检查各种牌型
        if HandEvaluator._is_royal_flush(sorted_cards):
            return HandResult(HandRank.ROYAL_FLUSH, sorted_cards, [14])
        
        if HandEvaluator._is_straight_flush(sorted_cards):
            high_card = HandEvaluator._get_straight_high_card(sorted_cards)
            return HandResult(HandRank.STRAIGHT_FLUSH, sorted_cards, [high_card])
        
        four_kind_result = HandEvaluator._check_four_of_a_kind(sorted_cards)
        if four_kind_result:
            return four_kind_result
        
        full_house_result = HandEvaluator._check_full_house(sorted_cards)
        if full_house_result:
            return full_house_result
        
        if HandEvaluator._is_flush(sorted_cards):
            values = [card.rank.value for card in sorted_cards]
            return HandResult(HandRank.FLUSH, sorted_cards, values)
        
        if HandEvaluator._is_straight(sorted_cards):
            high_card = HandEvaluator._get_straight_high_card(sorted_cards)
            return HandResult(HandRank.STRAIGHT, sorted_cards, [high_card])
        
        three_kind_result = HandEvaluator._check_three_of_a_kind(sorted_cards)
        if three_kind_result:
            return three_kind_result
        
        two_pair_result = HandEvaluator._check_two_pair(sorted_cards)
        if two_pair_result:
            return two_pair_result
        
        one_pair_result = HandEvaluator._check_one_pair(sorted_cards)
        if one_pair_result:
            return one_pair_result
        
        # 高牌
        values = [card.rank.value for card in sorted_cards]
        return HandResult(HandRank.HIGH_CARD, sorted_cards, values)
    
    @staticmethod
    def _is_royal_flush(cards: List[Card]) -> bool:
        """检查是否为皇家同花顺"""
        if not HandEvaluator._is_flush(cards):
            return False
        
        ranks = [card.rank.value for card in cards]
        return sorted(ranks) == [10, 11, 12, 13, 14]
    
    @staticmethod
    def _is_straight_flush(cards: List[Card]) -> bool:
        """检查是否为同花顺"""
        return HandEvaluator._is_flush(cards) and HandEvaluator._is_straight(cards)
    
    @staticmethod
    def _is_flush(cards: List[Card]) -> bool:
        """检查是否为同花"""
        suits = [card.suit for card in cards]
        return len(set(suits)) == 1
    
    @staticmethod
    def _is_straight(cards: List[Card]) -> bool:
        """检查是否为顺子"""
        ranks = sorted([card.rank.value for card in cards])
        
        # 检查常规顺子
        if ranks == list(range(ranks[0], ranks[0] + 5)):
            return True
        
        # 检查A-2-3-4-5顺子
        if ranks == [2, 3, 4, 5, 14]:
            return True
        
        return False
    
    @staticmethod
    def _get_straight_high_card(cards: List[Card]) -> int:
        """获取顺子的最高牌"""
        ranks = sorted([card.rank.value for card in cards])
        
        # A-2-3-4-5顺子，A算作1
        if ranks == [2, 3, 4, 5, 14]:
            return 5
        
        return ranks[-1]
    
    @staticmethod
    def _check_four_of_a_kind(cards: List[Card]) -> HandResult:
        """检查四条"""
        rank_counts = Counter(card.rank.value for card in cards)
        
        for rank, count in rank_counts.items():
            if count == 4:
                kicker = [r for r, c in rank_counts.items() if c == 1][0]
                return HandResult(HandRank.FOUR_OF_A_KIND, cards, [rank, kicker])
        
        return None
    
    @staticmethod
    def _check_full_house(cards: List[Card]) -> HandResult:
        """检查葫芦"""
        rank_counts = Counter(card.rank.value for card in cards)
        
        three_rank = None
        pair_rank = None
        
        for rank, count in rank_counts.items():
            if count == 3:
                three_rank = rank
            elif count == 2:
                pair_rank = rank
        
        if three_rank and pair_rank:
            return HandResult(HandRank.FULL_HOUSE, cards, [three_rank, pair_rank])
        
        return None
    
    @staticmethod
    def _check_three_of_a_kind(cards: List[Card]) -> HandResult:
        """检查三条"""
        rank_counts = Counter(card.rank.value for card in cards)
        
        for rank, count in rank_counts.items():
            if count == 3:
                kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
                return HandResult(HandRank.THREE_OF_A_KIND, cards, [rank] + kickers)
        
        return None
    
    @staticmethod
    def _check_two_pair(cards: List[Card]) -> HandResult:
        """检查两对"""
        rank_counts = Counter(card.rank.value for card in cards)
        pairs = [rank for rank, count in rank_counts.items() if count == 2]
        
        if len(pairs) == 2:
            pairs.sort(reverse=True)
            kicker = [r for r, c in rank_counts.items() if c == 1][0]
            return HandResult(HandRank.TWO_PAIR, cards, pairs + [kicker])
        
        return None
    
    @staticmethod
    def _check_one_pair(cards: List[Card]) -> HandResult:
        """检查一对"""
        rank_counts = Counter(card.rank.value for card in cards)
        
        for rank, count in rank_counts.items():
            if count == 2:
                kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
                return HandResult(HandRank.ONE_PAIR, cards, [rank] + kickers)
        
        return None
    
    @staticmethod
    def compare_hands(hand1: List[Card], hand2: List[Card]) -> int:
        """
        比较两手牌的大小
        
        Args:
            hand1: 第一手牌
            hand2: 第二手牌
            
        Returns:
            1: hand1胜, -1: hand2胜, 0: 平局
        """
        result1 = HandEvaluator.evaluate_hand(hand1)
        result2 = HandEvaluator.evaluate_hand(hand2)
        
        if result1 > result2:
            return 1
        elif result1 < result2:
            return -1
        else:
            return 0


if __name__ == "__main__":
    # 测试代码
    from .card import Deck
    
    deck = Deck()
    deck.shuffle()
    
    # 发7张牌测试
    test_cards = deck.deal_cards(7)
    print(f"测试牌: {[str(card) for card in test_cards]}")
    
    result = HandEvaluator.evaluate_hand(test_cards)
    print(f"最佳牌型: {result}")
    print(f"牌型等级: {result.hand_rank.name_zh}")
    print(f"比较值: {result.rank_values}")