# 德州扑克游戏 (Texas Hold'em Poker)

一个完整的德州扑克游戏实现，支持2-6人本地游戏，具备完整的游戏逻辑和命令行界面。

## 📋 项目概述

本项目实现了德州扑克的核心逻辑，包括发牌、下注、牌型判断、胜负判定等完整功能。当前版本提供命令行界面，后续可扩展图形界面。

## 🎯 功能特点

### 核心功能
- ✅ **完整德州扑克规则**: 2张底牌 + 5张公共牌
- ✅ **2-6人游戏支持**: 灵活的玩家数量
- ✅ **两种游戏模式**: 现金游戏 & 锦标赛模式
- ✅ **完整下注系统**: 盲注、跟注、加注、全押
- ✅ **智能牌型判断**: 支持所有10种牌型
- ✅ **边池管理**: 多人全押时的复杂分配
- ✅ **游戏统计**: 胜率、盈亏追踪

### 牌型支持
1. 🔥 **皇家同花顺** (Royal Flush)
2. 🌊 **同花顺** (Straight Flush)  
3. 💎 **四条** (Four of a Kind)
4. 🏠 **葫芦** (Full House)
5. ♠️ **同花** (Flush)
6. 📈 **顺子** (Straight)
7. 🎯 **三条** (Three of a Kind)
8. 👥 **两对** (Two Pair)
9. 💑 **一对** (One Pair)
10. 🃏 **高牌** (High Card)

## 🚀 快速开始

### 环境要求
- Python 3.11+
- 桌面 GUI（PyQt5）：可选
- Web 前端 + FastAPI（推荐）：提供跨平台现代 UI

### 安装运行
```bash
# 克隆项目
git clone <repository-url>
cd qs-texas-holdem

# 直接运行 CLI 版本
python main.py

# 运行 Web 版本（推荐）
pip install fastapi uvicorn

# 启动后端（WebSocket）
uvicorn server.app:app --reload --port 8000

# 打开前端
# 1) 直接用浏览器打开 web/index.html（建议在本地通过 Live Server / VSCode 插件或任何静态服务器打开）
# 2) 或使用任意静态服务: 例如 `python -m http.server 5500` 然后访问 http://localhost:5500/web/index.html
```

### 游戏操作
1. 启动游戏后，按提示设置游戏参数
2. 添加2-6位玩家，设置初始筹码
3. 游戏自动处理发牌、盲注等
4. 轮到你时，选择动作: 弃牌/过牌/跟注/加注/全押
5. 观看游戏进程，享受德州扑克乐趣！

## 📁 项目结构

```
qs-texas-holdem/
├── main.py              # 🎮 游戏主入口 (命令行界面)
├── config.json          # ⚙️ 游戏配置文件
├── README.md            # 📖 项目说明文档
├── PROJECT_LOG.md       # 📝 开发日志
├── game/                # 🎯 核心游戏逻辑
│   ├── __init__.py      #     包初始化
│   ├── card.py          # 🃏 扑克牌和牌堆类
│   ├── player.py        # 👤 玩家类
│   ├── hand_evaluator.py # 🔍 牌型评估器
│   ├── pot.py           # 💰 奖池管理
│   └── game_engine.py   # 🎲 游戏引擎主控制
├── gui/                 # 🖼️ 图形界面 (待开发)
├── assets/              # 🎨 游戏资源
│   ├── cards/           #     扑克牌图片
│   └── sounds/          #     音效文件
└── data/                # 📊 数据存储
    └── game.db          #     游戏数据库 (待实现)
```

## 🔧 技术架构

### 核心类设计

#### Card & Deck (扑克牌系统)
```python
class Card:          # 单张扑克牌 (花色 + 点数)
class Deck:          # 牌堆 (洗牌、发牌)
```

#### Player (玩家系统)
```python
class Player:        # 玩家 (筹码、状态、动作)
class PlayerStatus:  # 玩家状态枚举
class PlayerAction:  # 玩家动作枚举
```

#### HandEvaluator (牌型评估)
```python
class HandEvaluator: # 牌型判断器
class HandResult:    # 牌型结果
class HandRank:      # 牌型等级枚举
```

#### Pot (奖池管理)
```python
class Pot:           # 主奖池管理
class SidePot:       # 边池处理
```

#### Game (游戏引擎)
```python
class Game:          # 游戏主控制器
class GamePhase:     # 游戏阶段枚举
class GameMode:      # 游戏模式枚举
```

## 🎮 游戏流程

### 1. 游戏初始化
- 设置盲注级别
- 添加2-6位玩家
- 分配初始筹码

### 2. 手牌开始
- 洗牌发底牌 (每人2张)
- 下盲注 (小盲/大盲)
- 开始翻牌前下注

### 3. 四轮下注
1. **Pre-flop**: 翻牌前 (仅底牌)
2. **Flop**: 翻牌 (3张公共牌)
3. **Turn**: 转牌 (第4张公共牌)
4. **River**: 河牌 (第5张公共牌)

### 4. 摊牌结算
- 比较所有未弃牌玩家的牌型
- 分配奖池给获胜者
- 处理边池分配

## ⚙️ 配置说明

`config.json` 文件示例:
```json
{
  "small_blind": 10,
  "big_blind": 20,
  "default_chips": 1000,
  "game_mode": "cash_game"
}
```

## 🧪 测试运行

每个核心模块都包含测试代码，可单独运行:

```bash
# 测试扑克牌模块
python -m game.card

# 测试玩家模块  
python -m game.player

# 测试牌型评估
python -m game.hand_evaluator

# 测试奖池管理
python -m game.pot

# 测试游戏引擎
python -m game.game_engine
```

## 🏗️ 开发计划

### ✅ 阶段一: 核心逻辑 (已完成)
- [x] 扑克牌和牌堆类
- [x] 玩家管理系统
- [x] 牌型评估算法
- [x] 奖池和边池管理
- [x] 游戏引擎主控制
- [x] 命令行界面

### 🔄 阶段二: 图形界面 (开发中)
- [ ] GUI框架选择和集成
- [ ] 游戏桌面设计
- [ ] 玩家界面组件
- [ ] 动画效果实现

### 📋 阶段三: 功能完善 (计划中)
- [ ] 音效系统
- [ ] 数据库集成
- [ ] AI玩家实现
- [ ] 网络对战功能

## 🤝 贡献指南

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🎯 版本信息

- **当前版本**: v1.0.0
- **发布日期**: 2024年
- **Python版本**: 3.11+
- **开发状态**: 核心逻辑完成，GUI开发中

## 🙏 致谢

感谢所有为德州扑克游戏发展做出贡献的开发者和玩家！

---

🃏 **祝你游戏愉快，好运连连！** 🃏