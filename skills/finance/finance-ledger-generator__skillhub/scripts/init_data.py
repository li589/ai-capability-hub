#!/usr/bin/env python3
"""
财务凭证生成器 - 数据初始化模块
用于引导客户完成基础资料的初始化
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
import pandas as pd

# 数据目录路径
SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


@dataclass
class LedgerBook:
    """账簿信息"""
    code: str                    # 账簿编码
    name: str                    # 账簿名称
    start_date: str              # 启用日期 (YYYY-MM-DD)
    currency: str = "人民币"      # 币别
    status: str = "active"       # 状态: active/inactive
    description: str = ""         # 描述
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AccountCode:
    """科目信息"""
    code: str                    # 科目编码
    name: str                    # 科目名称
    category: str = ""           # 科目类别 (资产/负债/权益/成本/损益)
    is_auxiliary: bool = False   # 是否需要辅助核算
    auxiliary_types: List[str] = field(default_factory=list)  # 辅助核算类型
    direction: str = ""          # 余额方向 (借/贷)
    parent_code: str = ""         # 上级科目编码
    level: int = 1               # 科目级别
    is_detail: bool = True       # 是否明细科目
    status: str = "active"       # 状态
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AccountingRule:
    """核算规则"""
    rule_id: str                 # 规则ID
    business_type: str            # 业务类型
    source_field: str            # 源文件字段名
    target_account_code: str     # 目标科目编码
    target_account_name: str     # 目标科目名称
    entry_type: str              # 分录类型: debit/credit
    mapping_logic: str = ""      # 映射逻辑表达式
    priority: int = 100         # 优先级 (数字越小优先级越高)
    confidence: float = 1.0      # 置信度 (0-1, 仅自动学习的规则有)
    is_auto_learned: bool = False # 是否自动学习
    is_user_defined: bool = False  # 是否用户自定义
    status: str = "active"        # 状态
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Customer:
    """客户信息"""
    code: str                    # 客户编码
    name: str                    # 客户名称
    short_name: str = ""         # 简称
    tax_id: str = ""             # 税号
    bank_account: str = ""        # 银行账号
    bank_name: str = ""          # 开户行
    contact: str = ""            # 联系人
    phone: str = ""              # 电话
    address: str = ""            # 地址
    status: str = "active"       # 状态
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Supplier:
    """供应商信息"""
    code: str                    # 供应商编码
    name: str                    # 供应商名称
    short_name: str = ""         # 简称
    tax_id: str = ""             # 税号
    bank_account: str = ""       # 银行账号
    bank_name: str = ""          # 开户行
    contact: str = ""            # 联系人
    phone: str = ""              # 电话
    address: str = ""            # 地址
    status: str = "active"        # 状态
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Employee:
    """员工信息"""
    code: str                    # 员工编码
    name: str                    # 员工姓名
    department: str = ""         # 部门
    position: str = ""           # 职位
    email: str = ""              # 邮箱
    phone: str = ""              # 电话
    id_card: str = ""            # 身份证号
    bank_account: str = ""       # 银行账号
    status: str = "active"        # 状态
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ExchangeRate:
    """汇率信息"""
    currency_code: str           # 币种代码
    currency_name: str           # 币种名称
    rate_to_cny: float           # 兑人民币汇率
    effective_date: str          # 生效日期
    status: str = "active"        # 状态
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AuxiliaryData:
    """其他辅助资料"""
    data_type: str               # 数据类型 (项目/部门/合同等)
    code: str                    # 编码
    name: str                    # 名称
    category: str = ""           # 类别
    parent_code: str = ""         # 上级编码
    description: str = ""        # 描述
    status: str = "active"        # 状态
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class DataInitializer:
    """数据初始化器"""

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)

    def _load_json(self, filename: str) -> Any:
        """加载JSON文件"""
        filepath = self.data_dir / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def _save_json(self, filename: str, data: Any) -> None:
        """保存JSON文件"""
        filepath = self.data_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_status(self) -> Dict[str, Any]:
        """获取初始化状态"""
        files = {
            'ledger_books': '账簿清单',
            'account_codes': '科目档案',
            'accounting_rules': '核算规则',
            'customers': '客户清单',
            'suppliers': '供应商清单',
            'employees': '员工清单',
            'exchange_rates': '汇率表',
            'auxiliary_data': '辅助资料'
        }

        status = {
            'initialized': True,
            'items': {}
        }

        for filename, name in files.items():
            filepath = self.data_dir / f"{filename}.json"
            if filepath.exists():
                data = self._load_json(f"{filename}.json")
                count = len(data) if isinstance(data, list) else len(data.get('items', []))
                status['items'][filename] = {
                    'name': name,
                    'status': '已初始化',
                    'count': count,
                    'path': str(filepath)
                }
            else:
                status['items'][filename] = {
                    'name': name,
                    'status': '待初始化',
                    'count': 0,
                    'path': str(filepath)
                }

        return status

    def init_ledger_books(self, data: List[Dict]) -> Dict[str, Any]:
        """初始化账簿清单"""
        books = [LedgerBook(**item) for item in data]
        self._save_json('ledger_books.json', [asdict(b) for b in books])
        return {'success': True, 'count': len(books)}

    def init_account_codes(self, data: List[Dict]) -> Dict[str, Any]:
        """初始化科目档案"""
        accounts = [AccountCode(**item) for item in data]
        self._save_json('account_codes.json', [asdict(a) for a in accounts])
        return {'success': True, 'count': len(accounts)}

    def init_accounting_rules(self, data: List[Dict]) -> Dict[str, Any]:
        """初始化核算规则"""
        rules = [AccountingRule(**item) for item in data]
        self._save_json('accounting_rules.json', {
            'version': '1.0',
            'updated_at': datetime.now().isoformat(),
            'rules': [asdict(r) for r in rules]
        })
        return {'success': True, 'count': len(rules)}

    def init_customers(self, data: List[Dict]) -> Dict[str, Any]:
        """初始化客户清单"""
        customers = [Customer(**item) for item in data]
        self._save_json('customers.json', [asdict(c) for c in customers])
        return {'success': True, 'count': len(customers)}

    def init_suppliers(self, data: List[Dict]) -> Dict[str, Any]:
        """初始化供应商清单"""
        suppliers = [Supplier(**item) for item in data]
        self._save_json('suppliers.json', [asdict(s) for s in suppliers])
        return {'success': True, 'count': len(suppliers)}

    def init_employees(self, data: List[Dict]) -> Dict[str, Any]:
        """初始化员工清单"""
        employees = [Employee(**item) for item in data]
        self._save_json('employees.json', [asdict(e) for e in employees])
        return {'success': True, 'count': len(employees)}

    def init_exchange_rates(self, data: List[Dict]) -> Dict[str, Any]:
        """初始化汇率表"""
        rates = [ExchangeRate(**item) for item in data]
        self._save_json('exchange_rates.json', [asdict(r) for r in rates])
        return {'success': True, 'count': len(rates)}

    def init_auxiliary_data(self, data_type: str, data: List[Dict]) -> Dict[str, Any]:
        """初始化其他辅助资料"""
        aux_data = self._load_json('auxiliary_data.json') or {}
        items = [AuxiliaryData(**item) for item in data]
        aux_data[data_type] = [asdict(item) for item in items]
        self._save_json('auxiliary_data.json', aux_data)
        return {'success': True, 'count': len(items), 'type': data_type}

    def create_template(self, template_type: str) -> Dict[str, Any]:
        """生成初始化模板文件"""
        templates = {
            'ledger_books': {
                'filename': '账簿清单模板.xlsx',
                'columns': ['账簿编码', '账簿名称', '启用日期', '币别', '描述']
            },
            'account_codes': {
                'filename': '科目档案模板.xlsx',
                'columns': ['科目编码', '科目名称', '科目类别', '余额方向', '是否辅助核算', '辅助核算类型']
            },
            'customers': {
                'filename': '客户清单模板.xlsx',
                'columns': ['客户编码', '客户名称', '简称', '税号', '银行账号', '开户行', '联系人', '电话', '地址']
            },
            'suppliers': {
                'filename': '供应商清单模板.xlsx',
                'columns': ['供应商编码', '供应商名称', '简称', '税号', '银行账号', '开户行', '联系人', '电话', '地址']
            },
            'employees': {
                'filename': '员工清单模板.xlsx',
                'columns': ['员工编码', '员工姓名', '部门', '职位', '邮箱', '电话', '身份证号', '银行账号']
            },
            'exchange_rates': {
                'filename': '汇率表模板.xlsx',
                'columns': ['币种代码', '币种名称', '兑人民币汇率', '生效日期']
            }
        }

        if template_type not in templates:
            return {'success': False, 'error': f'未知模板类型: {template_type}'}

        template = templates[template_type]
        df = pd.DataFrame(columns=template['columns'])

        # 保存模板
        filepath = self.data_dir / template['filename']
        df.to_excel(filepath, index=False, engine='openpyxl')

        return {
            'success': True,
            'filename': template['filename'],
            'path': str(filepath),
            'columns': template['columns']
        }

    def create_all_templates(self) -> List[Dict[str, Any]]:
        """生成所有模板"""
        template_types = [
            'ledger_books', 'account_codes', 'customers',
            'suppliers', 'employees', 'exchange_rates'
        ]
        return [self.create_template(t) for t in template_types]


def get_initializer() -> DataInitializer:
    """获取数据初始化器实例"""
    return DataInitializer()


if __name__ == '__main__':
    # 测试代码
    initializer = DataInitializer()
    print("初始化状态:")
    print(json.dumps(initializer.get_status(), ensure_ascii=False, indent=2))
