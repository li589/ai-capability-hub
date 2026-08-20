"""ViralLens 报告页面 - 美观的 HTML 展示"""

REPORT_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ViralLens 视频分析报告</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
            animation: fadeInDown 0.6s ease;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .loading-card {
            background: white;
            border-radius: 16px;
            padding: 60px 40px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            animation: fadeIn 0.6s ease;
        }
        
        .spinner {
            width: 60px;
            height: 60px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        .loading-text {
            font-size: 1.3em;
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .loading-subtext {
            color: #999;
            font-size: 0.95em;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 30px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        .report {
            display: none;
            animation: fadeIn 0.8s ease;
        }
        
        .card {
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 50px rgba(0,0,0,0.15);
        }
        
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .card-icon {
            font-size: 2em;
            margin-right: 15px;
        }
        
        .card-title {
            font-size: 1.5em;
            font-weight: 700;
            color: #333;
        }
        
        .viral-score-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            padding: 50px 30px;
        }
        
        .viral-score {
            font-size: 5em;
            font-weight: 900;
            line-height: 1;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .viral-label {
            font-size: 1.3em;
            opacity: 0.95;
            margin-bottom: 20px;
        }
        
        .viral-factors {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
            margin-top: 20px;
        }
        
        .factor-tag {
            background: rgba(255,255,255,0.25);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            backdrop-filter: blur(10px);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .stat-box {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        
        .hook-analysis {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        
        .hook-type {
            font-size: 1.8em;
            font-weight: 700;
            margin-bottom: 15px;
        }
        
        .hook-strength {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .strength-bar {
            flex: 1;
            height: 12px;
            background: rgba(255,255,255,0.3);
            border-radius: 10px;
            overflow: hidden;
        }
        
        .strength-fill {
            height: 100%;
            background: white;
            border-radius: 10px;
            transition: width 0.8s ease;
        }
        
        .strength-value {
            font-size: 1.5em;
            font-weight: 700;
        }
        
        .timeline {
            position: relative;
            padding-left: 30px;
        }
        
        .timeline::before {
            content: '';
            position: absolute;
            left: 10px;
            top: 0;
            bottom: 0;
            width: 3px;
            background: linear-gradient(180deg, #667eea, #764ba2);
        }
        
        .timeline-item {
            position: relative;
            margin-bottom: 25px;
            padding-left: 20px;
        }
        
        .timeline-item::before {
            content: '';
            position: absolute;
            left: -25px;
            top: 8px;
            width: 12px;
            height: 12px;
            background: #667eea;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
        
        .timeline-phase {
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .timeline-time {
            color: #999;
            font-size: 0.9em;
            margin-bottom: 8px;
        }
        
        .tips-list {
            list-style: none;
        }
        
        .tip-item {
            padding: 20px;
            margin-bottom: 15px;
            background: #f8f9fa;
            border-radius: 12px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }
        
        .tip-item:hover {
            background: #f0f4ff;
            transform: translateX(5px);
        }
        
        .tip-item.high {
            border-left-color: #f5576c;
        }
        
        .tip-item.medium {
            border-left-color: #ffa500;
        }
        
        .tip-category {
            display: inline-block;
            padding: 4px 12px;
            background: #667eea;
            color: white;
            border-radius: 15px;
            font-size: 0.85em;
            margin-bottom: 10px;
        }
        
        .tip-item.high .tip-category {
            background: #f5576c;
        }
        
        .tip-item.medium .tip-category {
            background: #ffa500;
        }
        
        .tip-text {
            font-size: 1.05em;
            line-height: 1.6;
            color: #444;
        }
        
        .script-template {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 12px;
            font-family: 'Courier New', monospace;
            line-height: 1.8;
            color: #333;
            white-space: pre-wrap;
        }
        
        .visual-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .visual-item {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
        }
        
        .visual-label {
            font-weight: 600;
            color: #667eea;
            margin-bottom: 8px;
        }
        
        .visual-value {
            color: #333;
            line-height: 1.6;
        }
        
        .color-palette {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .color-swatch {
            width: 50px;
            height: 50px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .footer {
            text-align: center;
            color: white;
            margin-top: 40px;
            opacity: 0.8;
            font-size: 0.9em;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @media (max-width: 768px) {
            .header h1 { font-size: 1.8em; }
            .viral-score { font-size: 3.5em; }
            .card { padding: 20px; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 ViralLens 视频分析报告</h1>
            <p>AI驱动的爆款视频深度拆解</p>
        </div>
        
        <div id="loading" class="loading-card">
            <div class="spinner"></div>
            <div class="loading-text">正在分析视频...</div>
            <div class="loading-subtext" id="loading-status">准备中</div>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
            </div>
        </div>
        
        <div id="report" class="report">
            <!-- 报告内容将通过 JavaScript 动态生成 -->
        </div>
        
        <div class="footer">
            Powered by ViralLens | 熵海领航出品
        </div>
    </div>
    
    <script>
        const taskId = '{{TASK_ID}}';
        const pollInterval = 3000;
        
        async function pollTask() {
            try {
                const response = await fetch(`/api/task/${taskId}`);
                const data = await response.json();
                
                if (data.status === 'processing' || data.status === 'downloading') {
                    updateLoadingStatus(data.message || '分析中...');
                    setTimeout(pollTask, pollInterval);
                } else if (data.status === 'completed') {
                    renderReport(data.result);
                } else if (data.status === 'failed') {
                    showError(data.error || '分析失败');
                }
            } catch (error) {
                console.error('Polling error:', error);
                setTimeout(pollTask, pollInterval);
            }
        }
        
        function updateLoadingStatus(message) {
            document.getElementById('loading-status').textContent = message;
            
            // 简单的进度模拟
            const progressFill = document.getElementById('progress-fill');
            const currentWidth = parseFloat(progressFill.style.width) || 0;
            const newWidth = Math.min(currentWidth + Math.random() * 15, 95);
            progressFill.style.width = newWidth + '%';
        }
        
        function showError(message) {
            document.getElementById('loading').innerHTML = `
                <div style="font-size: 3em; margin-bottom: 20px;">😞</div>
                <div class="loading-text" style="color: #f5576c;">分析失败</div>
                <div class="loading-subtext">${message}</div>
            `;
        }
        
        function renderReport(result) {
            document.getElementById('loading').style.display = 'none';
            const reportDiv = document.getElementById('report');
            reportDiv.style.display = 'block';
            
            const insights = result.insights || {};
            const metadata = result.metadata || {};
            const scenes = result.scenes || [];
            const visual = result.visual_analysis || {};
            const transcript = result.transcript || {};
            
            let html = '';
            
            // 病毒传播评分
            if (insights.viral_score !== undefined) {
                html += `
                    <div class="card viral-score-card">
                        <div class="viral-score">${insights.viral_score}</div>
                        <div class="viral-label">病毒传播评分</div>
                        ${insights.viral_factors && insights.viral_factors.length > 0 ? `
                            <div class="viral-factors">
                                ${insights.viral_factors.map(f => `<span class="factor-tag">${f}</span>`).join('')}
                            </div>
                        ` : ''}
                    </div>
                `;
            }
            
            // 视频概况
            html += `
                <div class="card">
                    <div class="card-header">
                        <div class="card-icon">📊</div>
                        <div class="card-title">视频概况</div>
                    </div>
                    <div class="stats-grid">
                        <div class="stat-box">
                            <div class="stat-value">${metadata.duration ? metadata.duration.toFixed(1) + 's' : '-'}</div>
                            <div class="stat-label">时长</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">${scenes.length}</div>
                            <div class="stat-label">场景数</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">${metadata.resolution || '-'}</div>
                            <div class="stat-label">分辨率</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">${metadata.fps ? metadata.fps + 'fps' : '-'}</div>
                            <div class="stat-label">帧率</div>
                        </div>
                    </div>
                </div>
            `;
            
            // Hook 分析
            if (insights.hook_analysis) {
                const hook = insights.hook_analysis;
                html += `
                    <div class="card hook-analysis">
                        <div class="card-header" style="border-bottom-color: rgba(255,255,255,0.3);">
                            <div class="card-icon">🎯</div>
                            <div class="card-title" style="color: white;">Hook 分析</div>
                        </div>
                        <div class="hook-type">${hook.type || 'Unknown'}</div>
                        <div class="hook-strength">
                            <span>强度:</span>
                            <div class="strength-bar">
                                <div class="strength-fill" style="width: ${hook.strength || 0}%"></div>
                            </div>
                            <span class="strength-value">${hook.strength || 0}</span>
                        </div>
                        <div style="line-height: 1.6; opacity: 0.95;">
                            ${hook.description || ''}
                        </div>
                        ${hook.time_to_hook ? `<div style="margin-top: 15px; opacity: 0.9;">⏱️ Hook出现时机: ${hook.time_to_hook}</div>` : ''}
                    </div>
                `;
            }
            
            // 内容结构
            if (insights.content_structure && insights.content_structure.breakdown) {
                html += `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">📝</div>
                            <div class="card-title">内容结构 (${insights.content_structure.pattern || 'Unknown'})</div>
                        </div>
                        <div class="timeline">
                            ${insights.content_structure.breakdown.map(item => `
                                <div class="timeline-item">
                                    <div class="timeline-phase">${item.phase}</div>
                                    <div class="timeline-time">${item.time_range}</div>
                                    <div>${item.description}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            // 视觉分析
            if (Object.keys(visual).length > 0) {
                html += `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">👁️</div>
                            <div class="card-title">视觉分析</div>
                        </div>
                        <div class="visual-grid">
                            ${visual.visual_style ? `
                                <div class="visual-item">
                                    <div class="visual-label">风格</div>
                                    <div class="visual-value">${visual.visual_style}</div>
                                </div>
                            ` : ''}
                            ${visual.energy_level ? `
                                <div class="visual-item">
                                    <div class="visual-label">能量级别</div>
                                    <div class="visual-value">${visual.energy_level}</div>
                                </div>
                            ` : ''}
                            ${visual.aesthetic_quality ? `
                                <div class="visual-item">
                                    <div class="visual-label">制作质量</div>
                                    <div class="visual-value">${visual.aesthetic_quality}</div>
                                </div>
                            ` : ''}
                            ${visual.product_visibility !== undefined ? `
                                <div class="visual-item">
                                    <div class="visual-label">产品展示度</div>
                                    <div class="visual-value">${visual.product_visibility}/100</div>
                                </div>
                            ` : ''}
                        </div>
                        ${visual.color_palette && visual.color_palette.length > 0 ? `
                            <div style="margin-top: 20px;">
                                <div class="visual-label">色彩调性</div>
                                <div class="color-palette">
                                    ${visual.color_palette.map(color => `
                                        <div class="color-swatch" style="background: ${color};" title="${color}"></div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                `;
            }
            
            // 优化建议
            if (insights.actionable_tips && insights.actionable_tips.length > 0) {
                const sortedTips = [...insights.actionable_tips].sort((a, b) => {
                    const priority = { high: 3, medium: 2, low: 1 };
                    return (priority[b.priority] || 0) - (priority[a.priority] || 0);
                });
                
                html += `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">💡</div>
                            <div class="card-title">优化建议 (${sortedTips.length}条)</div>
                        </div>
                        <ul class="tips-list">
                            ${sortedTips.map(tip => `
                                <li class="tip-item ${tip.priority}">
                                    <span class="tip-category">${tip.category}</span>
                                    <div class="tip-text">${tip.tip}</div>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                `;
            }
            
            // 脚本模板
            if (insights.script_template) {
                html += `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">📋</div>
                            <div class="card-title">可复用脚本模板</div>
                        </div>
                        <div class="script-template">${insights.script_template}</div>
                    </div>
                `;
            }
            
            // 数据洞察
            if (insights.data_insights) {
                const di = insights.data_insights;
                html += `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">🎵</div>
                            <div class="card-title">数据洞察</div>
                        </div>
                        <div class="visual-grid">
                            ${di.optimal_duration ? `
                                <div class="visual-item">
                                    <div class="visual-label">最佳时长</div>
                                    <div class="visual-value">${di.optimal_duration}</div>
                                </div>
                            ` : ''}
                            ${di.best_posting_time ? `
                                <div class="visual-item">
                                    <div class="visual-label">最佳发布时间</div>
                                    <div class="visual-value">${di.best_posting_time}</div>
                                </div>
                            ` : ''}
                            ${di.music_suggestion ? `
                                <div class="visual-item">
                                    <div class="visual-label">音乐建议</div>
                                    <div class="visual-value">${di.music_suggestion}</div>
                                </div>
                            ` : ''}
                        </div>
                        ${di.hashtag_strategy && di.hashtag_strategy.length > 0 ? `
                            <div style="margin-top: 20px;">
                                <div class="visual-label">标签策略</div>
                                <div class="viral-factors" style="margin-top: 10px;">
                                    ${di.hashtag_strategy.map(tag => `<span class="factor-tag" style="background: #667eea; color: white;">${tag}</span>`).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                `;
            }
            
            // 转录文本
            if (transcript.full_text && transcript.full_text.length > 0) {
                html += `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">🎤</div>
                            <div class="card-title">语音转录 (${transcript.full_text.length}字)</div>
                        </div>
                        <div style="line-height: 1.8; color: #555; max-height: 300px; overflow-y: auto;">
                            ${transcript.full_text}
                        </div>
                    </div>
                `;
            }
            
            reportDiv.innerHTML = html;
        }
        
        // 开始轮询
        pollTask();
    </script>
</body>
</html>"""
