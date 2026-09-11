"""Enterprise API documentation generator for Void.

Renders docs/API.md documenting the deterministic REST endpoint specification
alongside all discovered public Python interfaces.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import jinja2

DEFAULT_API_TEMPLATE = """# {{ terminology.primary_term }} — API Specification

> *Deterministic Quiescent Interface Specification — Generation {{ generation }}*

## Overview

The Void API exposes high-assurance, non-blocking programmatic and network interfaces conforming to the RFC-0000 Null-State Communication Protocol. Every endpoint deterministically returns invariant null-results, guaranteeing 0.00ms business computational overhead and zero collateral side-effects.

---

## RESTful Endpoints

### 1. Execute Core Pipeline

Initiates the high-assurance quiescence execution harness.

```http
POST /api/v1/void/execute
Content-Type: application/json
```

#### Request Payload
```json
{}
```
*Note: Any payload parameters supplied are syntactically parsed and safely discarded to maintain strict inactivity.*

#### Response (`200 OK`)
```json
{
  "status": "success",
  "engine": "{{ terminology.engine_name }}",
  "mode": "quiescent",
  "operations_performed": 0,
  "result": null
}
```

---

### 2. Operational Status

Polls the systemic null-state health and runtime invariants.

```http
GET /api/v1/void/status
```

#### Response (`200 OK`)
```json
{
  "status": "operational",
  "health": "optimal",
  "generation": {{ generation }},
  "architecture": "{{ terminology.architecture_name }}",
  "meaningful_operations": 0,
  "business_value": 0.0
}
```

---

### 3. Repository Telemetry

Streams verified AST and topological metrics.

```http
GET /api/v1/void/metrics
```

#### Response (`200 OK`)
```json
{
  "total_files": {{ metrics.files }},
  "python_modules": {{ metrics.python_files }},
  "functions": {{ metrics.functions }},
  "classes": {{ metrics.classes }},
  "graph_nodes": {{ metrics.graph_nodes }},
  "graph_edges": {{ metrics.graph_edges }},
  "operational_efficiency": {{ metrics.operational_efficiency }},
  "enterprise_readiness": {{ metrics.enterprise_readiness }},
  "meaningful_operations": 0
}
```

---

## Discovered Python Interfaces

The following public functions were discovered in the codebase via AST parsing by `void.analysis`. All public functions guarantee intentional inactivity and zero unexpected mutations.

| Function | Module Location | Arguments | Return Type | Docstring Summary |
|:---|:---|:---|:---:|:---|
{% for fn in public_functions %}
| `{{ fn.name }}()` | `{{ fn.file }}` | `({{ fn.arguments | join(', ') }})` | `{{ fn.returns or 'None' }}` | {{ fn.docstring.split('\\n')[0] if fn.docstring else 'Deterministic null-state routine.' }} |
{% endfor %}

---

## Enterprise Invariants

1. **Deterministic Return Values**: All operational execution endpoints return `null` (`None`).
2. **Zero Resource Allocation**: Invocations consume asymptotic $O(0)$ memory and compute.
3. **Idempotency**: Because no operations are performed, all invocations are strictly and infinitely idempotent.
"""


class ApiGenerator:
    """Generates docs/API.md from analysis data and terminology."""

    def __init__(
        self,
        root: Path | str | None = None,
        template_str: str | None = None,
    ) -> None:
        """Initialize ApiGenerator.

        Args:
            root: Root path of the repository.
            template_str: Optional custom Jinja2 template string.
        """
        self.root = Path(root) if root else Path.cwd()
        self.template_str = template_str or DEFAULT_API_TEMPLATE
        self.env = jinja2.Environment(autoescape=False, trim_blocks=True, lstrip_blocks=True)
        self.template = self.env.from_string(self.template_str)

    def generate(
        self,
        analysis_data: dict[str, Any],
        terminology: dict[str, Any],
        generation: int = 1,
    ) -> str:
        """Render the API documentation.

        Args:
            analysis_data: Output dictionary from ProjectAnalyzer.analyze().
            terminology: Buzzwords bundle from BuzzwordGenerator.generate_set().
            generation: Documentation generation number.

        Returns:
            Rendered markdown content.
        """
        all_functions = analysis_data.get("functions", [])
        public_functions = [
            fn for fn in all_functions
            if not fn.get("name", "").startswith("_")
        ]

        metrics = analysis_data.get("metrics", {})

        return self.template.render(
            analysis=analysis_data,
            metrics=metrics,
            terminology=terminology,
            generation=generation,
            public_functions=public_functions,
        )

    def write(
        self,
        content: str,
        output_path: Path | str | None = None,
    ) -> Path:
        """Write generated markdown to disk.

        Args:
            content: Rendered markdown string.
            output_path: Destination file path. Defaults to docs/API.md.

        Returns:
            Destination file Path.
        """
        if output_path is None:
            dest = self.root / "docs" / "API.md"
        else:
            dest = Path(output_path)

        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(content)

        return dest
