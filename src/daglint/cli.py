"""Command-line interface for daglint."""

import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import click
from colorama import Fore, Style, init

from daglint.config import Config
from daglint.linter import DAGLinter
from daglint.models import LintIssue
from daglint.rules import AVAILABLE_RULES

FileResults = List[Tuple[Path, List[LintIssue]]]

# Initialize colorama for cross-platform colored output
init(autoreset=True)


@click.group()
@click.version_option()
def cli():
    """DAGLint - A linting tool for Apache Airflow DAG files."""
    pass


def _load_config(config_path: Optional[str]) -> Config:
    """Load configuration from file or use default."""
    if config_path:
        return Config.from_file(config_path)

    # Look for .daglint.yaml in current directory
    default_config = Path(".daglint.yaml")
    if default_config.exists():
        return Config.from_file(str(default_config))

    return Config.default()


def _collect_files(target_path: Path) -> list:
    """Collect Python files to lint."""
    if target_path.is_file():
        return [target_path]
    return list(target_path.rglob("*.py"))


def _severity_counts(issues: List[LintIssue]) -> dict:
    """Count issues by severity."""
    counts = {"errors": 0, "warnings": 0, "infos": 0}
    for issue in issues:
        if issue.severity == "error":
            counts["errors"] += 1
        elif issue.severity == "warning":
            counts["warnings"] += 1
        else:
            counts["infos"] += 1
    return counts


def _exit_code(issues: List[LintIssue], strict: bool) -> int:
    """Determine the exit code: 1 on errors (or any issue with --strict), else 0."""
    if strict:
        return 1 if issues else 0
    return 1 if any(issue.severity == "error" for issue in issues) else 0


def _print_issue(issue: LintIssue):
    """Print a single linting issue."""
    severity_color = Fore.RED if issue.severity == "error" else Fore.YELLOW
    click.echo(
        f"  {severity_color}{issue.severity.upper()}{Style.RESET_ALL} " f"[{issue.rule_id}] Line {issue.line}: {issue.message}"
    )


def _render_text(results: FileResults, exit_code: int, verbose: bool):
    """Render results as colorized human-readable text."""
    total_issues = 0
    for file_path, issues in results:
        if verbose:
            click.echo(f"\n{Fore.CYAN}Checking: {file_path}{Style.RESET_ALL}")
        if issues:
            total_issues += len(issues)
            click.echo(f"\n{Fore.RED}✗ {file_path}{Style.RESET_ALL}")
            for issue in issues:
                _print_issue(issue)
        else:
            click.echo(f"{Fore.GREEN}✓ {file_path}{Style.RESET_ALL}")

    click.echo(f"\n{'-' * 50}")
    if total_issues == 0:
        click.echo(f"{Fore.GREEN}All checks passed!{Style.RESET_ALL}")
        return

    counts = _severity_counts([issue for _, issues in results for issue in issues])
    detail = f"{counts['errors']} error(s), {counts['warnings']} warning(s)"
    if counts["infos"]:
        detail += f", {counts['infos']} info(s)"
    summary_color = Fore.RED if exit_code else Fore.YELLOW
    click.echo(f"{summary_color}Found {total_issues} issue(s) ({detail}) in {len(results)} file(s).{Style.RESET_ALL}")
    if exit_code == 0:
        click.echo("Warnings do not fail the build; use --strict to change that.")


def _render_json(results: FileResults):
    """Render results as a machine-readable JSON envelope."""
    all_issues = [issue for _, issues in results for issue in issues]
    payload = {
        "issues": [
            {
                "rule_id": issue.rule_id,
                "severity": issue.severity,
                "file": issue.file_path,
                "line": issue.line,
                "column": issue.column,
                "message": issue.message,
            }
            for issue in all_issues
        ],
        "summary": {"files_checked": len(results), **_severity_counts(all_issues)},
    }
    click.echo(json.dumps(payload, indent=2))


def _render_github(results: FileResults):
    """Render results as GitHub Actions workflow commands."""
    command_for_severity = {"error": "error", "warning": "warning", "info": "notice"}
    all_issues = [issue for _, issues in results for issue in issues]
    for issue in all_issues:
        command = command_for_severity[issue.severity]
        click.echo(
            f"::{command} file={issue.file_path},line={issue.line},col={issue.column}" f"::[{issue.rule_id}] {issue.message}"
        )

    counts = _severity_counts(all_issues)
    click.echo(
        f"daglint checked {len(results)} file(s): "
        f"{counts['errors']} error(s), {counts['warnings']} warning(s), {counts['infos']} info(s)."
    )


@cli.command()
@click.argument("path", type=click.Path(exists=True), required=True)
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to configuration file")
@click.option("--rules", "-r", help="Comma-separated list of rules to check")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "json", "github"]),
    default="text",
    help="Output format: colorized text, a JSON envelope, or GitHub Actions annotations",
)
@click.option("--strict", is_flag=True, help="Exit non-zero on any issue, not just errors")
def check(
    path: str,
    config: Optional[str],
    rules: Optional[str],
    verbose: bool,
    output_format: str,
    strict: bool,
):
    """Check DAG files for linting issues.

    PATH can be a single file or a directory containing DAG files.

    \b
    Exit codes:
      0  no issues (or only warnings/info without --strict)
      1  error-severity issues found (any issue with --strict)
      2  usage error
    """
    target_path = Path(path)

    # Load configuration
    cfg = _load_config(config)

    # Override rules if specified
    if rules is not None:
        rule_list = [r.strip() for r in rules.split(",") if r.strip()]
        if not rule_list:
            raise click.UsageError("--rules was given but contains no rule names")
        unknown = [r for r in rule_list if r not in AVAILABLE_RULES]
        if unknown:
            raise click.UsageError(
                f"Unknown rule(s): {', '.join(unknown)}. " f"Valid rules are: {', '.join(sorted(AVAILABLE_RULES))}"
            )
        cfg.set_active_rules(rule_list, all_rule_ids=list(AVAILABLE_RULES))

    # Collect files to lint
    files_to_check = _collect_files(target_path)

    if not files_to_check and output_format == "text":
        click.echo(f"{Fore.YELLOW}No Python files found to check.{Style.RESET_ALL}")
        sys.exit(0)

    # Run linter, collecting all results before presenting them
    linter = DAGLinter(cfg, verbose=verbose)
    results: FileResults = [(file_path, linter.lint_file(str(file_path))) for file_path in files_to_check]
    all_issues = [issue for _, issues in results for issue in issues]
    exit_code = _exit_code(all_issues, strict)

    if output_format == "json":
        _render_json(results)
    elif output_format == "github":
        _render_github(results)
    else:
        _render_text(results, exit_code, verbose)

    sys.exit(exit_code)


@cli.command()
def rules():
    """List all available linting rules."""
    click.echo(f"\n{Fore.CYAN}Available Linting Rules:{Style.RESET_ALL}\n")

    for rule_id, rule_class in AVAILABLE_RULES.items():
        rule = rule_class()
        click.echo(f"{Fore.GREEN}{rule_id}{Style.RESET_ALL}")
        click.echo(f"  {rule.description}")
        click.echo()


@cli.command(name="init")
@click.option("--output", "-o", default=".daglint.yaml", help="Output configuration file path")
def init_cmd(output: str):
    """Generate a default configuration file."""
    config_path = Path(output)

    if config_path.exists():
        if not click.confirm(f"{output} already exists. Overwrite?"):
            click.echo("Aborted.")
            return

    Config.generate_default_config(str(config_path))
    click.echo(f"{Fore.GREEN}Created configuration file: {output}{Style.RESET_ALL}")


if __name__ == "__main__":
    cli()
