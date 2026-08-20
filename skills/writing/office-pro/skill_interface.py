"""
Office Pro - OpenClaw Skill Interface

Standard interface for OpenClaw runtime integration
Provides capabilities, health check, and action execution
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from core import (
    OfficeProError,
    ErrorCode,
    ParameterError,
    TemplateNotFoundError,
    DataFileNotFoundError,
)
from word_processor import WordProcessor
from excel_processor import ExcelProcessor


def ensure_templates_exist() -> bool:
    """
    Ensure templates exist, generate if missing
    Called during skill initialization
    
    Returns:
        True if templates are available, False otherwise
    """
    skill_root = Path(__file__).parent
    templates_dir = skill_root / "assets" / "templates"
    word_dir = templates_dir / "word"
    excel_dir = templates_dir / "excel"
    
    # Check if templates already exist
    word_exists = word_dir.exists() and len(list(word_dir.glob("*.docx"))) >= 8
    excel_exists = excel_dir.exists() and len(list(excel_dir.glob("*.xlsx"))) >= 8
    
    if word_exists and excel_exists:
        return True
    
    # Try to generate templates
    try:
        generator_path = skill_root / "generate_premium_templates.py"
        if generator_path.exists():
            import subprocess
            result = subprocess.run(
                [sys.executable, str(generator_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
    except Exception:
        pass
    
    return False


class SkillInterface:
    """
    OpenClaw Skill Standard Interface
    
    Provides standardized methods for OpenClaw runtime:
    - get_capabilities(): Return skill capabilities
    - health_check(): Return health status
    - execute_action(): Execute a skill action
    """
    
    VERSION = "1.0.0"
    NAME = "office-pro"
    DESCRIPTION = "Enterprise-grade document automation suite"
    
    @staticmethod
    def get_capabilities() -> Dict[str, Any]:
        """
        Get skill capabilities declaration
        
        Returns:
            Capability dictionary with actions and their parameters
        """
        return {
            "name": SkillInterface.NAME,
            "version": SkillInterface.VERSION,
            "description": SkillInterface.DESCRIPTION,
            "actions": [
                {
                    "name": "word.generate",
                    "description": "Generate Word document from template",
                    "parameters": {
                        "template": {
                            "type": "string",
                            "required": True,
                            "description": "Template filename"
                        },
                        "data": {
                            "type": "object",
                            "required": True,
                            "description": "Template data (can be object or path to JSON file)"
                        },
                        "output": {
                            "type": "string",
                            "required": True,
                            "description": "Output file path"
                        },
                        "template_dir": {
                            "type": "string",
                            "required": False,
                            "description": "Custom template directory"
                        }
                    }
                },
                {
                    "name": "excel.generate",
                    "description": "Generate Excel report from template",
                    "parameters": {
                        "template": {
                            "type": "string",
                            "required": True,
                            "description": "Template filename"
                        },
                        "data": {
                            "type": "object",
                            "required": True,
                            "description": "Template data (can be object or path to JSON file)"
                        },
                        "output": {
                            "type": "string",
                            "required": True,
                            "description": "Output file path"
                        },
                        "template_dir": {
                            "type": "string",
                            "required": False,
                            "description": "Custom template directory"
                        }
                    }
                },
                {
                    "name": "templates.list",
                    "description": "List available templates",
                    "parameters": {
                        "type": {
                            "type": "string",
                            "required": False,
                            "enum": ["word", "excel", "all"],
                            "default": "all",
                            "description": "Template type to list"
                        },
                        "template_dir": {
                            "type": "string",
                            "required": False,
                            "description": "Custom template directory"
                        }
                    }
                },
                {
                    "name": "word.create",
                    "description": "Create blank Word document",
                    "parameters": {
                        "output": {
                            "type": "string",
                            "required": True,
                            "description": "Output file path"
                        },
                        "title": {
                            "type": "string",
                            "required": False,
                            "description": "Document title"
                        }
                    }
                },
                {
                    "name": "excel.create",
                    "description": "Create blank Excel workbook",
                    "parameters": {
                        "output": {
                            "type": "string",
                            "required": True,
                            "description": "Output file path"
                        },
                        "sheets": {
                            "type": "integer",
                            "required": False,
                            "default": 1,
                            "description": "Number of sheets"
                        }
                    }
                }
            ]
        }
    
    @staticmethod
    def health_check() -> Dict[str, Any]:
        """
        Perform health check
        
        Returns:
            Health status dictionary
        """
        checks = {
            "status": "healthy",
            "version": SkillInterface.VERSION,
            "timestamp": datetime.now().isoformat(),
            "dependencies": {},
            "templates": {
                "word": {"available": False, "count": 0, "generated": False},
                "excel": {"available": False, "count": 0, "generated": False}
            }
        }
        
        deps = [
            ("docx", "python-docx"),
            ("openpyxl", "openpyxl"),
            ("docxtpl", "docxtpl"),
            ("pandas", "pandas"),
            ("click", "click"),
        ]
        
        for module_name, display_name in deps:
            try:
                __import__(module_name)
                checks["dependencies"][display_name] = "ok"
            except ImportError:
                checks["dependencies"][display_name] = "missing"
                checks["status"] = "degraded"
        
        # Ensure templates exist (generate if needed)
        templates_generated = ensure_templates_exist()
        
        try:
            skill_root = Path(__file__).parent
            word_dir = skill_root / "assets" / "templates" / "word"
            if word_dir.exists():
                count = len(list(word_dir.glob("*.docx")))
                checks["templates"]["word"] = {
                    "available": count > 0,
                    "count": count,
                    "generated": templates_generated
                }
            
            excel_dir = skill_root / "assets" / "templates" / "excel"
            if excel_dir.exists():
                count = len(list(excel_dir.glob("*.xlsx")))
                checks["templates"]["excel"] = {
                    "available": count > 0,
                    "count": count,
                    "generated": templates_generated
                }
        except Exception:
            pass
        
        return checks
    
    @staticmethod
    def execute_action(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a skill action
        
        Args:
            action: Action name (e.g. 'word.generate')
            params: Action parameters
            
        Returns:
            Result dictionary with success status
        """
        try:
            if action == "word.generate":
                return SkillActions.word_generate(params)
            elif action == "excel.generate":
                return SkillActions.excel_generate(params)
            elif action == "templates.list":
                return SkillActions.list_templates(params)
            elif action == "word.create":
                return SkillActions.word_create(params)
            elif action == "excel.create":
                return SkillActions.excel_create(params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "error_code": ErrorCode.INVALID_PARAMS
                }
        except OfficeProError as e:
            return e.to_dict()
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": ErrorCode.INTERNAL_ERROR
            }


class SkillActions:
    """Skill action implementations"""
    
    @staticmethod
    def word_generate(params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Word document"""
        template = params.get("template")
        data = params.get("data")
        output = params.get("output")
        template_dir = params.get("template_dir")
        
        if not template:
            raise ParameterError("Missing required parameter: template")
        if not data:
            raise ParameterError("Missing required parameter: data")
        if not output:
            raise ParameterError("Missing required parameter: output")
        
        if isinstance(data, str):
            from .utils import load_json_file
            data = load_json_file(data, validate_path=True)
        
        wp = WordProcessor(template_dir=template_dir)
        wp.load_template(template)
        wp.render_and_save(data, output)
        
        return {
            "success": True,
            "output_path": output,
            "message": f"Word document generated: {output}"
        }
    
    @staticmethod
    def excel_generate(params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Excel report"""
        template = params.get("template")
        data = params.get("data")
        output = params.get("output")
        template_dir = params.get("template_dir")
        
        if not template:
            raise ParameterError("Missing required parameter: template")
        if not data:
            raise ParameterError("Missing required parameter: data")
        if not output:
            raise ParameterError("Missing required parameter: output")
        
        if isinstance(data, str):
            from .utils import load_json_file
            data = load_json_file(data, validate_path=True)
        
        ep = ExcelProcessor(template_dir=template_dir)
        ep.load_template(template)
        ep.render_and_save(data, output)
        
        return {
            "success": True,
            "output_path": output,
            "message": f"Excel report generated: {output}"
        }
    
    @staticmethod
    def list_templates(params: Dict[str, Any]) -> Dict[str, Any]:
        """List available templates"""
        template_type = params.get("type", "all")
        template_dir = params.get("template_dir")
        
        if template_dir:
            base_dir = Path(template_dir)
        else:
            skill_root = Path(__file__).parent
            base_dir = skill_root / "assets" / "templates"
        
        result = {"success": True, "templates": {}}
        
        if template_type in ("word", "all"):
            word_dir = base_dir / "word"
            if word_dir.exists():
                result["templates"]["word"] = [
                    f.name for f in sorted(word_dir.glob("*.docx"))
                ]
            else:
                result["templates"]["word"] = []
        
        if template_type in ("excel", "all"):
            excel_dir = base_dir / "excel"
            if excel_dir.exists():
                result["templates"]["excel"] = [
                    f.name for f in sorted(excel_dir.glob("*.xlsx"))
                ]
            else:
                result["templates"]["excel"] = []
        
        return result
    
    @staticmethod
    def word_create(params: Dict[str, Any]) -> Dict[str, Any]:
        """Create blank Word document"""
        output = params.get("output")
        title = params.get("title")
        
        if not output:
            raise ParameterError("Missing required parameter: output")
        
        wp = WordProcessor()
        wp.create_document()
        
        if title:
            wp.add_heading(title, level=1)
        
        wp.save(output)
        
        return {
            "success": True,
            "output_path": output,
            "message": f"Word document created: {output}"
        }
    
    @staticmethod
    def excel_create(params: Dict[str, Any]) -> Dict[str, Any]:
        """Create blank Excel workbook"""
        output = params.get("output")
        sheets = params.get("sheets", 1)
        
        if not output:
            raise ParameterError("Missing required parameter: output")
        
        ep = ExcelProcessor()
        ep.create_workbook()
        
        if sheets > 0:
            ws = ep.get_sheet()
            ws.title = "Sheet1"
        
        for i in range(2, sheets + 1):
            ep.create_sheet(f"Sheet{i}")
        
        ep.save(output)
        
        return {
            "success": True,
            "output_path": output,
            "message": f"Excel workbook created: {output}"
        }


def main():
    """CLI entry point for OpenClaw integration"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "No command specified",
            "error_code": ErrorCode.INVALID_PARAMS,
            "usage": "skill_interface.py --capabilities|--health|--execute <action> <params>"
        }, indent=2))
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "--capabilities":
        result = SkillInterface.get_capabilities()
    elif command == "--health":
        result = SkillInterface.health_check()
    elif command == "--execute":
        if len(sys.argv) < 4:
            result = {
                "success": False,
                "error": "Missing action or parameters",
                "error_code": ErrorCode.INVALID_PARAMS
            }
        else:
            action = sys.argv[2]
            try:
                params = json.loads(sys.argv[3])
            except json.JSONDecodeError:
                result = {
                    "success": False,
                    "error": "Invalid JSON parameters",
                    "error_code": ErrorCode.DATA_PARSE_ERROR
                }
            else:
                result = SkillInterface.execute_action(action, params)
    else:
        result = {
            "success": False,
            "error": f"Unknown command: {command}",
            "error_code": ErrorCode.INVALID_PARAMS
        }
    
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
