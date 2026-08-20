#!/usr/bin/env python3
"""
财务凭证生成器 - 规则学习模块
通过分析历史数据自动推断核算规则
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict
import pandas as pd
import numpy as np


@dataclass
class LearnedRule:
    """学习到的规则"""
    rule_id: str
    business_type: str
    source_field: str
    target_account_code: str
    target_account_name: str
    entry_type: str  # debit/credit
    confidence: float  # 0-1
    examples: List[Dict]
    mapping_logic: str = ""


class RuleLearner:
    """规则学习器"""

    # 常见业务类型关键词
    BUSINESS_TYPE_KEYWORDS = {
        '银行收款': ['收款', '收入', '到账', '回款', '收回'],
        '银行付款': ['付款', '支出', '汇出', '支付', '转出'],
        '现金收款': ['现金收入', '收现'],
        '现金付款': ['现金支出', '付现'],
        '应收账款': ['应收', '赊销', '销售'],
        '应付账款': ['应付', '赊购', '采购'],
        '工资薪酬': ['工资', '薪酬', '奖金', '补贴'],
        '税费缴纳': ['税金', '税费', '纳税'],
        '费用报销': ['报销', '费用', '开支'],
        '资产购置': ['购入', '购置', '购买'],
        '资产折旧': ['折旧', '摊销', '计提'],
        '利息收支': ['利息', '手续费'],
    }

    # 常见科目映射
    COMMON_ACCOUNT_PATTERNS = {
        '银行存款': {'keywords': ['银行', '转账', '汇款'], 'code': '1002'},
        '库存现金': {'keywords': ['现金', '现款'], 'code': '1001'},
        '应收账款': {'keywords': ['应收'], 'code': '1122'},
        '应付账款': {'keywords': ['应付'], 'code': '2202'},
        '主营业务收入': {'keywords': ['收入', '销货'], 'code': '6001'},
        '销售费用': {'keywords': ['销售费用', '推广'], 'code': '6601'},
        '管理费用': {'keywords': ['管理费用', '办公'], 'code': '6602'},
        '财务费用': {'keywords': ['财务费用', '利息', '手续费'], 'code': '6603'},
        '应付职工薪酬': {'keywords': ['工资', '薪酬', '奖金'], 'code': '2211'},
        '应交税费': {'keywords': ['税金', '税费', '增值税'], 'code': '2221'},
        '固定资产': {'keywords': ['固定资产', '设备', '车辆'], 'code': '1601'},
        '累计折旧': {'keywords': ['折旧', '累计折旧'], 'code': '1602'},
    }

    def __init__(self, data_manager=None):
        self.data_manager = data_manager
        self.accounts = []
        self.existing_rules = []

    def load_data(self, data_manager) -> None:
        """加载数据"""
        self.data_manager = data_manager
        self.accounts = data_manager.get_account_codes()
        self.existing_rules = data_manager.get_rules_list()

    def learn_from_history(self,
                           history_data: pd.DataFrame,
                           history_type: str = 'ledger') -> List[LearnedRule]:
        """从历史数据学习规则

        Args:
            history_data: 历史明细账数据
            history_type: 历史数据类型 ('ledger': 明细账, 'voucher': 凭证, 'manual': 手工凭证)

        Returns:
            学习到的规则列表
        """
        if history_type == 'ledger':
            return self._learn_from_ledger(history_data)
        elif history_type == 'voucher':
            return self._learn_from_voucher(history_data)
        elif history_type == 'manual':
            return self._learn_from_manual(history_data)
        else:
            return []

    def _learn_from_ledger(self, ledger_data: pd.DataFrame) -> List[LearnedRule]:
        """从明细账学习"""
        rules = []

        # 分析列结构
        columns = list(ledger_data.columns)
        amount_cols = self._identify_amount_columns(columns)
        account_cols = self._identify_account_columns(columns)
        date_cols = self._identify_date_columns(columns)
        summary_cols = self._identify_summary_columns(columns)

        # 学习借方科目规则
        for col in amount_cols:
            if '借' in col or 'debit' in col.lower():
                rule = self._infer_rule_from_column(
                    ledger_data, col, 'debit', account_cols, summary_cols
                )
                if rule:
                    rules.append(rule)

        # 学习贷方科目规则
        for col in amount_cols:
            if '贷' in col or 'credit' in col.lower():
                rule = self._infer_rule_from_column(
                    ledger_data, col, 'credit', account_cols, summary_cols
                )
                if rule:
                    rules.append(rule)

        # 学习科目编码与名称的对应关系
        account_mapping = self._learn_account_mapping(ledger_data, account_cols)

        return rules

    def _learn_from_voucher(self, voucher_data: pd.DataFrame) -> List[LearnedRule]:
        """从历史凭证学习"""
        rules = []

        # 查找科目列和金额列
        columns = list(voucher_data.columns)

        for idx, row in voucher_data.iterrows():
            summary = str(row.get('摘要', ''))
            account_code = str(row.get('科目编码', ''))
            account_name = str(row.get('科目名称', ''))
            debit = row.get('借方金额', 0) or 0
            credit = row.get('贷方金额', 0) or 0

            if not account_code or account_code == 'nan':
                continue

            # 确定分录类型
            entry_type = 'debit' if debit and debit > 0 else 'credit'

            # 确定业务类型
            business_type = self._infer_business_type(summary)

            rule_id = f"auto_{business_type}_{account_code}_{entry_type}"

            rule = LearnedRule(
                rule_id=rule_id,
                business_type=business_type,
                source_field=summary,  # 用摘要作为源字段标识
                target_account_code=account_code,
                target_account_name=account_name,
                entry_type=entry_type,
                confidence=0.85,  # 从历史凭证学习的置信度较高
                examples=[{'summary': summary, 'account': account_code}]
            )
            rules.append(rule)

        # 去重
        unique_rules = []
        seen = set()
        for rule in rules:
            key = (rule.business_type, rule.target_account_code, rule.entry_type)
            if key not in seen:
                seen.add(key)
                unique_rules.append(rule)

        return unique_rules

    def _learn_from_manual(self, manual_data: pd.DataFrame) -> List[LearnedRule]:
        """从财务核算手册学习"""
        rules = []

        # 解析财务核算手册
        # 手册通常包含：业务描述 -> 借方科目 -> 贷方科目 的映射

        for idx, row in manual_data.iterrows():
            business_desc = str(row.get('业务描述', ''))
            debit_account = str(row.get('借方科目', ''))
            credit_account = str(row.get('贷方科目', ''))
            amount_field = str(row.get('金额字段', ''))

            if not business_desc or business_desc == 'nan':
                continue

            business_type = self._infer_business_type(business_desc)

            # 添加借方规则
            if debit_account and debit_account != 'nan':
                account_info = self._find_account_info(debit_account)
                if account_info:
                    rule = LearnedRule(
                        rule_id=f"manual_{business_type}_debit_{account_info['code']}",
                        business_type=business_type,
                        source_field=amount_field or '金额',
                        target_account_code=account_info['code'],
                        target_account_name=account_info['name'],
                        entry_type='debit',
                        confidence=0.95,  # 手工配置的规则置信度最高
                        examples=[{'description': business_desc}]
                    )
                    rules.append(rule)

            # 添加贷方规则
            if credit_account and credit_account != 'nan':
                account_info = self._find_account_info(credit_account)
                if account_info:
                    rule = LearnedRule(
                        rule_id=f"manual_{business_type}_credit_{account_info['code']}",
                        business_type=business_type,
                        source_field=amount_field or '金额',
                        target_account_code=account_info['code'],
                        target_account_name=account_info['name'],
                        entry_type='credit',
                        confidence=0.95,
                        examples=[{'description': business_desc}]
                    )
                    rules.append(rule)

        return rules

    def _identify_amount_columns(self, columns: List[str]) -> List[str]:
        """识别金额相关列"""
        amount_keywords = ['金额', '发生额', '余额', 'debit', 'credit', 'amount', 'balance']
        return [col for col in columns if any(kw in col.lower() for kw in amount_keywords)]

    def _identify_account_columns(self, columns: List[str]) -> List[str]:
        """识别科目相关列"""
        account_keywords = ['科目', 'account', '编码', '名称']
        return [col for col in columns if any(kw in col.lower() for kw in account_keywords)]

    def _identify_date_columns(self, columns: List[str]) -> List[str]:
        """识别日期相关列"""
        date_keywords = ['日期', 'date', '时间', 'time']
        return [col for col in columns if any(kw in col.lower() for kw in date_keywords)]

    def _identify_summary_columns(self, columns: List[str]) -> List[str]:
        """识别摘要相关列"""
        summary_keywords = ['摘要', 'summary', '描述', 'description', '业务']
        return [col for col in columns if any(kw in col.lower() for kw in summary_keywords)]

    def _infer_rule_from_column(self,
                                data: pd.DataFrame,
                                amount_col: str,
                                entry_type: str,
                                account_cols: List[str],
                                summary_cols: List[str]) -> Optional[LearnedRule]:
        """从金额列推断规则"""
        # 获取非空行
        valid_data = data[data[amount_col].notna() & (data[amount_col] != 0)]

        if len(valid_data) == 0:
            return None

        # 获取第一行的科目信息
        first_row = valid_data.iloc[0]

        # 查找科目编码
        account_code = ""
        account_name = ""
        for col in account_cols:
            if '编码' in col or 'code' in col.lower():
                account_code = str(first_row.get(col, ''))
            if '名称' in col or 'name' in col.lower():
                account_name = str(first_row.get(col, ''))

        if not account_code or account_code == 'nan':
            return None

        # 获取摘要
        summary = ""
        for col in summary_cols:
            val = str(first_row.get(col, ''))
            if val and val != 'nan':
                summary = val
                break

        # 推断业务类型
        business_type = self._infer_business_type(summary)

        # 计算置信度
        confidence = self._calculate_confidence(valid_data, account_code, amount_col)

        return LearnedRule(
            rule_id=f"auto_{business_type}_{account_code}_{entry_type}",
            business_type=business_type,
            source_field=amount_col,
            target_account_code=account_code,
            target_account_name=account_name,
            entry_type=entry_type,
            confidence=confidence,
            examples=valid_data.head(3).to_dict('records')
        )

    def _learn_account_mapping(self, data: pd.DataFrame, account_cols: List[str]) -> Dict[str, str]:
        """学习科目编码与名称的映射"""
        mapping = {}

        code_col = None
        name_col = None

        for col in account_cols:
            if '编码' in col or 'code' in col.lower():
                code_col = col
            if '名称' in col or 'name' in col.lower():
                name_col = col

        if code_col and name_col:
            for idx, row in data.iterrows():
                code = str(row.get(code_col, ''))
                name = str(row.get(name_col, ''))
                if code and name and code != 'nan' and name != 'nan':
                    mapping[code] = name

        return mapping

    def _infer_business_type(self, text: str) -> str:
        """从文本推断业务类型"""
        text_lower = text.lower()

        for business_type, keywords in self.BUSINESS_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return business_type

        return 'general'

    def _find_account_info(self, account_ref: str) -> Optional[Dict]:
        """查找科目信息"""
        account_ref_lower = account_ref.lower()

        # 先从已加载的科目中查找
        for account in self.accounts:
            if (account.get('code') == account_ref or
                account.get('name', '').lower() == account_ref_lower):
                return account

        # 再从常见科目模式中查找
        for name, pattern in self.COMMON_ACCOUNT_PATTERNS.items():
            if account_ref_lower in name or any(kw in account_ref_lower for kw in pattern['keywords']):
                return {'code': pattern['code'], 'name': name}

        # 尝试匹配编码
        for name, pattern in self.COMMON_ACCOUNT_PATTERNS.items():
            if pattern['code'] == account_ref:
                return {'code': pattern['code'], 'name': name}

        return None

    def _calculate_confidence(self, data: pd.DataFrame, account_code: str, amount_col: str) -> float:
        """计算规则置信度"""
        if len(data) == 0:
            return 0.0

        # 样本越多，置信度越高
        sample_score = min(len(data) / 10, 1.0) * 0.3

        # 金额一致性
        amounts = data[amount_col].dropna()
        if len(amounts) > 1:
            std = amounts.std()
            mean = amounts.mean()
            if mean != 0:
                cv = abs(std / mean)  # 变异系数
                consistency_score = max(0, 1 - cv) * 0.3
            else:
                consistency_score = 0.3
        else:
            consistency_score = 0.3

        # 匹配度
        match_score = 0.4

        return min(sample_score + consistency_score + match_score, 1.0)

    def merge_with_existing_rules(self,
                                  new_rules: List[LearnedRule],
                                  strategy: str = 'user_first') -> List[Dict]:
        """合并学习到的规则与现有规则

        Args:
            new_rules: 新学习的规则
            strategy: 合并策略
                - 'user_first': 用户定义优先
                - 'auto_first': 自动学习优先
                - 'replace': 完全替换
                - 'merge': 智能合并

        Returns:
            合并后的规则列表
        """
        existing_rules = self.existing_rules.copy()
        result_rules = list(existing_rules)

        for new_rule in new_rules:
            new_rule_dict = asdict(new_rule)
            new_rule_dict['is_auto_learned'] = True
            new_rule_dict['is_user_defined'] = False
            new_rule_dict['created_at'] = datetime.now().isoformat()
            new_rule_dict['updated_at'] = datetime.now().isoformat()

            # 查找冲突的现有规则
            conflict_idx = None
            for i, existing in enumerate(result_rules):
                if (existing.get('business_type') == new_rule.business_type and
                    existing.get('target_account_code') == new_rule.target_account_code and
                    existing.get('entry_type') == new_rule.entry_type):
                    conflict_idx = i
                    break

            if conflict_idx is not None:
                if strategy == 'replace':
                    result_rules[conflict_idx] = new_rule_dict
                elif strategy == 'user_first':
                    if not result_rules[conflict_idx].get('is_user_defined', False):
                        result_rules[conflict_idx] = new_rule_dict
                elif strategy == 'auto_first':
                    if result_rules[conflict_idx].get('is_auto_learned', False):
                        if new_rule.confidence > result_rules[conflict_idx].get('confidence', 0):
                            result_rules[conflict_idx] = new_rule_dict
                elif strategy == 'merge':
                    # 智能合并：保留用户定义，更新置信度和示例
                    if not result_rules[conflict_idx].get('is_user_defined', False):
                        result_rules[conflict_idx]['confidence'] = new_rule.confidence
                        result_rules[conflict_idx]['examples'] = new_rule.examples
            else:
                result_rules.append(new_rule_dict)

        return result_rules

    def suggest_rule_corrections(self, rules: List[Dict]) -> List[Dict]:
        """建议规则修正

        分析现有规则，找出可能需要修正的地方
        """
        suggestions = []

        # 检查置信度较低的规则
        for rule in rules:
            if rule.get('confidence', 1.0) < 0.7:
                suggestions.append({
                    'rule_id': rule.get('rule_id'),
                    'type': 'low_confidence',
                    'message': f"规则 '{rule.get('rule_id')}' 置信度较低，建议人工确认",
                    'rule': rule
                })

        # 检查冲突的规则
        account_rules = defaultdict(list)
        for rule in rules:
            key = f"{rule.get('business_type')}_{rule.get('entry_type')}"
            account_rules[key].append(rule)

        for key, rule_list in account_rules.items():
            if len(rule_list) > 3:
                suggestions.append({
                    'type': 'too_many_rules',
                    'message': f"业务类型 '{key}' 有 {len(rule_list)} 条规则，可能存在冗余",
                    'rules': rule_list
                })

        # 检查缺少贷方的规则
        for rule in rules:
            if rule.get('entry_type') == 'debit':
                # 查找对应的贷方规则
                has_counter = any(
                    r.get('entry_type') == 'credit' and
                    r.get('business_type') == rule.get('business_type')
                    for r in rules
                )
                if not has_counter:
                    suggestions.append({
                        'rule_id': rule.get('rule_id'),
                        'type': 'missing_counter',
                        'message': f"规则 '{rule.get('rule_id')}' 缺少对应的贷方规则",
                        'rule': rule
                    })

        return suggestions

    def export_rules(self, rules: List[LearnedRule], output_path: str = None) -> str:
        """导出规则为JSON"""
        rules_data = {
            'exported_at': datetime.now().isoformat(),
            'total_rules': len(rules),
            'rules': [asdict(r) for r in rules]
        }

        if output_path is None:
            SKILL_DIR = Path(__file__).parent.parent
            output_path = SKILL_DIR / "data" / "learned_rules_export.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, ensure_ascii=False, indent=2)

        return str(output_path)


def get_rule_learner(data_manager=None) -> RuleLearner:
    """获取规则学习器实例"""
    return RuleLearner(data_manager)


if __name__ == '__main__':
    # 测试代码
    learner = RuleLearner()

    # 创建示例数据
    sample_data = pd.DataFrame({
        '日期': ['2024-01-01', '2024-01-02', '2024-01-03'],
        '摘要': ['银行收款', '支付费用', '收到货款'],
        '科目编码': ['1002', '6601', '1002'],
        '科目名称': ['银行存款', '管理费用', '银行存款'],
        '借方金额': [10000, 0, 5000],
        '贷方金额': [0, 1000, 0]
    })

    rules = learner._learn_from_voucher(sample_data)
    print(f"学习到 {len(rules)} 条规则:")
    for rule in rules:
        print(f"  - {rule.business_type}: {rule.target_account_code} ({rule.entry_type})")
