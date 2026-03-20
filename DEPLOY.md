# Zhihu Backup 部署指南

一个用于备份知乎内容的网页应用，支持导出为 Markdown、PDF、JSON、ZIP 格式。

## 快速部署（免费方案）

### 方案一：Railway（推荐）

1. **注册账号**
   - 访问 [railway.app](https://railway.app)
   - 使用 GitHub 账号登录

2. **部署步骤**
   ```bash
   # 1. Fork 本项目到你的 GitHub
   # 2. 在 Railway 中点击 "New Project" → "Deploy from GitHub repo"
   # 3. 选择你 Fork 的仓库
   # 4. Railway 会自动检测 Dockerfile 进行部署
   ```

3. **配置环境变量（如需要）**
   - `PORT`: 端口，默认 5001
   - `SECRET_KEY`: Flask 密钥

4. **访问应用**
   - 部署完成后，Railway 会提供 URL，如 `https://zhihu-backup.up.railway.app`

### 方案二：Render

1. **注册账号**
   - 访问 [render.com](https://render.com)
   - 使用 GitHub 账号登录

2. **部署步骤**
   ```bash
   # 1. Fork 本项目到你的 GitHub
   # 2. 在 Render 中点击 "New" → "Web Service"
   # 3. 连接你的 GitHub 仓库
   # 4. 设置：
   #    - Name: zhihu-backup
   #    - Region: Oregon (或靠近你的地区)
   #    - Branch: main
   #    - Root Directory: zhihu-backup
   #    - Runtime: Docker
   #    - Plan: Free
   # 5. 点击 "Create Web Service"
   ```

3. **访问应用**
   - 部署完成后，Render 会提供 URL，如 `https://zhihu-backup.onrender.com`

### 方案三：自托管（VPS/Docker）

```bash
# 1. 克隆项目
git clone <your-repo-url> zhihu-backup
cd zhihu-backup

# 2. 使用 Docker 部署
docker build -t zhihu-backup .
docker run -d -p 5001:5001 --name zhihu-backup zhihu-backup

# 3. 访问 http://your-server:5001
```

## 本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 安装 Playwright 浏览器
playwright install chromium

# 3. 启动服务
python app.py

# 访问 http://localhost:5001
```

## 使用说明

1. **基础使用**
   - 输入知乎文章/回答的 URL
   - 点击「提取内容」

2. **需要登录的内容**
   - 有些知乎内容需要登录后才能查看
   - 点击「粘贴Cookie」按钮，粘贴从知乎复制的 Cookie
   - 如何获取 Cookie：
     1. 在浏览器中打开知乎
     2. 登录你的账号
     3. 按 F12 打开开发者工具
     4. 切换到 Network 标签
     5. 刷新页面，点击任意请求
     6. 在 Headers 中找到 Cookie，复制完整内容

3. **导出格式**
   - **Markdown**: 纯文本格式，图片以链接形式存在
   - **PDF**: 包含图片的 PDF 文档
   - **JSON**: 原始数据格式
   - **ZIP**: Markdown + 元信息 + 图片压缩包

## 技术架构

- **后端**: Flask (Python)
- **爬虫**: Playwright (浏览器自动化)
- **内容解析**: BeautifulSoup4 + html2text
- **PDF生成**: Playwright 原生 PDF
- **部署**: Docker

## 注意事项

1. **免费额度**
   - Railway: 每月 $5 免费额度（约 500 小时运行）
   - Render: 免费计划有休眠机制，长时间不活跃会自动休眠

2. **性能**
   - PDF 生成需要较长时间（约 10-30 秒）
   - 请耐心等待，不要重复点击

3. **知乎反爬**
   - 部分内容可能需要提供 Cookie 才能访问
   - 建议登录后再获取 Cookie

4. **数据存储**
   - 应用不存储任何数据，所有处理都是临时的
   - 刷新页面后需要重新提取

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