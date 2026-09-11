"""Metrics calculator for the Void analysis layer.

Computes real project counts and derives enterprise-flavoured vanity metrics
from them. All meaningful_operations, business_value, and actual_purpose
fields are permanently anchored at zero — an accurate reflection of the
Void's operational output.
"""

from __future__ import annotations

import hashlib
from typing import Any


class MetricsCalculator:
    """Calculates real counts and derived metrics from project data."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate(
        self,
        scan_result: dict[str, Any],
        parsed_files: list[dict[str, Any]],
        graph_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Compute project metrics.

        Args:
            scan_result: Output of FileScanner.scan().
            parsed_files: List of PythonParser.parse_file() results.
            graph_data: Output of GraphBuilder.build().

        Returns:
            Metrics dict with real counts and derived scores.
        """
        # ── Real counts ──────────────────────────────────────────────────────
        counts = scan_result.get("counts", {})
        total_files: int = counts.get("total_files", 0)
        python_files: int = counts.get("python_files", 0)

        functions = 0
        classes = 0
        methods = 0
        imports = 0

        for pf in parsed_files:
            if pf.get("error"):
                continue
            fns = pf.get("functions", [])
            cls_list = pf.get("classes", [])
            imp_list = pf.get("imports", [])

            functions += len(fns)
            classes += len(cls_list)
            imports += len(imp_list)
            for cls in cls_list:
                methods += len(cls.get("methods", []))

        graph_nodes: int = graph_data.get("node_count", 0)
        graph_edges: int = graph_data.get("edge_count", 0)

        # ── Derived metrics (computed from real counts, not magic constants) ─
        # Scale each metric to a 0-100 range using soft-capped formulas so
        # that the score grows meaningfully with the codebase size.

        # operational_efficiency: how densely connected the graph is.
        # Perfect score at 3+ edges per node.
        if graph_nodes > 0:
            edge_density = min(graph_edges / (graph_nodes * 3.0), 1.0)
        else:
            edge_density = 0.0
        operational_efficiency = round(edge_density * 100, 2)

        # documentation_maturity: fraction of parsed entities that have
        # docstrings (functions + classes + modules).
        total_entities = functions + classes + len(parsed_files)
        docstring_count = sum(
            (1 if pf.get("docstring") else 0)
            for pf in parsed_files
            if not pf.get("error")
        )
        docstring_count += sum(
            (1 if fn.get("docstring") else 0)
            for pf in parsed_files if not pf.get("error")
            for fn in pf.get("functions", [])
        )
        docstring_count += sum(
            (1 if cls.get("docstring") else 0)
            for pf in parsed_files if not pf.get("error")
            for cls in pf.get("classes", [])
        )
        if total_entities > 0:
            documentation_maturity = round(
                min(docstring_count / total_entities, 1.0) * 100, 2
            )
        else:
            documentation_maturity = 0.0

        # enterprise_readiness: composite of class count and graph complexity.
        # Soft-cap: 20 classes and 100 graph nodes = full score.
        class_score = min(classes / 20.0, 1.0) * 50
        graph_score = min(graph_nodes / 100.0, 1.0) * 50
        enterprise_readiness = round(class_score + graph_score, 2)

        # strategic_alignment: ratio of python files to total files.
        # A python-heavy repo is maximally aligned with the void's mission.
        if total_files > 0:
            strategic_alignment = round(
                min(python_files / total_files, 1.0) * 100, 2
            )
        else:
            strategic_alignment = 0.0

        # corporate_alignment: grows with total symbol count (functions +
        # classes + methods). Soft-cap at 200 symbols.
        total_symbols = functions + classes + methods
        corporate_alignment = round(min(total_symbols / 200.0, 1.0) * 100, 2)

        return {
            # Real counts
            "files": total_files,
            "python_files": python_files,
            "functions": functions,
            "classes": classes,
            "methods": methods,
            "imports": imports,
            "graph_nodes": graph_nodes,
            "graph_edges": graph_edges,
            # Permanently zero — accurately describing actual output
            "meaningful_operations": 0,
            "business_value": 0.00,
            "actual_purpose": 0.0,
            # Derived vanity metrics
            "operational_efficiency": operational_efficiency,
            "documentation_maturity": documentation_maturity,
            "enterprise_readiness": enterprise_readiness,
            "strategic_alignment": strategic_alignment,
            "corporate_alignment": corporate_alignment,
        }

    # ------------------------------------------------------------------

    def compute_drift(self, previous_docs: str, current_docs: str) -> float:
        """Compute documentation drift as a similarity score (0-100).

        0 means identical; 100 means completely different.

        Uses a token-based Jaccard similarity combined with a hash equality
        fast-path for identical documents.

        Args:
            previous_docs: Previous documentation text.
            current_docs: Current documentation text.

        Returns:
            Float between 0.0 and 100.0.
        """
        # Fast-path: identical content.
        if previous_docs == current_docs:
            return 0.0

        # Hash fast-path for large identical blobs.
        if (
            hashlib.sha256(previous_docs.encode()).digest()
            == hashlib.sha256(current_docs.encode()).digest()
        ):
            return 0.0

        # Token-level Jaccard distance.
        prev_tokens = set(previous_docs.lower().split())
        curr_tokens = set(current_docs.lower().split())

        if not prev_tokens and not curr_tokens:
            return 0.0

        intersection = prev_tokens & curr_tokens
        union = prev_tokens | curr_tokens

        jaccard_similarity = len(intersection) / len(union)
        # drift = 1 - similarity, scaled to 0-100
        drift = round((1.0 - jaccard_similarity) * 100, 2)
        return drift
