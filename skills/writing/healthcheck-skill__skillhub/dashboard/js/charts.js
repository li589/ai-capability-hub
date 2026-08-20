// 工具函数
const utils = {
    formatDate: (date) => {
        return date.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', weekday: 'long', hour12: false }) + ' ' ' + date.toLocaleString('zh-CN', { hour12: false });
    },
    
    formatNumber: (num, decimals = 1) => {
        return num.toLocaleString('zh-CN', { minimumFractionDigits: decimals });
    },
    
    formatPercent: (num, decimals = 1) => {
        return num.toLocaleString('zh-CN', { style: 'percent', minimumFractionDigits: decimals }) + '%';
    }
};

// 主函数
document.addEventListener('DOMContentLoaded', function() {
    // 初始化
    initDashboard();
    
    // 定时刷新
    setInterval(refreshDashboard, 30000); // 5分钟
    
    // 按钮事件
    document.querySelector('.refresh-dashboard').addEventListener('click', refreshDashboard);
    document.querySelector('.export-report').addEventListener('click', exportReport);
    document.querySelector('.collect-baseline').addEventListener('click', collectBaseline);
});

// 初始化仪表盘
async function initDashboard() {
    updateLastUpdated();
    await refreshDashboard();
}

// 刷新仪表盘
async function refreshDashboard() {
    try {
        // 获取所有数据
        const [statusResponse, metricsResponse, anomaliesResponse, eventsResponse] = await Promise.all([
            fetch('/api/status'),
            fetch('/api/metrics'),
            fetch('/api/anomalies'),
            fetch('/api/events')
        ]);
        
        const status = await statusResponse.json();
        const metrics = await metricsResponse.json();
        const anomalies = await anomaliesResponse.json();
        const events = await eventsResponse.json();
        
        // 更新最后更新时间
        document.getElementById('last-updated').textContent = utils.formatDate(new Date());
        
        // 更新安全评分
        updateScore(status.security_score);
        
        // 更新实时监控
        updateMonitoring(metrics);
        
        // 更新CVE状态
        updateCVE(status.cve_status);
        
        // 更新误报率趋势
        await updateTrend(anomalies);
        
        // 更新威胁时间线
        updateTimeline(events);
        
        // 更新系统信息
        updateSystemInfo(status.system_info);
        
    } catch (error) {
        console.error('刷新仪表盘失败:', error);
    }
}

// 更新安全评分
function updateScore(score) {
    const scoreEl = document.getElementById('score-value');
    const statusEl = document.getElementById('score-status');
    
    if (score !== null) {
        scoreEl.textContent = utils.formatPercent(score);
        
        // 设置颜色
        if (score >= 90) {
            scoreEl.style.color = '#4CAF50'; // 绿色
            statusEl.textContent = '优秀';
        } else if (score >= 80) {
            scoreEl.style.color = '#FFA500'; // 橙色
            statusEl.textContent = '良好';
        } else if (score >= 60) {
            scoreEl.style.color = '#FFC107'; // 黄色
            statusEl.textContent = '注意';
        } else {
            scoreEl.style.color = '#F44336'; // 红色
            statusEl.textContent = '危险';
        }
    }
}

// 更新实时监控
function updateMonitoring(metrics) {
    if (!metrics || !metrics.current) return;
    
    // 更新CPU
    updateMonitoringCard('cpu-value', metrics.current?.cpu_percent, '高');
    
    // 更新内存
    updateMonitoringCard('mem-value', metrics.current?.memory_percent, '高');
    
    // 更新I/O
    let io_percent = (parseFloat(metrics.current?.io_wait_percent || 0);
    let io_level = '低';
    if (io_percent > 80) io_level = '严重';
    elif (io_percent > 60) io_level = '高';
    updateMonitoringCard('io-value', metrics.current?.io_wait_percent, io_level);
    
    // 更新网络
    if (metrics.current?.network_in_kbps) {
        const in_mbps = parseFloat(metrics.current.network_in_kbps);
        const in_level = in_mbps > 500 ? '严重' : in_mbps > 100 ? '高' : '正常';
        updateMonitoringCard('in-value', utils.formatNumber(in_mbps, 1), in_level);
    }
    
    if (metrics.current?.network_out_kbps) {
        const out_mbps = parseFloat(metrics.current.network_out_kbps);
        const out_level = out_mbps > 500 ? '严重' : in_mbps > 100 ? '高' : '正常';
        updateMonitoringCard('out-value', utils.formatNumber(out_mbps, 1), out_level);
    }
}

function updateMonitoringCard(elementId, value, level) {
    const el = document.getElementById(elementId);
    if (!el) return;
    
    el.textContent = utils.formatNumber(value);
    el.className = `monitor-card ${level}`;
}

// 更新CVE状态
function updateCVE(cveStatus) {
    if (!cveStatus) return;
    
    document.getElementById('cve-total').textContent = cveStatus.total || 0;
    document.getElementById('cve-vulnerable').textContent = cveStatus.vulnerable || 0;
    document.getElementById('cve-patched').textContent = cveStatus.patched || 0;
    
    // 设置颜色
    const critical_count = parseInt(cveStatus.vulnerable || 0);
    if (critical_count > 0) {
        document.getElementById('cve-total').style.color = '#DC2626'; // 红色
    }
}

// 更新误报率趋势
async function updateTrend(anomalies) {
    const chartContainer = document.getElementById('chart-container');
    if (!chartContainer) return;
    
    const anomalies = anomalies || [];
    // 解析数据
    const trendData = anomalies.filter(a => a.severity !== 'info');
    
    const dataPoints = trendData.map((a, index) => ({
        x: new Date(a.timestamp).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
        y: a.score
    }));
    
    // 销毁旧图表
    chartContainer.innerHTML = '';
    
    // 创建新图表
    const canvas = document.getElementById('trend-chart');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 绘制网格和轴
        drawGrid(ctx, canvas.width, canvas.height, dataPoints);
        drawAxes(ctx, canvas.width, canvas.height, dataPoints);
        drawLine(ctx, canvas.width, canvas.height, dataPoints);
        drawPoints(ctx, canvas.width, canvas.height, dataPoints);
        drawLine(ctx, canvas.width, canvas.height, dataPoints);
        
        // 绘制零线
        drawZeroLine(ctx, canvas.width, canvas.height);
    }
}

// 更新威胁时间线
function updateTimeline(events) {
    const container = document.getElementById('timeline-container');
    const itemsContainer = document.getElementById('timeline-items');
    
    if (!container || !itemsContainer) return;
    
    itemsContainer.innerHTML = '';
    
    const uniqueEvents = {};
    
    if (events && events.length > 0) {
        // 去重：只显示最近的20个事件
        const recentEvents = events.slice(-20);
        
        recentEvents.forEach(event => {
            const key = `${event.timestamp}`;
            if (!uniqueEvents[key]) {
                uniqueEvents[key] = event;
                
                const item = document.createElement('div');
                item.className = 'timeline-item';
                
                const timeStr = utils.formatDate(new Date(event.timestamp));
                let color = '#4CAF50'; // 绿色
                if (event.severity === 'critical') color = '#DC2626';
                if (event.severity === 'high') color = '#F59E0B4';
                if (event.severity === 'warning') color = '#F0A202';
                
                item.style.borderLeftColor = color;
                item.innerHTML = `
                    <div class="time">${timeStr}</div>
                    <div class="content">${event.message}</div>
                    <div class="severity ${event.severity}">${event.severity.toUpperCase()}</div>
                `;
                
                itemsContainer.appendChild(item);
            }
        });
    } else {
        itemsContainer.innerHTML = '<div style="color: #888; text-align: center; padding: 20px;">暂无事件数据</div>';
    }
}

// 更新系统信息
function updateSystemInfo(systemInfo) {
    if (!systemInfo) return;
    
    document.getElementById('info-hostname').textContent = systemInfo.hostname || '--';
    document.getElementById('info-os').textContent = systemInfo.os || '--';
    document.getElementById('info-version').textContent = systemInfo.version || '--';
    document.getElementById('info-cve').textContent = systemInfo.cve_count || 0;
    document.getElementById('info-fp').textContent = utils.formatPercent(systemInfo.false_positive_rate || 0);
    document.getElementById('threat-count').textContent = systemInfo.threat_count || 0;
}

// 导出报告
function exportReport() {
    alert('报告生成功能开发中...');
    // TODO: 实现报告生成和下载
}

// 学习基线
function collect_baseline() {
    alert('基线学习功能开发中...');
    // TODO: 实现基线学习功能
}

// 绘制网格
function drawGrid(ctx, width, height, data) {
    const padding = 50;
    const gridSize = 60;
    const xSteps = (width - padding * 2) / gridSize;
    const ySteps = (height - padding * 2) / gridSize;
    
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 0.5;
    ctx.font = '12px sans-serif';
    ctx.fillStyle = '#f8f9fa';
    
    // 绘制垂直网格线
    ctx.beginPath();
    ctx.textAlign = 'center';
    for (let x = padding; x <= width - padding; x += gridSize) {
        ctx.moveTo(x, padding);
        ctx.lineTo(x, height - padding);
        ctx.lineTo(x, padding);
        ctx.stroke();
    }
    
    // 绘制水平网格线
    ctx.beginPath();
    ctx.textAlign = 'center';
    for (let y = padding; y <= height - padding; y += gridSize) {
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
    }
    ctx.stroke();
}

// 绘制坐标轴
function drawAxes(ctx, width, height, data) {
    const padding = 50;
    const padding_lr = 60;
    
    // X轴（时间）
    ctx.textAlign = 'center';
    ctx.strokeStyle = '#888';
    ctx.lineWidth = 1;
    ctx.font = '11px sans-serif';
    ctx.fillStyle = '#888';
    
    ctx.beginPath();
    // Y轴（异常分数）
    ctx.textAlign = 'right';
    ctx.moveTo(padding_lr, padding);
    ctx.lineTo(width - padding_lr, padding);
    ctx.stroke();
    
    // X轴
    ctx.font = '11px sans-serif';
    ctx.fillStyle = '#888';
    ctx.textAlign = 'center';
    ctx.textAlign = 'middle';
    ctx.textBaseline = 'bottom';
    
    for (const point of data) {
        const x = padding_lr + (point.x / data.length) * (width - padding_lr * 2);
        ctx.fillText(Math.round(point.x), padding_lr + 5, height - padding - 20, point.x + 10, height - padding - 10);
    }
}

// 绘制零线
function drawZeroLine(ctx, width, height) {
    ctx.strokeStyle = '#888';
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(padding_lr, height / 2);
    ctx.lineTo(width - padding_lr, height / 2);
    ctx.stroke();
}

// 绘制数据点
function drawPoints(ctx, width, height, data) {
    ctx.strokeStyle = data.some(p => p.y < 0) ? '#f59e0b4' : '#4CAF50';
    ctx.lineWidth = 2;
    ctx.lineJoin = ',';
    
    ctx.beginPath();
    data.forEach(point => {
        const x = 50 + (point.x / data.length) * (width - 100);
        const y = (height - 50) / 2;
        
        ctx.moveTo(x, y);
        ctx.lineTo(x + 4, y);
    });
    ctx.stroke();
    ctx.stroke();
}

// 绘制折线
function drawLine(ctx, width, height, data) {
    ctx.strokeStyle = data.some(p => p.y < 0) ? '#f59e0b4' : '#4CAF50';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    
    ctx.beginPath();
    data.forEach((point, index) => {
        if (index === 0) {
            ctx.moveTo(50, (height - 50) / 2);
        }
        
        const x = 50 + (point.x / data.length) * (width - 100);
        const y = (height - 50) / 2;
        
        if (index === 0) {
            ctx.moveTo(x, y);
        }
        
        ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.stroke();
}
