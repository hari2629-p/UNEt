"""Corporate buzzword and terminology generator for Void.

Produces high-assurance, enterprise-grade terminology designed to articulate
intentional null-state execution with maximum syntactic sophistication.
"""

from __future__ import annotations

import json
from pathlib import Path
import random
from typing import Any


class BuzzwordGenerator:
    """Generates synthetic enterprise terminology across successive generations."""

    def __init__(self, vocabulary_path: Path | str | None = None) -> None:
        """Initialize the generator and load the vocabulary.

        Args:
            vocabulary_path: Optional path to vocabulary.json. Defaults to
                the sibling vocabulary.json file in this package.
        """
        if vocabulary_path is None:
            vocabulary_path = Path(__file__).parent / "vocabulary.json"
        else:
            vocabulary_path = Path(vocabulary_path)

        with open(vocabulary_path, "r", encoding="utf-8") as f:
            self.vocabulary: dict[str, list[str]] = json.load(f)

        self.rng: random.Random = random.Random()

    def seed(self, generation: int) -> None:
        """Seed the pseudorandom generator for deterministic per-generation terms.

        Args:
            generation: Monotonically increasing generation index.
        """
        self.rng = random.Random(generation)

    def _choice(self, category: str) -> str:
        """Pick a pseudorandom term from a vocabulary category."""
        items = self.vocabulary.get(category, [])
        if not items:
            return ""
        return self.rng.choice(items)

    def phrase(self, style: str = "title") -> str:
        """Generate a single buzzword phrase based on the requested style.

        Args:
            style: One of 'title', 'capability', or 'engine'.

        Returns:
            A formatted corporate string.
        """
        if style == "title":
            template = self.rng.choice([
                "{adj} {mod_title} {noun}",
                "{adj} {noun} {noun_2}",
                "{mod_title} {adj} {noun}",
            ])
            return template.format(
                adj=self._choice("adjectives"),
                mod_title=self._choice("modifiers").replace("-", " ").title(),
                noun=self._choice("nouns"),
                noun_2=self._choice("nouns"),
            )

        if style == "capability":
            template = self.rng.choice([
                "{verb} {mod} {noun} across {adj_lower} {noun_2_lower}s",
                "{verb} {adj_lower} {noun_lower} utilizing {mod} paradigms",
                "{verb} {mod} {noun_lower} without compromising {adj_lower} equilibria",
                "{verb} {adj_lower} {noun_lower} pipelines for {mod} continuity",
            ])
            return template.format(
                verb=self._choice("verbs").capitalize(),
                mod=self._choice("modifiers"),
                noun=self._choice("nouns").lower(),
                noun_lower=self._choice("nouns").lower(),
                adj_lower=self._choice("adjectives").lower(),
                noun_2_lower=self._choice("nouns").lower(),
            )

        if style == "engine":
            template = self.rng.choice([
                "{adj} {noun} Engine",
                "{mod_title} {noun} Engine",
                "{adj} {mod_title} Processing Engine",
            ])
            return template.format(
                adj=self._choice("adjectives"),
                noun=self._choice("nouns"),
                mod_title=self._choice("modifiers").replace("-", " ").title(),
            )

        return f"{self._choice('adjectives')} {self._choice('nouns')}"

    def generate_set(
        self,
        generation: int = 1,
        project_metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate a complete terminology bundle for a documentation cycle.

        Args:
            generation: Documentation generation epoch.
            project_metrics: Optional metrics dict from ProjectAnalyzer.

        Returns:
            Dictionary containing primary_term, secondary_term, tagline,
            capabilities, architecture_name, engine_name, and generation.
        """
        self.seed(generation)

        primary_term = self.phrase("title")
        mod = self._choice("modifiers").replace("-", " ").title()
        secondary_term = f"{mod} {self._choice('nouns')}"
        tagline = self._choice("taglines")

        capabilities = [self.phrase("capability") for _ in range(5)]
        architecture_name = (
            f"{self._choice('adjectives')} {self._choice('nouns')} Architecture"
        )
        engine_name = self.phrase("engine")

        return {
            "primary_term": primary_term,
            "secondary_term": secondary_term,
            "tagline": tagline,
            "capabilities": capabilities,
            "architecture_name": architecture_name,
            "engine_name": engine_name,
            "generation": generation,
        }
