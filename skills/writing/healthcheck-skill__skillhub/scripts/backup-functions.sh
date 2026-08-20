#!/bin/bash
# Home变量默认值处理（兼容沙盒环境）
: "${HOME:=/tmp}"

# Backup Functions - 备份函数库
# 版本: 4.0.0
# 用途: 提供自动备份和恢复功能

BACKUP_DIR="${HOME}/.openclawhealthcheck/backups"
MAX_BACKUPS=10  # 最多保留10个备份

# 初始化备份目录
init_backup() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        chmod 700 "$BACKUP_DIR"
    fi
}

# 创建备份
create_backup() {
    local file_path="$1"
    local description="${2:-自动备份}"

    if [ ! -f "$file_path" ]; then
        echo "❌ 文件不存在: $file_path"
        return 1
    fi

    # 初始化备份目录
    init_backup

    # 生成备份文件名
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local filename=$(basename "$file_path")
    local backup_file="${BACKUP_DIR}/${filename}.${timestamp}.backup"

    # 复制文件
    cp "$file_path" "$backup_file"
    if [ $? -eq 0 ]; then
        echo "✅ 备份已创建: $backup_file"
        echo "   说明: $description"

        # 记录备份日志
        echo "$(date '+%Y-%m-%d %H:%M:%S') | CREATE | $file_path | $backup_file | $description" >> "${BACKUP_DIR}/backup.log"

        # 清理旧备份
        cleanup_old_backups "$filename"

        return 0
    else
        echo "❌ 备份失败: $file_path"
        return 1
    fi
}

# 恢复备份
restore_backup() {
    local file_path="$1"
    local backup_number="${2:-1}"  # 默认恢复最新的备份

    if [ ! -f "$file_path" ]; then
        echo "❌ 目标文件不存在: $file_path"
        return 1
    fi

    local filename=$(basename "$file_path")
    local backup_files=($(ls -t "${BACKUP_DIR}/${filename}."*.backup 2>/dev/null))

    if [ ${#backup_files[@]} -eq 0 ]; then
        echo "❌ 未找到备份文件: $filename"
        return 1
    fi

    if [ $backup_number -gt ${#backup_files[@]} ]; then
        echo "❌ 备份编号超出范围: 共 ${#backup_files[@]} 个备份"
        return 1
    fi

    local backup_file="${backup_files[$((backup_number-1))]}"

    # 先备份当前文件
    local current_backup="${file_path}.before_restore"
    cp "$file_path" "$current_backup"

    # 恢复备份
    cp "$backup_file" "$file_path"
    if [ $? -eq 0 ]; then
        echo "✅ 已恢复备份: $backup_file"
        echo "   当前文件已备份到: $current_backup"

        # 记录恢复日志
        echo "$(date '+%Y-%m-%d %H:%M:%S') | RESTORE | $file_path | $backup_file | 自动备份当前文件到 $current_backup" >> "${BACKUP_DIR}/backup.log"

        return 0
    else
        echo "❌ 恢复失败: $backup_file"
        return 1
    fi
}

# 列出所有备份
list_backups() {
    local file_path="$1"
    local filename=$(basename "$file_path")
    local backup_files=($(ls -t "${BACKUP_DIR}/${filename}."*.backup 2>/dev/null))

    if [ ${#backup_files[@]} -eq 0 ]; then
        echo "未找到备份文件: $filename"
        return 0
    fi

    echo "📋 备份列表: $filename"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    local i=1
    for backup_file in "${backup_files[@]}"; do
        local backup_name=$(basename "$backup_file")
        local backup_date=$(echo "$backup_name" | grep -oP '\d{8}_\d{6}' | sed 's/_/ /')

        # 获取文件大小
        local file_size=$(stat -c "%s" "$backup_file" 2>/dev/null || stat -f "%z" "$backup_file" 2>/dev/null)
        local size_mb=$(echo "scale=2; $file_size / 1024 / 1024" | bc 2>/dev/null || echo "0")

        echo "[$i] $backup_name"
        echo "    日期: $backup_date"
        echo "    大小: ${size_mb} MB"
        echo ""
        ((i++))
    done
}

# 清理旧备份
cleanup_old_backups() {
    local filename="$1"

    if [ -z "$filename" ]; then
        # 清理所有旧备份
        find "$BACKUP_DIR" -name "*.backup" -type f -printf '%T@ %p\n' | sort -n | cut -d' ' -f2- | head -n -${MAX_BACKUPS} | xargs -r rm -f
        echo "🧹 已清理旧备份（保留最新${MAX_BACKUPS}个）"
    else
        # 清理特定文件的旧备份
        local backup_files=($(ls -t "${BACKUP_DIR}/${filename}."*.backup 2>/dev/null))

        if [ ${#backup_files[@]} -gt $MAX_BACKUPS ]; then
            local i=$MAX_BACKUPS
            while [ $i -lt ${#backup_files[@]} ]; do
                rm -f "${backup_files[$i]}"
                echo "🧹 已删除旧备份: $(basename ${backup_files[$i]})"
                ((i++))
            done
        fi
    fi
}

# 删除特定备份
delete_backup() {
    local backup_file="$1"

    if [ ! -f "$backup_file" ]; then
        echo "❌ 备份文件不存在: $backup_file"
        return 1
    fi

    # 确认删除
    read -p "确认删除备份: $(basename $backup_file)? (y/N): " -r confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        rm -f "$backup_file"
        echo "✅ 已删除备份: $(basename $backup_file)"

        # 记录删除日志
        echo "$(date '+%Y-%m-%d %H:%M:%S') | DELETE | $backup_file | 用户手动删除" >> "${BACKUP_DIR}/backup.log"

        return 0
    else
        echo "已取消删除"
        return 0
    fi
}

# 导出函数
export -f init_backup
export -f create_backup
export -f restore_backup
export -f list_backups
export -f cleanup_old_backups
export -f delete_backup
