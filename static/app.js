// Zhihu Backup Frontend Logic

(function() {
    'use strict';

    // DOM Elements
    const urlInput = document.getElementById('urlInput');
    const parseBtn = document.getElementById('parseBtn');
    const cookieInput = document.getElementById('cookieInput');
    const errorMessage = document.getElementById('errorMessage');
    const resultSection = document.getElementById('resultSection');
    const contentType = document.getElementById('contentType');
    const resultTitle = document.getElementById('resultTitle');
    const resultAuthor = document.getElementById('resultAuthor');
    const resultStats = document.getElementById('resultStats');
    const resultPreview = document.getElementById('resultPreview');
    const downloadMd = document.getElementById('downloadMd');
    const downloadZip = document.getElementById('downloadZip');
    const downloadJson = document.getElementById('downloadJson');
    const downloadPdf = document.getElementById('downloadPdf');
    const previewMdLink = document.getElementById('previewMdLink');
    const previewPdfLink = document.getElementById('previewPdfLink');
    const pdfPreviewModal = document.getElementById('pdfPreviewModal');
    const pdfPreviewFrame = document.getElementById('pdfPreviewFrame');
    const closePdfModal = document.getElementById('closePdfModal');

    // Current session
    let currentSessionId = null;

    // Event Listeners
    parseBtn.addEventListener('click', handleParse);
    urlInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') handleParse();
    });

    downloadMd.addEventListener('click', function() { downloadFile('md'); });
    downloadZip.addEventListener('click', function() { downloadFile('zip'); });
    downloadJson.addEventListener('click', function() { downloadFile('json'); });
    downloadPdf.addEventListener('click', function() { downloadFile('pdf'); });

    previewPdfLink.addEventListener('click', function(e) {
        e.preventDefault();
        showPdfPreview();
    });

    closePdfModal.addEventListener('click', hidePdfPreview);
    if (pdfPreviewModal) {
        pdfPreviewModal.querySelector('.modal-backdrop').addEventListener('click', hidePdfPreview);
    }

    // Handle Parse
    async function handleParse() {
        const url = urlInput.value.trim();
        const cookies = cookieInput ? cookieInput.value.trim() : '';

        if (!url) {
            showError('请输入知乎链接');
            return;
        }

        if (!isValidUrl(url)) {
            showError('请输入有效的URL');
            return;
        }

        if (!url.includes('zhihu.com')) {
            showError('请输入知乎链接');
            return;
        }

        setLoading(true);
        hideError();
        hideResult();

        try {
            const response = await fetch('/api/parse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url, cookies: cookies })
            });

            const data = await response.json();

            if (data.success) {
                currentSessionId = data.session_id;
                showResult(data);
            } else {
                showError(data.error || '解析失败');
            }
        } catch (error) {
            console.error('Parse error:', error);
            showError('网络错误，请检查网络连接');
        } finally {
            setLoading(false);
        }
    }

    // Show result
    function showResult(data) {
        contentType.textContent = getTypeName(data.type);
        resultTitle.textContent = data.title || '无标题';
        resultAuthor.textContent = data.author ? `👤 ${data.author}` : '';

        // Show stats
        const stats = data.stats || {};
        const statsParts = [];
        if (stats.vote_count) statsParts.push(`👍 ${stats.vote_count}`);
        if (stats.comment_count) statsParts.push(`💬 ${stats.comment_count}`);
        if (stats.collect_count) statsParts.push(`⭐ ${stats.collect_count}`);
        resultStats.textContent = statsParts.join(' | ');

        // Show preview
        resultPreview.textContent = data.preview || '无内容预览';

        // Set preview links
        previewMdLink.href = `/api/preview/${currentSessionId}`;
        previewPdfLink.href = `/api/preview/pdf/${currentSessionId}`;

        resultSection.style.display = 'flex';
        resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // Hide result
    function hideResult() {
        resultSection.style.display = 'none';
        currentSessionId = null;
    }

    // PDF Preview
    function showPdfPreview() {
        if (!currentSessionId) return;
        pdfPreviewFrame.src = `/api/preview/pdf/${currentSessionId}`;
        pdfPreviewModal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    function hidePdfPreview() {
        pdfPreviewModal.style.display = 'none';
        document.body.style.overflow = '';
        pdfPreviewFrame.src = '';
    }

    // Download file
    async function downloadFile(format) {
        if (!currentSessionId) {
            showError('请先解析内容');
            return;
        }

        try {
            const response = await fetch(`/api/download/${format}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: currentSessionId })
            });

            if (!response.ok) {
                const error = await response.json();
                showError(error.error || '下载失败');
                return;
            }

            // 获取文件名
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `zhihu-content.${format}`;
            if (contentDisposition) {
                const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (match) {
                    filename = match[1].replace(/['"]/g, '');
                }
            }

            // 下载文件
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();

        } catch (error) {
            console.error('Download error:', error);
            showError('下载失败，请重试');
        }
    }

    // Loading state
    function setLoading(loading) {
        parseBtn.disabled = loading;
        const btnText = parseBtn.querySelector('.btn-text');
        const btnLoading = parseBtn.querySelector('.btn-loading');

        if (loading) {
            btnText.style.display = 'none';
            btnLoading.style.display = 'inline-flex';
        } else {
            btnText.style.display = 'inline';
            btnLoading.style.display = 'none';
        }
    }

    // Error handling
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }

    function hideError() {
        errorMessage.style.display = 'none';
    }

    // Utilities
    function isValidUrl(string) {
        try {
            const url = new URL(string);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch (_) {
            return false;
        }
    }

    function getTypeName(type) {
        const types = {
            'article': '文章',
            'answer': '回答',
            'question': '问题',
            'pin': '想法',
            'collection': '收藏夹',
            'profile': '个人主页',
            'home': '首页'
        };
        return types[type] || type;
    }

    // ESC key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && pdfPreviewModal.style.display === 'flex') {
            hidePdfPreview();
        }
    });

})();
