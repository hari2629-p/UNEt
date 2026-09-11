"""Project Analyzer — coordination layer for the Void analysis pipeline.

Orchestrates the full analysis sequence:
  1. Scan the repository (FileScanner)
  2. Parse every Python file (PythonParser)
  3. Build the knowledge graph (GraphBuilder)
  4. Compute metrics (MetricsCalculator)

Returns one structured result dict that downstream generators can consume.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from void.scanner import FileScanner, PythonParser
from void.analysis.graph_builder import GraphBuilder
from void.analysis.metrics import MetricsCalculator


class ProjectAnalyzer:
    """Coordinates scanning, parsing, graph-building, and metrics."""

    def __init__(self, root: Path | None = None) -> None:
        """Initialise the analyzer.

        Args:
            root: Project root directory. Defaults to the current directory.
        """
        self.root = Path(root) if root else Path.cwd()
        self._scanner = FileScanner(root=self.root)
        self._parser = PythonParser(root=self.root)
        self._graph_builder = GraphBuilder()
        self._metrics_calculator = MetricsCalculator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self) -> dict[str, Any]:
        """Run the full analysis pipeline.

        Returns:
            Structured dict with the following keys:

            - scan: raw FileScanner output
            - parsed: list of PythonParser results (one per .py file)
            - graph: GraphBuilder output (nodes / edges / counts)
            - metrics: MetricsCalculator output
            - functions: aggregated list of {name, file, ...} across all files
            - classes: aggregated list of {name, file, methods, ...}
            - imports: aggregated list of {module, file, ...}
            - core_execute: info dict for a top-level `execute` function
              found in any file whose path contains "main.py", or None
            - meaningful_operations: always 0
        """
        # 1. Scan -----------------------------------------------------------------
        scan_result = self._scanner.scan()

        # 2. Parse all Python files -----------------------------------------------
        parsed_files: list[dict[str, Any]] = []
        for rel_path in scan_result.get("python_files", []):
            parsed = self._parser.parse_file(rel_path)
            parsed_files.append(parsed)

        # 3. Graph ----------------------------------------------------------------
        graph_data = self._graph_builder.build(parsed_files, scan_result)

        # 4. Metrics --------------------------------------------------------------
        metrics = self._metrics_calculator.calculate(
            scan_result, parsed_files, graph_data
        )

        # 5. Aggregate symbols ----------------------------------------------------
        all_functions: list[dict[str, Any]] = []
        all_classes: list[dict[str, Any]] = []
        all_imports: list[dict[str, Any]] = []
        core_execute: dict[str, Any] | None = None

        for pf in parsed_files:
            if pf.get("error"):
                continue

            file_path: str = pf.get("file", "")

            # Functions
            for fn in pf.get("functions", []):
                entry = dict(fn)
                entry["file"] = file_path
                all_functions.append(entry)

                # Detect core_execute: function named 'execute' in main.py
                if fn["name"] == "execute" and "main.py" in file_path:
                    if core_execute is None:
                        core_execute = dict(entry)

            # Classes
            for cls in pf.get("classes", []):
                entry = dict(cls)
                entry["file"] = file_path
                all_classes.append(entry)

            # Imports
            for imp in pf.get("imports", []):
                entry = dict(imp)
                entry["file"] = file_path
                all_imports.append(entry)

        return {
            "scan": scan_result,
            "parsed": parsed_files,
            "graph": graph_data,
            "metrics": metrics,
            "functions": all_functions,
            "classes": all_classes,
            "imports": all_imports,
            "core_execute": core_execute,
            "meaningful_operations": 0,
        }
