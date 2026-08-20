#!/usr/bin/env python3
"""
财务凭证生成器 - 数据管理模块
用于管理所有基础资料数据的增删改查操作
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


class DataManager:
    """数据管理器"""

    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            SKILL_DIR = Path(__file__).parent.parent
            data_dir = SKILL_DIR / "data"
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

    # ==================== 账簿管理 ====================

    def get_ledger_books(self) -> List[Dict]:
        """获取所有账簿"""
        data = self._load_json('ledger_books.json')
        return data if data else []

    def get_ledger_book(self, code: str) -> Optional[Dict]:
        """根据编码获取账簿"""
        books = self.get_ledger_books()
        for book in books:
            if book.get('code') == code:
                return book
        return None

    def add_ledger_book(self, book: Dict) -> Dict:
        """添加账簿"""
        books = self.get_ledger_books()
        if any(b.get('code') == book.get('code') for b in books):
            return {'success': False, 'error': '账簿编码已存在'}
        book['created_at'] = datetime.now().isoformat()
        books.append(book)
        self._save_json('ledger_books.json', books)
        return {'success': True, 'data': book}

    def update_ledger_book(self, code: str, updates: Dict) -> Dict:
        """更新账簿"""
        books = self.get_ledger_books()
        for i, book in enumerate(books):
            if book.get('code') == code:
                book.update(updates)
                book['updated_at'] = datetime.now().isoformat()
                books[i] = book
                self._save_json('ledger_books.json', books)
                return {'success': True, 'data': book}
        return {'success': False, 'error': '账簿不存在'}

    def delete_ledger_book(self, code: str) -> Dict:
        """删除账簿"""
        books = self.get_ledger_books()
        new_books = [b for b in books if b.get('code') != code]
        if len(new_books) == len(books):
            return {'success': False, 'error': '账簿不存在'}
        self._save_json('ledger_books.json', new_books)
        return {'success': True, 'deleted': code}

    # ==================== 科目管理 ====================

    def get_account_codes(self) -> List[Dict]:
        """获取所有科目"""
        data = self._load_json('account_codes.json')
        return data if data else []

    def get_account_code(self, code: str) -> Optional[Dict]:
        """根据编码获取科目"""
        accounts = self.get_account_codes()
        for account in accounts:
            if account.get('code') == code:
                return account
        return None

    def get_account_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取科目"""
        accounts = self.get_account_codes()
        for account in accounts:
            if account.get('name') == name:
                return account
        return None

    def search_accounts(self, keyword: str, search_in: str = 'both') -> List[Dict]:
        """搜索科目
        search_in: 'code'/'name'/'both'
        """
        accounts = self.get_account_codes()
        keyword = keyword.lower()
        results = []
        for account in accounts:
            if search_in in ['code', 'both']:
                if keyword in account.get('code', '').lower():
                    results.append(account)
                    continue
            if search_in in ['name', 'both']:
                if keyword in account.get('name', '').lower():
                    results.append(account)
        return results

    def add_account_code(self, account: Dict) -> Dict:
        """添加科目"""
        accounts = self.get_account_codes()
        if any(a.get('code') == account.get('code') for a in accounts):
            return {'success': False, 'error': '科目编码已存在'}
        account['created_at'] = datetime.now().isoformat()
        accounts.append(account)
        self._save_json('account_codes.json', accounts)
        return {'success': True, 'data': account}

    def update_account_code(self, code: str, updates: Dict) -> Dict:
        """更新科目"""
        accounts = self.get_account_codes()
        for i, account in enumerate(accounts):
            if account.get('code') == code:
                account.update(updates)
                account['updated_at'] = datetime.now().isoformat()
                accounts[i] = account
                self._save_json('account_codes.json', accounts)
                return {'success': True, 'data': account}
        return {'success': False, 'error': '科目不存在'}

    def delete_account_code(self, code: str) -> Dict:
        """删除科目"""
        accounts = self.get_account_codes()
        new_accounts = [a for a in accounts if a.get('code') != code]
        if len(new_accounts) == len(accounts):
            return {'success': False, 'error': '科目不存在'}
        self._save_json('account_codes.json', new_accounts)
        return {'success': True, 'deleted': code}

    def get_accounts_by_category(self, category: str) -> List[Dict]:
        """获取指定类别的科目"""
        accounts = self.get_account_codes()
        return [a for a in accounts if a.get('category') == category]

    def get_auxiliary_accounts(self) -> List[Dict]:
        """获取需要辅助核算的科目"""
        accounts = self.get_account_codes()
        return [a for a in accounts if a.get('is_auxiliary', False)]

    # ==================== 核算规则管理 ====================

    def get_accounting_rules(self) -> Dict:
        """获取所有核算规则"""
        data = self._load_json('accounting_rules.json')
        return data if data else {'version': '1.0', 'rules': []}

    def get_rules_list(self) -> List[Dict]:
        """获取规则列表"""
        rules_data = self.get_accounting_rules()
        return rules_data.get('rules', [])

    def get_rule(self, rule_id: str) -> Optional[Dict]:
        """根据ID获取规则"""
        rules = self.get_rules_list()
        for rule in rules:
            if rule.get('rule_id') == rule_id:
                return rule
        return None

    def get_rules_by_business_type(self, business_type: str) -> List[Dict]:
        """根据业务类型获取规则"""
        rules = self.get_rules_list()
        return [r for r in rules if r.get('business_type') == business_type]

    def get_rule_by_source_field(self, source_field: str) -> Optional[Dict]:
        """根据源字段获取规则"""
        rules = self.get_rules_list()
        for rule in rules:
            if rule.get('source_field') == source_field:
                return rule
        return None

    def add_accounting_rule(self, rule: Dict) -> Dict:
        """添加核算规则"""
        rules_data = self.get_accounting_rules()
        rules = rules_data.get('rules', [])

        # 检查是否已存在相同规则
        for existing_rule in rules:
            if (existing_rule.get('rule_id') == rule.get('rule_id') or
                (existing_rule.get('business_type') == rule.get('business_type') and
                 existing_rule.get('source_field') == rule.get('source_field'))):
                return {'success': False, 'error': '规则已存在'}

        rule['created_at'] = datetime.now().isoformat()
        rule['updated_at'] = datetime.now().isoformat()
        rules.append(rule)
        rules_data['rules'] = rules
        rules_data['updated_at'] = datetime.now().isoformat()
        self._save_json('accounting_rules.json', rules_data)
        return {'success': True, 'data': rule}

    def update_accounting_rule(self, rule_id: str, updates: Dict) -> Dict:
        """更新核算规则"""
        rules_data = self.get_accounting_rules()
        rules = rules_data.get('rules', [])

        for i, rule in enumerate(rules):
            if rule.get('rule_id') == rule_id:
                rule.update(updates)
                rule['updated_at'] = datetime.now().isoformat()
                rules[i] = rule
                rules_data['rules'] = rules
                rules_data['updated_at'] = datetime.now().isoformat()
                self._save_json('accounting_rules.json', rules_data)
                return {'success': True, 'data': rule}

        return {'success': False, 'error': '规则不存在'}

    def delete_accounting_rule(self, rule_id: str) -> Dict:
        """删除核算规则"""
        rules_data = self.get_accounting_rules()
        rules = rules_data.get('rules', [])
        new_rules = [r for r in rules if r.get('rule_id') != rule_id]

        if len(new_rules) == len(rules):
            return {'success': False, 'error': '规则不存在'}

        rules_data['rules'] = new_rules
        rules_data['updated_at'] = datetime.now().isoformat()
        self._save_json('accounting_rules.json', rules_data)
        return {'success': True, 'deleted': rule_id}

    def merge_rules(self, new_rules: List[Dict], strategy: str = 'user_first') -> Dict:
        """合并规则
        strategy: 'user_first' - 用户定义优先, 'auto_first' - 自动学习优先, 'replace' - 替换
        """
        rules_data = self.get_accounting_rules()
        existing_rules = rules_data.get('rules', [])
        merged = list(existing_rules)

        for new_rule in new_rules:
            existing_idx = None
            for i, existing in enumerate(merged):
                if (existing.get('business_type') == new_rule.get('business_type') and
                    existing.get('source_field') == new_rule.get('source_field')):
                    existing_idx = i
                    break

            if existing_idx is not None:
                if strategy == 'replace':
                    merged[existing_idx] = new_rule
                elif strategy == 'user_first':
                    if new_rule.get('is_user_defined', False):
                        merged[existing_idx] = new_rule
                elif strategy == 'auto_first':
                    if new_rule.get('is_auto_learned', False):
                        merged[existing_idx] = new_rule
            else:
                merged.append(new_rule)

        rules_data['rules'] = merged
        rules_data['updated_at'] = datetime.now().isoformat()
        self._save_json('accounting_rules.json', rules_data)
        return {'success': True, 'count': len(merged)}

    # ==================== 客户管理 ====================

    def get_customers(self) -> List[Dict]:
        """获取所有客户"""
        data = self._load_json('customers.json')
        return data if data else []

    def get_customer(self, code: str) -> Optional[Dict]:
        """根据编码获取客户"""
        customers = self.get_customers()
        for customer in customers:
            if customer.get('code') == code:
                return customer
        return None

    def get_customer_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取客户"""
        customers = self.get_customers()
        name_lower = name.lower()
        for customer in customers:
            if (customer.get('name', '').lower() == name_lower or
                customer.get('short_name', '').lower() == name_lower):
                return customer
        return None

    def search_customers(self, keyword: str) -> List[Dict]:
        """搜索客户"""
        customers = self.get_customers()
        keyword = keyword.lower()
        return [c for c in customers
                if keyword in c.get('code', '').lower() or
                   keyword in c.get('name', '').lower() or
                   keyword in c.get('short_name', '').lower()]

    def add_customer(self, customer: Dict) -> Dict:
        """添加客户"""
        customers = self.get_customers()
        if any(c.get('code') == customer.get('code') for c in customers):
            return {'success': False, 'error': '客户编码已存在'}
        customer['created_at'] = datetime.now().isoformat()
        customers.append(customer)
        self._save_json('customers.json', customers)
        return {'success': True, 'data': customer}

    def update_customer(self, code: str, updates: Dict) -> Dict:
        """更新客户"""
        customers = self.get_customers()
        for i, customer in enumerate(customers):
            if customer.get('code') == code:
                customer.update(updates)
                customer['updated_at'] = datetime.now().isoformat()
                customers[i] = customer
                self._save_json('customers.json', customers)
                return {'success': True, 'data': customer}
        return {'success': False, 'error': '客户不存在'}

    def delete_customer(self, code: str) -> Dict:
        """删除客户"""
        customers = self.get_customers()
        new_customers = [c for c in customers if c.get('code') != code]
        if len(new_customers) == len(customers):
            return {'success': False, 'error': '客户不存在'}
        self._save_json('customers.json', new_customers)
        return {'success': True, 'deleted': code}

    # ==================== 供应商管理 ====================

    def get_suppliers(self) -> List[Dict]:
        """获取所有供应商"""
        data = self._load_json('suppliers.json')
        return data if data else []

    def get_supplier(self, code: str) -> Optional[Dict]:
        """根据编码获取供应商"""
        suppliers = self.get_suppliers()
        for supplier in suppliers:
            if supplier.get('code') == code:
                return supplier
        return None

    def get_supplier_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取供应商"""
        suppliers = self.get_suppliers()
        name_lower = name.lower()
        for supplier in suppliers:
            if (supplier.get('name', '').lower() == name_lower or
                supplier.get('short_name', '').lower() == name_lower):
                return supplier
        return None

    def search_suppliers(self, keyword: str) -> List[Dict]:
        """搜索供应商"""
        suppliers = self.get_suppliers()
        keyword = keyword.lower()
        return [s for s in suppliers
                if keyword in s.get('code', '').lower() or
                   keyword in s.get('name', '').lower() or
                   keyword in s.get('short_name', '').lower()]

    def add_supplier(self, supplier: Dict) -> Dict:
        """添加供应商"""
        suppliers = self.get_suppliers()
        if any(s.get('code') == supplier.get('code') for s in suppliers):
            return {'success': False, 'error': '供应商编码已存在'}
        supplier['created_at'] = datetime.now().isoformat()
        suppliers.append(supplier)
        self._save_json('suppliers.json', suppliers)
        return {'success': True, 'data': supplier}

    def update_supplier(self, code: str, updates: Dict) -> Dict:
        """更新供应商"""
        suppliers = self.get_suppliers()
        for i, supplier in enumerate(suppliers):
            if supplier.get('code') == code:
                supplier.update(updates)
                supplier['updated_at'] = datetime.now().isoformat()
                suppliers[i] = supplier
                self._save_json('suppliers.json', suppliers)
                return {'success': True, 'data': supplier}
        return {'success': False, 'error': '供应商不存在'}

    def delete_supplier(self, code: str) -> Dict:
        """删除供应商"""
        suppliers = self.get_suppliers()
        new_suppliers = [s for s in suppliers if s.get('code') != code]
        if len(new_suppliers) == len(suppliers):
            return {'success': False, 'error': '供应商不存在'}
        self._save_json('suppliers.json', new_suppliers)
        return {'success': True, 'deleted': code}

    # ==================== 员工管理 ====================

    def get_employees(self) -> List[Dict]:
        """获取所有员工"""
        data = self._load_json('employees.json')
        return data if data else []

    def get_employee(self, code: str) -> Optional[Dict]:
        """根据编码获取员工"""
        employees = self.get_employees()
        for employee in employees:
            if employee.get('code') == code:
                return employee
        return None

    def get_employee_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取员工"""
        employees = self.get_employees()
        name_lower = name.lower()
        for employee in employees:
            if employee.get('name', '').lower() == name_lower:
                return employee
        return None

    def search_employees(self, keyword: str) -> List[Dict]:
        """搜索员工"""
        employees = self.get_employees()
        keyword = keyword.lower()
        return [e for e in employees
                if keyword in e.get('code', '').lower() or
                   keyword in e.get('name', '').lower() or
                   keyword in e.get('department', '').lower()]

    def add_employee(self, employee: Dict) -> Dict:
        """添加员工"""
        employees = self.get_employees()
        if any(e.get('code') == employee.get('code') for e in employees):
            return {'success': False, 'error': '员工编码已存在'}
        employee['created_at'] = datetime.now().isoformat()
        employees.append(employee)
        self._save_json('employees.json', employees)
        return {'success': True, 'data': employee}

    def update_employee(self, code: str, updates: Dict) -> Dict:
        """更新员工"""
        employees = self.get_employees()
        for i, employee in enumerate(employees):
            if employee.get('code') == code:
                employee.update(updates)
                employee['updated_at'] = datetime.now().isoformat()
                employees[i] = employee
                self._save_json('employees.json', employees)
                return {'success': True, 'data': employee}
        return {'success': False, 'error': '员工不存在'}

    def delete_employee(self, code: str) -> Dict:
        """删除员工"""
        employees = self.get_employees()
        new_employees = [e for e in employees if e.get('code') != code]
        if len(new_employees) == len(employees):
            return {'success': False, 'error': '员工不存在'}
        self._save_json('employees.json', new_employees)
        return {'success': True, 'deleted': code}

    # ==================== 汇率管理 ====================

    def get_exchange_rates(self) -> List[Dict]:
        """获取所有汇率"""
        data = self._load_json('exchange_rates.json')
        return data if data else []

    def get_exchange_rate(self, currency_code: str, effective_date: str = None) -> Optional[Dict]:
        """获取指定币种的汇率"""
        rates = self.get_exchange_rates()
        if effective_date:
            for rate in rates:
                if (rate.get('currency_code') == currency_code and
                    rate.get('effective_date') == effective_date):
                    return rate
        else:
            # 返回最新的汇率
            matching_rates = [r for r in rates if r.get('currency_code') == currency_code]
            if matching_rates:
                return sorted(matching_rates, key=lambda x: x.get('effective_date', ''), reverse=True)[0]
        return None

    def add_exchange_rate(self, rate: Dict) -> Dict:
        """添加汇率"""
        rates = self.get_exchange_rates()
        rate['created_at'] = datetime.now().isoformat()
        rates.append(rate)
        self._save_json('exchange_rates.json', rates)
        return {'success': True, 'data': rate}

    def update_exchange_rate(self, currency_code: str, effective_date: str, updates: Dict) -> Dict:
        """更新汇率"""
        rates = self.get_exchange_rates()
        for i, rate in enumerate(rates):
            if (rate.get('currency_code') == currency_code and
                rate.get('effective_date') == effective_date):
                rate.update(updates)
                rates[i] = rate
                self._save_json('exchange_rates.json', rates)
                return {'success': True, 'data': rate}
        return {'success': False, 'error': '汇率不存在'}

    def delete_exchange_rate(self, currency_code: str, effective_date: str) -> Dict:
        """删除汇率"""
        rates = self.get_exchange_rates()
        new_rates = [r for r in rates
                     if not (r.get('currency_code') == currency_code and
                             r.get('effective_date') == effective_date)]
        if len(new_rates) == len(rates):
            return {'success': False, 'error': '汇率不存在'}
        self._save_json('exchange_rates.json', new_rates)
        return {'success': True, 'deleted': {'currency_code': currency_code, 'effective_date': effective_date}}

    # ==================== 辅助资料管理 ====================

    def get_auxiliary_data(self, data_type: str = None) -> Dict:
        """获取辅助资料"""
        data = self._load_json('auxiliary_data.json')
        if data is None:
            return {}
        if data_type:
            return {data_type: data.get(data_type, [])}
        return data

    def get_auxiliary_items(self, data_type: str) -> List[Dict]:
        """获取指定类型的辅助资料"""
        all_data = self.get_auxiliary_data()
        return all_data.get(data_type, [])

    def add_auxiliary_item(self, data_type: str, item: Dict) -> Dict:
        """添加辅助资料项"""
        all_data = self.get_auxiliary_data()
        if data_type not in all_data:
            all_data[data_type] = []
        if any(i.get('code') == item.get('code') for i in all_data[data_type]):
            return {'success': False, 'error': '编码已存在'}
        item['created_at'] = datetime.now().isoformat()
        all_data[data_type].append(item)
        self._save_json('auxiliary_data.json', all_data)
        return {'success': True, 'data': item}

    def update_auxiliary_item(self, data_type: str, code: str, updates: Dict) -> Dict:
        """更新辅助资料项"""
        all_data = self.get_auxiliary_data()
        if data_type not in all_data:
            return {'success': False, 'error': '数据类型不存在'}
        items = all_data[data_type]
        for i, item in enumerate(items):
            if item.get('code') == code:
                item.update(updates)
                items[i] = item
                all_data[data_type] = items
                self._save_json('auxiliary_data.json', all_data)
                return {'success': True, 'data': item}
        return {'success': False, 'error': '项目不存在'}

    def delete_auxiliary_item(self, data_type: str, code: str) -> Dict:
        """删除辅助资料项"""
        all_data = self.get_auxiliary_data()
        if data_type not in all_data:
            return {'success': False, 'error': '数据类型不存在'}
        items = all_data[data_type]
        new_items = [i for i in items if i.get('code') != code]
        if len(new_items) == len(items):
            return {'success': False, 'error': '项目不存在'}
        all_data[data_type] = new_items
        self._save_json('auxiliary_data.json', all_data)
        return {'success': True, 'deleted': code}

    # ==================== 批量操作 ====================

    def batch_import(self, data_type: str, data: List[Dict]) -> Dict:
        """批量导入数据"""
        results = {'success': 0, 'failed': 0, 'errors': []}

        import_methods = {
            'ledger_books': self.add_ledger_book,
            'account_codes': self.add_account_code,
            'customers': self.add_customer,
            'suppliers': self.add_supplier,
            'employees': self.add_employee,
        }

        method = import_methods.get(data_type)
        if not method:
            return {'success': False, 'error': f'不支持的数据类型: {data_type}'}

        for item in data:
            result = method(item)
            if result.get('success'):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'item': item,
                    'error': result.get('error')
                })

        return results

    def export_all_data(self) -> Dict:
        """导出所有数据"""
        return {
            'exported_at': datetime.now().isoformat(),
            'ledger_books': self.get_ledger_books(),
            'account_codes': self.get_account_codes(),
            'accounting_rules': self.get_accounting_rules(),
            'customers': self.get_customers(),
            'suppliers': self.get_suppliers(),
            'employees': self.get_employees(),
            'exchange_rates': self.get_exchange_rates(),
            'auxiliary_data': self.get_auxiliary_data()
        }

    def import_all_data(self, data: Dict) -> Dict:
        """导入所有数据"""
        results = {}

        if 'ledger_books' in data:
            self._save_json('ledger_books.json', data['ledger_books'])
            results['ledger_books'] = len(data['ledger_books'])

        if 'account_codes' in data:
            self._save_json('account_codes.json', data['account_codes'])
            results['account_codes'] = len(data['account_codes'])

        if 'accounting_rules' in data:
            self._save_json('accounting_rules.json', data['accounting_rules'])
            results['accounting_rules'] = len(data['accounting_rules'].get('rules', []))

        if 'customers' in data:
            self._save_json('customers.json', data['customers'])
            results['customers'] = len(data['customers'])

        if 'suppliers' in data:
            self._save_json('suppliers.json', data['suppliers'])
            results['suppliers'] = len(data['suppliers'])

        if 'employees' in data:
            self._save_json('employees.json', data['employees'])
            results['employees'] = len(data['employees'])

        if 'exchange_rates' in data:
            self._save_json('exchange_rates.json', data['exchange_rates'])
            results['exchange_rates'] = len(data['exchange_rates'])

        if 'auxiliary_data' in data:
            self._save_json('auxiliary_data.json', data['auxiliary_data'])
            results['auxiliary_data'] = 'imported'

        return {'success': True, 'imported': results}


def get_data_manager() -> DataManager:
    """获取数据管理器实例"""
    return DataManager()


if __name__ == '__main__':
    # 测试代码
    dm = DataManager()
    print("数据导出:")
    print(json.dumps(dm.export_all_data(), ensure_ascii=False, indent=2))
