"""Command Line Interface for the Void platform.

Provides developer and enterprise operations commands to analyze, generate,
inspect, and serve the self-documenting Void repository.
"""

from __future__ import annotations

from pathlib import Path
import click

from void.engine import VoidEngine


def _find_root() -> Path:
    """Walk up from cwd to find directory containing config.yaml or pyproject.toml AND a void/ package."""
    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        has_config = (parent / "config.yaml").is_file() or (parent / "pyproject.toml").is_file()
        has_void = (parent / "void").is_dir() and (parent / "void" / "__init__.py").is_file()
        if has_config and has_void:
            return parent
    return current


@click.group()
@click.version_option(version="0.1.0", prog_name="void")
def cli() -> None:
    """Void - Self-Documenting Enterprise Inactivity Platform."""
    pass


@cli.command()
def analyze() -> None:
    """Run static AST analysis and inspect topological metrics."""
    root = _find_root()
    engine = VoidEngine(root)
    res = engine.analyze()
    metrics = res.get("metrics", {})

    click.echo("=== Void Repository Analysis ===")
    click.echo(f"Files:                  {metrics.get('files', 0)}")
    click.echo(f"Python Modules:         {metrics.get('python_files', 0)}")
    click.echo(f"Functions:              {metrics.get('functions', 0)}")
    click.echo(f"Classes:                {metrics.get('classes', 0)}")
    click.echo(f"Methods:                {metrics.get('methods', 0)}")
    if "graph_nodes" in metrics:
        click.echo(f"Graph Nodes:            {metrics.get('graph_nodes', 0)}")
    if "graph_edges" in metrics:
        click.echo(f"Graph Edges:            {metrics.get('graph_edges', 0)}")
    click.echo(f"Meaningful Operations:  {metrics.get('meaningful_operations', 0)}")
    if "business_value" in metrics:
        click.echo(f"Business Value:         {metrics.get('business_value', 0.0)}")
    if "corporate_alignment" in metrics:
        click.echo(f"Corporate Alignment:    {metrics.get('corporate_alignment', 0.0)}%")


@cli.command()
def generate() -> None:
    """Generate enterprise documentation suite and advance generation state."""
    root = _find_root()
    engine = VoidEngine(root)
    result = engine.generate(progress_callback=print)

    gen = result.get("generation", 1)
    primary_term = result.get("terms", {}).get("primary_term", "")
    drift = result.get("drift", 0.0)
    func_drift = result.get("functional_drift", 0.0)

    click.echo("")
    click.echo(f"Generation:             {gen}")
    click.echo(f"Primary Terminology:    {primary_term}")
    click.echo(f"Documentation Drift:    {drift:.2f}%")
    click.echo(f"Functional Drift:       {func_drift:.2f}%")
    click.echo("")
    click.echo("Generated Documents:")
    paths = result.get("paths", {})
    for doc_name, path in paths.items():
        click.echo(f"  - {doc_name.upper()}: {path}")


@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True, help="Host to bind the web server to.")
@click.option("--port", default=5000, type=int, show_default=True, help="Port to listen on.")
@click.option("--debug", is_flag=True, default=False, help="Run in debug mode.")
def serve(host: str, port: int, debug: bool) -> None:
    """Start the interactive Void web dashboard."""
    root = _find_root()
    try:
        from void.web.app import create_app
    except ImportError:
        click.echo("Web dashboard is not yet implemented (requires Phase 7).")
        return

    try:
        app = create_app(root)
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        click.echo(f"Error starting web dashboard: {e}")


@cli.command()
def status() -> None:
    """Display operational status, current generation, and verified metrics."""
    root = _find_root()
    engine = VoidEngine(root)
    st = engine.status()
    metrics = st.get("metrics", {})

    click.echo("=== Void Operational Status ===")
    click.echo(f"Status:                 {st.get('status', 'operational')}")
    click.echo(f"Generation:             {st.get('generation', 0)}")
    click.echo(f"Primary Term:           {st.get('primary_term', '')}")
    click.echo(f"Documentation Drift:    {st.get('drift', 0.0):.2f}%")
    click.echo(f"Functional Drift:       {st.get('functional_drift', 0.0):.2f}%")
    click.echo(f"Python Modules:         {metrics.get('python_files', 0)}")
    click.echo(f"Functions:              {metrics.get('functions', 0)}")
    click.echo(f"Classes:                {metrics.get('classes', 0)}")
    click.echo(f"Meaningful Operations:  {st.get('meaningful_operations', 0)}")
    click.echo(f"Business Value:         {metrics.get('business_value', 0.0)}")
    click.echo(f"Corporate Alignment:    {metrics.get('corporate_alignment', 0.0)}%")
    click.echo(f"Last Updated:           {st.get('last_updated', 'Never')}")
