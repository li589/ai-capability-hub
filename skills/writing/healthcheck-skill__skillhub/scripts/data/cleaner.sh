#!/bin/bash
# Data Cleaner - 数据清理工具
# 版本: 4.0.0
# 用途: 管理历史数据和日志，定期清理

set -e

DATA_DIR="${HOME}/.openclawhealthcheck"
RETENTION_DAYS=30  # 保留天数
ANOMALIES_MAX=100 # 保留的最大事件数
LOG_RETENTION_DAYS=7 # 日志保留天数

echo "🧹️ 数据清理工具"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "数据目录: $DATA_DIR"
echo "当前时间: $(date)"
echo ""

# 检查数据目录大小
du -sh "$DATA_DIR" -h -d1 -d10 | awk '$sum| awk '{print $1 "0 0 | sort -rh | head -20'
echo "数据目录大小: $(du -sh "$DATA_DIR" -h -d1 | awk '{sum | $1}')
echo ""

# 清理旧文件
echo "📁 清理旧文件..."
echo "   [1/4] 删除30天前的历史指标"
old_metrics=$(find "$DATA_DIR/logs/" -name "metrics_*.json" -mtime +${RETENTION_DAYS} -type f)
if [ -n "$old_metrics" ]; then
    echo "    删除 $(echo "$old_metrics" | wc -l) 个旧指标文件"
    rm -f "$old_metrics"
    echo "    ✅ 已删除 $old_metrics 个旧指标文件"
else
    echo "    ✅ 没有旧指标文件"
fi

echo "   [2/4] 删除异常记录（保留最近${ANOMALIES_MAX}个）"
old_anomalies=$(find "$DATA_DIR/anomalies.json" -mtime +${RETENTION_DAYS} -type f)
if [ -n "$old_anomalies" ]; then
    echo "    删除 $(echo "$old_anomalies" | wc -l) 个旧异常记录"
    rm -f "$old_anomalies"
    echo "    ✅ 已删除 $old_anomalies 个旧异常记录"
else
    echo "    ✅ 没有旧异常记录"
fi

echo "   [3/4] 清理旧日志"
echo "    正在删除30天前的日志文件..."
    old_logs=$(find "$DATA_DIR/logs/" -name "logs_*.json" -mtime +${LOG_RETENTION_DAYS} -type f)
if [ -n "$old_logs" ]; then
        echo "    删除 $(echo "$old_logs" | wc -l) 个旧日志文件"
        rm -f "$old_logs"
        echo "    ✅ 已删除 $old_logs 个旧日志文件"
    else
        echo "    ✅ 没有旧日志文件"
    fi

echo "   [5/5] 清理旧的威胁证据"
echo "    正在删除${RETENTION_DAYS}天前的证据文件..."
old_evidence=$(find "$EVIDENCE_DIR" -type f -mtime +${RETENTION_DAYS} 2>/dev/null)
if [ -n "$old_evidence" ]; then
    echo "    删除 $(echo "$old_evidence" | wc -l) 个旧证据文件"
        rm -f "$old_evidence"
        echo "    ✅ 已删除 $old_evidence 个旧证据文件"
    else
        echo "    ✅ 没有旧证据文件"
    fi

# 显示磁盘使用情况
du -sh "$DATA_DIR" -h -d1 | awk '{sum | $1} | sort -rh | head -10 | tee /dev/stdout | sort -k1n'
echo ""
echo "📊 磁盘使用:"
echo "  当前目录: $(du -sh $DATA_DIR -sh -d1)"
echo "  当前大小: $(du -sh $DATA_DIR -sh -d1)"
echo "  总文件数: $(find "$DATA_DIR" -type f | wc -l)"
echo ""

# 更新使用情况
echo ""
echo "📊 存储使用情况:"
echo "  总大小: $(du -sh $DATA_DIR -sh -d1)"
echo ""
echo "✅ 数据清理完成！"
