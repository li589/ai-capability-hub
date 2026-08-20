from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (SKILL_ROOT / rel_path).read_text(encoding="utf-8")


def test_required_skill_files_exist():
    for rel_path in [
        "info.json",
        "meta.json",
        "SKILL.md",
        "config.py",
        "melo_hf_bridge.py",
        "scripts/client.py",
        "scripts/server.py",
        "scripts/run.ps1",
        "scripts/ensure_models.py",
        "tests/test.ps1",
        "wheels/melotts-0.1.2-py3-none-any.whl",
    ]:
        assert (SKILL_ROOT / rel_path).exists(), rel_path


def test_legacy_melo_install_path_is_gone():
    assert not (SKILL_ROOT / "melo_wheels").exists(), "melo_wheels/ should be removed"
    assert not (SKILL_ROOT / "scripts" / "setup_extra.py").exists(), "setup_extra.py should be removed"
    assert "setup_extra" not in read("scripts/run.ps1")


def test_client_server_runtime_contract():
    client = read("scripts/client.py")
    server = read("scripts/server.py")
    run_ps1 = read("scripts/run.ps1")

    assert r"\\.\pipe\local-realtime-translator" in client
    assert r"\\.\pipe\local-realtime-translator" in server
    assert 'AUTHKEY = b"local-realtime-translator"' in client
    assert 'AUTHKEY = b"local-realtime-translator"' in server
    # server runs from the ~/.openvino/temp copy
    assert "temp" in client and "local-realtime-translator" in client
    assert "_sync_runtime_scripts" in client
    # the full import tree is synced
    for token in ("config.py", "melo_hf_bridge.py", "ensure_models.py",
                  "model_download.py", "translator", "nltk_data", "bin"):
        assert token in client, token
    # run.ps1 still drives the controller
    assert "client.py" in run_ps1


def test_server_dog_uses_canonical_shared_temp_root():
    """The server-dog is a machine-wide singleton (one dog brokers all skills),
    so it must live at the canonical ~/.openvino/temp/server-dog.py — NOT under a
    per-skill subdir. See docs/superpowers/specs/2026-05-26-shared-server-dog-design.md.
    """
    client = read("scripts/client.py")
    # TEMP_ROOT must be the shared temp dir, not a per-skill nested root.
    assert 'TEMP_ROOT = OPENVINO_ROOT / "temp"\n' in client, (
        "TEMP_ROOT must be OPENVINO_ROOT/'temp' (canonical shared dog location), "
        "not a per-skill subdir like temp/rt-translator"
    )
    # The skill's own server tree still lives under a per-skill subdir of temp.
    assert 'TEMP_DIR = TEMP_ROOT / "local-realtime-translator"' in client


def test_info_json_configures_hunyuan_model():
    info = read("info.json")
    assert '"snake7gun/Hunyuan-1.8B-Instruct-ov-int4"' in info
    assert '"dir_name": "Hunyuan-1.8B-Instruct-ov-int4"' in info
