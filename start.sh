#!/bin/bash
# Zhihu Backup 启动脚本

cd "$(dirname "$0")"

echo "正在检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 需要Python 3"
    exit 1
fi

echo "检查依赖..."
if ! pip show flask &> /dev/null; then
    echo "正在安装依赖..."
    pip install flask playwright beautifulsoup4 html2text requests
fi

echo "检查Playwright..."
if ! python3 -c "import playwright" &> /dev/null; then
    echo "正在安装Playwright..."
    pip install playwright
    playwright install chromium
fi

echo "启动Zhihu Backup服务..."
echo "访问 http://localhost:5001"
python3 app.py
