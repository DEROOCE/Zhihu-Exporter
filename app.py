"""
Zhihu Backup - 知乎内容备份工具
Flask 后端服务
"""

import os
import re
import json
import zipfile
import uuid
import base64
import logging
from datetime import datetime
from io import BytesIO
from flask import Flask, request, jsonify, render_template, send_file

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'downloads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())

# 确保下载目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化提取器
from extractor import ZhihuExtractor
extractor = ZhihuExtractor()


@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')


@app.route('/health')
def health():
    """健康检查"""
    return {'status': 'ok'}


@app.route('/api/parse', methods=['POST'])
def parse():
    """解析知乎链接并提取内容"""
    data = request.get_json()

    if not data or 'url' not in data:
        return jsonify({'success': False, 'error': '请提供URL'}), 400

    url = data['url'].strip()
    cookies = data.get('cookies', '')

    if not url.startswith(('http://', 'https://')):
        return jsonify({'success': False, 'error': 'URL格式无效'}), 400

    try:
        logger.info(f"正在解析: {url}")

        # 提取内容
        result = extractor.extract(url, cookies=cookies)

        if not result['success']:
            return jsonify({'success': False, 'error': result.get('error', '提取失败')}), 400

        # 保存解析结果到临时文件
        session_id = uuid.uuid4().hex
        result_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{session_id}.json')

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return jsonify({
            'success': True,
            'session_id': session_id,
            'title': result.get('title', '无标题'),
            'type': result.get('type', 'unknown'),
            'author': result.get('author', ''),
            'stats': result.get('stats', {}),
            'preview': result.get('content', '')[:500]
        })

    except Exception as e:
        logger.error(f"解析失败: {str(e)}")
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500


@app.route('/api/download/<format_type>', methods=['POST'])
def download(format_type):
    """下载指定格式的文件"""
    data = request.get_json()
    session_id = data.get('session_id')
    include_comments = data.get('include_comments', False)

    if not session_id:
        return jsonify({'success': False, 'error': '缺少session_id'}), 400

    result_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{session_id}.json')

    if not os.path.exists(result_file):
        return jsonify({'success': False, 'error': '会话已过期'}), 400

    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            result = json.load(f)

        filename = extractor.sanitize_filename(result.get('title', 'zhihu-content'))

        if format_type == 'md':
            # 下载Markdown
            content = extractor.generate_markdown(result, include_comments)
            return send_file(
                BytesIO(content.encode('utf-8')),
                mimetype='text/markdown',
                as_attachment=True,
                download_name=f'{filename}.md'
            )

        elif format_type == 'json':
            # 下载JSON
            return send_file(
                BytesIO(json.dumps(result, ensure_ascii=False, indent=2).encode('utf-8')),
                mimetype='application/json',
                as_attachment=True,
                download_name=f'{filename}.json'
            )

        elif format_type == 'zip':
            # 下载ZIP包
            zip_buffer = extractor.generate_zip(result, include_comments)
            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f'{filename}.zip'
            )

        elif format_type == 'pdf':
            # 下载PDF
            pdf_content = extractor.generate_pdf(result)
            if pdf_content is None:
                return jsonify({'success': False, 'error': 'PDF生成失败'}), 500
            return send_file(
                BytesIO(pdf_content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'{filename}.pdf'
            )

        else:
            return jsonify({'success': False, 'error': '不支持的格式'}), 400

    except Exception as e:
        logger.error(f"下载失败: {str(e)}")
        return jsonify({'success': False, 'error': f'下载失败: {str(e)}'}), 500


@app.route('/api/preview/<session_id>')
def preview(session_id):
    """预览Markdown内容"""
    result_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{session_id}.json')

    if not os.path.exists(result_file):
        return "Session not found", 404

    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            result = json.load(f)

        md_content = extractor.generate_markdown(result, False)

        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{result.get('title', 'Preview')}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.8; }}
                pre {{ background: #f5f5f5; padding: 20px; overflow-x: auto; border-radius: 8px; }}
                code {{ font-family: 'JetBrains Mono', monospace; }}
                img {{ max-width: 100%; }}
            </style>
        </head>
        <body>
            <pre>{md_content.replace('<', '&lt;').replace('>', '&gt;')}</pre>
        </body>
        </html>
        '''

    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route('/api/preview/pdf/<session_id>')
def preview_pdf(session_id):
    """预览PDF内容"""
    result_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{session_id}.json')

    if not os.path.exists(result_file):
        return "Session not found", 404

    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            result = json.load(f)

        pdf_content = extractor.generate_pdf(result)
        if pdf_content is None:
            return "PDF generation failed", 500

        return send_file(
            BytesIO(pdf_content),
            mimetype='application/pdf'
        )

    except Exception as e:
        logger.error(f"PDF预览失败: {str(e)}")
        return f"Error: {str(e)}", 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
