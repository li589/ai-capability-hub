import argparse, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import call_api, call_notice_api, success, run

def cmd_maps(args):
    params = {"PageNo": args.page_no, "PerPage": args.per_page}
    if args.keyword is not None:
        params["Keyword"] = args.keyword
    resp = call_api("ListAIWorkbenchResourceMaps", params)
    pr = resp.get("PageResult") or {}
    success({"action": "maps", "resource_maps": resp.get("ResourceMaps") or [],
             "page_result": {"total": pr.get("TotalCount"), "total_page": pr.get("TotalPage"),
                             "page_no": args.page_no, "per_page": args.per_page}})

def cmd_map(args):
    resp = call_api("DescribeAIWorkbenchResourceMap", {"ResourceMapId": args.resource_map_id})
    success({"action": "map", "resource_map": resp.get("ResourceMap") or resp})

def cmd_instances(args):
    params = {"ResourceMapId": args.resource_map_id,
              "PageParams": {"PageNo": args.page_no, "PerPage": args.per_page}}
    resp = call_api("ListAIWorkbenchResourceInstances", params)
    pr = resp.get("PageResult") or {}
    success({"action": "instances", "instances": resp.get("Instances") or [],
             "page_result": {"total": pr.get("TotalCount"), "total_page": pr.get("TotalPage"),
                             "page_no": args.page_no, "per_page": args.per_page}})

def cmd_skills(args):
    params = {"PageNo": args.page_no, "PerPage": args.per_page}

    if not args.all:
        params["Enabled"] = True
    if args.skill_ids is not None:
        params["SkillIds"] = [s.strip() for s in args.skill_ids.split(",") if s.strip()]
    if args.keyword is not None:
        params["Keyword"] = args.keyword
    resp = call_api("ListAIWorkbenchSkills", params)
    pr = resp.get("PageResult") or {}
    success({"action": "skills", "skills": resp.get("Skills") or [],
             "page_result": {"total": pr.get("TotalCount"), "total_page": pr.get("TotalPage"), "page_no": args.page_no, "per_page": args.per_page}})

def cmd_mcps(args):
    params = {"PageNo": args.page_no, "PerPage": args.per_page}

    if not args.all:
        params["Enabled"] = True
    if args.mcp_ids is not None:
        params["MCPIds"] = [s.strip() for s in args.mcp_ids.split(",") if s.strip()]
    if args.keyword is not None:
        params["Keyword"] = args.keyword
    resp = call_api("ListAIWorkbenchMCPs", params)
    pr = resp.get("PageResult") or {}
    success({"action": "mcps", "mcps": resp.get("MCPs") or [],
             "page_result": {"total": pr.get("TotalCount"), "total_page": pr.get("TotalPage"), "page_no": args.page_no, "per_page": args.per_page}})

def cmd_notices(args):

    params = {"Module": "monitor", "Order": "DESC", "PageNumber": 1, "PageSize": 50}
    if args.notice_ids is not None:
        params["NoticeIds"] = [s.strip() for s in args.notice_ids.split(",") if s.strip()]
    resp = call_notice_api("DescribeAlarmNotices", params)
    success({"action": "notices", "notices": resp.get("Notices") or [], "total": resp.get("TotalCount")})

def main():
    parser = argparse.ArgumentParser(description="Resource query tool")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("maps")
    p.add_argument("--keyword", default=None)
    p.add_argument("--page-no", type=int, default=1)
    p.add_argument("--per-page", type=int, default=20)

    p = sub.add_parser("map")
    p.add_argument("--resource-map-id", required=True)

    p = sub.add_parser("instances")
    p.add_argument("--resource-map-id", required=True)
    p.add_argument("--page-no", type=int, default=1)
    p.add_argument("--per-page", type=int, default=50)

    p = sub.add_parser("skills")
    p.add_argument("--skill-ids", default=None)
    p.add_argument("--keyword", default=None)
    p.add_argument("--all", action="store_true", default=False,
                   help="查全部（含停用）；省略则默认只列启用项")
    p.add_argument("--page-no", type=int, default=1)
    p.add_argument("--per-page", type=int, default=20)

    p = sub.add_parser("mcps")
    p.add_argument("--mcp-ids", default=None)
    p.add_argument("--keyword", default=None)
    p.add_argument("--all", action="store_true", default=False,
                   help="查全部（含停用）；省略则默认只列启用项")
    p.add_argument("--page-no", type=int, default=1)
    p.add_argument("--per-page", type=int, default=20)

    p = sub.add_parser("notices")
    p.add_argument("--notice-ids", default=None)

    args = parser.parse_args()
    dispatch = {"maps": cmd_maps, "map": cmd_map, "instances": cmd_instances, "skills": cmd_skills,
                "mcps": cmd_mcps, "notices": cmd_notices}
    dispatch[args.cmd](args)

if __name__ == "__main__":
    run(main)
