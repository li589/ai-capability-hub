# -*- coding: utf-8 -*-
"""
智能交付主入口（AI 对话层使用）：
1. 未提供映射时，先输出【接口字段清单】+【Excel 表头】，由 AI 生成智能映射
2. 提供映射后，执行完整交付（分批调用 + 报告）

用法:
  python deliver.py inspect <api_name> <excel_path> [--sheet SHEET]   # 查看字段对照
  python deliver.py run <api_name> <excel_path> [--map '{json}'] [--dry-run] [--sheet SHEET] [--batch N]
"""
import json
import sys
from pathlib import Path
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_payload import load_spec
from parse_excel import preview
from batch_runner import run_delivery


def cmd_inspect(api_name, excel_path, sheet_name=None):
    """打印接口字段 vs Excel 表头，供 AI 智能映射"""
    spec = load_spec(api_name)
    data = preview(excel_path, sheet_name=sheet_name, n=3)

    print("=" * 60)
    print(f"接口: {api_name}  endpoint={spec['endpoint']}  batch_mode={spec.get('batch_mode')}")
    print("=" * 60)
    if "nested" in spec:
        print("\n【接口字段清单】嵌套结构 content[].head + content[].body")
        for sec in ("head", "body"):
            print(f"  -- {sec} --")
            for f in spec["nested"].get(sec, []):
                print(f"  {f['api_field']:<24} | {f.get('label',''):<16} | {f.get('type','string'):<8} | "
                      f"{'必填' if f.get('required') else '可选':<4} | {f.get('desc','')}")
    else:
        print("\n【接口字段清单】(api_field | label | type | required | 说明)")
        for f in spec["fields"]:
            print(f"  {f['api_field']:<24} | {f.get('label',''):<16} | {f.get('type','string'):<8} | "
                  f"{'必填' if f.get('required') else '可选':<4} | {f.get('desc','')}")
    if spec.get("payload"):
        print("\n【请求包装】:", json.dumps(spec["payload"], ensure_ascii=False))
    if spec.get("fixed_values"):
        print("\n【固定值】:", json.dumps(spec["fixed_values"], ensure_ascii=False))

    print("\n【Excel 表头】:")
    for i, h in enumerate(data["headers"]):
        print(f"  [{i}] {h}")
    print(f"\n【数据预览】共 {data['total']} 行（显示前 {min(3, data['total'])} 行）:")
    for r in data["rows"][:3]:
        print("  ", json.dumps(r, ensure_ascii=False, default=str))

    print("\n" + "=" * 60)
    print("下一步: 根据表头与字段清单生成映射，然后执行:")
    print(f"  python deliver.py run {api_name} \"{excel_path}\" --map '{{\"api字段名\": \"Excel列名\", ...}}'")
    print("=" * 60)


def cmd_run(api_name, excel_path, **kwargs):
    # 运行前检查服务器连接（--skip-check 可跳过）
    if not kwargs.pop("skip_check", False):
        import setup_config
        cfg = setup_config.load_config()
        srv = cfg.get("server", {})
        host, port = srv.get("host"), srv.get("port")
        if not host or not port:
            print("⚠️ 尚未配置服务器地址！请先运行:")
            print("   python scripts/setup_config.py            # 交互式配置")
            print("   或 python scripts/setup_config.py --set 192.168.1.10:20201")
            sys.exit(1)
        ok, msg = setup_config.test_connection(host, port)
        if not ok:
            print(f"⚠️ 服务器连接失败: {msg}")
            print("  请修改配置后重试:")
            print("   python scripts/setup_config.py --set <新IP>:<新端口>")
            print("   或 python scripts/setup_config.py         # 交互式修改")
            sys.exit(1)
        print(f"✅ 服务器连接正常: {host}:{port}")
    result = run_delivery(api_name, excel_path, **kwargs)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return result


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    # config 子命令：透传给 setup_config.py
    if args[0] == "config":
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import setup_config
        sys.argv = ["setup_config.py"] + args[1:]
        sys.exit(setup_config.main())
    if len(args) < 2 or args[0] not in ("inspect", "run"):
        print(__doc__)
        sys.exit(1)
    cmd, api = args[0], args[1]
    excel = args[2] if len(args) > 2 else None
    kwargs = {}
    if "--sheet" in args:
        kwargs["sheet_name"] = args[args.index("--sheet") + 1]
    if "--map" in args:
        kwargs["col_map"] = json.loads(args[args.index("--map") + 1])
    if "--dry-run" in args:
        kwargs["dry_run"] = True
    if "--batch" in args:
        kwargs["batch_size"] = int(args[args.index("--batch") + 1])
    if "--skip-check" in args:
        kwargs["skip_check"] = True

    if cmd == "inspect":
        cmd_inspect(api, excel, kwargs.get("sheet_name"))
    else:
        cmd_run(api, excel, **kwargs)
