"""
知乎内容提取器
智能识别并提取知乎文章、回答、想法等内容
"""

import re
import os
import json
import requests
import html2text
import zipfile
from io import BytesIO
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import logging

logger = logging.getLogger(__name__)


class ZhihuExtractor:
    """知乎内容提取器"""

    # 移动端User-Agent
    MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'

    # 桌面端User-Agent
    DESKTOP_UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.DESKTOP_UA})

    def sanitize_filename(self, title):
        """清理文件名"""
        filename = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', title)
        filename = re.sub(r'[-\s]+', '-', filename)
        return filename[:50] or 'zhihu-content'

    def is_zhihu_url(self, url):
        """验证是否为知乎URL"""
        try:
            result = urlparse(url)
            return 'zhihu.com' in result.netloc.lower()
        except:
            return False

    def detect_content_type(self, url, soup=None):
        """检测内容类型"""
        parsed = urlparse(url)
        path = parsed.path.lower()

        if 'zhuanlan.zhihu.com' in parsed.netloc:
            return 'article'
        elif '/p/' in path:
            return 'pin'  # 想法
        elif '/question/' in path and '/answer/' in path:
            return 'answer'
        elif '/question/' in path:
            return 'question'
        elif '/collection/' in path:
            return 'collection'
        elif '/people/' in path or parsed.netloc == 'www.zhihu.com':
            if path == '/' or path == '':
                return 'home'
            return 'profile'

        return 'unknown'

    def parse_cookies(self, cookie_string):
        """解析Cookie字符串"""
        if not cookie_string:
            return []

        cookies = []
        for part in cookie_string.split(';'):
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                cookies.append({
                    'name': key.strip(),
                    'value': value.strip(),
                    'domain': '.zhihu.com',
                    'path': '/'
                })
        return cookies

    def extract(self, url, cookies=None):
        """提取知乎内容"""
        if not self.is_zhihu_url(url):
            return {'success': False, 'error': '请输入有效的知乎链接'}

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox'
                    ]
                )

                context = browser.new_context(
                    user_agent=self.MOBILE_UA,
                    viewport={'width': 390, 'height': 844},
                    ignore_https_errors=True,
                    locale='zh-CN'
                )

                if cookies:
                    cookie_list = self.parse_cookies(cookies)
                    if cookie_list:
                        context.add_cookies(cookie_list)

                page = context.new_page()
                page.set_default_timeout(30000)

                page.on("dialog", lambda dialog: dialog.dismiss())

                logger.info(f"正在访问: {url}")
                response = page.goto(url, wait_until='domcontentloaded', timeout=20000)

                if response and response.status == 403:
                    browser.close()
                    return {'success': False, 'error': '访问被拒绝，请提供Cookie'}

                page.wait_for_timeout(3000)

                title = page.title()
                html_content = page.content()

                browser.close()

                # 解析内容
                result = self.parse_content(url, html_content, title)
                return result

        except Exception as e:
            logger.error(f"提取失败: {str(e)}")
            return {'success': False, 'error': f'提取失败: {str(e)}'}

    def parse_content(self, url, html_content, title):
        """解析HTML内容"""
        soup = BeautifulSoup(html_content, 'lxml')

        # 移除无关标签
        for tag in soup.find_all(['script', 'style', 'nav', 'iframe', 'noscript']):
            tag.decompose()

        content_type = self.detect_content_type(url, soup)

        # 提取作者信息
        author = self.extract_author(soup)

        # 提取统计信息
        stats = self.extract_stats(soup, content_type)

        # 提取正文内容
        content = self.extract_body(soup, content_type)

        # 生成frontmatter
        frontmatter = self.generate_frontmatter(title, author, stats, url)

        return {
            'success': True,
            'type': content_type,
            'title': title,
            'url': url,
            'author': author,
            'stats': stats,
            'frontmatter': frontmatter,
            'content': content,
            'extracted_at': self.get_current_time()
        }

    def extract_author(self, soup):
        """提取作者信息"""
        # 尝试多种选择器
        selectors = [
            '.Author-info .name',
            '.UserLink-name',
            '.author-name',
            '[itemprop="author"]',
            '.zm-item-author-info'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()

        # 从meta获取
        author = soup.find('meta', {'name': 'author'})
        if author:
            return author.get('content', '')

        return ''

    def extract_stats(self, soup, content_type):
        """提取统计信息"""
        stats = {}

        # 点赞数
        like_selectors = ['.VoteButton .count', '.like-button .count', '[class*="vote"]']
        for selector in like_selectors:
            element = soup.select_one(selector)
            if element:
                try:
                    stats['vote_count'] = int(element.get_text().strip())
                    break
                except:
                    pass

        # 评论数
        comment_selectors = ['.CommentItemCount', '.comment-count', '[class*="comment"]']
        for selector in comment_selectors:
            element = soup.select_one(selector)
            if element:
                try:
                    stats['comment_count'] = int(element.get_text().strip())
                    break
                except:
                    pass

        # 收藏数
        collect_selectors = ['.CollectButton .count', '[class*="collect"]']
        for selector in collect_selectors:
            element = soup.select_one(selector)
            if element:
                try:
                    stats['collect_count'] = int(element.get_text().strip())
                    break
                except:
                    pass

        return stats

    def extract_body(self, soup, content_type):
        """提取正文内容"""
        # 知乎正文区域选择器
        selectors = [
            '.RichText',
            '.Post-RichText',
            '.AnswerItem .RichText',
            '.QuestionWaiting-answer',
            '.ArticleContent',
            '.PinContent',
            '[itemprop="articleBody"]',
            '.content-wrap'
        ]

        body_element = None
        for selector in selectors:
            element = soup.select_one(selector)
            if element and len(element.get_text()) > 100:
                body_element = element
                break

        if not body_element:
            # 尝试获取整个body
            body_element = soup.find('body')
            if not body_element:
                return ''

        # 处理懒加载图片：将data-src移至src
        for img in body_element.find_all('img'):
            data_src = img.get('data-src') or img.get('data-original') or img.get('data-lazy-src')
            if data_src:
                img['src'] = data_src

        # 转换为Markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0

        text = h.handle(str(body_element))

        # 清理链接格式: [文字](url) -> 文字
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # 清理空图片标记 ![][](...) 和 ![]，保留有URL的图片
        text = re.sub(r'!\[\]\([^\)]+\)', '', text)  # 移除空alt有URL的
        text = re.sub(r'!\[\]\(\)', '', text)  # 移除完全空的
        text = re.sub(r'!\[\]', '', text)  # 移除只有alt没有URL的
        # 清理data:image/svg的内联SVG图片（无法在PDF中渲染）
        text = re.sub(r'!\[[^\]]*\]\(data:image/svg\+xml;[^\)]+\)', '', text)
        # 清理多余的空行
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def generate_frontmatter(self, title, author, stats, url):
        """生成YAML frontmatter"""
        lines = ['---']
        lines.append(f'title: "{title}"')
        if author:
            lines.append(f'author: "{author}"')
        lines.append(f'source: "{url}"')

        if stats.get('vote_count'):
            lines.append(f'vote_count: {stats["vote_count"]}')
        if stats.get('comment_count'):
            lines.append(f'comment_count: {stats["comment_count"]}')
        if stats.get('collect_count'):
            lines.append(f'collect_count: {stats["collect_count"]}')

        lines.append(f'created: "{self.get_current_time()}"')
        lines.append('tags: [zhihu]')
        lines.append('---')
        lines.append('')

        return '\n'.join(lines)

    def get_current_time(self):
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def generate_markdown(self, result, include_comments=False):
        """生成Markdown内容"""
        lines = []

        # 添加frontmatter
        if result.get('frontmatter'):
            lines.append(result['frontmatter'])

        # 添加标题
        lines.append(f'# {result.get("title", "无标题")}')
        lines.append('')

        # 添加作者和统计
        if result.get('author'):
            lines.append(f'**作者**: {result.get("author")}')
            lines.append('')

        if result.get('stats'):
            stats = result['stats']
            stats_parts = []
            if stats.get('vote_count'):
                stats_parts.append(f'👍 {stats["vote_count"]}')
            if stats.get('comment_count'):
                stats_parts.append(f'💬 {stats["comment_count"]}')
            if stats.get('collect_count'):
                stats_parts.append(f'⭐ {stats["collect_count"]}')

            if stats_parts:
                lines.append(' | '.join(stats_parts))
                lines.append('')

        # 添加原文链接
        lines.append(f'**原文链接**: {result.get("url", "")}')
        lines.append('')
        lines.append('---')
        lines.append('')

        # 添加正文
        if result.get('content'):
            lines.append(result['content'])

        return '\n'.join(lines)

    def generate_zip(self, result, include_comments=False):
        """生成ZIP包"""
        buffer = BytesIO()

        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            filename = self.sanitize_filename(result.get('title', 'zhihu-content'))

            # 添加Markdown文件
            md_content = self.generate_markdown(result, include_comments)
            zf.writestr(f'{filename}.md', md_content.encode('utf-8'))

            # 添加元信息JSON
            meta = {
                'title': result.get('title'),
                'author': result.get('author'),
                'url': result.get('url'),
                'type': result.get('type'),
                'stats': result.get('stats'),
                'extracted_at': result.get('extracted_at')
            }
            zf.writestr('meta.json', json.dumps(meta, ensure_ascii=False, indent=2).encode('utf-8'))

        buffer.seek(0)
        return buffer

    def extract_comments(self, html_content):
        """提取评论（如果需要）"""
        # 评论提取逻辑
        soup = BeautifulSoup(html_content, 'lxml')

        comments = []
        comment_elements = soup.select('.CommentItem')

        for elem in comment_elements:
            author = elem.select_one('.UserLink-name')
            content = elem.select_one('.CommentContent')
            time = elem.select_one('.CommentTime')

            if content:
                comment = {
                    'author': author.get_text().strip() if author else '匿名',
                    'content': content.get_text().strip(),
                    'time': time.get_text().strip() if time else ''
                }
                comments.append(comment)

        return comments

    def markdown_to_html(self, markdown_content):
        """将Markdown转换为HTML"""
        import markdown

        # 启用图片和链接扩展
        html_content = markdown.markdown(
            markdown_content,
            extensions=['fenced_code', 'tables', 'nl2br']
        )

        return html_content

    def generate_pdf_html(self, result):
        """生成用于PDF的HTML"""
        title = result.get('title', '无标题')
        author = result.get('author', '')
        url = result.get('url', '')
        stats = result.get('stats', {})
        content = result.get('content', '')

        # 转换Markdown为HTML
        content_html = self.markdown_to_html(content)

        # 生成统计信息
        stats_parts = []
        if stats.get('vote_count'):
            stats_parts.append(f'<span class="stat">👍 {stats["vote_count"]}</span>')
        if stats.get('comment_count'):
            stats_parts.append(f'<span class="stat">💬 {stats["comment_count"]}</span>')
        if stats.get('collect_count'):
            stats_parts.append(f'<span class="stat">⭐ {stats["collect_count"]}</span>')
        stats_html = ' | '.join(stats_parts)

        html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 14px;
            line-height: 1.8;
            color: #333;
            padding: 40px;
            max-width: 800px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 28px;
            font-weight: 700;
            color: #1a1a1a;
            margin-bottom: 16px;
            line-height: 1.3;
        }}
        .meta {{
            color: #666;
            font-size: 14px;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid #eee;
        }}
        .meta .author {{
            color: #1E8AE8;
            font-weight: 500;
        }}
        .stats {{
            margin-top: 8px;
            font-size: 13px;
        }}
        .stats .stat {{
            margin-right: 16px;
        }}
        .content {{
            text-align: justify;
            hyphens: auto;
        }}
        .content p {{
            margin-bottom: 16px;
        }}
        .content img {{
            max-width: 100%;
            max-height: 400px;
            object-fit: contain;
            display: block;
            margin: 20px auto;
            border-radius: 8px;
        }}
        .content a {{
            color: #1E8AE8;
            text-decoration: none;
        }}
        .content h1, .content h2, .content h3 {{
            margin-top: 24px;
            margin-bottom: 12px;
            font-weight: 600;
        }}
        .content h1 {{ font-size: 22px; }}
        .content h2 {{ font-size: 18px; }}
        .content h3 {{ font-size: 16px; }}
        .content pre {{
            background: #f5f5f5;
            padding: 16px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 13px;
            margin: 16px 0;
        }}
        .content code {{
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
        }}
        .content pre code {{
            background: none;
            padding: 0;
        }}
        .content blockquote {{
            border-left: 4px solid #1E8AE8;
            padding-left: 16px;
            margin: 16px 0;
            color: #555;
        }}
        .content ul, .content ol {{
            margin: 16px 0;
            padding-left: 24px;
        }}
        .content li {{
            margin-bottom: 8px;
        }}
        .content table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }}
        .content th, .content td {{
            border: 1px solid #ddd;
            padding: 10px 14px;
            text-align: left;
        }}
        .content th {{
            background: #f5f5f5;
            font-weight: 600;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #999;
        }}
    </style>
</head>
<body>
    <article>
        <h1>{title}</h1>
        <div class="meta">
            <span class="author">{author}</span>
            {f'<div class="stats">{stats_html}</div>' if stats_html else ''}
        </div>
        <div class="content">
            {content_html}
        </div>
        <div class="footer">
            原文链接: <a href="{url}">{url}</a>
        </div>
    </article>
</body>
</html>'''
        return html_template

    def generate_pdf(self, result):
        """使用Playwright生成PDF"""
        try:
            html_content = self.generate_pdf_html(result)
            title = result.get('title', 'zhihu-content')
            filename = self.sanitize_filename(title)

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={'width': 1200, 'height': 1600})

                # 设置内容
                page.set_content(html_content, wait_until='domcontentloaded', timeout=30000)

                # 等待所有图片加载完成
                page.evaluate("""
                    async () => {
                        const images = Array.from(document.querySelectorAll('img'));
                        const promises = images.map(img => {
                            if (img.complete) return Promise.resolve();
                            return new Promise((resolve, reject) => {
                                img.onload = resolve;
                                img.onerror = resolve; // 即使加载失败也继续
                                setTimeout(resolve, 5000); // 5秒超时
                            });
                        });
                        await Promise.all(promises);
                    }
                """)

                # 额外等待确保渲染完成
                page.wait_for_timeout(1000)

                # 生成PDF
                pdf_content = page.pdf(
                    format='A4',
                    margin={
                        'top': '2cm',
                        'right': '2cm',
                        'bottom': '2cm',
                        'left': '2cm'
                    },
                    display_header_footer=False,
                    print_background=True
                )

                browser.close()

                return pdf_content

        except Exception as e:
            logger.error(f"PDF生成失败: {str(e)}")
            return None
