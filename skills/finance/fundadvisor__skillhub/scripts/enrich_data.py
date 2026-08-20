# -*- coding: utf-8 -*-
"""
数据丰富脚本
为基金产品添加费率信息，为基金经理添加管理规模，为基金公司添加规模排名

使用压缩JSON格式 (_f/c/d) 保持项目一致性
数据来源: 天天基金网 (eastmoney.com)
"""
import json
import time
import sys
import re
import argparse
import logging
from datetime import datetime
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False

# ── 路径配置 ──────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"

# ── 日志配置 ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("enrich")

# ── 东财请求头 ─────────────────────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://fund.eastmoney.com/",
    "Accept": "text/html,application/json,*/*",
}


# ══════════════════════════════════════════════════════════
#  工具函数
# ══════════════════════════════════════════════════════════

def http_get(url, params=None, timeout=15):
    """兼容 requests / urllib 的 GET 请求"""
    if HAS_REQUESTS:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    else:
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{qs}"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")


def load_compressed(filepath: Path) -> dict:
    """加载压缩JSON文件, 返回 {"_f":"c", "c":[...], "d":[[...], ...]}"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_compressed(filepath: Path, data: dict):
    """保存压缩JSON文件"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def col_index(data: dict, col_name: str) -> int:
    """获取列索引, -1 表示不存在"""
    try:
        return data["c"].index(col_name)
    except ValueError:
        return -1


def ensure_column(data: dict, col_name: str, default=None):
    """确保列存在, 如果不存在则添加并填充默认值"""
    if col_name not in data["c"]:
        data["c"].append(col_name)
        for row in data["d"]:
            row.append(default)
        log.debug(f"  添加新列: {col_name}")


# ══════════════════════════════════════════════════════════
#  费率采集 (基金产品 → 管理费/托管费/申购费/赎回费)
# ══════════════════════════════════════════════════════════

def fetch_fund_fees(fund_code: str) -> dict:
    """
    从天天基金网获取基金费率信息
    通过 fund detail API 获取管理费、托管费等
    """
    fees = {}

    try:
        # 使用天天基金的 pingzhongdata 接口获取基础数据
        url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
        text = http_get(url, timeout=10)

        # 从JS变量中提取费率
        # 管理费率
        m = re.search(r'fund_managementFee\s*=\s*["\']?([\d.]+)["\']?', text)
        if m:
            fees["management_fee"] = float(m.group(1))

        # 托管费率
        m = re.search(r'fund_custodyFee\s*=\s*["\']?([\d.]+)["\']?', text)
        if m:
            fees["custody_fee"] = float(m.group(1))

        # 申购费率
        m = re.search(r'fund_purchaseFee\s*=\s*["\']?([\d.]+)["\']?', text)
        if m:
            fees["purchase_fee"] = float(m.group(1))

        # 赎回费率
        m = re.search(r'fund_redeemFee\s*=\s*["\']?([\d.]+)["\']?', text)
        if m:
            fees["redeem_fee"] = float(m.group(1))

    except Exception as e:
        log.debug(f"  获取费率失败 {fund_code}: {e}")

    # 如果 pingzhongdata 未返回, 尝试 fund detail 页面
    if not fees:
        try:
            url = f"https://fund.eastmoney.com/{fund_code}.html"
            text = http_get(url, timeout=10)

            # 管理费
            m = re.search(r'管理费率[：:]?\s*([\d.]+)%', text)
            if m:
                fees["management_fee"] = float(m.group(1))

            # 托管费
            m = re.search(r'托管费率[：:]?\s*([\d.]+)%', text)
            if m:
                fees["custody_fee"] = float(m.group(1))

        except Exception as e:
            log.debug(f"  获取费率(备选)失败 {fund_code}: {e}")

    return fees


def enrich_fund_fees(data: dict, dry_run: bool = False, limit: int = 0,
                     skip_existing: bool = True) -> dict:
    """
    丰富基金产品费率数据

    参数:
        data: 压缩格式基金产品数据
        dry_run: 仅预览不写入
        limit: 限制处理数量 (0=全部)
        skip_existing: 跳过已有费率数据的产品

    返回:
        {"total": N, "enriched": M, "skipped": S, "errors": E}
    """
    log.info("=" * 60)
    log.info("开始丰富基金产品费率数据")
    log.info("=" * 60)

    # 确保费率列存在
    fee_cols = ["management_fee", "custody_fee", "purchase_fee", "redeem_fee"]
    for col in fee_cols:
        ensure_column(data, col, None)

    code_idx = col_index(data, "fund_code")
    name_idx = col_index(data, "fund_name")
    mgmt_fee_idx = col_index(data, "management_fee")

    stats = {"total": len(data["d"]), "enriched": 0, "skipped": 0, "errors": 0}
    process_count = limit if limit > 0 else stats["total"]

    log.info(f"共 {stats['total']} 只基金, 处理上限: {process_count}")
    log.info(f"模式: {'预览 (dry-run)' if dry_run else '实际写入'}")
    log.info("-" * 60)

    processed = 0
    for i, row in enumerate(data["d"]):
        if processed >= process_count:
            break

        fund_code = str(row[code_idx])
        fund_name = str(row[name_idx])

        # 跳过已有数据
        if skip_existing and row[mgmt_fee_idx] is not None:
            stats["skipped"] += 1
            continue

        processed += 1
        if processed % 100 == 0:
            log.info(f"进度: {processed}/{process_count} "
                     f"(丰富{stats['enriched']}, 跳过{stats['skipped']}, 错误{stats['errors']})")

        # 获取费率
        fees = fetch_fund_fees(fund_code)

        if fees:
            if not dry_run:
                for col in fee_cols:
                    idx = col_index(data, col)
                    row[idx] = fees.get(col.replace("_", ""), fees.get(col))
                # 直接赋值
                row[col_index(data, "management_fee")] = fees.get("management_fee")
                row[col_index(data, "custody_fee")] = fees.get("custody_fee")
                row[col_index(data, "purchase_fee")] = fees.get("purchase_fee")
                row[col_index(data, "redeem_fee")] = fees.get("redeem_fee")

            stats["enriched"] += 1
            if dry_run and stats["enriched"] <= 5:
                log.info(f"  [预览] {fund_code} {fund_name}: {fees}")
        else:
            stats["errors"] += 1

        # 请求间隔
        time.sleep(0.15)

    log.info("-" * 60)
    log.info(f"费率丰富完成: 丰富{stats['enriched']}, 跳过{stats['skipped']}, 错误{stats['errors']}")
    return stats


# ══════════════════════════════════════════════════════════
#  经理AUM采集 (基金经理 → 管理规模)
# ══════════════════════════════════════════════════════════

def fetch_manager_aum(manager_id: str) -> float | None:
    """
    从天天基金获取基金经理最新管理规模 (亿元)
    """
    try:
        url = f"https://fund.eastmoney.com/manager/{manager_id}.html"
        text = http_get(url, timeout=10)

        # 匹配管理规模: xx.xx亿元
        m = re.search(r'管理规模[：:]?\s*([\d,.]+)\s*亿', text)
        if m:
            return float(m.group(1).replace(",", ""))

        # 备选: 从数据接口中提取
        m = re.search(r'"totalscale"\s*:\s*([\d.]+)', text)
        if m:
            return float(m.group(1))

    except Exception as e:
        log.debug(f"  获取AUM失败 {manager_id}: {e}")

    return None


def enrich_manager_aum(data: dict, dry_run: bool = False, limit: int = 0,
                       skip_existing: bool = True) -> dict:
    """
    丰富基金经理管理规模数据

    返回:
        {"total": N, "enriched": M, "skipped": S, "errors": E}
    """
    log.info("=" * 60)
    log.info("开始丰富基金经理管理规模")
    log.info("=" * 60)

    # 确保列存在
    ensure_column(data, "latest_aum", None)
    ensure_column(data, "aum_updated", None)

    id_idx = col_index(data, "manager_id")
    name_idx = col_index(data, "name")
    scale_idx = col_index(data, "total_scale")
    aum_idx = col_index(data, "latest_aum")
    aum_date_idx = col_index(data, "aum_updated")

    stats = {"total": len(data["d"]), "enriched": 0, "skipped": 0, "errors": 0}
    process_count = limit if limit > 0 else stats["total"]

    log.info(f"共 {stats['total']} 位经理, 处理上限: {process_count}")
    log.info("-" * 60)

    processed = 0
    for i, row in enumerate(data["d"]):
        if processed >= process_count:
            break

        manager_id = str(row[id_idx])
        manager_name = str(row[name_idx])

        # 跳过已有最新AUM
        if skip_existing and row[aum_idx] is not None:
            stats["skipped"] += 1
            continue

        processed += 1
        if processed % 50 == 0:
            log.info(f"进度: {processed}/{process_count}")

        aum = fetch_manager_aum(manager_id)
        if aum is not None:
            if not dry_run:
                row[aum_idx] = aum
                row[aum_date_idx] = datetime.now().strftime("%Y-%m-%d")
            stats["enriched"] += 1
            if dry_run and stats["enriched"] <= 5:
                log.info(f"  [预览] {manager_name}: {aum}亿 (原: {row[scale_idx]})")
        else:
            stats["errors"] += 1

        time.sleep(0.15)

    log.info("-" * 60)
    log.info(f"AUM丰富完成: 丰富{stats['enriched']}, 跳过{stats['skipped']}, 错误{stats['errors']}")
    return stats


# ══════════════════════════════════════════════════════════
#  公司排名采集 (基金公司 → 规模排名)
# ══════════════════════════════════════════════════════════

def fetch_company_rankings() -> dict:
    """
    从天天基金获取基金公司规模排名
    返回: {公司名称: {"rank": 排名, "scale": 规模(亿)}}
    """
    rankings = {}

    try:
        # 天天基金公司排名接口
        url = "https://fund.eastmoney.com/Company/home/KFSFundRank"
        params = {
            "fundType": "0",
            "sort": "desc",
            "orderby": "totalMoney",
            "pageIndex": "1",
            "pageSize": "200",
        }
        text = http_get(url, params=params, timeout=15)

        # 尝试解析HTML表格
        # 匹配排名数据
        rows = re.findall(
            r'<td[^>]*>(\d+)</td>.*?<a[^>]*>([^<]+)</a>.*?<td[^>]*>([\d,.]+)</td>',
            text, re.DOTALL
        )
        for rank, name, scale in rows:
            rankings[name.strip()] = {
                "rank": int(rank),
                "scale": float(scale.replace(",", ""))
            }

    except Exception as e:
        log.warning(f"获取公司排名失败: {e}")

    # 备选: 从现有数据按 total_scale 排序生成本地排名
    if not rankings:
        log.info("API排名获取失败, 将基于本地数据生成排名")

    return rankings


def enrich_company_rankings(data: dict, dry_run: bool = False) -> dict:
    """
    丰富基金公司规模排名

    返回:
        {"total": N, "enriched": M, "source": "api|local"}
    """
    log.info("=" * 60)
    log.info("开始丰富基金公司规模排名")
    log.info("=" * 60)

    # 确保列存在
    ensure_column(data, "scale_rank", None)
    ensure_column(data, "rank_updated", None)

    name_idx = col_index(data, "name")
    scale_idx = col_index(data, "total_scale")
    rank_idx = col_index(data, "scale_rank")
    rank_date_idx = col_index(data, "rank_updated")

    stats = {"total": len(data["d"]), "enriched": 0, "source": "none"}

    # 尝试API排名
    api_rankings = fetch_company_rankings()

    if api_rankings:
        stats["source"] = "api"
        log.info(f"从API获取到 {len(api_rankings)} 家公司排名")
        for row in data["d"]:
            company_name = str(row[name_idx])
            if company_name in api_rankings:
                if not dry_run:
                    row[rank_idx] = api_rankings[company_name]["rank"]
                    row[rank_date_idx] = datetime.now().strftime("%Y-%m-%d")
                stats["enriched"] += 1
    else:
        # 本地排名: 按 total_scale 降序
        stats["source"] = "local"
        log.info("使用本地数据生成排名")

        # 构建 (index, scale) 列表
        indexed = []
        for i, row in enumerate(data["d"]):
            scale = row[scale_idx] if row[scale_idx] is not None else 0
            indexed.append((i, float(scale)))

        # 按规模降序排序
        indexed.sort(key=lambda x: -x[1])

        for rank, (idx, scale) in enumerate(indexed, 1):
            if not dry_run:
                data["d"][idx][rank_idx] = rank
                data["d"][idx][rank_date_idx] = datetime.now().strftime("%Y-%m-%d")
            stats["enriched"] += 1

            if dry_run and rank <= 5:
                name = data["d"][idx][name_idx]
                log.info(f"  [预览] #{rank}: {name} ({scale}亿)")

    log.info("-" * 60)
    log.info(f"排名丰富完成: {stats['enriched']}家公司, 数据源: {stats['source']}")
    return stats


# ══════════════════════════════════════════════════════════
#  主流程
# ══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="基金数据丰富工具 - 补充费率、AUM、排名等信息"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="预览模式, 不实际修改数据文件")
    parser.add_argument("--fees", action="store_true",
                        help="丰富基金产品费率")
    parser.add_argument("--aum", action="store_true",
                        help="丰富基金经理管理规模")
    parser.add_argument("--rankings", action="store_true",
                        help="丰富基金公司规模排名")
    parser.add_argument("--all", action="store_true",
                        help="执行所有丰富任务")
    parser.add_argument("--limit", type=int, default=0,
                        help="限制每个任务的处理数量 (0=全部)")
    parser.add_argument("--skip-existing", action="store_true", default=True,
                        help="跳过已有数据的条目 (默认开启)")
    parser.add_argument("--overwrite", action="store_true",
                        help="覆盖已有数据")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="详细日志输出")

    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    # 如果没有指定任何任务, 显示帮助
    if not (args.fees or args.aum or args.rankings or args.all):
        parser.print_help()
        print("\n示例:")
        print("  python enrich_data.py --all --dry-run       # 预览所有任务")
        print("  python enrich_data.py --fees --limit 100     # 处理100只基金的费率")
        print("  python enrich_data.py --aum --rankings       # 丰富AUM和排名")
        return

    skip_existing = not args.overwrite
    all_stats = {}

    log.info("基金数据丰富工具启动")
    log.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"数据目录: {DATA_DIR}")
    log.info(f"模式: {'预览 (dry-run)' if args.dry_run else '实际写入'}")
    log.info("")

    # ── 丰富费率 ──────────────────────────────────────────
    if args.fees or args.all:
        products_path = DATA_DIR / "fund_products.json"
        if not products_path.exists():
            log.error(f"文件不存在: {products_path}")
        else:
            data = load_compressed(products_path)
            stats = enrich_fund_fees(data, args.dry_run, args.limit, skip_existing)
            all_stats["fees"] = stats

            if not args.dry_run:
                save_compressed(products_path, data)
                log.info(f"已保存: {products_path}")

    # ── 丰富AUM ──────────────────────────────────────────
    if args.aum or args.all:
        managers_path = DATA_DIR / "fund_managers_distilled.json"
        if not managers_path.exists():
            log.error(f"文件不存在: {managers_path}")
        else:
            data = load_compressed(managers_path)
            stats = enrich_manager_aum(data, args.dry_run, args.limit, skip_existing)
            all_stats["aum"] = stats

            if not args.dry_run:
                save_compressed(managers_path, data)
                log.info(f"已保存: {managers_path}")

    # ── 丰富排名 ──────────────────────────────────────────
    if args.rankings or args.all:
        companies_path = DATA_DIR / "fund_companies_distilled.json"
        if not companies_path.exists():
            log.error(f"文件不存在: {companies_path}")
        else:
            data = load_compressed(companies_path)
            stats = enrich_company_rankings(data, args.dry_run)
            all_stats["rankings"] = stats

            if not args.dry_run:
                save_compressed(companies_path, data)
                log.info(f"已保存: {companies_path}")

    # ── 汇总 ─────────────────────────────────────────────
    log.info("")
    log.info("=" * 60)
    log.info("丰富任务汇总")
    log.info("=" * 60)
    for task, stats in all_stats.items():
        log.info(f"  {task}: {json.dumps(stats, ensure_ascii=False)}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
