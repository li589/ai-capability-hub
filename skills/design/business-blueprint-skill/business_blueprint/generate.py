from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .clarify import build_clarify_requests
from .model import load_json, new_revision_meta, write_json
from .normalize import merge_or_create_system


# ─── Flow sequence definitions: ordered steps within named processes ───
# Each entry: (process_name, [step_trigger_keywords_in_order])
FLOW_SEQUENCES: tuple[tuple[str, list[tuple[str, str]]], ...] = (
    # Membership lifecycle
    ("会员生命周期", [
        ("注册", "flow-membership-register"),
        ("下单", "flow-order-create"),
        ("累计", "flow-points-accrual"),
    ]),
    # Order fulfillment
    ("订单履约", [
        ("下单", "flow-order-create"),
        ("跟进", "flow-service-followup"),
    ]),
    # Production cycle
    ("生产周期", [
        ("排产", "flow-production-scheduling"),
        ("来料检验", "flow-incoming-inspection"),
        ("入库", "flow-warehouse-inbound"),
    ]),
    # Supply chain
    ("供应链流程", [
        ("采购", "flow-purchase-request"),
    ]),
    # Credit lifecycle
    ("信贷流程", [
        ("信贷申请", "flow-credit-application"),
        ("风险评级", "flow-risk-assessment"),
        ("合规检查", "flow-compliance-check"),
        ("客户画像", "flow-customer-profiling"),
    ]),
)


# ─── Common actor rules (all industries) ───
ACTOR_RULES: tuple[tuple[str, str, str], ...] = (
    ("导购", "actor-store-guide", "门店导购"),
    ("客服", "actor-service", "客服"),
    ("运营", "actor-ops", "运营"),
    ("生产经理", "actor-production-mgr", "生产经理"),
    ("质检", "actor-quality-inspector", "质检员"),
    ("仓库管理", "actor-warehouse-mgr", "仓库管理员"),
    ("采购", "actor-purchasing", "采购专员"),
    ("风控", "actor-risk-analyst", "风控分析师"),
    ("信贷审批", "actor-credit-approver", "信贷审批员"),
    ("合规", "actor-compliance", "合规专员"),
    ("项目经理", "actor-project-mgr", "项目经理"),
    ("财务", "actor-finance", "财务专员"),
)

# ─── Common capability rules ───
CAPABILITY_RULES: tuple[tuple[str, str, str, str], ...] = (
    ("会员", "cap-membership", "会员运营", "管理会员拉新、促活和留存。"),
    ("订单", "cap-order", "订单管理", "管理订单创建、处理和履约。"),
    ("门店", "cap-store-ops", "门店运营", "支撑门店日常经营和导购协作。"),
    ("生产计划", "cap-production-plan", "生产计划管理", "管理生产排程、产能规划和生产调度。"),
    ("质检", "cap-quality-control", "质量管理", "管理来料检验、过程检验和成品检验。"),
    ("仓储", "cap-warehouse", "仓储管理", "管理入库、出库、库存和库位。"),
    ("供应链", "cap-supply-chain", "供应链协同", "管理供应商协同、采购计划和物流。"),
    ("风控", "cap-risk-control", "风险控制", "管理风险评估、预警和处置。"),
    ("信贷", "cap-credit", "信贷管理", "管理信贷申请、审批和放款。"),
    ("合规", "cap-compliance", "合规管理", "管理合规检查、审计和报告。"),
    ("客户画像", "cap-customer-profile", "客户画像", "构建和维护客户360度画像。"),
)

# ─── Common flow rules ───
FLOW_RULES: tuple[tuple[str, dict[str, Any]], ...] = (
    # Retail flows
    (
        "注册",
        {
            "id": "flow-membership-register",
            "name": "会员注册",
            "actorId": "actor-store-guide",
            "capabilityIds": ["cap-membership"],
        },
    ),
    (
        "下单",
        {
            "id": "flow-order-create",
            "name": "订单创建",
            "actorId": "actor-store-guide",
            "capabilityIds": ["cap-order"],
        },
    ),
    (
        "累计",
        {
            "id": "flow-points-accrual",
            "name": "积分累计",
            "actorId": "actor-store-guide",
            "capabilityIds": ["cap-membership"],
        },
    ),
    (
        "跟进",
        {
            "id": "flow-service-followup",
            "name": "售后跟进",
            "actorId": "actor-service",
            "capabilityIds": ["cap-order"],
        },
    ),
    # Manufacturing flows
    (
        "排产",
        {
            "id": "flow-production-scheduling",
            "name": "生产排程",
            "actorId": "actor-production-mgr",
            "capabilityIds": ["cap-production-plan"],
        },
    ),
    (
        "生产计划",
        {
            "id": "flow-production-scheduling",
            "name": "生产排程",
            "actorId": "actor-production-mgr",
            "capabilityIds": ["cap-production-plan"],
        },
    ),
    (
        "来料检验",
        {
            "id": "flow-incoming-inspection",
            "name": "来料检验",
            "actorId": "actor-quality-inspector",
            "capabilityIds": ["cap-quality-control"],
        },
    ),
    (
        "质检",
        {
            "id": "flow-incoming-inspection",
            "name": "来料检验",
            "actorId": "actor-quality-inspector",
            "capabilityIds": ["cap-quality-control"],
        },
    ),
    (
        "入库",
        {
            "id": "flow-warehouse-inbound",
            "name": "入库作业",
            "actorId": "actor-warehouse-mgr",
            "capabilityIds": ["cap-warehouse"],
        },
    ),
    (
        "仓储",
        {
            "id": "flow-warehouse-inbound",
            "name": "入库作业",
            "actorId": "actor-warehouse-mgr",
            "capabilityIds": ["cap-warehouse"],
        },
    ),
    (
        "采购申请",
        {
            "id": "flow-purchase-request",
            "name": "采购申请",
            "actorId": "actor-purchasing",
            "capabilityIds": ["cap-supply-chain"],
        },
    ),
    (
        "采购",
        {
            "id": "flow-purchase-request",
            "name": "采购申请",
            "actorId": "actor-purchasing",
            "capabilityIds": ["cap-supply-chain"],
        },
    ),
    (
        "供应链",
        {
            "id": "flow-purchase-request",
            "name": "采购申请",
            "actorId": "actor-purchasing",
            "capabilityIds": ["cap-supply-chain"],
        },
    ),
    # Finance flows
    (
        "信贷申请",
        {
            "id": "flow-credit-application",
            "name": "信贷申请",
            "actorId": "actor-credit-approver",
            "capabilityIds": ["cap-credit"],
        },
    ),
    (
        "风险评级",
        {
            "id": "flow-risk-assessment",
            "name": "风险评级",
            "actorId": "actor-risk-analyst",
            "capabilityIds": ["cap-risk-control"],
        },
    ),
    (
        "合规检查",
        {
            "id": "flow-compliance-check",
            "name": "合规检查",
            "actorId": "actor-compliance",
            "capabilityIds": ["cap-compliance"],
        },
    ),
    (
        "客户画像",
        {
            "id": "flow-customer-profiling",
            "name": "客户画像构建",
            "actorId": "actor-risk-analyst",
            "capabilityIds": ["cap-customer-profile"],
        },
    ),
)

# ─── Common system rules ───
SYSTEM_RULES: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    # Retail systems
    ("CRM", "CRM", "客户关系管理系统", ("cap-membership", "cap-order", "cap-customer-profile")),
    ("POS", "POS", "门店收银与交易系统", ("cap-order",)),
    ("ERP", "ERP", "企业资源计划系统", ("cap-store-ops", "cap-production-plan", "cap-warehouse")),
    # Manufacturing systems
    ("MES", "MES", "制造执行系统", ("cap-production-plan", "cap-quality-control")),
    ("WMS", "WMS", "仓储管理系统", ("cap-warehouse",)),
    ("SCM", "SCM", "供应链管理系统", ("cap-supply-chain",)),
    # Finance systems
    ("风控引擎", "risk-engine", "风控引擎系统", ("cap-risk-control", "cap-customer-profile")),
    ("信贷系统", "credit-system", "信贷管理系统", ("cap-credit",)),
    ("反欺诈", "anti-fraud", "反欺诈系统", ("cap-risk-control",)),
)


def load_seed(repo_root: Path, industry: str) -> dict[str, Any]:
    seed_path = repo_root / "business_blueprint" / "templates" / industry / "seed.json"
    return load_json(seed_path)


def _contains(source_text: str, trigger: str) -> bool:
    return trigger.casefold() in source_text.casefold()


def _ensure_actor(
    blueprint: dict[str, Any],
    actor_id: str,
    actor_name: str,
) -> dict[str, Any]:
    for actor in blueprint["library"]["actors"]:
        if actor.get("id") == actor_id or actor.get("name") == actor_name:
            return actor
    actor = {"id": actor_id, "name": actor_name}
    blueprint["library"]["actors"].append(actor)
    return actor


def _ensure_capability(
    blueprint: dict[str, Any],
    capability_id: str,
    capability_name: str,
    description: str,
) -> dict[str, Any]:
    for capability in blueprint["library"]["capabilities"]:
        if capability.get("id") == capability_id or capability.get("name") == capability_name:
            capability.setdefault("description", description)
            capability.setdefault("level", 1)
            capability.setdefault("ownerActorIds", [])
            capability.setdefault("supportingSystemIds", [])
            return capability

    capability = {
        "id": capability_id,
        "name": capability_name,
        "level": 1,
        "description": description,
        "ownerActorIds": [],
        "supportingSystemIds": [],
    }
    blueprint["library"]["capabilities"].append(capability)
    return capability


def _populate_actors(blueprint: dict[str, Any], source_text: str) -> None:
    for trigger, actor_id, actor_name in ACTOR_RULES:
        if _contains(source_text, trigger):
            _ensure_actor(blueprint, actor_id, actor_name)


def _populate_capabilities(
    blueprint: dict[str, Any],
    source_text: str,
) -> list[str]:
    matched_capability_ids: list[str] = []
    for trigger, capability_id, capability_name, description in CAPABILITY_RULES:
        if _contains(source_text, trigger):
            _ensure_capability(
                blueprint,
                capability_id,
                capability_name,
                description,
            )
            matched_capability_ids.append(capability_id)
    return matched_capability_ids


def _generated_capability_ids(blueprint: dict[str, Any]) -> set[str]:
    return {
        capability["id"]
        for capability in blueprint["library"]["capabilities"]
        if isinstance(capability, dict) and capability.get("id")
    }


def _infer_actor_id(
    blueprint: dict[str, Any],
    preferred_actor_id: str,
) -> str:
    if any(actor.get("id") == preferred_actor_id for actor in blueprint["library"]["actors"]):
        return preferred_actor_id
    return ""


def _populate_flow_steps(
    blueprint: dict[str, Any],
    source_text: str,
    allowed_capability_ids: set[str],
) -> None:
    for trigger, flow in FLOW_RULES:
        if _contains(source_text, trigger):
            capability_ids = [
                capability_id
                for capability_id in flow["capabilityIds"]
                if capability_id in allowed_capability_ids
            ]
            flow_step = {
                "id": flow["id"],
                "name": flow["name"],
                "actorId": _infer_actor_id(blueprint, flow["actorId"]),
                "capabilityIds": capability_ids,
                "systemIds": [],
                "stepType": "task",
                "inputRefs": [],
                "outputRefs": [],
            }
            if not any(step.get("id") == flow_step["id"] for step in blueprint["library"]["flowSteps"]):
                blueprint["library"]["flowSteps"].append(flow_step)


def _infer_flow_sequences(blueprint: dict[str, Any], source_text: str) -> None:
    """Add process sequence metadata to flow steps and generate next-step relations."""
    flow_steps = blueprint["library"]["flowSteps"]
    step_by_id = {s["id"]: s for s in flow_steps}
    matched_flow_ids: set[str] = set()

    for process_name, sequence_rules in FLOW_SEQUENCES:
        # Check if any trigger from this sequence appears in source
        triggers = [t for t, _ in sequence_rules]
        if not any(_contains(source_text, t) for t in triggers):
            continue

        # Build ordered list of flow IDs that actually exist in this blueprint
        ordered_ids = []
        for trigger, flow_id in sequence_rules:
            if flow_id in step_by_id and flow_id not in matched_flow_ids:
                ordered_ids.append(flow_id)
                matched_flow_ids.add(flow_id)

        # Add processName and seqIndex to each matched step
        for idx, fid in enumerate(ordered_ids):
            step = step_by_id[fid]
            step["processName"] = process_name
            step["seqIndex"] = idx

        # Generate nextStep links (within same actor = same lane)
        for i in range(len(ordered_ids) - 1):
            from_step = step_by_id[ordered_ids[i]]
            to_step = step_by_id[ordered_ids[i + 1]]
            from_step.setdefault("nextStepIds", []).append(to_step["id"])


def _infer_relations(blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate relations array from blueprint entities."""
    relations: list[dict[str, Any]] = []
    lib = blueprint["library"]

    # System → Capability relations (from capabilityIds on systems)
    for system in lib.get("systems", []):
        for cid in system.get("capabilityIds", []):
            relations.append({
                "id": f"rel-{system['id']}-{cid}",
                "type": "supports",
                "from": system["id"],
                "to": cid,
                "label": "支撑",
            })

    # Capability → Actor relations (from flow steps linking actors to capabilities)
    seen_cap_actor: set[tuple[str, str]] = set()
    for step in lib.get("flowSteps", []):
        aid = step.get("actorId", "")
        for cid in step.get("capabilityIds", []):
            key = (cid, aid)
            if aid and key not in seen_cap_actor:
                seen_cap_actor.add(key)
                relations.append({
                    "id": f"rel-{cid}-{aid}",
                    "type": "owned-by",
                    "from": cid,
                    "to": aid,
                    "label": "执行",
                })

    # Flow step sequence relations
    for step in lib.get("flowSteps", []):
        for next_id in step.get("nextStepIds", []):
            relations.append({
                "id": f"rel-flow-{step['id']}-{next_id}",
                "type": "flows-to",
                "from": step["id"],
                "to": next_id,
                "label": "→",
            })

    return relations


def _populate_systems(
    blueprint: dict[str, Any],
    source_text: str,
    allowed_capability_ids: set[str],
) -> None:
    for trigger, raw_name, description, supported_capability_ids in SYSTEM_RULES:
        if _contains(source_text, trigger):
            system = merge_or_create_system(
                blueprint["library"]["systems"],
                raw_name=raw_name,
                description=description,
            )
            allowed_capabilities = [
                capability_id
                for capability_id in supported_capability_ids
                if capability_id in allowed_capability_ids
            ]
            system["capabilityIds"] = allowed_capabilities


def _link_system_backlinks(blueprint: dict[str, Any]) -> None:
    capability_by_id = {
        capability["id"]: capability
        for capability in blueprint["library"]["capabilities"]
        if isinstance(capability, dict) and capability.get("id")
    }
    for system in blueprint["library"]["systems"]:
        for capability_id in system.get("capabilityIds", []):
            capability = capability_by_id.get(capability_id)
            if capability is None:
                continue
            supporting_system_ids = capability.setdefault("supportingSystemIds", [])
            if system["id"] not in supporting_system_ids:
                supporting_system_ids.append(system["id"])


def _missing_flow_capability_requests(blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for flow_step in blueprint["library"]["flowSteps"]:
        if flow_step.get("capabilityIds"):
            continue
        requests.append(
            {
                "code": "MISSING_FLOW_CAPABILITY_LINKAGE",
                "question": f"Flow step '{flow_step.get('name', '')}' is missing a capability linkage.",
                "affectedIds": [flow_step["id"]],
            }
        )
    return requests


def _build_views(blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": "view-capability",
            "type": "business-capability-map",
            "title": "业务能力蓝图",
            "includedNodeIds": [entity["id"] for entity in blueprint["library"]["capabilities"]],
            "includedRelationIds": [],
            "layout": {"groups": []},
            "annotations": [],
        },
        {
            "id": "view-swimlane",
            "type": "swimlane-flow",
            "title": "泳道流程图",
            "includedNodeIds": [
                entity["id"]
                for entity in blueprint["library"]["actors"] + blueprint["library"]["flowSteps"]
            ],
            "includedRelationIds": [],
            "layout": {"lanes": [actor["id"] for actor in blueprint["library"]["actors"]]},
            "annotations": [],
        },
        {
            "id": "view-architecture",
            "type": "application-architecture",
            "title": "应用架构图",
            "includedNodeIds": [
                entity["id"]
                for entity in blueprint["library"]["systems"] + blueprint["library"]["capabilities"]
            ],
            "includedRelationIds": [],
            "layout": {"groups": []},
            "annotations": [],
        },
    ]


def create_blueprint_from_text(
    source_text: str,
    industry: str,
    repo_root: Path,
) -> dict[str, Any]:
    blueprint = deepcopy(load_seed(repo_root, industry))
    blueprint["meta"] = {
        "title": "Generated Blueprint",
        "industry": industry,
        **new_revision_meta(parent_revision_id=None, modified_by="ai"),
    }
    blueprint["context"]["sourceRefs"] = [{"type": "inline-text", "excerpt": source_text}]

    _populate_actors(blueprint, source_text)
    _populate_capabilities(blueprint, source_text)
    generated_capability_ids = _generated_capability_ids(blueprint)
    _populate_flow_steps(blueprint, source_text, generated_capability_ids)
    _infer_flow_sequences(blueprint, source_text)
    _populate_systems(blueprint, source_text, generated_capability_ids)
    _link_system_backlinks(blueprint)
    blueprint["relations"] = _infer_relations(blueprint)

    blueprint["views"] = _build_views(blueprint)
    blueprint["context"]["clarifyRequests"] = [
        *build_clarify_requests(blueprint),
        *_missing_flow_capability_requests(blueprint),
    ]
    return blueprint


def write_plan_output(
    output_path: Path,
    source_text: str,
    industry: str,
    repo_root: Path,
) -> dict[str, Any]:
    blueprint = create_blueprint_from_text(source_text, industry, repo_root)
    write_json(output_path, blueprint)
    return blueprint
