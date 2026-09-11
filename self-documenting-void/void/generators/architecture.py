"""Enterprise Architecture documentation generator for Void.

Renders architectural topologies and component specifications using Mermaid graph TD
derived from real analysis graph data.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any
import jinja2


def sanitize_mermaid_id(raw_id: str) -> str:
    """Sanitize node identifiers for Mermaid compatibility.

    Replaces colon, slash, dot, hyphen, and space with underscore.
    """
    cleaned = str(raw_id)
    for ch in [":", "/", ".", "-", " "]:
        cleaned = cleaned.replace(ch, "_")
    return cleaned


DEFAULT_ARCHITECTURE_TEMPLATE = """# {{ terminology.architecture_name }}

> *Topological Specification and Component Telemetry - Generation {{ generation }}*

## System Overview

The **{{ terminology.architecture_name }}** formalizes the structural boundaries and directional data flows sustaining the Void's intentional null-state equilibrium. Orchestrated by the **{{ terminology.engine_name }}**, the topology maintains deterministic quiescence across all integrated planes.

## Component Topology

```mermaid
graph TD
{% for node in component_nodes %}
    {{ node.safe_id }}["{{ node.label }}"]
{% endfor %}

{% for edge in component_edges %}
  {% if edge.relation %}
    {{ edge.safe_source }} -->|{{ edge.relation }}| {{ edge.safe_target }}
  {% else %}
    {{ edge.safe_source }} --> {{ edge.safe_target }}
  {% endif %}
{% endfor %}
```

## Architectural Components

The following subsystems comprise the certified structural footprint of the Void core framework:

| Component Name | Topology Node ID | Primary Role | Operational Mode |
|:---|:---|:---|:---:|
{% for node in component_nodes %}
| **{{ node.label }}** | `{{ node.safe_id }}` | Core topological participant | Quiescent |
{% endfor %}

## Invariant Data Flows

As mapped in the topological knowledge graph:

{% for edge in component_edges %}
- **{{ edge.source }}** $\\xrightarrow{\\text{ {{ edge.relation or 'links' }} }}$ **{{ edge.target }}**
{% endfor %}

## Architectural Guarantees

1. **Deterministic Zero Throughput**: Components communicate purely for topological and documentation synthesis without invoking collateral runtime work.
2. **Structural Cohesion**: All subsystem dependencies are strictly documented via AST analysis and registered within the knowledge graph.
3. **Intentional Inactivity**: Operational transitions preserve null-state invariants across all lifecycle hooks.
"""


class ArchitectureGenerator:
    """Generates ARCHITECTURE.md containing Mermaid diagrams of the component graph."""

    def __init__(
        self,
        root: Path | str | None = None,
        template_str: str | None = None,
    ) -> None:
        """Initialize the ArchitectureGenerator.

        Args:
            root: Root path of the repository.
            template_str: Optional custom Jinja2 template string.
        """
        self.root = Path(root) if root else Path.cwd()
        self.template_str = template_str or DEFAULT_ARCHITECTURE_TEMPLATE
        self.env = jinja2.Environment(autoescape=False, trim_blocks=True, lstrip_blocks=True)
        self.template = self.env.from_string(self.template_str)

    def generate(
        self,
        analysis_data: dict[str, Any],
        terminology: dict[str, Any],
        generation: int = 1,
    ) -> str:
        """Render the ARCHITECTURE markdown with Mermaid topology.

        Args:
            analysis_data: Structured output from ProjectAnalyzer.analyze().
            terminology: Terminology bundle from BuzzwordGenerator.generate_set().
            generation: Documentation generation number.

        Returns:
            Rendered markdown string.
        """
        graph = analysis_data.get("graph", {})
        all_nodes = graph.get("nodes", [])
        all_edges = graph.get("edges", [])

        # Filter for component nodes, or fallback to all nodes
        component_nodes_raw = [
            n for n in all_nodes if n.get("type") == "component"
        ]
        if not component_nodes_raw:
            component_nodes_raw = all_nodes

        comp_ids = {n.get("id") for n in component_nodes_raw}

        component_edges_raw = [
            e for e in all_edges
            if e.get("source") in comp_ids and e.get("target") in comp_ids
        ]

        # Prepare sanitized entries for Mermaid rendering
        component_nodes = []
        for n in component_nodes_raw:
            raw_id = n.get("id", "")
            component_nodes.append({
                "id": raw_id,
                "label": n.get("label", raw_id),
                "safe_id": sanitize_mermaid_id(raw_id),
                "type": n.get("type", "component"),
            })

        component_edges = []
        for e in component_edges_raw:
            component_edges.append({
                "source": e.get("source", ""),
                "target": e.get("target", ""),
                "safe_source": sanitize_mermaid_id(e.get("source", "")),
                "safe_target": sanitize_mermaid_id(e.get("target", "")),
                "relation": e.get("relation", ""),
            })

        metrics = analysis_data.get("metrics", {})

        return self.template.render(
            analysis=analysis_data,
            metrics=metrics,
            terminology=terminology,
            generation=generation,
            component_nodes=component_nodes,
            component_edges=component_edges,
        )

    def write(
        self,
        content: str,
        output_path: Path | str | None = None,
    ) -> Path:
        """Write generated markdown content to disk.

        Args:
            content: Rendered markdown string.
            output_path: Destination file path. Defaults to self.root / "docs" / "ARCHITECTURE.md".

        Returns:
            The Path of the written file.
        """
        if output_path is None:
            dest = self.root / "docs" / "ARCHITECTURE.md"
        else:
            dest = Path(output_path)

        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(content)

        return dest
