from typing import Optional, List, Tuple
import os
import math
from PyQt5.QtCore import Qt, QRectF, QPointF, QTimer, QRect
from PyQt5.QtGui import (QPainter, QBrush, QPen, QColor, QFont, QPixmap, 
                         QLinearGradient, QRadialGradient, QPainterPath,
                         QFontDatabase, QPolygonF, QTransform)
from PyQt5.QtWidgets import QWidget, QGraphicsDropShadowEffect

from game import Game, Player, PlayerStatus


class GameTableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.game: Optional[Game] = None
        self.setMinimumSize(2000, 1300)
        self.setAutoFillBackground(True)
        
        # 动画相关
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._animate)
        self.animation_timer.start(50)
        self.glow_phase = 0
        
        # 加载资源
        self._icons = self._load_icons()
        self._init_colors()
        self._init_fonts()
        # 全局缩放系数，整体放大约4倍
        self.UI_SCALE = 2.5
        
    def _init_colors(self):
        """初始化优雅配色方案"""
        self.colors = {
            # 主色调 - 深邃奢华
            'table_dark': QColor(25, 35, 45),
            'table_light': QColor(35, 48, 62),
            'table_border': QColor(15, 20, 25),
            'table_felt': QColor(28, 42, 56),  # 牌桌毡面
            
            # 金色系 - 尊贵感
            'gold': QColor(255, 215, 0),
            'gold_light': QColor(255, 235, 100),
            'gold_dark': QColor(218, 165, 32),
            
            # 卡牌色
            'card_bg': QColor(252, 252, 250),
            'card_shadow': QColor(0, 0, 0, 80),
            'red_suit': QColor(220, 20, 60),
            'black_suit': QColor(20, 20, 20),
            
            # 玩家座位
            'seat_active': QColor(45, 55, 68, 240),
            'seat_inactive': QColor(30, 35, 45, 200),
            'seat_folded': QColor(25, 28, 35, 160),
            'seat_highlight': QColor(255, 215, 0, 60),
            
            # 文字
            'text_primary': QColor(245, 245, 245),
            'text_secondary': QColor(180, 185, 190),
            'text_disabled': QColor(120, 125, 130),
            
            # 特效
            'glow': QColor(100, 200, 255, 60),
            'highlight': QColor(255, 245, 200, 40)
        }
        
    def _init_fonts(self):
        """初始化字体系统"""
        base_size = min(self.width() / 150, self.height() / 100)
        scale = 2.0
        self.fonts = {
            'title': self._create_font(int(18*scale), True),
            'subtitle': self._create_font(int(14*scale), True),
            'body': self._create_font(int(12*scale), False),
            'small': self._create_font(int(10*scale), False),
            'card': self._create_font(int(24*scale), True),
            'pot': self._create_font(int(26*scale), True),
            'chips': self._create_font(int(16*scale), True)
        }
        
    def _create_font(self, size: int, bold: bool) -> QFont:
        """创建优雅字体"""
        font = QFont("Segoe UI", size)
        if bold:
            font.setWeight(QFont.Bold)
        font.setStyleStrategy(QFont.PreferAntialias)
        return font
        
    def resizeEvent(self, event):
        """窗口大小改变时重新初始化字体"""
        super().resizeEvent(event)
        self._init_fonts()
        
    def attach_game(self, game: Game):
        self.game = game
        self.update()
        
    def _animate(self):
        """动画更新"""
        self.glow_phase = (self.glow_phase + 0.1) % (2 * math.pi)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        self._draw_background(painter)
        self._draw_table(painter)
        
        if self.game:
            self._draw_players(painter)
            self._draw_community_cards(painter)
            self._draw_pot(painter)
            self._draw_game_status(painter)
            
    def _draw_background(self, p: QPainter):
        """绘制优雅背景"""
        rect = self.rect()
        
        # 深色渐变背景
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0.0, QColor(15, 20, 28))
        grad.setColorAt(0.3, QColor(20, 28, 38))
        grad.setColorAt(0.7, QColor(20, 28, 38))
        grad.setColorAt(1.0, QColor(15, 20, 28))
        p.fillRect(rect, QBrush(grad))
        
        # 添加微妙的点状纹理
        p.setPen(QPen(QColor(255, 255, 255, 3), 1))
        for x in range(20, rect.width(), 40):
            for y in range(20, rect.height(), 40):
                p.drawPoint(x, y)
                
    def _draw_table(self, p: QPainter):
        """绘制精致牌桌"""
        # 计算牌桌区域
        margin = min(self.width() * 0.05, self.height() * 0.05)
        rect = QRectF(self.rect()).adjusted(float(margin), float(margin), float(-margin), float(-margin))
        
        # 外发光效果
        glow_size = 15
        glow_rect = rect.adjusted(-glow_size, -glow_size, glow_size, glow_size)
        glow_grad = QRadialGradient(glow_rect.center(), max(glow_rect.width(), glow_rect.height()) / 2)
        glow_intensity = int(20 + 10 * math.sin(self.glow_phase))
        glow_grad.setColorAt(0.85, QColor(100, 150, 200, glow_intensity))
        glow_grad.setColorAt(1.0, QColor(100, 150, 200, 0))
        p.setBrush(QBrush(glow_grad))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(glow_rect, 80, 80)
        
        # 牌桌阴影
        shadow_rect = rect.adjusted(5, 5, 5, 5)
        p.setBrush(QBrush(QColor(0, 0, 0, 60)))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(shadow_rect, 75, 75)
        
        # 主牌桌
        table_grad = QRadialGradient(rect.center(), max(rect.width(), rect.height()) / 2)
        table_grad.setColorAt(0.0, self.colors['table_felt'])
        table_grad.setColorAt(0.6, self.colors['table_dark'])
        table_grad.setColorAt(1.0, QColor(15, 22, 30))
        
        p.setBrush(QBrush(table_grad))
        p.setPen(QPen(self.colors['gold_dark'], 2))
        p.drawRoundedRect(rect, 75, 75)
        
        # 内边框装饰（双线）
        inner_rect = rect.adjusted(12, 12, -12, -12)
        p.setPen(QPen(QColor(218, 165, 32, 80), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(inner_rect, 70, 70)
        
        inner_rect2 = rect.adjusted(18, 18, -18, -18)
        p.setPen(QPen(QColor(218, 165, 32, 40), 1, Qt.DotLine))
        p.drawRoundedRect(inner_rect2, 68, 68)
        
        # 中心装饰
        self._draw_center_decoration(p, rect)
        
    def _draw_center_decoration(self, p: QPainter, table_rect: QRectF):
        """绘制牌桌中心装饰"""
        cx, cy = table_rect.center().x(), table_rect.center().y()
        
        # 中心圆形装饰
        center_size = min(table_rect.width(), table_rect.height()) * 0.15
        center_rect = QRectF(cx - center_size/2, cy - center_size/2, center_size, center_size)
        
        # 渐变光晕
        center_grad = QRadialGradient(center_rect.center(), center_size/2)
        center_grad.setColorAt(0, QColor(255, 215, 0, 20))
        center_grad.setColorAt(0.5, QColor(255, 215, 0, 10))
        center_grad.setColorAt(1, QColor(255, 215, 0, 0))
        
        p.setBrush(QBrush(center_grad))
        p.setPen(QPen(QColor(218, 165, 32, 60), 1))
        p.drawEllipse(center_rect)
        
        # 游戏标题
        p.setPen(self.colors['text_secondary'])
        p.setFont(self.fonts['small'])
        p.drawText(center_rect, Qt.AlignCenter, "德州扑克")
        
    def _seat_positions(self, n: int) -> List[Tuple[QPointF, float]]:
        """计算座位位置 - 优化分布"""
        margin = min(self.width() * 0.05, self.height() * 0.05)
        table_rect = QRectF(self.rect()).adjusted(float(margin), float(margin), float(-margin), float(-margin))
        
        cx = table_rect.center().x()
        cy = table_rect.center().y()
        
        # 椭圆参数
        rx = table_rect.width() * 0.42
        ry = table_rect.height() * 0.38
        
        positions = []
        
        # 优化座位分布角度
        if n == 2:
            # 对坐
            angles = [math.pi * 0.5, math.pi * 1.5]
        elif n == 3:
            # 三角形分布
            angles = [math.pi * 0.5, math.pi * 1.1, math.pi * 1.9]
        elif n == 4:
            # 四角分布
            angles = [math.pi * 0.5, math.pi * 0.9, math.pi * 1.1, math.pi * 1.5]
        else:
            # 均匀分布
            angles = [math.pi * (0.5 + 2 * i / n) for i in range(n)]
        
        for angle in angles:
            x = cx + rx * math.cos(angle)
            y = cy + ry * math.sin(angle)
            # 座位朝向中心
            face_angle = math.atan2(cy - y, cx - x)
            positions.append((QPointF(x, y), face_angle))
            
        return positions
        
    def _draw_players(self, p: QPainter):
        """绘制玩家座位"""
        if not self.game:
            return
            
        players = self.game.players
        if not players:
            return
            
        positions = self._seat_positions(len(players))
        current_index = getattr(self.game, 'current_player_index', -1)
        dealer_index = getattr(self.game, 'dealer_position', -1)
        
        for i, player in enumerate(players):
            if i < len(positions):
                pos, angle = positions[i]
                self._draw_player_seat(p, player, pos, i == current_index, i == dealer_index, i)
                
    def _draw_player_seat(self, p: QPainter, player: Player, pos: QPointF, is_current: bool, is_dealer: bool, index: int):
        """绘制单个玩家座位 - 改进版"""
        # 座位尺寸 - 增加宽度，减少高度避免拥挤
        w = min(self.width() * 0.18, 360) * (self.UI_SCALE / 2.5)
        h = min(self.height() * 0.11, 160) * (self.UI_SCALE / 2.5)
        seat_rect = QRectF(pos.x() - w/2, pos.y() - h/2, w, h)
        
        # 当前玩家高亮背景
        if is_current and player.can_act():
            highlight_rect = seat_rect.adjusted(-8, -8, 8, 8)
            highlight_grad = QRadialGradient(highlight_rect.center(), highlight_rect.width()/2)
            alpha = int(80 + 40 * math.sin(self.glow_phase))
            highlight_grad.setColorAt(0, QColor(255, 215, 0, alpha))
            highlight_grad.setColorAt(1, QColor(255, 215, 0, 0))
            p.setBrush(QBrush(highlight_grad))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(highlight_rect, 25, 25)
        
        # 座位阴影
        shadow_rect = seat_rect.adjusted(2, 2, 2, 2)
        p.setBrush(QBrush(QColor(0, 0, 0, 50)))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(shadow_rect, 15, 15)
        
        # 座位背景
        if player.status == PlayerStatus.FOLDED:
            bg_color = self.colors['seat_folded']
        elif is_current and player.can_act():
            bg_color = self.colors['seat_active']
        else:
            bg_color = self.colors['seat_inactive']
            
        seat_grad = QLinearGradient(seat_rect.topLeft(), seat_rect.bottomRight())
        seat_grad.setColorAt(0, bg_color.lighter(115))
        seat_grad.setColorAt(1, bg_color)
        p.setBrush(QBrush(seat_grad))
        
        # 边框
        if is_current and player.can_act():
            p.setPen(QPen(self.colors['gold'], 2))
        else:
            p.setPen(QPen(QColor(60, 60, 60), 1))
            
        p.drawRoundedRect(seat_rect, 15, 15)
        
        # 绘制座位内容
        self._draw_seat_content(p, player, seat_rect, is_current)
        
        # 庄家标识 - 调整位置到座位外右上角
        if is_dealer:
            self._draw_dealer_button_outside(p, seat_rect)
            
    def _draw_seat_content(self, p: QPainter, player: Player, rect: QRectF, is_current: bool):
        """绘制座位内容 - 优化布局避免重叠"""
        padding = 10
        content_rect = rect.adjusted(padding, padding, -padding, -padding)
        
        # 计算布局尺寸
        total_height = content_rect.height()
        
        # 分配空间：上部信息区60%，下部手牌区40%
        info_height = total_height * 0.6
        cards_height = total_height * 0.4
        
        # === 上部信息区布局 ===
        info_rect = QRectF(content_rect.left(), content_rect.top(), 
                          content_rect.width(), info_height)
        
        # 头像尺寸（左侧）
        avatar_size = min(info_height * 0.9, 80) * (self.UI_SCALE / 2.5)
        avatar_rect = QRectF(
            info_rect.left(),
            info_rect.top() + (info_height - avatar_size) / 2,  # 垂直居中
            avatar_size,
            avatar_size
        )
        
        # 绘制头像
        self._draw_avatar(p, avatar_rect, player.name)
        
        # 文字信息区域（右侧）
        text_left = avatar_rect.right() + 10  # 增加间距
        text_width = max(160.0, info_rect.width() - avatar_size - 16)
        
        # 玩家名字（上半部分）
        name_rect = QRectF(
            text_left,
            info_rect.top() + 2,
            text_width,
            info_height * 0.45
        )
        p.setFont(self.fonts['subtitle'])
        text_color = self.colors['text_primary'] if player.status != PlayerStatus.FOLDED else self.colors['text_disabled']
        p.setPen(text_color)
        
        # 确保名字不会太长
        display_name = player.name[:10] + "..." if len(player.name) > 10 else player.name
        p.drawText(name_rect, Qt.AlignLeft | Qt.AlignVCenter, display_name)
        
        # 筹码显示（下半部分）
        chips_rect = QRectF(
            text_left,
            name_rect.bottom(),
            text_width,
            info_height * 0.45
        )
        self._draw_chips_amount(p, chips_rect, player.chips)
        
        # === 下部手牌区域 ===
        if player.hole_cards:
            # 手牌区域留出顶部间距
            cards_rect = QRectF(
                content_rect.left(),
                content_rect.top() + info_height + 5,  # 留出5像素间距
                content_rect.width(),
                cards_height - 5
            )
            self._draw_hole_cards(p, cards_rect, player.hole_cards, is_current)
            
    def _draw_chips_amount(self, p: QPainter, rect: QRectF, chips: int):
        """绘制筹码数量 - 优化布局避免重叠"""
        # 使用水平布局，图标和文字并排
        available_width = rect.width()
        
        # 筹码图标
        if self._icons.get('chip'):
            icon_size = min(rect.height() * 0.75, 36)  # 放大筹码图标
            
            # 图标绘制在左侧，垂直居中
            icon_y = rect.top() + (rect.height() - icon_size) / 2
            icon_rect = QRectF(rect.left(), icon_y, icon_size, icon_size)
            
            # 绘制缩放后的图标
            scaled_pixmap = self._icons['chip'].scaled(
                int(icon_size), int(icon_size), 
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            p.drawPixmap(icon_rect.toRect(), scaled_pixmap)
            
            # 调整文字区域，避免与图标重叠
            text_rect = QRectF(
                rect.left() + icon_size + 5,  # 图标右侧留5像素间距
                rect.top(),
                rect.width() - icon_size - 5,
                rect.height()
            )
        else:
            text_rect = rect
        
        # 绘制筹码数字
        # 放大筹码数字显示
        f = QFont(self.fonts['chips'])
        f.setPointSize(int(f.pointSize() * 1.6))
        p.setFont(f)
        p.setPen(self.colors['gold'])
        
        # 格式化大数字
        if chips >= 1000000:
            chips_text = f"{chips/1000000:.1f}M"
        elif chips >= 1000:
            chips_text = f"{chips/1000:.1f}K"
        else:
            chips_text = str(chips)
            
        p.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, chips_text)
        
    def _draw_hole_cards(self, p: QPainter, rect: QRectF, cards, show_cards: bool):
        """绘制手牌 - 迷你卡片样式（优化间距）"""
        card_count = len(cards)
        if card_count == 0:
            return
            
        # 计算卡片尺寸和间距
        max_card_width = rect.width() / (card_count + 0.2)  # 留出总宽度的20%作为间距
        card_width = min(max_card_width, rect.height() * 0.65)  # 限制最大宽度
        card_height = rect.height() * 0.9  # 使用90%的高度
        
        # 卡片之间的间距
        spacing = card_width * 0.15
        
        # 计算总宽度和起始位置
        total_width = card_count * card_width + (card_count - 1) * spacing
        
        # 如果总宽度超过可用宽度，重新调整
        if total_width > rect.width():
            card_width = (rect.width() - (card_count - 1) * spacing) / card_count
            total_width = rect.width()
        
        start_x = rect.center().x() - total_width / 2
        start_y = rect.top() + (rect.height() - card_height) / 2  # 垂直居中
        
        for i, card in enumerate(cards):
            card_rect = QRectF(
                start_x + i * (card_width + spacing),
                start_y,
                card_width,
                card_height
            )
            
            if show_cards:
                self._draw_mini_card(p, card_rect, str(card))
            else:
                self._draw_card_back(p, card_rect)
                
    def _draw_mini_card(self, p: QPainter, rect: QRectF, card_text: str):
        """绘制迷你卡片"""
        # 白色背景
        p.setBrush(QBrush(self.colors['card_bg']))
        p.setPen(QPen(QColor(180, 180, 180), 1))
        p.drawRoundedRect(rect, 3, 3)
        
        # 卡片内容
        is_red = "♥" in card_text or "♦" in card_text
        p.setPen(self.colors['red_suit'] if is_red else self.colors['black_suit'])
        p.setFont(QFont("Arial", int(rect.height() * 0.4), QFont.Bold))
        p.drawText(rect, Qt.AlignCenter, card_text[:2])
        
    def _draw_card_back(self, p: QPainter, rect: QRectF):
        """绘制卡片背面"""
        # 深色背景
        back_grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        back_grad.setColorAt(0, QColor(40, 50, 60))
        back_grad.setColorAt(1, QColor(30, 40, 50))
        p.setBrush(QBrush(back_grad))
        p.setPen(QPen(QColor(100, 100, 100), 1))
        p.drawRoundedRect(rect, 3, 3)
        
        # 简单图案
        p.setPen(QPen(QColor(80, 90, 100), 1))
        p.drawLine(rect.center() - QPointF(rect.width()*0.2, 0), 
                  rect.center() + QPointF(rect.width()*0.2, 0))
        
    def _draw_community_cards(self, p: QPainter):
        """绘制公共牌"""
        if not self.game or not self.game.community_cards:
            return
            
        cards = self.game.community_cards
        
        # 计算位置 - 牌桌中心上方
        margin = min(self.width() * 0.05, self.height() * 0.05)
        table_rect = QRectF(self.rect()).adjusted(float(margin), float(margin), float(-margin), float(-margin))
        cx = table_rect.center().x()
        cy = table_rect.center().y() - table_rect.height() * 0.15
        
        # 卡片尺寸
        card_w = min(self.width() * 0.12, 160)
        card_h = card_w * 1.45
        gap = card_w * 0.18
        
        total_w = len(cards) * card_w + (len(cards) - 1) * gap
        left = cx - total_w / 2
        
        for i, card in enumerate(cards):
            x = left + i * (card_w + gap)
            card_rect = QRectF(x, cy - card_h/2, card_w, card_h)
            self._draw_community_card(p, card_rect, str(card), i)
            
    def _draw_community_card(self, p: QPainter, rect: QRectF, card_text: str, index: int):
        """绘制单张公共牌 - 精美效果"""
        # 卡片阴影
        shadow_rect = rect.adjusted(2, 2, 2, 2)
        p.setBrush(QBrush(QColor(0, 0, 0, 60)))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(shadow_rect, 8, 8)
        
        # 卡片背景
        card_grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        card_grad.setColorAt(0, QColor(255, 255, 255))
        card_grad.setColorAt(0.5, QColor(252, 252, 252))
        card_grad.setColorAt(1, QColor(245, 245, 245))
        p.setBrush(QBrush(card_grad))
        p.setPen(QPen(QColor(160, 160, 160), 1))
        p.drawRoundedRect(rect, 8, 8)
        
        # 内边框
        inner_rect = rect.adjusted(3, 3, -3, -3)
        p.setPen(QPen(QColor(200, 200, 200), 0.5))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(inner_rect, 6, 6)
        
        # 解析卡片
        is_red = "♥" in card_text or "♦" in card_text
        rank = card_text[:-1]
        suit = card_text[-1]
        
        color = self.colors['red_suit'] if is_red else self.colors['black_suit']
        p.setPen(color)
        
        # 左上角
        p.setFont(QFont("Arial", int(rect.height() * 0.15), QFont.Bold))
        rank_rect = QRectF(rect.left() + 5, rect.top() + 5, rect.width()/3, rect.height()/4)
        p.drawText(rank_rect, Qt.AlignLeft | Qt.AlignTop, rank)
        
        # 中心大花色
        p.setFont(QFont("Arial", int(rect.height() * 0.3)))
        center_rect = QRectF(rect.left(), rect.top() + rect.height()*0.25, 
                            rect.width(), rect.height()*0.5)
        p.drawText(center_rect, Qt.AlignCenter, suit)
        
        # 右下角（旋转180度）
        p.save()
        p.translate(rect.right() - 5, rect.bottom() - 5)
        p.rotate(180)
        p.setFont(QFont("Arial", int(rect.height() * 0.15), QFont.Bold))
        p.drawText(QRectF(-rect.width()/3, -rect.height()/4, rect.width()/3, rect.height()/4),
                  Qt.AlignLeft | Qt.AlignTop, rank)
        p.restore()
        
    def _draw_pot(self, p: QPainter):
        """绘制奖池"""
        if not self.game:
            return
            
        pot = self.game.pot.get_total_pot()
        if pot <= 0:
            return
            
        # 位置 - 牌桌中心下方
        margin = min(self.width() * 0.05, self.height() * 0.05)
        table_rect = QRectF(self.rect()).adjusted(float(margin), float(margin), float(-margin), float(-margin))
        cx = table_rect.center().x()
        cy = table_rect.center().y() + table_rect.height() * 0.18
        
        # 奖池容器
        pot_width = min(self.width() * 0.25, 250)
        pot_height = min(self.height() * 0.08, 60)
        pot_rect = QRectF(cx - pot_width/2, cy - pot_height/2, pot_width, pot_height)
        
        # 发光效果
        glow_rect = pot_rect.adjusted(-8, -8, 8, 8)
        glow_grad = QRadialGradient(glow_rect.center(), glow_rect.width()/2)
        glow_alpha = int(30 + 15 * math.sin(self.glow_phase))
        glow_grad.setColorAt(0, QColor(255, 215, 0, glow_alpha))
        glow_grad.setColorAt(1, QColor(255, 215, 0, 0))
        p.setBrush(QBrush(glow_grad))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(glow_rect, 30, 30)
        
        # 主背景
        pot_grad = QLinearGradient(pot_rect.topLeft(), pot_rect.bottomRight())
        pot_grad.setColorAt(0, QColor(35, 35, 35, 230))
        pot_grad.setColorAt(0.5, QColor(45, 40, 35, 230))
        pot_grad.setColorAt(1, QColor(35, 35, 35, 230))
        p.setBrush(QBrush(pot_grad))
        p.setPen(QPen(self.colors['gold'], 2))
        p.drawRoundedRect(pot_rect, 25, 25)
        
        # 筹码图标（叠加效果）
        if self._icons.get('chip'):
            chip_size = pot_height * 0.6
            chip_x = pot_rect.left() + 15
            chip_y = pot_rect.center().y() - chip_size/2
            
            # 绘制多个筹码叠加
            for i in range(3):
                offset = i * 3
                p.setOpacity(0.9 - i * 0.2)
                chip_pixmap = self._icons['chip'].scaled(
                    int(chip_size), int(chip_size), 
                    Qt.KeepAspectRatio, Qt.SmoothTransformation)
                p.drawPixmap(int(chip_x + offset), int(chip_y - offset), chip_pixmap)
            p.setOpacity(1.0)
        
        # 奖池文字
        text_rect = QRectF(pot_rect.left() + pot_height * 0.8, pot_rect.top(),
                          pot_rect.width() - pot_height * 0.8, pot_rect.height())
        p.setFont(self.fonts['pot'])
        p.setPen(self.colors['gold_light'])
        p.drawText(text_rect, Qt.AlignCenter, f"奖池: {pot:,}")
        
    def _draw_game_status(self, p: QPainter):
        """绘制游戏状态"""
        if not self.game:
            return
            
        # 顶部状态栏
        status_height = 35
        status_rect = QRectF(10, 10, self.width() - 20, status_height)
        
        # 半透明背景
        status_grad = QLinearGradient(status_rect.topLeft(), status_rect.bottomLeft())
        status_grad.setColorAt(0, QColor(0, 0, 0, 160))
        status_grad.setColorAt(1, QColor(0, 0, 0, 100))
        p.setBrush(QBrush(status_grad))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(status_rect, 15, 15)
        
        # 游戏阶段文字
        p.setFont(self.fonts['subtitle'])
        p.setPen(self.colors['text_primary'])
        stage_text = "游戏进行中"
        p.drawText(status_rect, Qt.AlignCenter, stage_text)
        
    def _draw_avatar(self, p: QPainter, rect: QRectF, name: str):
        """绘制玩家头像 - 圆形"""
        # 保存画家状态
        p.save()
        
        # 创建圆形裁剪路径
        path = QPainterPath()
        path.addEllipse(rect)
        p.setClipPath(path)
        
        if self._icons.get('avatar'):
            # 缩放并绘制头像
            pixmap = self._icons['avatar'].scaled(
                int(rect.width()), int(rect.height()),
                Qt.KeepAspectRatio, Qt.SmoothTransformation)
            p.drawPixmap(rect.toRect(), pixmap)
        else:
            # 默认头像 - 渐变背景
            avatar_grad = QRadialGradient(rect.center(), rect.width()/2)
            avatar_grad.setColorAt(0, QColor(100, 150, 200))
            avatar_grad.setColorAt(1, QColor(70, 120, 170))
            p.setBrush(QBrush(avatar_grad))
            p.setPen(Qt.NoPen)
            p.drawEllipse(rect)
            
            # 绘制首字母
            p.setPen(QColor(255, 255, 255))
            p.setFont(QFont("Arial", int(rect.height() * 0.5), QFont.Bold))
            p.drawText(rect, Qt.AlignCenter, name[0].upper() if name else "P")
        
        # 恢复裁剪
        p.restore()
        
        # 头像边框
        p.setPen(QPen(QColor(100, 100, 100), 1))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(rect)
        
    def _draw_dealer_button_outside(self, p: QPainter, seat_rect: QRectF):
        """绘制庄家按钮 - 在座位外部"""
        # 位置 - 座位右上角外侧
        size = min(seat_rect.width() * 0.15, 24)
        dealer_rect = QRectF(
            seat_rect.right() - size * 0.3,  # 稍微偏内
            seat_rect.top() - size * 0.7,    # 在座位上方
            size, size
        )
        
        # 发光背景
        glow_rect = dealer_rect.adjusted(-3, -3, 3, 3)
        glow_grad = QRadialGradient(glow_rect.center(), glow_rect.width()/2)
        glow_grad.setColorAt(0, QColor(255, 215, 0, 100))
        glow_grad.setColorAt(0.5, QColor(255, 215, 0, 60))
        glow_grad.setColorAt(1, QColor(255, 215, 0, 0))
        p.setBrush(QBrush(glow_grad))
        p.setPen(Qt.NoPen)
        p.drawEllipse(glow_rect)
        
        if self._icons.get('dealer'):
            # 皇冠图标
            pixmap = self._icons['dealer'].scaled(
                int(size), int(size),
                Qt.KeepAspectRatio, Qt.SmoothTransformation)
            p.drawPixmap(dealer_rect.toRect(), pixmap)
        else:
            # 默认D标识
            p.setBrush(self.colors['gold'])
            p.setPen(QPen(self.colors['gold_dark'], 1))
            p.drawEllipse(dealer_rect)
            
            p.setPen(QColor(30, 30, 30))
            p.setFont(QFont("Arial", int(size * 0.6), QFont.Bold))
            p.drawText(dealer_rect, Qt.AlignCenter, "D")
    
    def _load_icons(self) -> dict:
        """加载所有图标资源"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        icons = {}
        
        # 图标文件映射
        icon_files = {
            'chip': 'assets/icons/chip.png',
            'dealer': 'assets/icons/dealer.png', 
            'avatar': 'assets/icons/avatar.png',
            'sparkle': 'assets/icons/sparkle.png',
            'star': 'assets/icons/star.png',
            'hearts': 'assets/cards/hearts.png',
            'diamonds': 'assets/cards/diamonds.png',
            'clubs': 'assets/cards/clubs.png',
            'spades': 'assets/cards/spades.png'
        }
        
        for name, path in icon_files.items():
            full_path = os.path.join(base_dir, path)
            if os.path.exists(full_path):
                try:
                    pixmap = QPixmap(full_path)
                    if not pixmap.isNull():
                        icons[name] = pixmap
                except Exception as e:
                    print(f"加载 {name} 失败: {e}")
                    
        return icons