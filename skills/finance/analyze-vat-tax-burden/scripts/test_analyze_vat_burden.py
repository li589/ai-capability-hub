import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("analyze_vat_burden.py")
SPEC = importlib.util.spec_from_file_location("analyze_vat_burden", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def base_period(period="2026-01"):
    return {
        "period": period,
        "taxpayer_type": "general",
        "sales_general": "1000000",
        "output_tax": "130000",
        "input_tax_credit": "100000",
        "input_tax_transfer_out": "0",
        "opening_credit_balance": "0",
        "closing_credit_balance": "0",
        "tax_general": "30000",
        "sales_simple": "0",
        "tax_simple": "0",
        "tax_reduction": "0",
        "additional_credit": "0",
        "vat_payable": "30000",
        "vat_paid": "30000",
    }


class AnalyzeVatBurdenTests(unittest.TestCase):
    def test_playbook_rates_and_comparison(self):
        january = base_period()
        february = base_period("2026-02")
        february.update({"sales_general": "1100000", "output_tax": "143000", "input_tax_credit": "85000", "tax_general": "58000", "vat_payable": "58000", "vat_paid": "58000"})
        result = MODULE.analyze({"entity": "Example", "unit": "yuan", "periods": [january, february]})
        self.assertEqual(result["metrics"][0]["comprehensive_burden_rate_pct"], "3.00")
        self.assertEqual(result["metrics"][1]["comprehensive_burden_rate_pct"], "5.27")
        self.assertEqual(result["comparisons"][0]["burden_rate_change_percentage_points"], "2.27")
        self.assertEqual(result["issue_counts"]["warning"], 0)

    def test_credit_balance_formation(self):
        row = base_period()
        row.update({"sales_general": "400000", "output_tax": "50000", "input_tax_credit": "80000", "opening_credit_balance": "10000", "closing_credit_balance": "40000", "tax_general": "0", "vat_payable": "0", "vat_paid": "0"})
        result = MODULE.analyze({"entity": "Example", "unit": "yuan", "periods": [row]})
        self.assertEqual(result["metrics"][0]["derived_closing_credit_balance"], "40000.00")
        self.assertEqual(result["issue_counts"]["warning"], 0)

    def test_zero_sales_does_not_divide(self):
        row = base_period()
        row.update({"sales_general": "0", "output_tax": "0", "input_tax_credit": "0", "tax_general": "0", "vat_payable": "100"})
        result = MODULE.analyze({"entity": "Example", "unit": "yuan", "periods": [row]})
        self.assertIsNone(result["metrics"][0]["comprehensive_burden_rate_pct"])
        self.assertTrue(any(item["code"] == "zero_taxable_sales" for item in result["issues"]))

    def test_credit_discontinuity_warns(self):
        january = base_period()
        january["closing_credit_balance"] = "20000"
        january["input_tax_credit"] = "120000"
        january["tax_general"] = "10000"
        january["vat_payable"] = "10000"
        february = base_period("2026-02")
        february["opening_credit_balance"] = "5000"
        february["input_tax_credit"] = "95000"
        result = MODULE.analyze({"entity": "Example", "unit": "yuan", "periods": [january, february]})
        self.assertTrue(any(item["code"] == "credit_balance_discontinuity" for item in result["issues"]))

    def test_mixed_method_and_exempt_sales(self):
        row = base_period()
        row.update({"sales_simple": "100000", "tax_simple": "3000", "exempt_sales": "200000", "vat_payable": "33000", "vat_paid": "33000"})
        result = MODULE.analyze({"entity": "Example", "unit": "yuan", "periods": [row]})
        metrics = result["metrics"][0]
        self.assertEqual(metrics["taxable_sales"], "1100000.00")
        self.assertEqual(metrics["simple_burden_rate_pct"], "3.00")
        self.assertEqual(metrics["comprehensive_burden_rate_pct"], "3.00")
        self.assertTrue(any(item["code"] == "exempt_sales_excluded" for item in result["issues"]))

    def test_unexplained_negative_is_error(self):
        row = base_period()
        row["input_tax_credit"] = "-1"
        result = MODULE.analyze({"entity": "Example", "unit": "yuan", "periods": [row]})
        self.assertEqual(result["status"], "数据异常")
        self.assertTrue(any(item["code"] == "unexplained_negative" for item in result["issues"]))

    def test_ten_thousand_yuan_uses_scaled_one_yuan_tolerance(self):
        row = base_period()
        for field in MODULE.MONEY_FIELDS:
            if field in row and row[field] is not None:
                row[field] = str(Decimal(row[field]) / Decimal("10000"))
        row["tax_general"] = "3.00005"
        row["vat_payable"] = "3.00005"
        result = MODULE.analyze({"entity": "Example", "unit": "ten_thousand_yuan", "periods": [row]})
        self.assertFalse(any(item["code"] == "general_tax_mismatch" for item in result["issues"]))

    def test_duplicate_period_is_rejected(self):
        with self.assertRaises(MODULE.InputError):
            MODULE.analyze({"entity": "Example", "unit": "yuan", "periods": [base_period(), base_period()]})

    def test_decimal_precision(self):
        self.assertEqual(MODULE.percent(Decimal("1"), Decimal("3")), "33.33")

    def test_command_line_end_to_end(self):
        payload = {"entity": "Example", "unit": "yuan", "periods": [base_period()]}
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(MODULE_PATH), str(input_path)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        output = json.loads(completed.stdout)
        self.assertEqual(output["metrics"][0]["comprehensive_burden_rate_pct"], "3.00")

    def test_command_line_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "bad.json"
            input_path.write_text("{not-json", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(MODULE_PATH), str(input_path)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("invalid JSON", completed.stderr)


if __name__ == "__main__":
    unittest.main()
