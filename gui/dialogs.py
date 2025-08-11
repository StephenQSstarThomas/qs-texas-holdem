from dataclasses import dataclass
from typing import List
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QDialogButtonBox, QSpinBox, QComboBox, QLineEdit, QLabel, QVBoxLayout, QWidget, QPushButton
)

from game import GameMode


@dataclass
class SetupConfig:
    mode: GameMode
    small_blind: int
    big_blind: int
    initial_chips: int
    player_names: List[str]


class SetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新游戏设置")
        self.result_config: SetupConfig | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.combo_mode = QComboBox(self)
        self.combo_mode.addItem("现金游戏", GameMode.CASH_GAME)
        self.combo_mode.addItem("锦标赛", GameMode.TOURNAMENT)

        self.spin_sb = QSpinBox(self)
        self.spin_sb.setRange(1, 100000)
        self.spin_sb.setValue(10)

        self.spin_bb = QSpinBox(self)
        self.spin_bb.setRange(2, 200000)
        self.spin_bb.setValue(20)

        self.spin_chips = QSpinBox(self)
        self.spin_chips.setRange(100, 10_000_000)
        self.spin_chips.setValue(1000)

        self.edit_players = QLineEdit(self)
        self.edit_players.setPlaceholderText("以逗号分隔的玩家名，例如：Alice,Bob,Charlie")
        self.edit_players.setText("Alice,Bob")

        form.addRow("模式:", self.combo_mode)
        form.addRow("小盲注:", self.spin_sb)
        form.addRow("大盲注:", self.spin_bb)
        form.addRow("初始筹码:", self.spin_chips)
        form.addRow("玩家:", self.edit_players)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        names = [n.strip() for n in self.edit_players.text().split(',') if n.strip()]
        names = names[:6]
        if len(names) < 2:
            names = ["Alice", "Bob"]
        self.result_config = SetupConfig(
            mode=self.combo_mode.currentData(),
            small_blind=self.spin_sb.value(),
            big_blind=self.spin_bb.value(),
            initial_chips=self.spin_chips.value(),
            player_names=names,
        )
        self.accept()


