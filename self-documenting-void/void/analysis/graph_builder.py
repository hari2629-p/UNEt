"""Graph builder for the Void analysis layer.

Constructs a serializable knowledge graph from parsed Python files and
scan results. Nodes represent modules, classes, functions, and fixed
architectural components. Edges represent structural and semantic
relationships between them.
"""

from __future__ import annotations

from typing import Any

# Fixed architectural component nodes that always appear in the graph.
COMPONENT_NODES = [
    "Void Orchestrator",
    "Repository Scanner",
    "Project Analyzer",
    "Knowledge Graph",
    "README Generator",
    "API Generator",
    "Architecture Generator",
    "Changelog Generator",
    "Buzzword Engine",
    "Web Dashboard",
]

# Directed edges between fixed components (source, target, relation).
COMPONENT_EDGES = [
    ("Repository Scanner", "Project Analyzer", "feeds"),
    ("Project Analyzer", "Knowledge Graph", "feeds"),
    ("Knowledge Graph", "README Generator", "uses"),
    ("Knowledge Graph", "API Generator", "uses"),
    ("Knowledge Graph", "Architecture Generator", "uses"),
    ("Knowledge Graph", "Changelog Generator", "uses"),
    ("Buzzword Engine", "README Generator", "uses"),
    ("Buzzword Engine", "API Generator", "uses"),
    ("Buzzword Engine", "Architecture Generator", "uses"),
    ("Buzzword Engine", "Changelog Generator", "uses"),
    ("README Generator", "Web Dashboard", "feeds"),
    ("API Generator", "Web Dashboard", "feeds"),
    ("Architecture Generator", "Web Dashboard", "feeds"),
    ("Changelog Generator", "Web Dashboard", "feeds"),
    ("Void Orchestrator", "Repository Scanner", "uses"),
    ("Void Orchestrator", "Project Analyzer", "uses"),
]

# Map void.* module names to component node names where resolvable.
_VOID_MODULE_MAP: dict[str, str] = {
    "void.main": "Void Orchestrator",
    "void.scanner": "Repository Scanner",
    "void.scanner.file_scanner": "Repository Scanner",
    "void.scanner.python_parser": "Repository Scanner",
    "void.analysis": "Project Analyzer",
    "void.analysis.project_analyzer": "Project Analyzer",
    "void.analysis.graph_builder": "Knowledge Graph",
    "void.analysis.metrics": "Project Analyzer",
    "void.generators": "README Generator",
    "void.buzzwords": "Buzzword Engine",
    "void.web": "Web Dashboard",
}


def _module_id(rel_path: str) -> str:
    """Convert a relative file path to a Python module identifier."""
    return rel_path.replace("/", ".").replace("\\", ".").removesuffix(".py")


class GraphBuilder:
    """Builds a serializable knowledge graph from project parse data."""

    def build(
        self,
        parsed_files: list[dict[str, Any]],
        scan_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the knowledge graph.

        Args:
            parsed_files: List of parse results from PythonParser.parse_file().
            scan_result: Scan result dict from FileScanner.scan().

        Returns:
            Serializable dict with keys: nodes, edges, node_count, edge_count.
            Each node: {"id": str, "type": str, "label": str, **extra}
            Each edge: {"source": str, "target": str, "relation": str}
        """
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []

        # Track node ids to avoid duplicates and enable edge resolution.
        node_ids: set[str] = set()

        def _add_node(node: dict[str, Any]) -> None:
            if node["id"] not in node_ids:
                node_ids.add(node["id"])
                nodes.append(node)

        def _add_edge(source: str, target: str, relation: str) -> None:
            edges.append({"source": source, "target": target, "relation": relation})

        # -- Fixed component nodes -------------------------------------------
        for comp in COMPONENT_NODES:
            _add_node({"id": comp, "type": "component", "label": comp})

        for src, tgt, rel in COMPONENT_EDGES:
            _add_edge(src, tgt, rel)

        # -- Nodes from parsed Python files -----------------------------------
        for pf in parsed_files:
            if pf.get("error"):
                continue

            rel_path: str = pf.get("file", "")
            mod_id = _module_id(rel_path)

            _add_node({
                "id": mod_id,
                "type": "module",
                "label": mod_id,
                "file": rel_path,
                "docstring": pf.get("docstring"),
            })

            # Classes
            for cls in pf.get("classes", []):
                cls_id = f"{mod_id}.{cls['name']}"
                _add_node({
                    "id": cls_id,
                    "type": "class",
                    "label": cls["name"],
                    "module": mod_id,
                    "file": rel_path,
                    "lineno": cls.get("lineno"),
                    "bases": cls.get("bases", []),
                    "docstring": cls.get("docstring"),
                })
                _add_edge(mod_id, cls_id, "defines")

                # Methods
                for method in cls.get("methods", []):
                    m_id = f"{cls_id}.{method['name']}"
                    _add_node({
                        "id": m_id,
                        "type": "method",
                        "label": method["name"],
                        "class": cls_id,
                        "module": mod_id,
                        "file": rel_path,
                        "lineno": method.get("lineno"),
                        "docstring": method.get("docstring"),
                    })
                    _add_edge(cls_id, m_id, "contains")

            # Top-level functions
            for fn in pf.get("functions", []):
                fn_id = f"{mod_id}.{fn['name']}"
                _add_node({
                    "id": fn_id,
                    "type": "function",
                    "label": fn["name"],
                    "module": mod_id,
                    "file": rel_path,
                    "lineno": fn.get("lineno"),
                    "docstring": fn.get("docstring"),
                })
                _add_edge(mod_id, fn_id, "defines")

            # Import edges
            for imp in pf.get("imports", []):
                imported_mod = imp.get("module") or ""
                # Resolve void.* imports to component nodes when possible.
                target_id = _VOID_MODULE_MAP.get(imported_mod)
                if target_id is None:
                    target_id = imported_mod
                    if target_id and target_id not in node_ids:
                        _add_node({
                            "id": target_id,
                            "type": "external_module",
                            "label": target_id,
                        })
                if target_id:
                    _add_edge(mod_id, target_id, "imports")

        # -- Module containment edges (parent package -> child module) --------
        seen_contains: set[tuple[str, str]] = set()
        for pf in parsed_files:
            if pf.get("error"):
                continue
            rel_path = pf.get("file", "")
            mod_id = _module_id(rel_path)
            parts = mod_id.split(".")
            if len(parts) > 1:
                parent_id = ".".join(parts[:-1])
                key = (parent_id, mod_id)
                if key not in seen_contains and parent_id in node_ids:
                    seen_contains.add(key)
                    _add_edge(parent_id, mod_id, "contains")

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }
