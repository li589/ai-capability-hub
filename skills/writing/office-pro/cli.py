"""
Office Pro - CLI Entry Point

Command line interface for document generation and template management
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import click
    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False

from core import (
    OfficeProError,
    DataFileNotFoundError,
    DataParseError,
    DataEncodingError,
    TemplateNotFoundError,
    PathTraversalError,
    ErrorCode,
    load_json_file,
    validate_template_path,
    get_template_dir,
)
from word_processor import WordProcessor
from excel_processor import ExcelProcessor


def handle_error(error: Exception, exit_code: int = 1) -> None:
    """Handle exceptions and exit with appropriate code"""
    if isinstance(error, OfficeProError):
        click.echo(f"[ERROR] {error.message}", err=True)
        if hasattr(error, 'error_code'):
            click.echo(f"  Code: {error.error_code}", err=True)
        sys.exit(exit_code)
    elif isinstance(error, FileNotFoundError):
        click.echo(f"[ERROR] File not found: {error}", err=True)
        sys.exit(2)
    elif isinstance(error, json.JSONDecodeError):
        click.echo(f"[ERROR] Invalid JSON format: {error}", err=True)
        sys.exit(3)
    else:
        click.echo(f"[ERROR] Unexpected error: {error}", err=True)
        sys.exit(99)


def safe_load_data(data_path: str) -> Dict[str, Any]:
    """
    Safely load JSON data file with comprehensive error handling
    
    Args:
        data_path: Path to JSON data file
        
    Returns:
        Parsed JSON data
    """
    try:
        return load_json_file(data_path, validate_path=True)
    except DataFileNotFoundError:
        raise click.ClickException(f"Data file not found: {data_path}")
    except DataParseError as e:
        raise click.ClickException(f"Invalid JSON in data file: {e.message}")
    except DataEncodingError as e:
        raise click.ClickException(f"Encoding error in data file: {e.message}")
    except PathTraversalError as e:
        raise click.ClickException(f"Invalid path: {e.message}")


if CLICK_AVAILABLE:
    @click.group()
    @click.version_option(version="1.0.0", prog_name="office-pro")
    def cli():
        """Office Pro - Enterprise Document Automation Tool"""
        pass

    @cli.group()
    def word():
        """Word document operations"""
        pass

    @word.command('generate')
    @click.option('--template', '-t', required=True, help='Template filename')
    @click.option('--data', '-d', required=True, help='Data JSON file path')
    @click.option('--output', '-o', required=True, help='Output file path')
    @click.option('--template-dir', help='Custom template directory')
    def word_generate(template: str, data: str, output: str, template_dir: Optional[str]):
        """Generate Word document from template"""
        try:
            context = safe_load_data(data)
            
            wp = WordProcessor(template_dir=template_dir)
            wp.load_template(template)
            wp.render_and_save(context, output)
            
            click.echo(f"[OK] Document generated: {output}")
            
        except OfficeProError as e:
            handle_error(e, 1)
        except click.ClickException:
            raise
        except Exception as e:
            handle_error(e, 99)

    @word.command('create')
    @click.option('--output', '-o', required=True, help='Output file path')
    @click.option('--title', help='Document title')
    def word_create(output: str, title: Optional[str]):
        """Create blank Word document"""
        try:
            wp = WordProcessor()
            wp.create_document()
            
            if title:
                wp.add_heading(title, level=1)
            
            wp.save(output)
            click.echo(f"[OK] Document created: {output}")
            
        except OfficeProError as e:
            handle_error(e, 1)
        except Exception as e:
            handle_error(e, 99)

    @cli.group()
    def excel():
        """Excel spreadsheet operations"""
        pass

    @excel.command('generate')
    @click.option('--template', '-t', required=True, help='Template filename')
    @click.option('--data', '-d', required=True, help='Data JSON file path')
    @click.option('--output', '-o', required=True, help='Output file path')
    @click.option('--template-dir', help='Custom template directory')
    def excel_generate(template: str, data: str, output: str, template_dir: Optional[str]):
        """Generate Excel report from template"""
        try:
            context = safe_load_data(data)
            
            ep = ExcelProcessor(template_dir=template_dir)
            ep.load_template(template)
            ep.render_and_save(context, output)
            
            click.echo(f"[OK] Report generated: {output}")
            
        except OfficeProError as e:
            handle_error(e, 1)
        except click.ClickException:
            raise
        except Exception as e:
            handle_error(e, 99)

    @excel.command('create')
    @click.option('--output', '-o', required=True, help='Output file path')
    @click.option('--sheets', '-s', default=1, help='Number of sheets')
    def excel_create(output: str, sheets: int):
        """Create blank Excel workbook"""
        try:
            ep = ExcelProcessor()
            ep.create_document()
            
            if sheets > 0:
                ws = ep.get_sheet()
                ws.title = "Sheet1"
            
            for i in range(2, sheets + 1):
                ep.create_sheet(f"Sheet{i}")
            
            ep.save(output)
            click.echo(f"[OK] Workbook created: {output}")
            
        except OfficeProError as e:
            handle_error(e, 1)
        except Exception as e:
            handle_error(e, 99)

    @excel.command('csv-import')
    @click.option('--input', '-i', 'input_file', required=True, help='CSV file path')
    @click.option('--output', '-o', required=True, help='Output Excel path')
    @click.option('--delimiter', '-d', default=',', help='Delimiter character')
    def csv_import(input_file: str, output: str, delimiter: str):
        """Import data from CSV"""
        try:
            ep = ExcelProcessor()
            ep.create_document()
            ep.import_csv(input_file, delimiter=delimiter)
            ep.save(output)
            click.echo(f"[OK] Data imported: {output}")
            
        except OfficeProError as e:
            handle_error(e, 1)
        except Exception as e:
            handle_error(e, 99)

    @excel.command('csv-export')
    @click.option('--input', '-i', 'input_file', required=True, help='Excel file path')
    @click.option('--output', '-o', required=True, help='Output CSV path')
    @click.option('--sheet', '-s', help='Sheet name')
    @click.option('--delimiter', '-d', default=',', help='Delimiter character')
    def csv_export(input_file: str, output: str, sheet: Optional[str], delimiter: str):
        """Export data to CSV"""
        try:
            ep = ExcelProcessor()
            ep.load_document(input_file)
            ep.export_csv(output, sheet=sheet, delimiter=delimiter)
            click.echo(f"[OK] Data exported: {output}")
            
        except OfficeProError as e:
            handle_error(e, 1)
        except Exception as e:
            handle_error(e, 99)

    @cli.group()
    def templates():
        """Template management"""
        pass

    @templates.command('list')
    @click.option('--type', 'template_type', 
                  type=click.Choice(['word', 'excel', 'all']), 
                  default='all')
    @click.option('--template-dir', help='Custom template directory')
    def list_templates(template_type: str, template_dir: Optional[str]):
        """List available templates"""
        try:
            if template_dir:
                base_dir = Path(template_dir)
            else:
                skill_root = Path(__file__).parent.parent
                base_dir = skill_root / "assets" / "templates"
            
            templates = {'word': [], 'excel': []}
            
            if template_type in ('word', 'all'):
                word_dir = base_dir / "word"
                if word_dir.exists():
                    templates['word'] = [f.name for f in word_dir.glob("*.docx")]
            
            if template_type in ('excel', 'all'):
                excel_dir = base_dir / "excel"
                if excel_dir.exists():
                    templates['excel'] = [f.name for f in excel_dir.glob("*.xlsx")]
            
            if template_type in ('word', 'all'):
                click.echo("\n[Word Templates]")
                if templates['word']:
                    for t in sorted(templates['word']):
                        click.echo(f"  - {t}")
                else:
                    click.echo("  (none)")
            
            if template_type in ('excel', 'all'):
                click.echo("\n[Excel Templates]")
                if templates['excel']:
                    for t in sorted(templates['excel']):
                        click.echo(f"  - {t}")
                else:
                    click.echo("  (none)")
            
            click.echo()
            
        except OfficeProError as e:
            handle_error(e, 1)
        except Exception as e:
            handle_error(e, 99)

    def main():
        """CLI entry point"""
        if not CLICK_AVAILABLE:
            print("Error: click module not installed. Run: pip install click")
            sys.exit(1)
        
        cli()

else:
    def main():
        print("Error: click module not installed. Run: pip install click")
        sys.exit(1)


if __name__ == '__main__':
    main()
