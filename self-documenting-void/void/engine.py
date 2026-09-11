"""Void Engine — centralized orchestration pipeline.

Unifies repository analysis, synthetic corporate terminology generation,
documentation synthesis (README, Architecture, API, Changelog), drift
measurement, and persistent state management into a single deterministic harness.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from void.analysis import ProjectAnalyzer, MetricsCalculator
from void.buzzwords import BuzzwordGenerator
from void.generators import (
    ReadmeGenerator,
    ArchitectureGenerator,
    ApiGenerator,
    ChangelogGenerator,
)
from void.state import StateManager


class VoidEngine:
    """Core orchestration engine coordinating documentation cycles and quiescence."""

    def __init__(self, root: Path | str | None = None) -> None:
        """Initialize VoidEngine.

        Args:
            root: Root path of the repository. Defaults to cwd.
        """
        self.root = Path(root) if root else Path.cwd()
        self.analyzer = ProjectAnalyzer(root=self.root)
        self.buzzword_gen = BuzzwordGenerator()
        self.readme_gen = ReadmeGenerator(root=self.root)
        self.arch_gen = ArchitectureGenerator(root=self.root)
        self.api_gen = ApiGenerator(root=self.root)
        self.changelog_gen = ChangelogGenerator(root=self.root)
        self.state_manager = StateManager(root=self.root)
        self.metrics_calculator = MetricsCalculator()

    def analyze(self) -> dict[str, Any]:
        """Perform comprehensive repository analysis via ProjectAnalyzer."""
        return self.analyzer.analyze()

    def status(self) -> dict[str, Any]:
        """Return high-level operational status and generation metrics."""
        self.state_manager.load()
        history = self.state_manager.get_history()
        last_record = history[-1] if history else {}

        if self.state_manager.previous_terms:
            primary_term = self.state_manager.previous_terms[-1]
        elif last_record.get("primary_term"):
            primary_term = last_record["primary_term"]
        else:
            primary_term = "Void Inactivity Core"

        last_metrics = self.state_manager.last_metrics
        if not last_metrics:
            analysis = self.analyzer.analyze()
            last_metrics = analysis.get("metrics", {})

        drift = float(last_record.get("drift", 0.0))

        return {
            "generation": self.state_manager.generation,
            "primary_term": primary_term,
            "metrics": last_metrics,
            "drift": drift,
            "functional_drift": 0.0,
            "meaningful_operations": 0,
        }

    def generate(
        self,
        progress_callback: Callable[[str, str], None] | Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """Execute a complete documentation synthesis and drift analysis cycle.

        Args:
            progress_callback: Optional callback invoked as each step concludes.

        Returns:
            Dictionary containing generation telemetry, buzzwords, analysis,
            written document paths, and computed drift.
        """
        def _report(step: str, status_text: str = "DONE") -> None:
            line = f"{step:.<27} {status_text}"
            if progress_callback is not None:
                try:
                    progress_callback(step, status_text)
                except TypeError:
                    progress_callback(line)
            else:
                print(line)

        # 1. Analyze repository
        analysis = self.analyzer.analyze()
        _report("Scanning repository", "DONE")
        _report("Analyzing architecture", "DONE")

        # 2. Advance generation
        generation = self.state_manager.next_generation()

        # 3. Generate buzzwords
        terms = self.buzzword_gen.generate_set(generation, analysis.get("metrics"))
        _report("Generating terminology", "DONE")

        # 4. Generate + write documents
        # Retrieve previous README for drift analysis
        last_docs = self.state_manager.get_last_docs()
        if isinstance(last_docs, dict):
            prev_readme = last_docs.get("readme", "")
        elif isinstance(last_docs, str):
            prev_readme = last_docs
        else:
            prev_readme = ""

        # README
        readme_content = self.readme_gen.generate(analysis, terms, generation)
        readme_path = self.readme_gen.write(readme_content)
        _report("Updating README", "DONE")

        # Architecture
        arch_content = self.arch_gen.generate(analysis, terms, generation)
        arch_path = self.arch_gen.write(arch_content)
        _report("Updating Architecture", "DONE")

        # API
        api_content = self.api_gen.generate(analysis, terms, generation)
        api_path = self.api_gen.write(api_content)
        _report("Updating API", "DONE")

        # Changelog
        changelog_content = self.changelog_gen.generate(
            analysis, terms, generation, history=self.state_manager.get_history()
        )
        changelog_path = self.changelog_gen.write(changelog_content)
        _report("Updating Changelog", "DONE")

        # 5. Compute documentation drift
        if prev_readme:
            drift = self.metrics_calculator.compute_drift(prev_readme, readme_content)
        else:
            drift = 0.0

        # 6. Record generation in state
        docs_payload = {
            "readme": readme_content,
            "architecture": arch_content,
            "api": api_content,
            "changelog": changelog_content,
        }
        self.state_manager.record_generation(
            generation=generation,
            terms=terms,
            metrics=analysis.get("metrics", {}),
            docs=docs_payload,
            drift=drift,
        )

        _report("Meaningful work", "SKIPPED")

        now = datetime.now(timezone.utc).isoformat()
        return {
            "generation": generation,
            "terms": terms,
            "analysis": analysis,
            "metrics": analysis.get("metrics", {}),
            "drift": drift,
            "functional_drift": 0.0,
            "paths": {
                "readme": str(readme_path),
                "architecture": str(arch_path),
                "api": str(api_path),
                "changelog": str(changelog_path),
            },
            "timestamp": now,
        }
