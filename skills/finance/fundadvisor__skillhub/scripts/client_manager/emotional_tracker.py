"""
投资心态跟踪器 v1.0
跟踪客户的情绪变化，分析亏损/盈利原因，生成调整建议，及时提醒客户调整投资
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent.parent / "data"


class EmotionalTracker:
    """投资心态跟踪器"""

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self.emotions_path = self.data_dir / 'emotional_records.json'
        self.alerts_path = self.data_dir / 'emotional_alerts.json'
        self.emotions = self._load_emotions()
        self.alerts = self._load_alerts()

    def _load_emotions(self) -> dict:
        """加载情绪记录"""
        try:
            if self.emotions_path.exists():
                with open(self.emotions_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_emotions(self):
        """保存情绪记录"""
        try:
            with open(self.emotions_path, 'w', encoding='utf-8') as f:
                json.dump(self.emotions, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_alerts(self) -> dict:
        """加载告警记录"""
        try:
            if self.alerts_path.exists():
                with open(self.alerts_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_alerts(self):
        """保存告警记录"""
        try:
            with open(self.alerts_path, 'w', encoding='utf-8') as f:
                json.dump(self.alerts, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def record_emotion(self, user_id: str, emotion_data: dict) -> dict:
        """
        记录用户情绪变化

        Args:
            user_id: 用户ID
            emotion_data: 情绪数据，包含：
                - emotion: 情绪类型（焦虑、恐惧、贪婪、平静、乐观等）
                - cause: 原因（亏损、盈利、市场波动等）
                - intensity: 强度 1-10
                - timestamp: 时间戳（可选，自动使用当前时间）

        Returns:
            dict: 情绪分析结果
        """
        if user_id not in self.emotions:
            self.emotions[user_id] = []

        record = {
            'timestamp': emotion_data.get('timestamp', datetime.now().isoformat()),
            'emotion': emotion_data.get('emotion', '未知'),
            'cause': emotion_data.get('cause', ''),
            'intensity': emotion_data.get('intensity', 5),
            'profit_pct': emotion_data.get('profit_pct'),  # 当前盈亏百分比
            'notes': emotion_data.get('notes', '')
        }

        self.emotions[user_id].append(record)

        # 限制记录数量（保留最近100条）
        if len(self.emotions[user_id]) > 100:
            self.emotions[user_id] = self.emotions[user_id][-100:]

        self._save_emotions()

        # 生成分析和建议
        analysis = self.analyze_emotion_change(user_id)

        return analysis

    def analyze_emotion_change(self, user_id: str) -> dict:
        """分析用户情绪变化"""
        if user_id not in self.emotions or len(self.emotions[user_id]) == 0:
            return {'status': 'no_records', 'message': '暂无情绪记录'}

        records = self.emotions[user_id]
        latest = records[-1]

        # 计算情绪趋势
        analysis = {
            'latest_emotion': latest['emotion'],
            'latest_timestamp': latest['timestamp'],
            'intensity': latest['intensity'],
            'cause': latest['cause'],
            'trend': self._calculate_trend(user_id),
            'warning': self._check_warning(latest),
            'suggestion': self._generate_suggestion(latest)
        }

        return analysis

    def get_composure_score(self, user_id: str) -> dict:
        """计算投资者镇静度评分（0-100），分数越高越理性"""
        if user_id not in self.emotions or len(self.emotions[user_id]) == 0:
            return {'score': 75, 'level': '数据不足', 'summary': '暂无足够情绪数据'}
        records = self.emotions[user_id]
        factors = []
        negative_count = sum(1 for r in records[-10:] if r.get('emotion') in ['焦虑','恐惧','崩溃'])
        negative_ratio = negative_count / min(len(records[-10:]), 10)
        factors.append(1.0 - negative_ratio)
        intensities = [r.get('intensity', 5) for r in records[-10:]]
        if intensities:
            avg_intensity = sum(intensities) / len(intensities)
            factors.append(max(0, 1.0 - (avg_intensity - 3) / 7))
        if len(records) >= 5:
            recent_intensities = [r.get('intensity', 5) for r in records[-5:]]
            earlier_intensities = [r.get('intensity', 5) for r in records[-10:-5]]
            if earlier_intensities and recent_intensities:
                trend = sum(recent_intensities)/len(recent_intensities) - sum(earlier_intensities)/len(earlier_intensities)
                factors.append(max(0, 1.0 - trend / 5))
            else:
                factors.append(0.7)
        else:
            factors.append(0.7)
        score = round(sum(factors) / len(factors) * 100)
        if score >= 75:
            level = '沉稳'
        elif score >= 50:
            level = '正常波动'
        elif score >= 30:
            level = '情绪紧张'
        else:
            level = '高度焦虑'
        return {'score': score, 'level': level,
                'negative_ratio': round(negative_ratio, 2),
                'avg_intensity': round(avg_intensity, 1) if intensities else 0,
                'total_records': len(records)}

    def _calculate_trend(self, user_id: str) -> str:
        """计算情绪趋势（基于最近10条记录）"""
        records = self.emotions[user_id]
        if len(records) < 2:
            return 'stable'
        recent = records[-10:]
        intensities = [r.get('intensity', 5) for r in recent]
        if len(intensities) < 3:
            return 'stable'
        window = min(5, len(intensities) // 2)
        early_avg = sum(intensities[:window]) / window
        late_avg = sum(intensities[-window:]) / window
        change = late_avg - early_avg
        negative_emotions = sum(1 for r in recent[-3:] if r.get('emotion') in ['焦虑','恐惧','崩溃'])
        if change > 1.5 or negative_emotions >= 2:
            return 'worsening'
        elif change < -1.5:
            return 'improving'
        else:
            return 'stable'

    def _check_warning(self, latest_record: dict) -> Optional[str]:
        """检查是否需要告警（增强版：四级告警）"""
        emotion = latest_record.get('emotion', '')
        intensity = latest_record.get('intensity', 5)
        cause = latest_record.get('cause', '')
        if intensity >= 8 and emotion in ['焦虑', '恐惧', '崩溃']:
            return 'CRITICAL_NEGATIVE'
        if '亏' in cause and intensity >= 7:
            return 'LOSS_INDUCED_ANXIETY'
        if emotion == '贪婪' and intensity >= 7:
            return 'GREED_SIGNAL'
        if intensity >= 6 and emotion in ['焦虑', '恐惧']:
            return 'ELEVATED_CONCERN'
        return None

    def _generate_suggestion(self, latest_record: dict) -> str:
        """生成调整建议（增强版：区分亏损比例给出不同建议）"""
        emotion = latest_record.get('emotion', '')
        intensity = latest_record.get('intensity', 5)
        cause = latest_record.get('cause', '')
        profit_pct = latest_record.get('profit_pct')
        suggestions = []
        if emotion in ['焦虑', '恐惧', '崩溃']:
            if intensity >= 8:
                suggestions.append('情绪波动较大时，建议先冷静24小时再做任何操作。')
                if profit_pct is not None and profit_pct < -20:
                    suggestions.append('亏损超过20%确实很煎熬。建议我们一起分析：是市场原因还是选基问题？如果是市场原因，耐心持有通常会修复。')
                elif profit_pct is not None and profit_pct < -10:
                    suggestions.append('亏损10%以上确实让人焦虑。但现在的关键是判断：继续持有还是止损？我帮你分析。')
                else:
                    suggestions.append('暂时不要看账户了，给自己一个情绪缓冲期。')
            else:
                suggestions.append('有一点焦虑是正常的，但不要让情绪左右你的判断。')
        if emotion == '贪婪':
            suggestions.append('市场赚钱效应容易让人忘记风险。建议设一个止盈线，到了就执行。')
            if profit_pct is not None and profit_pct > 20:
                suggestions.append('你已经赚了{:.0f}%了，分批止盈至少先拿回本金吧。')
        if emotion == '平静' or emotion == '乐观':
            suggestions.append('保持这种心态，你已经超越了90%的散户。')
        if '亏' in cause:
            suggestions.append('亏钱的时候最忌讳的就是在恐慌中做决定。先分析原因再行动。')
        if '盈利' in cause and profit_pct is not None and profit_pct > 15:
            suggestions.append('收益可观！考虑分批止盈，锁定一部分利润。')
        if not suggestions:
            suggestions.append('保持理性，有问题随时找我。')
        result = ' '.join(suggestions)
        if profit_pct is not None and emotion == '贪婪' and profit_pct > 20:
            result = result.format(profit_pct)
        return result

    def get_emotion_analysis(self, user_id: str, include_composure: bool = True) -> str:
        """获取情绪分析报告（增强版：含镇静度评分）"""
        if user_id not in self.emotions or len(self.emotions[user_id]) == 0:
            return '你还没有情绪记录。我会持续关注你的投资心态变化。'
        records = self.emotions[user_id]
        latest = records[-1]
        lines = []
        lines.append('')
        lines.append('【投资心态分析报告】')
        lines.append('')
        lines.append(f"最近情绪：{latest['emotion']}")
        lines.append(f"发生时间：{latest['timestamp']}")
        lines.append(f"诱因：{latest.get('cause', '未记录')}")
        lines.append(f"强度：{'❤️' * min(latest.get('intensity', 5), 5)}")
        if include_composure:
            comp = self.get_composure_score(user_id)
            lines.append(f"镇静度：{comp['score']}分 ({comp['level']})")
        lines.append('')
        trend = self._calculate_trend(user_id)
        trend_desc = {'stable':'情绪保持稳定','improving':'情绪有所好转','worsening':'情绪趋于负面'}
        lines.append(f"趋势：{trend_desc.get(trend, '稳定')}")
        lines.append('')
        warning = self._check_warning(latest)
        if warning:
            lines.append('⚠️ 告警提示：')
            warning_msgs = {'CRITICAL_NEGATIVE':'负面情绪强度很高，强烈建议暂停操作，冷静后再决策。',
                'LOSS_INDUCED_ANXIETY':'亏损带来较大心理压力，建议重新评估持仓和风险承受能力。',
                'GREED_SIGNAL':'贪念信号较强，注意不要追高，分批减仓更稳妥。',
                'ELEVATED_CONCERN':'情绪有所波动，建议多关注长期目标而非短期涨跌。'}
            lines.append(f"  {warning_msgs.get(warning, '')}")
            lines.append('')
        suggestion = self._generate_suggestion(latest)
        lines.append('💡 建议：')
        lines.append(f"  {suggestion}")
        lines.append('')
        return '\n'.join(lines)

    def daily_check(self, user_id: str, holdings: list) -> list:
        """
        每日检查 - 检查是否需要发送提醒

        Args:
            user_id: 用户ID
            holdings: 用户持仓列表

        Returns:
            list: 需要提醒的列表
        """
        alerts = []

        if user_id not in self.emotions or len(self.emotions[user_id]) == 0:
            return alerts

        records = self.emotions[user_id]
        latest = records[-1]

        # 检查是否需要提醒
        warning = self._check_warning(latest)
        if warning:
            alert = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'warning_type': warning,
                'emotion': latest['emotion'],
                'intensity': latest['intensity'],
                'cause': latest.get('cause', ''),
                'message': self._generate_alert_message(warning, latest)
            }
            alerts.append(alert)

            # 保存告警
            if user_id not in self.alerts:
                self.alerts[user_id] = []
            self.alerts[user_id].append(alert)
            self._save_alerts()

        return alerts

    def _generate_alert_message(self, warning: str, latest_record: dict) -> str:
        """生成告警消息"""
        messages = {
            'CRITICAL_NEGATIVE': (
                f"检测到您当前情绪波动较大（{latest_record['emotion']}，强度{latest_record.get('intensity', 5)}）。"
                f"强烈建议暂停一切操作，冷静24小时后再做决定。"
            ),
            'LOSS_INDUCED_ANXIETY': (
                f"亏损可能给您带来了较大的心理压力。"
                f"建议我们一起分析一下持仓情况，看看是否需要调整。"
            ),
            'GREED_SIGNAL': (
                f"检测到您可能有追高的倾向。"
                f"建议不要被行情左右，可以考虑分批减仓锁定收益。"
            ),
            'ELEVATED_CONCERN': (
                f"检测到您有些情绪波动（{latest_record['emotion']}，强度{latest_record.get('intensity', 5)}）。"
                f"建议多关注长期投资目标，短期波动是市场常态。"
            )
        }
        return messages.get(warning, "我注意到您最近情绪有些波动，有什么需要帮忙的吗？")

    def get_recent_emotions(self, user_id: str, days: int = 7) -> list:
        """获取最近的情绪记录"""
        if user_id not in self.emotions:
            return []

        cutoff = datetime.now().timestamp() - days * 86400
        recent = []

        for record in reversed(self.emotions[user_id]):
            timestamp = datetime.fromisoformat(record['timestamp']).timestamp()
            if timestamp >= cutoff:
                recent.append(record)
            else:
                break

        return recent

    def clear_old_records(self, user_id: str, days: int = 30):
        """清除旧记录"""
        if user_id not in self.emotions:
            return

        cutoff = datetime.now().timestamp() - days * 86400
        filtered = []

        for record in self.emotions[user_id]:
            timestamp = datetime.fromisoformat(record['timestamp']).timestamp()
            if timestamp >= cutoff:
                filtered.append(record)

        self.emotions[user_id] = filtered
        self._save_emotions()


def main():
    """测试"""
    tracker = EmotionalTracker()

    user_id = "test_user"

    print("=== 投资心态跟踪器测试 ===\n")

    # 记录情绪
    print("记录焦虑情绪...")
    result = tracker.record_emotion(user_id, {
        'emotion': '焦虑',
        'cause': '亏损15%',
        'intensity': 7,
        'profit_pct': -15
    })
    print(f"分析结果: {result}")
    print()

    # 记录乐观情绪
    print("记录乐观情绪...")
    result = tracker.record_emotion(user_id, {
        'emotion': '乐观',
        'cause': '盈利5%',
        'intensity': 6,
        'profit_pct': 5
    })
    print(f"分析结果: {result}")
    print()

    # 获取分析报告
    print("获取情绪分析报告...")
    report = tracker.get_emotion_analysis(user_id)
    print(report)


if __name__ == '__main__':
    main()
