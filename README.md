# Zhihu Exporter

一个优雅的知乎内容备份网页工具，输入知乎文章/回答链接，一键提取内容并导出为 Markdown、PDF、JSON 或 ZIP 格式。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Flask](https://img.shields.io/badge/flask-3.0-orange.svg)

## 功能特性

- 🌐 **网页服务** - 输入 URL 即可提取，无需命令行操作
- 📄 **多格式导出** - 支持 Markdown、PDF、JSON、ZIP 四种格式
- 📝 **PDF 渲染** - 导出包含图片的精美 PDF 文档
- 🖼️ **图片保留** - 支持知乎图片链接的提取与渲染
- 🔒 **隐私优先** - 不存储任何数据，所有处理都是临时的
- 📦 **ZIP 打包** - 下载包含 Markdown + 图片 + 元信息的完整包
- 🍪 **Cookie 支持** - 对于需要登录的内容，可提供 Cookie 访问

## 快速部署

### Railway（推荐）

1. Fork 本项目到你的 GitHub
2. 访问 [railway.app](https://railway.app)，登录后创建新项目
3. 选择 "Deploy from GitHub repo"，连接你的仓库
4. Railway 会自动检测 Dockerfile 并部署

### Render

1. Fork 本项目到你的 GitHub
2. 访问 [render.com](https://render.com)，创建 Web Service
3. 连接 GitHub 仓库，选择 Docker runtime
4. 部署完成获得 URL

### Docker 本地部署

```bash
docker build -t zhihu-exporter .
docker run -d -p 5001:5001 zhihu-exporter
```

## 本地开发

```bash
# 克隆项目
git clone https://github.com/DEROOCE/Zhihu-Exporter.git
cd Zhihu-Exporter

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium

# 启动服务
python app.py

# 访问 http://localhost:5001
```

## 使用说明

### 基础使用

1. 输入知乎文章或回答的 URL
2. 点击「提取内容」
3. 等待处理完成
4. 选择导出格式（Markdown / PDF / JSON / ZIP）

### 需要登录的内容

部分知乎内容（如关注者专属回答）需要登录后才能访问：

1. 在浏览器中打开知乎并登录
2. 按 F12 打开开发者工具 → Network 标签
3. 刷新页面，点击任意请求
4. 在 Headers 中找到 `Cookie` 字段，复制完整内容
5. 在应用页面点击「需要登录？点此提供Cookie」，粘贴 Cookie
6. 重新提取内容

### 导出格式说明

| 格式 | 说明 |
|------|------|
| Markdown | 纯文本格式，兼容 Obsidian 等笔记软件 |
| PDF | 包含图片的 PDF 文档，适合打印阅读 |
| JSON | 原始结构化数据，便于程序处理 |
| ZIP | Markdown + 图片 + 元信息完整打包 |

## 技术栈

- **后端**: Flask (Python)
- **爬虫**: Playwright (浏览器自动化)
- **内容解析**: BeautifulSoup4 + html2text
- **PDF 生成**: Playwright 原生 PDF
- **前端**: 纯 HTML/CSS/JS，无框架依赖

## 项目结构

```
zhihu-backup/
├── app.py              # Flask 主应用
├── extractor.py        # 内容提取核心逻辑
├── templates/
│   └── index.html      # 前端页面
├── static/
│   ├── style.css       # 样式
│   └── app.js          # 前端脚本
├── downloads/          # 临时文件目录
├── Dockerfile          # Docker 配置
├── requirements.txt    # Python 依赖
├── railway.toml        # Railway 配置
├── render.yaml         # Render 配置
└── README.md           # 说明文档
```

## 灵感来源

本项目在开发过程中参考了以下开源项目：

- **[zhihu-save](https://github.com/the0ne001/zhihu-save)** - 知乎内容保存工具，提供了知乎内容解析的思路
- **[html2text](https://github.com/Alir3z4/html2text)** - HTML 转 Markdown 的 Python 库
- **[Playwright](https://github.com/microsoft/playwright)** - 微软开源的浏览器自动化工具

知乎的页面结构和小米生态内容是我实际测试的重要来源。

## 免责声明

- 本工具仅供个人学习研究使用
- 请遵守知乎的服务条款，合理使用
- 请勿频繁请求或用于商业目的
- 尊重内容创作者的版权，转载请注明出处

## License

MIT License

Copyright (c) 2026 DEROOCE

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

如果你觉得这个项目有帮助，请点个 ⭐ Star！
