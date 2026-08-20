---
name: business-blueprint-skill
description: Use when turning presales requirements, meeting notes, or solution materials into editable business capability blueprints, swimlane flows, and application architecture diagrams. Use when generating blueprint JSON, static HTML viewers, or exporting to SVG, draw.io, Excalidraw, or Mermaid formats.
install_source: official
install_method: download
skill_id: official_h77EGUsp
enabled_at: 1787232530603
version: 1.0.0
name_zh: 业务蓝图技能
---

# Business Blueprint Skill

Use the Python scripts in this repository as the execution surface.

## Workflow Decision Tree

```
User provides raw requirements / meeting notes?
  → Does a canonical blueprint JSON already exist?
    → No:  --plan (generate JSON only)
    → Yes: --generate (JSON + viewer refresh)

User has an existing blueprint JSON to modify?
  → --edit (refresh viewer only)

User needs diagram files (SVG, draw.io, etc.)?
  → --validate first, then --export

User unsure about blueprint quality?
  → --validate
```

## Commands

1. Use `--plan` when starting from raw source material and no canonical blueprint exists yet.
2. Use `--generate` after a canonical blueprint exists and the user needs the static viewer package.
3. Use `--edit` to refresh the viewer for an existing blueprint revision.
4. Use `--validate` before claiming a blueprint is complete.
5. Use `--export` when downstream skills need SVG, draw.io, Excalidraw, or Mermaid artifacts.

## Handoff Rules

- Treat `solution.blueprint.json` as the only source of truth.
- Never treat `solution.viewer.html` as the source of truth.
- Preserve `editor.fieldLocks` and human-edited fields during regeneration.
- If `context.clarifyRequests` is non-empty, surface them instead of pretending the blueprint is complete.

## Export Formats

| Format | File | Use Case |
|--------|------|----------|
| SVG | `solution.exports/solution.svg` | Quick preview, embedding |
| draw.io | `solution.exports/solution.drawio` | Editable diagrams |
| Excalidraw | `solution.exports/solution.excalidraw` | Whiteboard-style diagrams |
| Mermaid | `solution.exports/solution.mermaid.md` | GitHub-native rendering |

## Collaboration Boundary

This skill produces **semantic intermediate artifacts**. Downstream skills consume them:

- `report-creator` consumes blueprint → assembles reports
- `slide-creator` consumes blueprint → assembles presentations
- Other skills may consume `relations` → generate PlantUML or other diagram syntax
- Downstream skills should **never directly edit** `solution.blueprint.json`

## Sandbox Execution

When running in an isolated Python sandbox (Jupyter, notebook, cloud REPL) that auto-installs dependencies:

1. **The sandbox auto-installs `business-blueprint-skill` from PyPI.** Do NOT try to `pip install -e` or use `sys.path` hacks with `__file__` — `__file__` is undefined in Jupyter.

2. **After auto-install, run code like this — copy exactly:**
   ```python
   from business_blueprint.cli import main
   import sys
   sys.argv = [
       "business-blueprint",
       "--plan",
       "solution.blueprint.json",
       "--from",
       "your source text or requirements here",
       "--industry",
       "common"
   ]
   main()
   ```

3. **For `--generate` (after blueprint JSON exists):**
   ```python
   from pathlib import Path
   from business_blueprint.generate import write_plan_output
   source_text = "your source text"
   output_path = Path("solution.blueprint.json")
   write_plan_output(output_path, source_text, "common", Path.cwd())
   ```

4. **For `--export` (after blueprint JSON exists):**
   ```python
   from pathlib import Path
   from business_blueprint.model import load_json
   from business_blueprint.export_svg import export_svg
   from business_blueprint.export_drawio import export_drawio
   from business_blueprint.export_excalidraw import export_excalidraw
   from business_blueprint.export_mermaid import export_mermaid

   blueprint_path = Path("solution.blueprint.json")
   blueprint = load_json(blueprint_path)
   export_dir = blueprint_path.with_name("solution.exports")
   export_dir.mkdir(parents=True, exist_ok=True)
   export_svg(blueprint, export_dir / "solution.svg")
   export_drawio(blueprint, export_dir / "solution.drawio")
   export_excalidraw(blueprint, export_dir / "solution.excalidraw")
   export_mermaid(blueprint, export_dir / "solution.mermaid.md")
   ```

5. **Prohibited patterns in sandbox:**
   - `__file__` — undefined in Jupyter
   - `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` — will raise NameError
   - `subprocess.run(["business-blueprint", ...])` — sandbox runs Python cells, not shell
   - `os.system()` — same reason

## Error Handling

- If source text is too ambiguous to extract any entities: run `--plan` with minimal output, then surface `clarifyRequests`.
- If `--validate` returns errors: fix structural issues before proceeding to `--export`.
- If `--validate` returns only warnings: proceed but note the warnings in any handoff.
- If Python version < 3.12: the package will refuse to install. Use `python3 -m business_blueprint.cli` with system Python as fallback.
