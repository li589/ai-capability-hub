import argparse, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import call_api, success, fail, run

def _normalize_nonempty(value, field_name):
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        fail(f"--{field_name} 不能为空或全空白")
    return normalized

def cmd_list(args):
    resp = call_api("ListAIWorkbenchAgents", {})
    agents = resp.get("Agents") or []
    pr = resp.get("PageResult") or {}
    success({
        "action": "list",
        "count": len(agents),
        "total_count": pr.get("TotalCount", len(agents)),
        "agents": agents,
    })

def cmd_describe(args):
    resp = call_api("DescribeAIWorkbenchAgent", {"AgentId": args.agent_id})
    success({"action": "describe", "agent": resp.get("Agent") or resp})

def cmd_executions(args):
    params = {"AgentId": args.agent_id, "PageNo": args.page_no, "PerPage": args.per_page}
    if args.status is not None:
        params["Status"] = args.status
    if args.task_id is not None:
        params["TaskIds"] = [args.task_id]
    resp = call_api("ListAIWorkbenchExecutions", params)
    pr = resp.get("PageResult") or {}
    success({
        "action": "executions",
        "executions": resp.get("Executions") or [],
        "page_result": {
            "total_count": pr.get("TotalCount", 0),
            "total_page": pr.get("TotalPage", 0),
            "page_no": args.page_no,
            "per_page": args.per_page,
        },
    })

def cmd_create(args):
    params = {"Name": _normalize_nonempty(args.name, "name"), "Source": "custom"}
    if args.description is not None:
        params["Description"] = args.description
    if args.icon is not None:
        params["Icon"] = args.icon
    if args.category is not None:
        params["Category"] = args.category
    if args.instruction is not None:
        try:
            params["Instruction"] = json.loads(args.instruction)
        except json.JSONDecodeError as e:
            fail(f"--instruction 不是合法 JSON: {e}")
    if args.skill_ids is not None:
        params["SkillIds"] = [s.strip() for s in args.skill_ids.split(",") if s.strip()]
    if args.mcp_ids is not None:
        params["MCPIds"] = [s.strip() for s in args.mcp_ids.split(",") if s.strip()]
    if args.resource_map_id is not None:
        params["ResourceMapId"] = args.resource_map_id
    resp = call_api("CreateAIWorkbenchAgent", params)
    success({**resp, "action": "create", "agent_id": resp.get("AgentId")})

def cmd_update(args):
    params = {"AgentId": args.agent_id}
    if args.name is not None:
        params["Name"] = _normalize_nonempty(args.name, "name")
    if args.description is not None:
        params["Description"] = args.description
    if args.instruction is not None:
        try:
            params["Instruction"] = json.loads(args.instruction)
        except json.JSONDecodeError as e:
            fail(f"--instruction 不是合法 JSON: {e}")
    if args.skill_ids is not None:
        params["SkillIds"] = [s.strip() for s in args.skill_ids.split(",") if s.strip()]
    if args.mcp_ids is not None:
        params["MCPIds"] = [s.strip() for s in args.mcp_ids.split(",") if s.strip()]
    if args.resource_map_id is not None:
        params["ResourceMapId"] = args.resource_map_id
    if args.disable_write_todo is not None:
        params["DisableWriteTodo"] = args.disable_write_todo == "true"
    resp = call_api("UpdateAIWorkbenchAgent", params)
    success({**resp, "action": "update"})

def cmd_delete(args):
    resp = call_api("DeleteAIWorkbenchAgent", {"AgentId": args.agent_id})
    success({**resp, "action": "delete"})

def main():
    parser = argparse.ArgumentParser(description="分身管理 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="列出所有分身")

    p_desc = sub.add_parser("describe", help="查看分身详情")
    p_desc.add_argument("--agent-id", required=True, help="Agent ID")

    p_exec = sub.add_parser("executions", help="查看分身执行记录")
    p_exec.add_argument("--agent-id", required=True, help="Agent ID")
    p_exec.add_argument("--status", default=None, help="按执行状态过滤")
    p_exec.add_argument("--task-id", default=None, help="按任务 ID 过滤（查单任务执行记录）")
    p_exec.add_argument("--per-page", type=int, default=10, help="每页条数（默认 10）")
    p_exec.add_argument("--page-no", type=int, default=1, help="页码（默认 1）")

    p_create = sub.add_parser("create", help="创建数字分身")
    p_create.add_argument("--name", required=True, help="分身名称")
    p_create.add_argument("--description", default=None, help="分身描述")
    p_create.add_argument("--icon", default=None, help="图标名称（可选）")
    p_create.add_argument("--category", default=None, help="分类（如 monitor）")
    p_create.add_argument("--instruction", default=None, help="身份定义 JSON（含 RolePosition/CoreDuty/CoreTruths/Boundaries/Vibe）")
    p_create.add_argument("--skill-ids", default=None, help="逗号分隔的 Skill ID 列表")
    p_create.add_argument("--mcp-ids", default=None, help="逗号分隔的 MCP ID 列表")
    p_create.add_argument("--resource-map-id", default=None, help="资源地图 ID")

    p_upd = sub.add_parser("update", help="更新分身配置")
    p_upd.add_argument("--agent-id", required=True, help="Agent ID")
    p_upd.add_argument("--name", default=None, help="新名称")
    p_upd.add_argument("--description", default=None, help="新描述")
    p_upd.add_argument("--instruction", default=None, help="角色设定 JSON 字符串")
    p_upd.add_argument("--skill-ids", default=None, help="逗号分隔的 Skill ID 列表")
    p_upd.add_argument("--mcp-ids", default=None, help="逗号分隔的 MCP ID 列表")
    p_upd.add_argument("--resource-map-id", default=None, help="资源映射 ID")
    p_upd.add_argument("--disable-write-todo", choices=["true", "false"], default=None,
                       help="禁用写入 TODO: true/false")

    p_del = sub.add_parser("delete", help="删除数字分身")
    p_del.add_argument("--agent-id", required=True, help="Agent ID（agt-xxx）")

    args = parser.parse_args()
    commands = {
        "list": cmd_list,
        "describe": cmd_describe,
        "executions": cmd_executions,
        "create": cmd_create,
        "update": cmd_update,
        "delete": cmd_delete,
    }
    commands[args.command](args)

if __name__ == "__main__":
    run(main)
