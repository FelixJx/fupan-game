#!/bin/bash

# 最简化部署脚本 - 直接在服务器执行
echo "股票复盘游戏 - 简化部署"

# 安装基础依赖
apt update
apt install -y python3 python3-pip git curl

# 下载项目
cd /opt
rm -rf fupan-game
git clone https://github.com/FelixJx/fupan-game.git
cd fupan-game

# 安装最少依赖
pip3 install fastapi uvicorn jinja2 pandas numpy requests

# 创建简化启动文件
cat > simple_main.py << 'EOF'
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="股票复盘游戏")

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>股票复盘游戏</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>🎮 股票复盘游戏</h1>
        <h2>基于千牛哥复盘方法论</h2>
        <p>服务器运行正常！</p>
        <p>访问时间: <span id="time"></span></p>
        <script>
            document.getElementById('time').innerText = new Date().toLocaleString();
        </script>
    </body>
    </html>
    """

@app.get("/api/test")
async def test():
    return {"status": "ok", "message": "API正常运行"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# 杀死可能存在的进程
pkill -f python3
pkill -f uvicorn

# 启动应用
echo "启动应用..."
nohup python3 simple_main.py > /var/log/game.log 2>&1 &

sleep 5

# 检查状态
echo "检查服务状态..."
ps aux | grep python3
curl -f http://localhost:8000/ && echo "✅ 应用启动成功!"

echo "🌐 请访问: http://47.98.233.7:8000"