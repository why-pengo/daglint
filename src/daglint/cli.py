"""Command-line interface for daglint."""

import sys
from pathlib import Path
from typing import Optional

import click
from colorama import Fore, Style, init

from daglint.config import Config
from daglint.linter import DAGLinter
from daglint.rules import AVAILABLE_RULES

# Initialize colorama for cross-platform colored output
init(autoreset=True)


@click.group()
@click.version_option()
def cli():
    """DAGLint - A linting tool for Apache Airflow DAG files."""
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True), required=True)
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to configuration file")
@click.option("--rules", "-r", help="Comma-separated list of rules to check")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--fix", is_flag=True, help="Automatically fix issues where possible")
def check(path: str, config: Optional[str], rules: Optional[str], verbose: bool, fix: bool):
    """Check DAG files for linting issues.

    PATH can be a single file or a directory containing DAG files.
    """
    target_path = Path(path)

    # Load configuration
    if config:
        cfg = Config.from_file(config)
    else:
        # Look for .daglint.yaml in current directory
        default_config = Path(".daglint.yaml")
        if default_config.exists():
            cfg = Config.from_file(str(default_config))
        else:
            cfg = Config.default()

    # Override rules if specified
    if rules:
        rule_list = [r.strip() for r in rules.split(",")]
        cfg.set_active_rules(rule_list)

    # Collect files to lint
    files_to_check = []
    if target_path.is_file():
        files_to_check.append(target_path)
    else:
        files_to_check.extend(target_path.rglob("*.py"))

    if not files_to_check:
        click.echo(f"{Fore.YELLOW}No Python files found to check.{Style.RESET_ALL}")
        sys.exit(0)

    # Run linter
    linter = DAGLinter(cfg, verbose=verbose)
    total_issues = 0

    for file_path in files_to_check:
        if verbose:
            click.echo(f"\n{Fore.CYAN}Checking: {file_path}{Style.RESET_ALL}")

        issues = linter.lint_file(str(file_path))

        if issues:
            total_issues += len(issues)
            click.echo(f"\n{Fore.RED}✗ {file_path}{Style.RESET_ALL}")
            for issue in issues:
                severity_color = Fore.RED if issue.severity == "error" else Fore.YELLOW
                click.echo(
                    f"  {severity_color}{issue.severity.upper()}{Style.RESET_ALL} "
                    f"[{issue.rule_id}] Line {issue.line}: {issue.message}"
                )
        else:
            click.echo(f"{Fore.GREEN}✓ {file_path}{Style.RESET_ALL}")

    # Summary
    click.echo(f"\n{'-' * 50}")
    if total_issues == 0:
        click.echo(f"{Fore.GREEN}All checks passed!{Style.RESET_ALL}")
        sys.exit(0)
    else:
        click.echo(f"{Fore.RED}Found {total_issues} issue(s) in {len(files_to_check)} file(s).{Style.RESET_ALL}")
        sys.exit(1)


@cli.command()
def rules():
    """List all available linting rules."""
    click.echo(f"\n{Fore.CYAN}Available Linting Rules:{Style.RESET_ALL}\n")

    for rule_id, rule_class in AVAILABLE_RULES.items():
        rule = rule_class()
        click.echo(f"{Fore.GREEN}{rule_id}{Style.RESET_ALL}")
        click.echo(f"  {rule.description}")
        click.echo()


@cli.command()
@click.option("--output", "-o", default=".daglint.yaml", help="Output configuration file path")
def init(output: str):
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
