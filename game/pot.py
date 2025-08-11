"""
奖池管理类实现
Pot management for Texas Hold'em poker game
"""

from typing import List, Dict, Tuple
from .player import Player


class SidePot:
    """边池类"""
    
    def __init__(self, amount: int, eligible_players: List[Player]):
        """
        初始化边池
        
        Args:
            amount: 边池金额
            eligible_players: 有资格争夺此边池的玩家列表
        """
        self.amount = amount
        self.eligible_players = eligible_players.copy()
    
    def __str__(self) -> str:
        """返回边池信息"""
        player_names = [p.name for p in self.eligible_players]
        return f"边池: {self.amount} 筹码 (参与者: {', '.join(player_names)})"


class Pot:
    """奖池管理类"""
    
    def __init__(self):
        """初始化奖池"""
        self.main_pot = 0
        self.side_pots: List[SidePot] = []
        self.player_contributions: Dict[Player, int] = {}
    
    def reset(self):
        """重置奖池"""
        self.main_pot = 0
        self.side_pots = []
        self.player_contributions = {}
    
    def add_bet(self, player: Player, amount: int):
        """
        添加玩家下注到奖池
        
        Args:
            player: 下注玩家
            amount: 下注金额
        """
        if player not in self.player_contributions:
            self.player_contributions[player] = 0
        
        self.player_contributions[player] += amount
        self.main_pot += amount
    
    def create_side_pots(self, players: List[Player]):
        """
        创建边池 (当有玩家全押时)
        
        Args:
            players: 参与的玩家列表
        """
        if not self.player_contributions:
            return
        
        # 清空之前的边池
        self.side_pots = []
        
        # 获取所有玩家的总下注金额并排序
        contributions = []
        for player in players:
            if player in self.player_contributions:
                contributions.append((player, self.player_contributions[player]))
        
        # 按下注金额排序
        contributions.sort(key=lambda x: x[1])
        
        previous_amount = 0
        remaining_players = players.copy()
        
        for i, (current_player, current_amount) in enumerate(contributions):
            if current_amount > previous_amount:
                # 计算这一层的边池金额
                pot_amount = (current_amount - previous_amount) * len(remaining_players)
                
                if pot_amount > 0:
                    # 创建边池
                    eligible_players = [p for p in remaining_players if p.is_in_hand()]
                    if eligible_players:
                        side_pot = SidePot(pot_amount, eligible_players)
                        self.side_pots.append(side_pot)
                
                previous_amount = current_amount
            
            # 移除已经达到上限的玩家
            if current_player in remaining_players:
                remaining_players.remove(current_player)
    
    def distribute_winnings(self, winners_by_pot: List[List[Player]]) -> Dict[Player, int]:
        """
        分配奖金
        
        Args:
            winners_by_pot: 每个奖池的获胜者列表 (主池 + 边池)
            
        Returns:
            每个玩家获得的奖金字典
        """
        winnings = {}
        
        # 分配边池 (从最小的开始)
        for i, side_pot in enumerate(self.side_pots):
            if i < len(winners_by_pot):
                pot_winners = [p for p in winners_by_pot[i] if p in side_pot.eligible_players]
                if pot_winners:
                    amount_per_winner = side_pot.amount // len(pot_winners)
                    remainder = side_pot.amount % len(pot_winners)
                    
                    for j, winner in enumerate(pot_winners):
                        if winner not in winnings:
                            winnings[winner] = 0
                        winnings[winner] += amount_per_winner
                        # 余数给前几个获胜者
                        if j < remainder:
                            winnings[winner] += 1
        
        return winnings
    
    def get_total_pot(self) -> int:
        """获取总奖池金额"""
        return self.main_pot
    
    def get_side_pot_info(self) -> List[str]:
        """获取边池信息"""
        info = []
        if self.side_pots:
            for i, side_pot in enumerate(self.side_pots):
                info.append(f"边池 {i+1}: {side_pot.amount} 筹码")
        else:
            info.append(f"主池: {self.main_pot} 筹码")
        return info
    
    def has_side_pots(self) -> bool:
        """检查是否有边池"""
        return len(self.side_pots) > 0
    
    def get_eligible_players_for_pot(self, pot_index: int) -> List[Player]:
        """
        获取指定奖池的有资格玩家
        
        Args:
            pot_index: 奖池索引 (0为主池)
            
        Returns:
            有资格的玩家列表
        """
        if pot_index < len(self.side_pots):
            return self.side_pots[pot_index].eligible_players.copy()
        return []
    
    def __str__(self) -> str:
        """返回奖池信息字符串"""
        if self.side_pots:
            info = [f"总奖池: {self.main_pot} 筹码"]
            for i, side_pot in enumerate(self.side_pots):
                info.append(f"  {side_pot}")
            return "\n".join(info)
        else:
            return f"奖池: {self.main_pot} 筹码"


if __name__ == "__main__":
    # 测试代码
    from .player import Player
    
    # 创建测试玩家
    players = [
        Player("Alice", 1000, 0),
        Player("Bob", 500, 1),
        Player("Charlie", 200, 2)
    ]
    
    # 模拟下注
    pot = Pot()
    
    # 第一轮下注
    pot.add_bet(players[0], 100)  # Alice 下注 100
    pot.add_bet(players[1], 100)  # Bob 下注 100
    pot.add_bet(players[2], 100)  # Charlie 下注 100
    
    print(f"第一轮下注后: {pot}")
    
    # 第二轮，Charlie 全押
    pot.add_bet(players[0], 100)  # Alice 再下注 100
    pot.add_bet(players[1], 100)  # Bob 再下注 100
    pot.add_bet(players[2], 100)  # Charlie 全押剩余 100
    
    print(f"第二轮下注后: {pot}")
    
    # 创建边池
    pot.create_side_pots(players)
    print(f"\n创建边池后:")
    print(pot)