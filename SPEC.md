# Zhihu Backup - 知乎内容备份工具

## Concept & Vision

一个优雅的知乎内容备份网页工具，输入知乎文章/回答/想法链接，一键提取内容并导出为Markdown、ZIP或图片。界面简洁现代，操作流畅，像一个专业的信息管理工具。

## Design Language

**Aesthetic**: 极简工具美学，参考 Notion、Linear 的设计风格

**Color Palette**:
- Primary: `#1E8AE8` (知乎蓝)
- Secondary: `#FF6B6B` (点缀红)
- Background: `#FAFAFA`
- Surface: `#FFFFFF`
- Text Primary: `#1F2937`
- Text Secondary: `#6B7280`
- Success: `#10B981`
- Warning: `#F59E0B`

**Typography**:
- 主字体: Inter
- 代码/Markdown: JetBrains Mono

## Features

### 核心功能
1. **输入链接** - 支持知乎文章、回答、想法、个人主页等
2. **智能提取** - 自动识别内容类型，提取标题、正文、图片、评论
3. **导出格式**:
   - Markdown (.md) - 纯文本格式
   - ZIP包 - 包含图片+Markdown+元信息
   - JSON - 结构化数据

### 内容识别
- 文章 (zhuanlan.zhihu.com)
- 回答 (www.zhihu.com/question/*/answer/*)
- 想法 (www.zhihu.com/p/*)
- 收藏夹

### 知乎特有优化
- 提取点赞数、评论数、作者信息
- 保留文章/回答的格式化内容
- 提取评论（可选）
- 生成符合Obsidian的frontmatter

## Technical Approach

- **后端**: Python Flask + Playwright
- **前端**: 纯HTML/CSS/JS
- **内容提取**: DOM解析 + BeautifulSoup
- **导出**: Markdown生成 + ZIP打包
