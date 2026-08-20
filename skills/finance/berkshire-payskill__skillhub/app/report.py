"""AI Berkshire 四维投研分析报告模板"""

REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Berkshire 四维投研报告 - {{COMPANY_NAME}}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        
        .container { max-width: 1200px; margin: 0 auto; }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        
        .header h1 { font-size: 2.5em; color: #667eea; margin-bottom: 10px; font-weight: 700; }
        .header .subtitle { font-size: 1.2em; color: #666; margin-bottom: 20px; }
        .header .stock-info {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 30px;
            border-radius: 50px;
            font-size: 1.1em;
            font-weight: 600;
        }
        
        .loading-section {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 60px 40px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px; height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        .progress-text { font-size: 1.2em; color: #667eea; margin-bottom: 10px; }
        .progress-detail { color: #999; font-size: 0.95em; }
        
        .section-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 35px;
            margin-bottom: 25px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }
        
        .section-title {
            font-size: 1.6em;
            font-weight: 700;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .section-title .badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.7em;
            font-weight: 600;
        }
        
        .dimensions-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .dimension-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
            border-top: 4px solid;
        }
        
        .dimension-card:hover { transform: translateY(-5px); }
        .dimension-card.business { border-top-color: #4A90E2; }
        .dimension-card.financial { border-top-color: #7B68EE; }
        .dimension-card.industry { border-top-color: #FF6B6B; }
        .dimension-card.risk { border-top-color: #FFA500; }
        
        .dimension-header { display: flex; align-items: center; margin-bottom: 15px; }
        .dimension-icon { font-size: 2em; margin-right: 15px; }
        .dimension-title { flex: 1; }
        .dimension-title h3 { font-size: 1.3em; color: #333; margin-bottom: 5px; }
        .dimension-title .analyst { font-size: 0.9em; color: #999; }
        
        .score-badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 1.1em;
        }
        
        .dimension-summary { color: #666; line-height: 1.6; margin-top: 15px; }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin: 20px 0;
        }
        
        .chart-container.small { height: 250px; }
        
        .two-col {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 0.95em;
        }
        
        .data-table thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .data-table th {
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
        }
        
        .data-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }
        
        .data-table tbody tr:hover { background: #f8f9fa; }
        
        .data-table .highlight { font-weight: 600; color: #667eea; }
        .data-table .good { color: #4CAF50; }
        .data-table .warn { color: #FFA500; }
        .data-table .bad { color: #f44336; }
        
        .overall-score {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .overall-score .score {
            font-size: 4.5em;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }
        
        .overall-score .level { font-size: 1.5em; color: #666; font-weight: 600; }
        
        .thesis-section {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
        }
        
        .thesis-section h3 { color: #667eea; margin-bottom: 15px; font-size: 1.3em; }
        .thesis-section p { color: #555; line-height: 1.8; }
        
        .bull-bear-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 25px;
        }
        
        .bull-case, .bear-case {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
        }
        
        .bull-case { border-left: 4px solid #4CAF50; }
        .bear-case { border-left: 4px solid #f44336; }
        .bull-case h3 { color: #4CAF50; margin-bottom: 15px; }
        .bear-case h3 { color: #f44336; margin-bottom: 15px; }
        
        .bull-case ul, .bear-case ul { list-style: none; padding: 0; }
        .bull-case li, .bear-case li { padding: 8px 0; color: #555; line-height: 1.6; }
        .bull-case li::before { content: "✓ "; color: #4CAF50; font-weight: bold; margin-right: 8px; }
        .bear-case li::before { content: "✗ "; color: #f44336; font-weight: bold; margin-right: 8px; }
        
        .recommendation-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 25px;
        }
        
        .recommendation-section h3 { margin-bottom: 20px; font-size: 1.5em; }
        
        .recommendation-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        
        .recommendation-item {
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            border-radius: 10px;
            padding: 20px;
        }
        
        .recommendation-item .label { font-size: 0.9em; opacity: 0.8; margin-bottom: 8px; }
        .recommendation-item .value { font-size: 1.2em; font-weight: 600; }
        
        .checklist-section {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
        }
        
        .checklist-item {
            display: flex;
            align-items: flex-start;
            padding: 12px 0;
            border-bottom: 1px solid #eee;
        }
        
        .checklist-item:last-child { border-bottom: none; }
        
        .checklist-icon {
            width: 24px; height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
            flex-shrink: 0;
            font-size: 0.8em;
            color: white;
            margin-top: 2px;
        }
        
        .checklist-icon.pass { background: #4CAF50; }
        .checklist-icon.fail { background: #f44336; }
        
        .checklist-content { flex: 1; }
        .checklist-content .item-name { font-weight: 600; color: #333; margin-bottom: 4px; }
        .checklist-content .item-note { color: #666; font-size: 0.9em; }
        
        .final-verdict {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            border: 2px solid #667eea;
        }
        
        .final-verdict h3 { color: #667eea; margin-bottom: 15px; font-size: 1.5em; }
        .final-verdict p { color: #555; font-size: 1.1em; line-height: 1.8; }
        
        .detail-text { color: #555; line-height: 1.8; margin: 10px 0; }
        .detail-label { font-weight: 600; color: #667eea; margin-bottom: 8px; }
        
        .moat-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        
        .moat-item .name { font-weight: 600; color: #333; }
        .moat-item .desc { color: #666; font-size: 0.9em; flex: 1; margin: 0 15px; }
        .moat-item .score { color: #667eea; font-weight: 700; }
        
        .competitor-row {
            display: flex;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .competitor-name { font-weight: 600; width: 120px; color: #333; }
        .competitor-bar { flex: 1; height: 20px; background: #f0f0f0; border-radius: 10px; margin: 0 15px; overflow: hidden; }
        .competitor-fill { height: 100%; border-radius: 10px; transition: width 0.8s ease; }
        .competitor-share { font-weight: 600; color: #667eea; width: 60px; text-align: right; }
        
        .risk-item {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #FFA500;
        }
        
        .risk-item.high { border-left-color: #f44336; }
        .risk-item.medium { border-left-color: #FFA500; }
        .risk-item.low { border-left-color: #4CAF50; }
        
        .risk-item .risk-title { font-weight: 600; color: #333; margin-bottom: 5px; }
        .risk-item .risk-desc { color: #666; font-size: 0.9em; }
        
        .footer {
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            margin-top: 40px;
            font-size: 0.9em;
        }
        
        .hidden { display: none; }
        
        @media (max-width: 768px) {
            .two-col, .bull-bear-grid { grid-template-columns: 1fr; }
            .dimensions-grid { grid-template-columns: 1fr; }
        }
        
        /* 风险矩阵样式 */
        .risk-matrix-score {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 0.9em;
            color: white;
        }
        .risk-matrix-score.high { background: #f44336; }
        .risk-matrix-score.medium { background: #FFA500; }
        .risk-matrix-score.low { background: #4CAF50; }
        
        /* 监测指标仪表盘样式 */
        .monitoring-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 15px;
        }
        
        .monitoring-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 12px;
            padding: 20px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            transition: transform 0.2s ease;
        }
        
        .monitoring-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .monitoring-card .indicator-name {
            font-weight: 700;
            color: #667eea;
            font-size: 1.05em;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .monitoring-card .indicator-details {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 8px;
            font-size: 0.9em;
            color: #555;
        }
        
        .monitoring-card .indicator-details .label {
            font-weight: 600;
            color: #666;
        }
        
        .monitoring-card.priority-high {
            border-left-color: #f44336;
        }
        .monitoring-card.priority-medium {
            border-left-color: #FFA500;
        }
        .monitoring-card.priority-low {
            border-left-color: #4CAF50;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 AI Berkshire 四维投研报告</h1>
            <div class="subtitle">段永平 · 巴菲特 · 芒格 · 李录</div>
            <div class="stock-info">{{COMPANY_NAME}} ({{STOCK_CODE}})</div>
        </div>
        
        <div id="loading-section" class="loading-section">
            <div class="spinner"></div>
            <div class="progress-text">正在分析中...</div>
            <div class="progress-detail" id="progress-detail">初始化分析团队</div>
        </div>
        
        <div id="result-section" class="hidden">
            <!-- 四维评分概览 -->
            <div class="dimensions-grid" id="dimensions-grid"></div>
            
            <!-- 综合投资评估 -->
            <div class="section-card">
                <div class="section-title">🎯 综合投资评估</div>
                <div class="overall-score">
                    <div class="score" id="overall-score">0.0</div>
                    <div class="level" id="score-level">评估中</div>
                </div>
                
                <div class="thesis-section">
                    <h3>📝 投资论点</h3>
                    <p id="investment-thesis"></p>
                </div>
                
                <div class="bull-bear-grid">
                    <div class="bull-case">
                        <h3>🟢 看多理由</h3>
                        <ul id="bull-case-list"></ul>
                    </div>
                    <div class="bear-case">
                        <h3>🔴 看空理由</h3>
                        <ul id="bear-case-list"></ul>
                    </div>
                </div>
            </div>
            
            <!-- 商业模式详情 -->
            <div class="section-card" id="business-detail" style="display:none">
                <div class="section-title">🏢 商业模式分析 <span class="badge">段永平视角</span></div>
                <div id="business-model-text"></div>
                <div class="two-col">
                    <div>
                        <div class="detail-label">护城河雷达图</div>
                        <div class="chart-container small">
                            <canvas id="moat-radar-chart"></canvas>
                        </div>
                    </div>
                    <div>
                        <div class="detail-label">护城河明细</div>
                        <div id="moat-details"></div>
                    </div>
                </div>
            </div>
            
            <!-- 财务分析详情 -->
            <div class="section-card" id="financial-detail" style="display:none">
                <div class="section-title">💰 财务分析 <span class="badge">巴菲特视角</span></div>
                <div id="financial-summary"></div>
                
                <div class="two-col" style="margin-top: 25px">
                    <div>
                        <div class="detail-label">财务趋势（近5年）</div>
                        <div class="chart-container small">
                            <canvas id="financial-trend-chart"></canvas>
                        </div>
                    </div>
                    <div>
                        <div class="detail-label">同行估值对比</div>
                        <div class="chart-container small">
                            <canvas id="peer-comparison-chart"></canvas>
                        </div>
                    </div>
                </div>
                
                <div class="detail-label" style="margin-top: 25px">业务分拆数据</div>
                <table class="data-table" id="segment-financials-table">
                    <thead>
                        <tr><th>业务板块</th><th>收入(亿)</th><th>增速</th><th>毛利率</th><th>利润贡献</th></tr>
                    </thead>
                    <tbody></tbody>
                </table>
                
                <div class="detail-label" style="margin-top: 25px">关键财务指标</div>
                <table class="data-table" id="financial-metrics-table">
                    <thead>
                        <tr><th>指标</th><th>公司</th><th>行业平均</th><th>评估</th></tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
            
            <!-- 行业格局详情 -->
            <div class="section-card" id="industry-detail" style="display:none">
                <div class="section-title">🌍 行业格局分析 <span class="badge">芒格视角</span></div>
                <div id="industry-summary"></div>
                
                <div class="two-col" style="margin-top: 25px">
                    <div>
                        <div class="detail-label">市场份额分布</div>
                        <div class="chart-container small">
                            <canvas id="market-share-chart"></canvas>
                        </div>
                    </div>
                    <div>
                        <div class="detail-label">竞争对手分析</div>
                        <div id="competitors-list"></div>
                    </div>
                </div>
                
                <div class="detail-label" style="margin-top: 25px">行业关键指标</div>
                <table class="data-table" id="industry-metrics-table">
                    <thead>
                        <tr><th>指标</th><th>数值</th><th>趋势</th></tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
            
            <!-- 风险评估详情 -->
            <div class="section-card" id="risk-detail" style="display:none">
                <div class="section-title">⚠️ 风险评估 <span class="badge">李录视角</span></div>
                <div id="risk-summary"></div>
                
                <div class="detail-label" style="margin-top: 20px">风险收益评估</div>
                <div class="two-col">
                    <div>
                        <div class="chart-container small">
                            <canvas id="risk-reward-chart"></canvas>
                        </div>
                    </div>
                    <div id="risk-items-list"></div>
                </div>
                
                <!-- 风险矩阵 -->
                <div class="detail-label" style="margin-top: 30px">🎯 风险矩阵（概率×影响）</div>
                <table class="data-table" id="risk-matrix-table">
                    <thead>
                        <tr>
                            <th>风险因素</th>
                            <th>概率<br><small>(1-5)</small></th>
                            <th>影响<br><small>(1-5)</small></th>
                            <th>风险评分</th>
                            <th>应对措施</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
                
                <!-- 监测指标仪表盘 -->
                <div class="detail-label" style="margin-top: 30px">📊 关键监测指标仪表盘</div>
                <div class="monitoring-dashboard">
                    <div class="monitoring-grid" id="monitoring-indicators"></div>
                </div>
                
                <!-- 事件驱动日历 -->
                <div class="detail-label" style="margin-top: 30px">📅 事件驱动日历</div>
                <table class="data-table" id="event-calendar-table">
                    <thead>
                        <tr>
                            <th>时间节点</th>
                            <th>事件</th>
                            <th>预期影响</th>
                            <th>应对策略</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
            
            <!-- 投资建议 -->
            <div class="section-card">
                <div class="section-title">💡 投资建议</div>
                
                <div class="recommendation-section">
                    <h3>🎯 操作建议</h3>
                    <div class="recommendation-grid">
                        <div class="recommendation-item">
                            <div class="label">操作建议</div>
                            <div class="value" id="action-type">-</div>
                        </div>
                        <div class="recommendation-item">
                            <div class="label">建议仓位</div>
                            <div class="value" id="position-size">-</div>
                        </div>
                        <div class="recommendation-item">
                            <div class="label">建仓策略</div>
                            <div class="value" id="entry-strategy">-</div>
                        </div>
                        <div class="recommendation-item">
                            <div class="label">退出条件</div>
                            <div class="value" id="exit-conditions">-</div>
                        </div>
                    </div>
                </div>
                
                <div class="checklist-section">
                    <div class="detail-label">📋 巴菲特买入检查清单</div>
                    <div id="checklist-items"></div>
                </div>
                
                <div class="final-verdict">
                    <h3>✅ 最终结论</h3>
                    <p id="final-verdict"></p>
                </div>
            </div>
        </div>
        
        <div id="error-section" class="section-card hidden" style="border-top: 4px solid #f44336;">
            <h2 style="color: #f44336; margin-bottom: 20px;">分析失败</h2>
            <p id="error-message" style="color: #666;"></p>
        </div>
        
        <div class="footer">
            <p>AI Berkshire 四维投研分析系统 | 仅供参考，不构成投资建议</p>
            <p style="margin-top: 5px; opacity: 0.7;">Powered by 熵海领航</p>
        </div>
    </div>
    
    <script>
        const taskId = "{{TASK_ID}}";
        const pollInterval = 3000;
        
        async function pollTaskStatus() {
            try {
                const response = await fetch(`../api/task/${taskId}`);
                const data = await response.json();
                
                if (data.status === 'completed') {
                    displayResult(data.result);
                } else if (data.status === 'failed') {
                    displayError(data.error || '分析失败');
                } else if (data.status === 'processing') {
                    updateProgress(data.progress);
                    setTimeout(pollTaskStatus, pollInterval);
                } else {
                    setTimeout(pollTaskStatus, pollInterval);
                }
            } catch (error) {
                console.error('Polling error:', error);
                setTimeout(pollTaskStatus, pollInterval);
            }
        }
        
        function updateProgress(progress) {
            if (!progress) return;
            const detail = document.getElementById('progress-detail');
            const messages = Object.entries(progress).map(([k,v]) => `${k}: ${v}`);
            if (messages.length > 0) detail.textContent = messages.join(' | ');
        }
        
        function displayResult(result) {
            document.getElementById('loading-section').classList.add('hidden');
            document.getElementById('result-section').classList.remove('hidden');
            
            const dimensions = [
                { id: 'business', name: '商业模式', analyst: '段永平', icon: '🏢' },
                { id: 'financial', name: '财务分析', analyst: '巴菲特', icon: '💰' },
                { id: 'industry', name: '行业格局', analyst: '芒格', icon: '🌍' },
                { id: 'risk', name: '风险评估', analyst: '李录', icon: '⚠️' }
            ];
            
            const grid = document.getElementById('dimensions-grid');
            dimensions.forEach(dim => {
                const d = result.dimensions[dim.id];
                if (!d) return;
                const card = document.createElement('div');
                card.className = `dimension-card ${dim.id}`;
                card.innerHTML = `
                    <div class="dimension-header">
                        <div class="dimension-icon">${dim.icon}</div>
                        <div class="dimension-title">
                            <h3>${dim.name}</h3>
                            <div class="analyst">${dim.analyst}视角</div>
                        </div>
                        <div class="score-badge">${d.score || 0}/5</div>
                    </div>
                    <div class="dimension-summary">${d.summary || '分析完成'}</div>
                `;
                grid.appendChild(card);
            });
            
            // 综合评估
            const synthesis = result.synthesis || {};
            document.getElementById('overall-score').textContent = (synthesis.overall_score || 0).toFixed(1);
            document.getElementById('score-level').textContent = synthesis.score_level || '评估完成';
            document.getElementById('investment-thesis').textContent = synthesis.investment_thesis || '';
            
            // 看多/看空
            (synthesis.bull_case || []).forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                document.getElementById('bull-case-list').appendChild(li);
            });
            (synthesis.bear_case || []).forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                document.getElementById('bear-case-list').appendChild(li);
            });
            
            // 投资建议
            const action = synthesis.action_recommendation || {};
            document.getElementById('action-type').textContent = action.type || '-';
            document.getElementById('position-size').textContent = action.position_size || '-';
            document.getElementById('entry-strategy').textContent = action.entry_strategy || '-';
            document.getElementById('exit-conditions').textContent = action.exit_conditions || '-';
            
            // 检查清单
            const checklistDiv = document.getElementById('checklist-items');
            (synthesis.checklist || []).forEach(item => {
                const div = document.createElement('div');
                div.className = 'checklist-item';
                div.innerHTML = `
                    <div class="checklist-icon ${item.pass ? 'pass' : 'fail'}">${item.pass ? '✓' : '✗'}</div>
                    <div class="checklist-content">
                        <div class="item-name">${item.item || ''}</div>
                        <div class="item-note">${item.note || ''}</div>
                    </div>
                `;
                checklistDiv.appendChild(div);
            });
            
            document.getElementById('final-verdict').textContent = synthesis.final_verdict || '';
            
            // 渲染详情
            renderBusinessDetail(result.dimensions.business);
            renderFinancialDetail(result.dimensions.financial);
            renderIndustryDetail(result.dimensions.industry);
            renderRiskDetail(result.dimensions.risk);
        }
        
        function renderBusinessDetail(d) {
            if (!d) return;
            const section = document.getElementById('business-detail');
            section.style.display = 'block';
            
            // 商业模式文字
            const textDiv = document.getElementById('business-model-text');
            textDiv.innerHTML = `
                <div class="detail-label">生意本质</div>
                <p class="detail-text">${d.business_model || '-'}</p>
                <div class="detail-label" style="margin-top:15px">差异化与定价权</div>
                <p class="detail-text">${d.differentiation || '-'}</p>
                <div class="detail-label" style="margin-top:15px">可持续竞争优势</div>
                <p class="detail-text">${d.competitive_advantage || '-'}</p>
                <div class="detail-label" style="margin-top:15px">管理层评估</div>
                <p class="detail-text">${d.management || '-'}</p>
            `;
            
            // 护城河雷达图
            const moat = d.moat_analysis || {};
            const moatData = d.moat_radar || [
                moat.brand?.score || 3,
                moat.switching_cost?.score || 3,
                moat.network_effect?.score || 3,
                moat.scale_economy?.score || 3,
                moat.tech_barrier?.score || 3
            ];
            
            new Chart(document.getElementById('moat-radar-chart'), {
                type: 'radar',
                data: {
                    labels: ['品牌', '转换成本', '网络效应', '规模效应', '技术壁垒'],
                    datasets: [{
                        label: '护城河评分',
                        data: moatData,
                        backgroundColor: 'rgba(102, 126, 234, 0.2)',
                        borderColor: '#667eea',
                        borderWidth: 2,
                        pointBackgroundColor: '#667eea',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: '#667eea'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: { beginAtZero: true, max: 5, ticks: { stepSize: 1 } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
            
            // 护城河明细
            const moatDetails = document.getElementById('moat-details');
            const moatNames = { brand: '品牌', switching_cost: '转换成本', network_effect: '网络效应', scale_economy: '规模效应', tech_barrier: '技术壁垒' };
            Object.entries(moatNames).forEach(([key, name]) => {
                const m = moat[key];
                if (!m) return;
                const desc = typeof m === 'object' ? m.desc : m;
                const score = typeof m === 'object' ? m.score : '-';
                const div = document.createElement('div');
                div.className = 'moat-item';
                div.innerHTML = `<span class="name">${name}</span><span class="desc">${desc}</span><span class="score">${score}/5</span>`;
                moatDetails.appendChild(div);
            });
        }
        
        function renderFinancialDetail(d) {
            if (!d) return;
            const section = document.getElementById('financial-detail');
            section.style.display = 'block';
            
            // 财务摘要
            const summary = document.getElementById('financial-summary');
            const p = d.profitability || {};
            const cf = d.cash_flow || {};
            const bs = d.balance_sheet || {};
            const g = d.growth || {};
            const v = d.valuation || {};
            
            summary.innerHTML = `
                <div class="two-col">
                    <div>
                        <div class="detail-label">盈利能力</div>
                        <p class="detail-text">${p.analysis || '-'}</p>
                        <div class="detail-label" style="margin-top:10px">现金流质量</div>
                        <p class="detail-text">${cf.quality || '-'}</p>
                    </div>
                    <div>
                        <div class="detail-label">资产负债健康度</div>
                        <p class="detail-text">${bs.health || '-'}</p>
                        <div class="detail-label" style="margin-top:10px">增长质量</div>
                        <p class="detail-text">${g.quality || '-'}</p>
                    </div>
                </div>
                <div class="detail-label" style="margin-top:15px">估值评估</div>
                <p class="detail-text">当前PE: ${v.current_pe || '-'} | PB: ${v.current_pb || '-'} | ${v.assessment || ''}</p>
                <p class="detail-text"><strong>安全边际：</strong>${d.margin_of_safety || '-'}</p>
            `;
            
            // 财务趋势图 (5年)
            const trends5y = d.financial_trends_5y || {};
            const years = trends5y.years || ['2019', '2020', '2021', '2022', '2023'];
            const revenue = trends5y.revenue || [];
            const profit = trends5y.profit || [];
            const cashFlow = trends5y.cash_flow || [];
            
            if (revenue.length > 0 || profit.length > 0) {
                new Chart(document.getElementById('financial-trend-chart'), {
                    type: 'bar',
                    data: {
                        labels: years.slice(0, Math.max(revenue.length, profit.length)),
                        datasets: [
                            {
                                label: '营收(亿)',
                                data: revenue,
                                backgroundColor: 'rgba(102, 126, 234, 0.7)',
                                borderRadius: 5,
                                order: 2
                            },
                            {
                                label: '净利润(亿)',
                                data: profit,
                                backgroundColor: 'rgba(123, 104, 238, 0.7)',
                                borderRadius: 5,
                                order: 2
                            },
                            {
                                label: '现金流(亿)',
                                type: 'line',
                                data: cashFlow,
                                borderColor: '#FF6B6B',
                                backgroundColor: 'rgba(255, 107, 107, 0.1)',
                                borderWidth: 2,
                                fill: true,
                                order: 1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { position: 'top' } },
                        scales: { y: { beginAtZero: true } }
                    }
                });
            }
            
            // 业务分拆表
            const segTable = document.getElementById('segment-financials-table');
            if (segTable) {
                const tbody = segTable.querySelector('tbody');
                (d.segment_financials || []).forEach(s => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td class="highlight">${s.name || ''}</td>
                        <td><strong>${s.revenue || '-'}</strong></td>
                        <td>${s.growth || '-'}</td>
                        <td>${s.margin || '-'}</td>
                        <td>${s.contribution || '-'}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
            
            // 同行对比图
            const peer = d.peer_comparison || {};
            const peerLabels = ['PE', 'PB', 'ROE(%)'];
            const companyVals = [
                parseFloat(peer.pe?.company) || 0,
                parseFloat(peer.pb?.company) || 0,
                parseFloat(peer.roe?.company) || 0
            ];
            const avgVals = [
                parseFloat(peer.pe?.avg) || 0,
                parseFloat(peer.pb?.avg) || 0,
                parseFloat(peer.roe?.avg) || 0
            ];
            
            if (companyVals.some(v => v > 0)) {
                new Chart(document.getElementById('peer-comparison-chart'), {
                    type: 'bar',
                    data: {
                        labels: peerLabels,
                        datasets: [
                            {
                                label: '{{COMPANY_NAME}}',
                                data: companyVals,
                                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                                borderRadius: 5
                            },
                            {
                                label: '行业平均',
                                data: avgVals,
                                backgroundColor: 'rgba(200, 200, 200, 0.6)',
                                borderRadius: 5
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { position: 'top' } },
                        scales: { y: { beginAtZero: true } }
                    }
                });
            }
            
            // 关键指标表
            const tbody = document.querySelector('#financial-metrics-table tbody');
            (d.key_metrics || []).forEach(m => {
                const tr = document.createElement('tr');
                const assessment = m.assessment || '';
                const cls = /优秀|极高|很高|很强/.test(assessment) ? 'good' : /一般|适中/.test(assessment) ? 'warn' : /偏高|偏低|较差/.test(assessment) ? 'bad' : '';
                tr.innerHTML = `
                    <td class="highlight">${m.name || ''}</td>
                    <td><strong>${m.value || ''}</strong></td>
                    <td>${m.industry_avg || '-'}</td>
                    <td class="${cls}">${assessment}</td>
                `;
                tbody.appendChild(tr);
            });
        }
        
        function renderIndustryDetail(d) {
            if (!d) return;
            const section = document.getElementById('industry-detail');
            section.style.display = 'block';
            
            const ms = d.market_size || {};
            const comp = d.competition || {};
            const summary = document.getElementById('industry-summary');
            summary.innerHTML = `
                <div class="two-col">
                    <div>
                        <div class="detail-label">行业空间</div>
                        <p class="detail-text">市场规模: ${ms.current || '-'} | 增速: ${ms.growth_rate || '-'}</p>
                        <p class="detail-text">天花板: ${ms.ceiling || '-'}</p>
                        <p class="detail-text">${ms.assessment || ''}</p>
                    </div>
                    <div>
                        <div class="detail-label">竞争格局</div>
                        <p class="detail-text">集中度: ${comp.concentration || '-'}</p>
                        <p class="detail-text">市场地位: ${comp.position || '-'}</p>
                        <p class="detail-text">${comp.dynamics || ''}</p>
                    </div>
                </div>
                <div class="detail-label" style="margin-top:15px">护城河持续性</div>
                <p class="detail-text">${d.moat_sustainability || '-'}</p>
                <div class="detail-label" style="margin-top:10px">替代风险</div>
                <p class="detail-text">${d.substitution_risk || '-'}</p>
            `;
            
            // 市场份额饼图
            const shareData = d.market_share_data || {};
            const shareLabels = [];
            const shareValues = [];
            
            if (shareData.company || shareData.top1) {
                if (shareData.top1) { shareLabels.push('第一名'); shareValues.push(parseFloat(shareData.top1) || 0); }
                if (shareData.top2) { shareLabels.push('第二名'); shareValues.push(parseFloat(shareData.top2) || 0); }
                if (shareData.top3) { shareLabels.push('第三名'); shareValues.push(parseFloat(shareData.top3) || 0); }
                if (shareData.company) { shareLabels.push('{{COMPANY_NAME}}'); shareValues.push(parseFloat(shareData.company) || 0); }
                const others = 100 - shareValues.reduce((a,b) => a+b, 0);
                if (others > 0) { shareLabels.push('其他'); shareValues.push(others); }
            }
            
            if (shareValues.length > 0) {
                new Chart(document.getElementById('market-share-chart'), {
                    type: 'doughnut',
                    data: {
                        labels: shareLabels,
                        datasets: [{
                            data: shareValues,
                            backgroundColor: ['#4A90E2', '#7B68EE', '#FF6B6B', '#667eea', '#e0e0e0'],
                            borderWidth: 2,
                            borderColor: '#fff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom' }
                        }
                    }
                });
            }
            
            // 竞争对手列表
            const compList = document.getElementById('competitors-list');
            const players = comp.players || [];
            if (Array.isArray(players)) {
                players.forEach(p => {
                    const share = parseFloat(p.share) || 0;
                    const div = document.createElement('div');
                    div.className = 'competitor-row';
                    div.innerHTML = `
                        <span class="competitor-name">${p.name || ''}</span>
                        <div class="competitor-bar">
                            <div class="competitor-fill" style="width:${Math.min(share*3, 100)}%; background: linear-gradient(90deg, #667eea, #764ba2);"></div>
                        </div>
                        <span class="competitor-share">${p.share || ''}</span>
                    `;
                    compList.appendChild(div);
                });
            }
            
            // 行业指标表
            const tbody = document.querySelector('#industry-metrics-table tbody');
            (d.industry_metrics || []).forEach(m => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="highlight">${m.name || ''}</td>
                    <td><strong>${m.value || ''}</strong></td>
                    <td>${m.trend || ''}</td>
                `;
                tbody.appendChild(tr);
            });
        }
        
        function renderRiskDetail(d) {
            if (!d) return;
            const section = document.getElementById('risk-detail');
            section.style.display = 'block';
            
            const sr = d.systematic_risks || {};
            const cr = d.company_risks || {};
            const rr = d.risk_reward || {};
            
            const summary = document.getElementById('risk-summary');
            summary.innerHTML = `
                <div class="two-col">
                    <div>
                        <div class="detail-label">系统性风险</div>
                        <p class="detail-text">${sr.assessment || '-'}</p>
                        <div class="detail-label" style="margin-top:10px">估值风险</div>
                        <p class="detail-text">${d.valuation_risk || '-'}</p>
                    </div>
                    <div>
                        <div class="detail-label">公司特定风险</div>
                        <p class="detail-text">${cr.assessment || '-'}</p>
                        <div class="detail-label" style="margin-top:10px">风险缓释</div>
                        ${(d.mitigation || []).map(m => `<p class="detail-text">• ${m}</p>`).join('')}
                    </div>
                </div>
            `;
            
            // 风险收益图
            const upside = parseFloat(rr.upside) || 0;
            const downside = parseFloat(rr.downside) || 0;
            
            new Chart(document.getElementById('risk-reward-chart'), {
                type: 'bar',
                data: {
                    labels: ['潜在上涨', '潜在下跌'],
                    datasets: [{
                        data: [upside || 30, downside || 20],
                        backgroundColor: ['rgba(76, 175, 80, 0.7)', 'rgba(244, 67, 54, 0.7)'],
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false },
                        tooltip: { callbacks: { label: ctx => `${ctx.raw}%` } }
                    },
                    scales: {
                        x: { beginAtZero: true, ticks: { callback: v => v + '%' } }
                    }
                }
            });
            
            // 风险列表
            const riskList = document.getElementById('risk-items-list');
            const allRisks = [
                ...(d.key_risks || []).map(r => ({ title: r, level: 'medium' })),
                ...(d.black_swan || []).map(r => ({ title: r, level: 'high' })),
                ...(d.long_term_risks || []).map(r => ({ title: r, level: 'low' }))
            ];
            
            allRisks.forEach(r => {
                const div = document.createElement('div');
                div.className = `risk-item ${r.level}`;
                div.innerHTML = `<div class="risk-title">${r.level === 'high' ? '🔴' : r.level === 'medium' ? '🟡' : '🟢'} ${r.title}</div>`;
                riskList.appendChild(div);
            });
            
            // 风险矩阵
            const riskMatrix = d.risk_matrix || [];
            if (riskMatrix.length > 0) {
                const tbody = document.querySelector('#risk-matrix-table tbody');
                riskMatrix.forEach(r => {
                    const score = r.score || (r.probability * r.impact);
                    const cls = score >= 15 ? 'high' : score >= 8 ? 'medium' : 'low';
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td class="highlight">${r.risk || ''}</td>
                        <td style="text-align:center">${r.probability || '-'}/5</td>
                        <td style="text-align:center">${r.impact || '-'}/5</td>
                        <td><span class="risk-matrix-score ${cls}">${score}</span></td>
                        <td>${r.mitigation || '-'}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
            
            // 监测指标仪表盘
            const monitoringDiv = document.getElementById('monitoring-indicators');
            const indicators = d.monitoring_indicators || [];
            indicators.forEach(m => {
                const priority = (m.priority || 'medium').toLowerCase();
                const priorityIcon = priority === 'high' ? '🔴' : priority === 'medium' ? '🟡' : '🟢';
                const div = document.createElement('div');
                div.className = `monitoring-card priority-${priority}`;
                div.innerHTML = `
                    <div class="indicator-name">${priorityIcon} ${m.indicator || ''}</div>
                    <div class="indicator-details">
                        <span class="label">频率:</span><span>${m.frequency || '-'}</span>
                        <span class="label">阈值:</span><span>${m.threshold || '-'}</span>
                        <span class="label">行动:</span><span>${m.action || '-'}</span>
                    </div>
                `;
                monitoringDiv.appendChild(div);
            });
            
            // 事件驱动日历
            const events = d.event_calendar || [];
            if (events.length > 0) {
                const tbody = document.querySelector('#event-calendar-table tbody');
                events.forEach(e => {
                    const impact = e.impact || '';
                    const impactCls = /高/.test(impact) ? 'bad' : /中/.test(impact) ? 'warn' : 'good';
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td class="highlight">${e.date || '-'}</td>
                        <td>${e.event || ''}</td>
                        <td class="${impactCls}">${impact}</td>
                        <td>${e.strategy || '-'}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        }
        
        function displayError(error) {
            document.getElementById('loading-section').classList.add('hidden');
            document.getElementById('error-section').classList.remove('hidden');
            document.getElementById('error-message').textContent = error;
        }
        
        pollTaskStatus();
    </script>
</body>
</html>
"""
