import json
from pathlib import Path

from business_blueprint.export_drawio import export_drawio
from business_blueprint.export_excalidraw import export_excalidraw
from business_blueprint.export_svg import export_svg


BLUEPRINT = {
    "meta": {"title": "Demo"},
    "library": {
        "capabilities": [{"id": "cap-membership", "name": "会员运营"}],
        "actors": [],
        "flowSteps": [],
        "systems": [{"id": "sys-crm", "name": "CRM", "capabilityIds": ["cap-membership"]}],
    },
    "views": [
        {
            "id": "view-capability",
            "type": "business-capability-map",
            "title": "业务能力蓝图",
            "includedNodeIds": ["cap-membership", "sys-crm"],
            "includedRelationIds": [],
            "layout": {},
            "annotations": [],
        }
    ],
}


def test_export_svg_writes_svg_markup(tmp_path: Path) -> None:
    target = tmp_path / "diagram.svg"
    export_svg(BLUEPRINT, target)
    assert target.read_text(encoding="utf-8").startswith("<svg")


def test_export_drawio_writes_mxfile(tmp_path: Path) -> None:
    target = tmp_path / "diagram.drawio"
    export_drawio(BLUEPRINT, target)
    assert "<mxfile" in target.read_text(encoding="utf-8")


def test_export_excalidraw_writes_json(tmp_path: Path) -> None:
    target = tmp_path / "diagram.excalidraw"
    export_excalidraw(BLUEPRINT, target)
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["type"] == "excalidraw"
