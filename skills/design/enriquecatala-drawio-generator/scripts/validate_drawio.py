#!/usr/bin/env python3
"""
Draw.io XML Validator

Validates .drawio files for structural correctness:
- XML well-formedness
- Correct root structure (mxfile > diagram > mxGraphModel > root)
- Unique IDs across all mxCell elements
- Valid edge references (source/target exist as vertices)
- No forbidden <Array> elements
- Minimum component count

Usage:
    python validate_drawio.py <file.drawio>
    python validate_drawio.py --strict <file.drawio>   # Fail on warnings too
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def validate_drawio(filepath: str, strict: bool = False) -> tuple[bool, list[str], list[str]]:
    """
    Validate a .drawio file.
    
    Returns:
        (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    path = Path(filepath)
    if not path.exists():
        return False, [f"File not found: {filepath}"], []
    
    content = path.read_text(encoding="utf-8")
    
    # 1. XML well-formedness
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        return False, [f"XML parse error: {e}"], []
    
    # 2. Root structure validation
    if root.tag != "mxfile":
        errors.append(f"Root element is '{root.tag}', expected 'mxfile'")
    
    diagram = root.find("diagram")
    if diagram is None:
        errors.append("Missing <diagram> element under <mxfile>")
        return False, errors, warnings
    
    graph_model = diagram.find("mxGraphModel")
    if graph_model is None:
        errors.append("Missing <mxGraphModel> element under <diagram>")
        return False, errors, warnings
    
    graph_root = graph_model.find("root")
    if graph_root is None:
        errors.append("Missing <root> element under <mxGraphModel>")
        return False, errors, warnings
    
    # 3. Collect all cells
    cells = graph_root.findall("mxCell")
    if len(cells) < 2:
        errors.append(f"Found only {len(cells)} mxCell elements (need at least id=0 and id=1)")
    
    # 4. Check unique IDs
    all_ids = {}
    vertex_ids = set()
    edge_cells = []
    
    for cell in cells:
        cell_id = cell.get("id")
        if cell_id is None:
            errors.append(f"mxCell missing 'id' attribute: {ET.tostring(cell, encoding='unicode')[:100]}")
            continue
        
        if cell_id in all_ids:
            errors.append(f"Duplicate id='{cell_id}'")
        all_ids[cell_id] = cell
        
        if cell.get("vertex") == "1":
            vertex_ids.add(cell_id)
        
        if cell.get("edge") == "1":
            edge_cells.append(cell)
    
    # 5. Validate edge references
    for edge in edge_cells:
        edge_id = edge.get("id", "?")
        source = edge.get("source")
        target = edge.get("target")
        
        if source and source not in all_ids:
            errors.append(f"Edge '{edge_id}' references non-existent source='{source}'")
        if target and target not in all_ids:
            errors.append(f"Edge '{edge_id}' references non-existent target='{target}'")
        if not source:
            warnings.append(f"Edge '{edge_id}' has no source attribute")
        if not target:
            warnings.append(f"Edge '{edge_id}' has no target attribute")
    
    # 6. Check for forbidden <Array> elements
    for array_el in graph_root.iter("Array"):
        parent = None
        # Walk tree to find parent
        for cell in graph_root.iter():
            if array_el in list(cell):
                parent = cell
                break
        parent_id = parent.get("id", "?") if parent is not None else "unknown"
        errors.append(f"Forbidden <Array> element found (near cell '{parent_id}') — this crashes draw.io!")
    
    # Also check in mxGeometry children
    for geom in graph_root.iter("mxGeometry"):
        for child in geom:
            if child.tag == "Array":
                errors.append("Forbidden <Array> inside <mxGeometry> — remove it and use self-closing geometry")
    
    # 7. Component count check
    shape_count = len(vertex_ids)
    edge_count = len(edge_cells)
    
    if shape_count < 3:
        warnings.append(f"Only {shape_count} shapes — diagram may be too simple (recommend 8-15)")
    
    if edge_count == 0 and shape_count > 1:
        warnings.append("No edges/connectors found — shapes are unconnected")
    
    is_valid = len(errors) == 0
    if strict and len(warnings) > 0:
        is_valid = False
    
    return is_valid, errors, warnings


def main():
    strict = "--strict" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--strict"]
    
    if not args:
        print("Usage: python validate_drawio.py [--strict] <file.drawio>")
        sys.exit(1)
    
    filepath = args[0]
    is_valid, errors, warnings = validate_drawio(filepath, strict)
    
    if errors:
        print("❌ ERRORS:")
        for e in errors:
            print(f"   • {e}")
    
    if warnings:
        print("⚠️  WARNINGS:")
        for w in warnings:
            print(f"   • {w}")
    
    # Count components for summary
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        graph_root = root.find(".//root")
        if graph_root is not None:
            cells = graph_root.findall("mxCell")
            shapes = sum(1 for c in cells if c.get("vertex") == "1")
            edges = sum(1 for c in cells if c.get("edge") == "1")
        else:
            shapes = edges = 0
    except Exception:
        shapes = edges = 0
    
    if is_valid:
        print(f"\n✅ Valid draw.io file: {shapes} shapes, {edges} edges")
        sys.exit(0)
    else:
        print(f"\n❌ Invalid draw.io file ({len(errors)} errors, {len(warnings)} warnings)")
        sys.exit(1)


if __name__ == "__main__":
    main()
