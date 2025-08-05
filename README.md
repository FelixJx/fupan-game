# 🎮 股票复盘游戏

基于千牛哥复盘方法论的游戏化股票分析工具

## ✨ 特色功能

- 🎯 **六步复盘法游戏化**：市场鸟瞰 → 风险扫描 → 机会扫描 → 资金验证 → 逻辑核对 → 标记分组
- 📊 **实时数据获取**：多数据源融合，包括akshare、yfinance等
- 🔮 **预测挑战系统**：每日预测题目，验证分析能力
- 📈 **技能点升级**：六大核心技能培养
- 🏆 **排行榜系统**：与其他玩家比拼分析能力

## 🚀 快速部署到阿里云

### 方法1：一行命令部署（推荐）

在阿里云ECS服务器上执行：

```bash
curl -fsSL https://raw.githubusercontent.com/FelixJx/fupan-game/main/install.sh | bash
```

### 方法2：手动部署

1. **克隆项目**：
```bash
cd /opt
git clone https://github.com/FelixJx/fupan-game.git
cd fupan-game
```

2. **安装依赖**：
```bash
apt update
apt install -y python3 python3-pip nginx
pip3 install -r requirements.txt
```

3. **启动应用**：
```bash
mkdir -p data logs
python3 main.py
```

4. **配置Nginx**（可选）：
```bash
# 配置反向代理到80端口
systemctl restart nginx
```

## 📋 系统要求

- **操作系统**：Ubuntu 18.04+ / CentOS 7+ / Alibaba Cloud Linux
- **Python**：3.7+
- **内存**：建议2GB+
- **存储**：建议10GB+

## 🔧 配置说明

### 端口设置
- **8000**：应用主端口
- **80**：Nginx反向代理端口（可选）

### 安全组设置
确保阿里云安全组开放以下端口：
- TCP 22 （SSH）
- TCP 80 （HTTP）
- TCP 8000 （应用）

## 🎯 使用指南

### 游戏模式

1. **传统复盘模式**：
   - 访问：`http://your-server/`
   - 按六步法进行复盘分析

2. **预测挑战模式**：
   - 访问：`http://your-server/prediction`
   - 参与每日预测挑战

### API接口

- `GET /api/market_data` - 获取市场数据
- `POST /api/start_game` - 开始新游戏
- `GET /api/daily_questions/{date}` - 获取每日题目
- `GET /api/leaderboard` - 查看排行榜

## 🛠️ 开发指南

### 本地开发

```bash
# 克隆项目
git clone https://github.com/FelixJx/fupan-game.git
cd fupan-game

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python main.py
```

### 项目结构

```
fupan-game/
├── main.py                 # FastAPI主程序
├── data_system.py          # 数据系统
├── scoring_system.py       # 评分系统
├── prediction_game_engine.py # 预测游戏引擎
├── game_interface.html     # 传统复盘界面
├── prediction_game_interface.html # 预测游戏界面
├── requirements.txt        # Python依赖
└── deploy/                 # 部署脚本
```

### 数据源

- **akshare**：A股数据
- **yfinance**：美股数据
- **实时新闻**：财经新闻抓取
- **技术指标**：自动计算

## 📊 监控与维护

### 查看服务状态
```bash
# 查看应用进程
ps aux | grep python

# 查看日志
tail -f logs/app.log

# 重启应用
pkill -f python
python3 main.py &
```

### 更新代码
```bash
cd /opt/fupan-game
git pull
# 重启应用
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发规范
- 代码风格：PEP 8
- 提交信息：使用英文，描述清晰
- 测试：确保功能正常

## 📄 许可证

本项目采用 MIT 许可证

## 🙏 致谢

- 千牛哥复盘方法论
- akshare数据支持
- FastAPI框架

## 📞 联系方式

- GitHub Issues: [提交问题](https://github.com/FelixJx/fupan-game/issues)
- 项目地址: https://github.com/FelixJx/fupan-game

---

🎮 **让复盘变成游戏，提升先知先觉能力！**