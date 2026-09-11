"""State manager for Void.

Persists and manages metadata across generation cycles in `.void/state.json`.
Guarantees high-assurance fault tolerance: missing or corrupt state files
gracefully recover to generation 0 defaults without interrupting execution.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


class StateManager:
    """Manages persistent generation state and documentation history."""

    def __init__(
        self,
        root: Path | str | None = None,
        state_file: Path | str | None = None,
    ) -> None:
        """Initialize StateManager.

        Args:
            root: Root path of the repository. Defaults to cwd.
            state_file: Optional explicit path to state.json. Defaults to `.void/state.json`.
        """
        self.root = Path(root) if root else Path.cwd()
        if state_file:
            self.state_file = Path(state_file)
        else:
            self.state_file = self.root / ".void" / "state.json"

        self.generation: int = 0
        self.previous_terms: list[str] = []
        self.history: list[dict[str, Any]] = []
        self.last_docs: dict[str, Any] | str | None = None
        self.last_metrics: dict[str, Any] = {}
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.updated_at: str = datetime.now(timezone.utc).isoformat()

        self.load()

    def _default_state(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "generation": 0,
            "previous_terms": [],
            "history": [],
            "last_docs": {},
            "last_metrics": {},
            "created_at": now,
            "updated_at": now,
        }

    def load(self) -> dict[str, Any]:
        """Load state from disk. Recovers gracefully to defaults if missing or corrupt."""
        defaults = self._default_state()
        if not self.state_file.is_file():
            self._apply_state(defaults)
            return defaults

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = defaults
        except Exception:
            data = defaults

        self._apply_state(data)
        return data

    def _apply_state(self, data: dict[str, Any]) -> None:
        self.generation = int(data.get("generation", 0))
        self.previous_terms = list(data.get("previous_terms", []))
        self.history = list(data.get("history", []))
        self.last_docs = data.get("last_docs", {})
        self.last_metrics = dict(data.get("last_metrics", {}))
        self.created_at = str(data.get("created_at") or datetime.now(timezone.utc).isoformat())
        self.updated_at = str(data.get("updated_at") or datetime.now(timezone.utc).isoformat())

    def save(self) -> None:
        """Persist state to .void/state.json."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "generation": self.generation,
                "previous_terms": self.previous_terms,
                "history": self.history,
                "last_docs": self.last_docs,
                "last_metrics": self.last_metrics,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            # Fault-tolerant write; do not crash runtime
            pass

    def next_generation(self) -> int:
        """Increment generation count, update timestamp, save, and return the new generation."""
        self.generation += 1
        self.updated_at = datetime.now(timezone.utc).isoformat()
        self.save()
        return self.generation

    def record_generation(
        self,
        generation: int,
        terms: dict[str, Any],
        metrics: dict[str, Any],
        docs: dict[str, Any] | str,
        drift: float = 0.0,
    ) -> dict[str, Any]:
        """Record a completed documentation generation cycle.

        Args:
            generation: The generation index.
            terms: Generated buzzword terminology dictionary.
            metrics: Computed repository metrics dictionary.
            docs: Dictionary of document contents or primary doc string.
            drift: Documentation drift percentage relative to previous cycle.

        Returns:
            The recorded history entry.
        """
        now = datetime.now(timezone.utc).isoformat()
        self.generation = generation
        primary_term = terms.get("primary_term", "") if isinstance(terms, dict) else str(terms)
        if primary_term and primary_term not in self.previous_terms:
            self.previous_terms.append(primary_term)

        entry = {
            "generation": generation,
            "primary_term": primary_term,
            "terms": terms,
            "metrics": metrics,
            "drift": drift,
            "timestamp": now,
        }

        self.history.append(entry)
        self.last_docs = docs
        self.last_metrics = metrics
        self.updated_at = now
        self.save()
        return entry

    def get_history(self) -> list[dict[str, Any]]:
        """Return full generation history."""
        return list(self.history)

    def get_last_docs(self) -> dict[str, Any] | str | None:
        """Return the most recently recorded documentation payload."""
        if self.last_docs:
            return self.last_docs

        # Fallback to existing disk README if state is empty but doc exists
        readme_path = self.root / "docs" / "README.md"
        if readme_path.is_file():
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    return {"readme": f.read()}
            except Exception:
                pass

        return None
