import json
import subprocess
import sys
from pathlib import Path

from business_blueprint.validate import validate_blueprint


ROOT = Path(__file__).resolve().parents[1]


def test_plan_writes_blueprint_json(tmp_path: Path) -> None:
    source = tmp_path / "brief.txt"
    source.write_text(
        "零售客户需要会员运营和门店运营，导购负责会员注册，运营负责活动执行，客服负责售后跟进，CRM、POS和ERP需要支撑订单管理与积分累计。",
        encoding="utf-8",
    )
    output = tmp_path / "solution.blueprint.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "business_blueprint.cli",
            "--plan",
            str(output),
            "--from",
            str(source),
            "--industry",
            "retail",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["meta"]["industry"] == "retail"
    assert any(cap["name"] == "会员运营" for cap in payload["library"]["capabilities"])
    assert any(cap["name"] == "订单管理" for cap in payload["library"]["capabilities"])
    assert any(cap["name"] == "门店运营" for cap in payload["library"]["capabilities"])
    assert any(actor["name"] == "门店导购" for actor in payload["library"]["actors"])
    assert any(actor["name"] == "客服" for actor in payload["library"]["actors"])
    assert any(actor["name"] == "运营" for actor in payload["library"]["actors"])
    assert any(step["name"] == "会员注册" for step in payload["library"]["flowSteps"])
    assert any(system["name"] == "CRM" for system in payload["library"]["systems"])
    assert any(system["name"] == "POS" for system in payload["library"]["systems"])
    assert any(system["name"] == "ERP" for system in payload["library"]["systems"])

    membership = next(cap for cap in payload["library"]["capabilities"] if cap["name"] == "会员运营")
    order = next(cap for cap in payload["library"]["capabilities"] if cap["name"] == "订单管理")
    store_ops = next(cap for cap in payload["library"]["capabilities"] if cap["name"] == "门店运营")
    assert "sys-crm" in membership["supportingSystemIds"]
    assert "sys-pos" in order["supportingSystemIds"]
    assert "sys-erp" in store_ops["supportingSystemIds"]

    flow_step = next(step for step in payload["library"]["flowSteps"] if step["name"] == "会员注册")
    assert flow_step["actorId"] == "actor-store-guide"
    assert flow_step["capabilityIds"] == ["cap-membership"]
    assert flow_step["systemIds"] == []
    assert flow_step["stepType"] == "task"
    assert flow_step["inputRefs"] == []
    assert flow_step["outputRefs"] == []
    assert "actorIds" not in flow_step

    assert [view["id"] for view in payload["views"]] == [
        "view-capability",
        "view-swimlane",
        "view-architecture",
    ]
    assert [view["type"] for view in payload["views"]] == [
        "business-capability-map",
        "swimlane-flow",
        "application-architecture",
    ]
    assert [view["title"] for view in payload["views"]] == [
        "业务能力蓝图",
        "泳道流程图",
        "应用架构图",
    ]
    assert payload["views"][0]["includedRelationIds"] == []
    assert payload["views"][1]["includedRelationIds"] == []
    assert payload["views"][2]["includedRelationIds"] == []
    assert payload["views"][0]["layout"] == {"groups": []}
    assert payload["views"][1]["layout"] == {
        "lanes": ["actor-store-guide", "actor-service", "actor-ops"]
    }
    assert payload["views"][2]["layout"] == {"groups": []}


def test_plan_with_flow_only_does_not_create_missing_capability_refs(tmp_path: Path) -> None:
    source = tmp_path / "brief.txt"
    source.write_text("只需要下单流程。", encoding="utf-8")
    output = tmp_path / "flow-only.blueprint.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "business_blueprint.cli",
            "--plan",
            str(output),
            "--from",
            str(source),
            "--industry",
            "retail",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    flow_step = next(step for step in payload["library"]["flowSteps"] if step["name"] == "订单创建")
    assert flow_step["capabilityIds"] == []
    assert flow_step["actorId"] == ""
    assert any(
        request["code"] == "MISSING_FLOW_CAPABILITY_LINKAGE"
        and request["affectedIds"] == [flow_step["id"]]
        for request in payload["context"]["clarifyRequests"]
    )
    assert not any(
        issue["errorCode"] == "MISSING_CAPABILITY_REFERENCE"
        for issue in validate_blueprint(payload)["issues"]
    )
