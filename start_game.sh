#!/bin/bash

# 股票复盘游戏启动脚本
# 基于千牛哥复盘方法论

echo "🎮 股票复盘游戏启动器"
echo "基于千牛哥复盘方法论"
echo "让复盘变成RPG游戏，提升先知先觉能力！"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

echo "✅ Python环境检查通过"

# 检查依赖包
echo "📦 检查依赖包..."
if ! python3 -c "import fastapi, uvicorn, sqlite3, pandas, json" 2>/dev/null; then
    echo "⚠️ 部分依赖包缺失，正在安装..."
    pip3 install fastapi uvicorn pandas
else
    echo "✅ 核心依赖包检查通过"
fi

# 创建数据库
echo "💾 初始化游戏数据库..."
python3 -c "
from data_system import StockDataSystem
system = StockDataSystem()
print('✅ 数据库初始化完成')
"

# 启动游戏服务器
echo ""
echo "🚀 启动游戏服务器..."
echo "🌐 游戏地址: http://localhost:8000"
echo "📚 基于千牛哥六步复盘法"
echo "🎯 按 Ctrl+C 停止服务器"
echo ""
echo "千牛哥金句：价格永远领先情绪，先手赚后手的钱！"
echo ""

# 启动服务器
python3 main.py