from typing import List, Optional
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QLinearGradient, QBrush
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QComboBox, QLineEdit, QMessageBox, QFrame, QSplitter,
    QGroupBox, QGridLayout, QTextEdit, QScrollArea, QSizePolicy
)

from game import Game, GameMode, Player, PlayerAction, GamePhase
from .game_table import GameTableWidget
from .dialogs import SetupDialog


class ActionButton(QPushButton):
    """自定义动作按钮"""
    def __init__(self, text: str, color: str = "#2563eb", parent=None):
        super().__init__(text, parent)
        self.default_color = color
        self.setMinimumHeight(45)
        self.setCursor(Qt.PointingHandCursor)
        

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("德州扑克 - Texas Hold'em Poker")
        self.setMinimumSize(2200, 1400)
        
        # 深色主题窗口背景
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f1419;
            }
        """)
        
        self.game: Optional[Game] = None
        self.table: Optional[GameTableWidget] = None
        self.action_buttons = {}
        self.last_action_label: Optional[QLabel] = None
        
        self._build_ui()
        self._apply_theme()
        self._init_shortcuts()
        
        # 自动开始新游戏
        QTimer.singleShot(100, self._new_game_via_dialog)

    def _build_ui(self):
        """构建UI布局"""
        root = QWidget(self)
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 游戏桌面
        self.table = GameTableWidget(self)
        self.table.setMinimumWidth(1400)
        
        # 右侧面板
        right_panel = self._build_right_panel()
        right_panel.setMaximumWidth(520)
        right_panel.setMinimumWidth(420)

        # 分隔器
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(self.table)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        splitter.setHandleWidth(1)
        
        # 设置分隔器样式
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #2a2e36;
            }
        """)

        root_layout.addWidget(splitter)

    def _build_right_panel(self) -> QWidget:
        """构建右侧控制面板"""
        panel = QWidget(self)
        panel.setObjectName("rightPanel")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 标题区域
        title_widget = self._create_title_section()
        layout.addWidget(title_widget)
        
        # 游戏信息区域
        info_widget = self._create_info_section()
        layout.addWidget(info_widget)
        
        # 动作按钮区域
        action_widget = self._create_action_section()
        layout.addWidget(action_widget)
        
        # 加注控制区域
        bet_widget = self._create_bet_section()
        layout.addWidget(bet_widget)
        
        # 在动作区与加注区都创建完成后再统一设置按钮可用状态
        self._update_action_buttons(False)
        
        # 游戏控制区域
        control_widget = self._create_control_section()
        layout.addWidget(control_widget)
        
        # 历史记录区域
        history_widget = self._create_history_section()
        layout.addWidget(history_widget, 1)  # 占用剩余空间
        
        return panel
    
    def _create_title_section(self) -> QWidget:
        """创建标题区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 主标题
        title = QLabel("德州扑克")
        title.setObjectName("mainTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setObjectName("titleLine")
        layout.addWidget(line)
        
        return widget
    
    def _create_info_section(self) -> QGroupBox:
        """创建游戏信息区域"""
        group = QGroupBox("游戏信息")
        group.setObjectName("infoGroup")
        
        layout = QGridLayout(group)
        layout.setSpacing(10)
        
        # 游戏状态标签
        self.status_label = QLabel("等待开始")
        self.status_label.setObjectName("statusLabel")
        
        # 当前玩家标签
        self.current_player_label = QLabel("当前玩家: -")
        self.current_player_label.setObjectName("currentPlayerLabel")
        
        # 奖池标签
        self.pot_label = QLabel("奖池: 0")
        self.pot_label.setObjectName("potLabel")
        
        # 游戏阶段标签
        self.phase_label = QLabel("阶段: -")
        self.phase_label.setObjectName("phaseLabel")
        
        # 最后动作标签
        self.last_action_label = QLabel("最后动作: -")
        self.last_action_label.setObjectName("lastActionLabel")
        
        # 布局
        layout.addWidget(self.status_label, 0, 0, 1, 2)
        layout.addWidget(self.phase_label, 1, 0)
        layout.addWidget(self.pot_label, 1, 1)
        layout.addWidget(self.current_player_label, 2, 0, 1, 2)
        layout.addWidget(self.last_action_label, 3, 0, 1, 2)
        
        return group
    
    def _create_action_section(self) -> QGroupBox:
        """创建动作按钮区域"""
        group = QGroupBox("玩家动作")
        group.setObjectName("actionGroup")
        
        layout = QGridLayout(group)
        layout.setSpacing(8)
        
        # 创建动作按钮
        self.btn_fold = ActionButton("弃牌 (F)", "#dc2626")
        self.btn_check = ActionButton("过牌 (C)", "#059669")
        self.btn_call = ActionButton("跟注 (Space)", "#2563eb")
        self.btn_raise = ActionButton("加注 (R)", "#7c3aed")
        self.btn_allin = ActionButton("全押 (A)", "#dc2626")
        
        # 存储按钮引用
        self.action_buttons = {
            'fold': self.btn_fold,
            'check': self.btn_check,
            'call': self.btn_call,
            'raise': self.btn_raise,
            'allin': self.btn_allin
        }
        
        # 连接信号
        self.btn_fold.clicked.connect(lambda: self._on_action(PlayerAction.FOLD))
        self.btn_check.clicked.connect(lambda: self._on_action(PlayerAction.CHECK))
        self.btn_call.clicked.connect(lambda: self._on_action(PlayerAction.CALL))
        self.btn_raise.clicked.connect(self._on_raise_clicked)
        self.btn_allin.clicked.connect(lambda: self._on_action(PlayerAction.ALL_IN))
        
        # 布局按钮 - 2x3网格
        layout.addWidget(self.btn_fold, 0, 0)
        layout.addWidget(self.btn_check, 0, 1)
        layout.addWidget(self.btn_call, 1, 0)
        layout.addWidget(self.btn_raise, 1, 1)
        layout.addWidget(self.btn_allin, 2, 0, 1, 2)
        
        # 初始状态禁用（延后到右侧面板构建完成后统一设置）
        
        return group
    
    def _create_bet_section(self) -> QGroupBox:
        """创建加注控制区域"""
        group = QGroupBox("加注金额")
        group.setObjectName("betGroup")
        
        layout = QVBoxLayout(group)
        
        # 加注输入框
        self.raise_input = QSpinBox()
        self.raise_input.setRange(0, 10_000_000)
        self.raise_input.setSingleStep(100)
        self.raise_input.setPrefix("¥ ")
        self.raise_input.setMinimumHeight(40)
        
        # 快速加注按钮
        quick_bet_layout = QHBoxLayout()
        
        self.btn_min_bet = QPushButton("最小")
        self.btn_half_pot = QPushButton("1/2底池")
        self.btn_pot = QPushButton("底池")
        self.btn_2x_pot = QPushButton("2x底池")
        
        for btn in [self.btn_min_bet, self.btn_half_pot, self.btn_pot, self.btn_2x_pot]:
            btn.setObjectName("quickBetBtn")
            btn.setCursor(Qt.PointingHandCursor)
            quick_bet_layout.addWidget(btn)
        
        # 连接快速加注按钮
        self.btn_min_bet.clicked.connect(lambda: self._set_bet_amount('min'))
        self.btn_half_pot.clicked.connect(lambda: self._set_bet_amount('half'))
        self.btn_pot.clicked.connect(lambda: self._set_bet_amount('pot'))
        self.btn_2x_pot.clicked.connect(lambda: self._set_bet_amount('2x'))
        
        layout.addWidget(self.raise_input)
        layout.addLayout(quick_bet_layout)
        
        return group
    
    def _create_control_section(self) -> QGroupBox:
        """创建游戏控制区域"""
        group = QGroupBox("游戏控制")
        group.setObjectName("controlGroup")
        
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # 控制按钮
        self.btn_new = QPushButton("🎮 新游戏")
        self.btn_deal = QPushButton("🃏 发牌")
        self.btn_settings = QPushButton("⚙️ 设置")
        
        for btn in [self.btn_new, self.btn_deal, self.btn_settings]:
            btn.setObjectName("controlBtn")
            btn.setMinimumHeight(35)
            btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(btn)
        
        # 连接信号
        self.btn_new.clicked.connect(self._new_game_via_dialog)
        self.btn_deal.clicked.connect(self._on_deal_clicked)
        self.btn_settings.clicked.connect(self._show_settings)
        
        return group
    
    def _create_history_section(self) -> QGroupBox:
        """创建历史记录区域"""
        group = QGroupBox("游戏历史")
        group.setObjectName("historyGroup")
        
        layout = QVBoxLayout(group)
        
        # 历史记录文本框
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setObjectName("historyText")
        self.history_text.setMaximumHeight(150)
        
        layout.addWidget(self.history_text)
        
        return group

    def _apply_theme(self):
        """应用优雅的深色主题"""
        self.setStyleSheet("""
            /* 主窗口背景 */
            QMainWindow {
                background-color: #0f1419;
            }
            
            /* 右侧面板 */
            #rightPanel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1f29, stop:1 #151921);
                border-left: 1px solid #2a2e36;
            }
            
            /* 主标题 */
            #mainTitle {
                color: #fbbf24;
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
                font-family: 'Segoe UI', 'Microsoft YaHei';
            }
            
            #titleLine {
                background-color: #2a2e36;
                max-height: 2px;
                margin: 5px 0;
            }
            
            /* 分组框 */
            QGroupBox {
                color: #e5e7eb;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #2a2e36;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e2329, stop:1 #181c22);
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                background-color: #1a1f29;
                color: #fbbf24;
            }
            
            /* 标签样式 */
            QLabel {
                color: #e5e7eb;
                font-size: 13px;
                padding: 2px;
            }
            
            #statusLabel {
                color: #60a5fa;
                font-size: 14px;
                font-weight: bold;
            }
            
            #currentPlayerLabel {
                color: #fbbf24;
                font-size: 13px;
            }
            
            #potLabel {
                color: #10b981;
                font-size: 13px;
                font-weight: bold;
            }
            
            /* 动作按钮 */
            ActionButton, QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #374151, stop:1 #1f2937);
                color: white;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: bold;
            }
            
            ActionButton:hover, QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4b5563, stop:1 #374151);
                border: 1px solid #6b7280;
            }
            
            ActionButton:pressed, QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1f2937, stop:1 #111827);
            }
            
            ActionButton:disabled, QPushButton:disabled {
                background: #1f2937;
                color: #6b7280;
                border: 1px solid #374151;
            }
            
            /* 特殊按钮颜色 */
            #controlBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563eb, stop:1 #1e40af);
            }
            
            #controlBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
            }
            
            #quickBetBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #059669, stop:1 #047857);
                min-height: 28px;
            }
            
            #quickBetBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #10b981, stop:1 #059669);
            }
            
            /* 输入框 */
            QSpinBox {
                background-color: #1f2937;
                color: #fbbf24;
                border: 2px solid #374151;
                border-radius: 6px;
                padding: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #374151;
                border: none;
                width: 20px;
            }
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #4b5563;
            }
            
            /* 历史记录 */
            #historyText {
                background-color: #111827;
                color: #9ca3af;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 5px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
            
            /* 滚动条 */
            QScrollBar:vertical {
                background: #1f2937;
                width: 10px;
                border-radius: 5px;
            }
            
            QScrollBar::handle:vertical {
                background: #4b5563;
                border-radius: 5px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #6b7280;
            }
        """)
        
    def _init_shortcuts(self):
        """初始化键盘快捷键"""
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        
        # 动作快捷键
        QShortcut(QKeySequence("F"), self).activated.connect(
            lambda: self._on_action(PlayerAction.FOLD))
        QShortcut(QKeySequence("C"), self).activated.connect(
            lambda: self._on_action(PlayerAction.CHECK))
        QShortcut(QKeySequence("Space"), self).activated.connect(
            lambda: self._on_action(PlayerAction.CALL))
        QShortcut(QKeySequence("R"), self).activated.connect(
            self._on_raise_clicked)
        QShortcut(QKeySequence("A"), self).activated.connect(
            lambda: self._on_action(PlayerAction.ALL_IN))

    def _update_action_buttons(self, enabled: bool):
        """更新动作按钮状态"""
        for btn in self.action_buttons.values():
            btn.setEnabled(enabled)
        self.raise_input.setEnabled(enabled)
        
        # 快速加注按钮
        for btn in [self.btn_min_bet, self.btn_half_pot, self.btn_pot, self.btn_2x_pot]:
            btn.setEnabled(enabled)

    def _new_game_via_dialog(self):
        """通过对话框创建新游戏"""
        dlg = SetupDialog(self)
        if dlg.exec_() == dlg.Accepted:
            cfg = dlg.result_config
            self.game = Game(cfg.mode, cfg.small_blind, cfg.big_blind)
            for name in cfg.player_names:
                self.game.add_player(Player(name, cfg.initial_chips))
            self.table.attach_game(self.game)
            
            # 更新状态
            self.status_label.setText(f"模式: {cfg.mode.value}")
            self.phase_label.setText(f"盲注: {cfg.small_blind}/{cfg.big_blind}")
            self._update_action_buttons(True)
            self._add_history(f"新游戏开始 - {len(cfg.player_names)}名玩家")
            self.table.update()

    def _on_deal_clicked(self):
        """处理发牌按钮点击"""
        if not self.game or not self.game.can_start_game():
            QMessageBox.warning(self, "提示", "玩家数量不足，至少需要2人。")
            return
        try:
            self.game.start_new_hand()
            self.table.update()
            self._refresh_status()
            self._add_history("新一轮开始，发牌完成")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def _on_action(self, action: PlayerAction, amount: int = 0):
        """处理玩家动作"""
        if not self.game:
            return
        current = self.game.get_current_player()
        if not current or not current.can_act():
            return
            
        ok = self.game.player_action(current, action, amount)
        if not ok:
            QMessageBox.information(self, "无效操作", "当前操作不可用或金额非法。")
            return
            
        # 更新历史
        action_text = f"{current.name} {action.value}"
        if amount > 0:
            action_text += f" ¥{amount}"
        self._add_history(action_text)
        self.last_action_label.setText(f"最后动作: {action_text}")
        
        if self.game.is_hand_complete():
            self._showdown_message()
            
        self.table.update()
        self._refresh_status()
        
    def _on_raise_clicked(self):
        """处理加注按钮点击"""
        amount = self.raise_input.value()
        if amount <= 0:
            QMessageBox.warning(self, "提示", "请输入有效的加注金额")
            return
        self._on_action(PlayerAction.RAISE, amount)
        
    def _set_bet_amount(self, bet_type: str):
        """设置快速加注金额"""
        if not self.game:
            return
            
        pot = self.game.pot.get_total_pot()
        
        if bet_type == 'min':
            # 最小加注 = 大盲注
            amount = self.game.big_blind
        elif bet_type == 'half':
            amount = pot // 2
        elif bet_type == 'pot':
            amount = pot
        elif bet_type == '2x':
            amount = pot * 2
        else:
            amount = 0
            
        self.raise_input.setValue(amount)

    def _refresh_status(self):
        """刷新游戏状态显示"""
        if not self.game:
            return
            
        state = self.game.get_game_state()
        cp = state.get("current_player")
        pot = state.get("pot_size", 0)
        phase = state.get("phase", "-")
        
        self.current_player_label.setText(f"当前玩家: {cp or '-'}")
        self.pot_label.setText(f"奖池: ¥{pot:,}")
        self.phase_label.setText(f"阶段: {phase}")
        
        # 更新按钮状态
        if cp:
            self.status_label.setText("游戏进行中")
            self._update_action_buttons(True)
        else:
            self.status_label.setText("等待行动")
            
    def _add_history(self, text: str):
        """添加历史记录"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.history_text.append(f"[{timestamp}] {text}")
        
        # 自动滚动到底部
        scrollbar = self.history_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _showdown_message(self):
        """显示摊牌结果"""
        if not self.game:
            return
            
        # 构建结果消息
        community = " ".join(str(c) for c in self.game.community_cards)
        msg = f"公共牌: {community}\n\n"
        
        winners = []
        for p in self.game.players:
            cards = " ".join(str(c) for c in (p.hole_cards or []))
            status = p.status.value if hasattr(p, 'status') else "活跃"
            msg += f"{p.name}:\n"
            msg += f"  状态: {status}\n"
            msg += f"  筹码: ¥{p.chips:,}\n"
            msg += f"  手牌: {cards}\n\n"
            
            # 判断赢家（简化逻辑）
            if p.chips > 0 and status != "弃牌":
                winners.append(p.name)
        
        # 显示赢家
        if winners:
            msg += f"赢家: {', '.join(winners)}"
            self._add_history(f"本轮结束 - 赢家: {', '.join(winners)}")
        
        # 自定义消息框
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("摊牌结果")
        msgBox.setText("本轮游戏结束")
        msgBox.setDetailedText(msg)
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setStyleSheet("""
            QMessageBox {
                background-color: #1f2937;
                color: #e5e7eb;
            }
            QMessageBox QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
                min-width: 60px;
            }
            QMessageBox QPushButton:hover {
                background-color: #3b82f6;
            }
            QMessageBox QDetailedText {
                background-color: #111827;
                color: #e5e7eb;
                border: 1px solid #374151;
            }
        """)
        msgBox.exec_()
        
    def _show_settings(self):
        """显示设置对话框"""
        QMessageBox.information(self, "设置", "设置功能正在开发中...")
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出游戏吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()