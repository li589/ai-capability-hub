import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_generate_and_export_end_to_end(tmp_path: Path) -> None:
    source = tmp_path / "brief.txt"
    source.write_text(
        "零售客户需要会员运营，门店导购负责会员注册，客服负责售后跟进，CRM和POS需要支撑订单管理与积分累计。",
        encoding="utf-8",
    )
    blueprint = tmp_path / "solution.blueprint.json"
    viewer = tmp_path / "solution.viewer.html"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "business_blueprint.cli",
            "--plan",
            str(blueprint),
            "--from",
            str(source),
            "--industry",
            "retail",
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "business_blueprint.cli",
            "--generate",
            str(viewer),
            "--from",
            str(blueprint),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "business_blueprint.cli", "--export", str(blueprint)],
        cwd=ROOT,
        check=True,
    )

    assert viewer.exists()
    assert (tmp_path / "solution.exports" / "solution.svg").exists()
    validation = subprocess.run(
        [sys.executable, "-m", "business_blueprint.cli", "--validate", str(blueprint)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(validation.stdout)
    assert "summary" in payload
    assert payload["summary"]["orphan_capability_count"] >= 1
    assert payload["summary"]["flow_step_missing_actor_count"] == 0
    assert payload["summary"]["capability_to_system_coverage"] >= 0.5
    assert payload["summary"]["shared_capability_count"] >= 1
