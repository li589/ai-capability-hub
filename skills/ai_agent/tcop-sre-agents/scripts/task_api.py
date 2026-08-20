import argparse, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import call_api, success, fail, run

def _split_ids(raw):
    return [i.strip() for i in raw.split(",") if i.strip()]

def _parse_bool(val):
    return val.lower() == "true"

def cmd_list(args):
    params = {"AgentId": args.agent_id}
    if args.keyword is not None:
        params["Keyword"] = args.keyword
    if args.enabled is not None:
        params["Enabled"] = _parse_bool(args.enabled)
    resp = call_api("ListAIWorkbenchTasks", params)
    success({"action": "list", "tasks": resp.get("Tasks") or []})

def cmd_describe(args):
    resp = call_api("DescribeAIWorkbenchTask", {"TaskId": args.task_id})
    success({"action": "describe", "task": resp.get("Task") or resp})

def cmd_create(args):

    if args.trigger_type == "cron" and not (args.cron or "").strip():
        fail("创建 cron 任务必须提供 --cron 表达式（如 '0 9 * * *'），否则任务没有触发时间")
    params = {"AgentId": args.agent_id, "Name": args.name, "TriggerType": args.trigger_type}
    if args.description is not None:
        params["Description"] = args.description
    if args.cron is not None:
        params["CronExpr"] = args.cron
    if args.cron_timezone is not None:
        params["CronTimezone"] = args.cron_timezone
    if args.prompt is not None:
        params["PromptTemplate"] = args.prompt
    if args.output_format is not None:
        params["OutputFormat"] = args.output_format
    if args.enabled is not None:
        params["Enabled"] = _parse_bool(args.enabled)
    if args.notify_ids is not None:
        params["NotifyIds"] = _split_ids(args.notify_ids)
    if args.timeout_sec is not None:
        params["TimeoutSec"] = args.timeout_sec
    if args.retry_count is not None:
        params["RetryCount"] = args.retry_count
    if args.resource_map_id is not None:
        params["ResourceMapId"] = args.resource_map_id
    if args.skill_ids is not None:
        params["SkillIds"] = _split_ids(args.skill_ids)
    if args.mcp_ids is not None:
        params["McpEndpointIds"] = _split_ids(args.mcp_ids)
    resp = call_api("CreateAIWorkbenchTask", params)
    success({**resp, "action": "create"})

def cmd_update(args):

    if args.trigger_type == "cron" and not (args.cron or "").strip():
        fail("触发类型改为 cron 时必须同时提供 --cron 表达式（如 '0 9 * * *'）")
    params = {"TaskId": args.task_id}
    if args.name is not None:
        params["Name"] = args.name
    if args.description is not None:
        params["Description"] = args.description
    if args.trigger_type is not None:
        params["TriggerType"] = args.trigger_type
    if args.cron is not None:
        params["CronExpr"] = args.cron
    if args.cron_timezone is not None:
        params["CronTimezone"] = args.cron_timezone
    if args.prompt is not None:
        params["PromptTemplate"] = args.prompt
    if args.output_format is not None:
        params["OutputFormat"] = args.output_format
    if args.enabled is not None:
        params["Enabled"] = _parse_bool(args.enabled)
    if args.notify_ids is not None:
        params["NotifyIds"] = _split_ids(args.notify_ids)
    if args.timeout_sec is not None:
        params["TimeoutSec"] = args.timeout_sec
    if args.retry_count is not None:
        params["RetryCount"] = args.retry_count
    if args.resource_map_id is not None:
        params["ResourceMapId"] = args.resource_map_id
    if args.skill_ids is not None:
        params["SkillIds"] = _split_ids(args.skill_ids)
    if args.mcp_ids is not None:
        params["McpEndpointIds"] = _split_ids(args.mcp_ids)
    resp = call_api("UpdateAIWorkbenchTask", params)
    success({**resp, "action": "update"})

def cmd_trigger(args):
    resp = call_api("TriggerAIWorkbenchTask", {"TaskId": args.task_id})
    success({**resp, "action": "trigger", "task_id": args.task_id})

def cmd_delete(args):
    resp = call_api("DeleteAIWorkbenchTask", {"TaskId": args.task_id})
    success({**resp, "action": "delete"})

def cmd_templates(_args):
    resp = call_api("ListAIWorkbenchTaskTemplates", {})
    success({"action": "templates", "templates": resp.get("Templates") or []})

def main():
    parser = argparse.ArgumentParser(description="AI Workbench Task API")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="ListAIWorkbenchTasks")
    p.add_argument("--agent-id", required=True)
    p.add_argument("--keyword", default=None)
    p.add_argument("--enabled", default=None, choices=["true", "false"],
                   help="按启用状态过滤；省略=不过滤")

    p = sub.add_parser("describe", help="DescribeAIWorkbenchTask")
    p.add_argument("--task-id", required=True)

    p = sub.add_parser("create", help="CreateAIWorkbenchTask")
    p.add_argument("--agent-id", required=True, help="关联 Agent ID")
    p.add_argument("--name", required=True, help="任务名称")
    p.add_argument("--trigger-type", default="cron", choices=["cron", "manual", "webhook"],
                   help="触发类型（默认 cron）")
    p.add_argument("--description", default=None, help="任务描述")
    p.add_argument("--cron", default=None, help="Cron 表达式（trigger-type=cron 时必填）")
    p.add_argument("--cron-timezone", default=None, help="Cron 时区（默认 Asia/Shanghai）")
    p.add_argument("--prompt", default=None, help="PromptTemplate 提示词模板")
    p.add_argument("--output-format", default=None, choices=["markdown", "json"],
                   help="输出格式（默认 markdown）")
    p.add_argument("--enabled", default="true", choices=["true", "false"],
                   help="是否启用（默认 true：创建即启用，见 references/sop.md 默认值策略）")
    p.add_argument("--notify-ids", default=None, help="通知模板 ID，逗号分隔")
    p.add_argument("--timeout-sec", type=int, default=None, help="超时时间（秒）")
    p.add_argument("--retry-count", type=int, default=None, help="重试次数")
    p.add_argument("--resource-map-id", default=None, help="资源地图 ID")
    p.add_argument("--skill-ids", default=None, help="Skill ID 列表，逗号分隔")
    p.add_argument("--mcp-ids", default=None, help="MCP 端点 ID 列表，逗号分隔")

    p = sub.add_parser("update", help="UpdateAIWorkbenchTask")
    p.add_argument("--task-id", required=True, help="任务 ID")
    p.add_argument("--name", default=None, help="新名称")
    p.add_argument("--description", default=None, help="新描述")
    p.add_argument("--trigger-type", default=None, choices=["cron", "manual", "webhook"],
                   help="变更触发类型")
    p.add_argument("--cron", default=None, help="新 Cron 表达式")
    p.add_argument("--cron-timezone", default=None, help="新 Cron 时区")
    p.add_argument("--prompt", default=None, help="新 PromptTemplate")
    p.add_argument("--output-format", default=None, choices=["markdown", "json"],
                   help="新输出格式")
    p.add_argument("--enabled", default=None, choices=["true", "false"],
                   help="启用/停用；省略=不变")
    p.add_argument("--notify-ids", default=None, help="通知模板 ID，逗号分隔")
    p.add_argument("--timeout-sec", type=int, default=None, help="超时时间（秒）")
    p.add_argument("--retry-count", type=int, default=None, help="重试次数")
    p.add_argument("--resource-map-id", default=None, help="资源地图 ID")
    p.add_argument("--skill-ids", default=None, help="Skill ID 列表，逗号分隔")
    p.add_argument("--mcp-ids", default=None, help="MCP 端点 ID 列表，逗号分隔")

    p = sub.add_parser("trigger", help="TriggerAIWorkbenchTask")
    p.add_argument("--task-id", required=True)

    p = sub.add_parser("delete", help="DeleteAIWorkbenchTask")
    p.add_argument("--task-id", required=True)

    sub.add_parser("templates", help="ListAIWorkbenchTaskTemplates")

    args = parser.parse_args()
    dispatch = {
        "list": cmd_list, "describe": cmd_describe, "create": cmd_create,
        "update": cmd_update, "trigger": cmd_trigger, "delete": cmd_delete,
        "templates": cmd_templates,
    }
    dispatch[args.cmd](args)

if __name__ == "__main__":
    run(main)
