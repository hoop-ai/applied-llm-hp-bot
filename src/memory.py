"""Conversation memory: last-N turns with simple summarization once we exceed N.

Each turn is (user, assistant). When the buffer would exceed MEMORY_TURNS,
the oldest turn is folded into a running 1-line summary so we keep long-range
pronoun anchors without inflating the prompt.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Turn:
    user: str
    assistant: str


@dataclass
class Memory:
    turns: list[Turn] = field(default_factory=list)
    summary: str = ""

    def append(self, user: str, assistant: str) -> None:
        self.turns.append(Turn(user=user, assistant=assistant))
        max_turns = int(os.getenv("MEMORY_TURNS", "5"))
        while len(self.turns) > max_turns:
            oldest = self.turns.pop(0)
            self._fold(oldest)

    def _fold(self, t: Turn) -> None:
        """Compress one turn into the running summary, capped to ~200 chars."""
        snippet = f"User asked: {t.user[:80]}. Assistant answered: {t.assistant[:80]}."
        if self.summary:
            self.summary = (self.summary + " " + snippet)[-400:]
        else:
            self.summary = snippet

    def render(self) -> str:
        """Format for inclusion in the LLM prompt."""
        if not self.turns and not self.summary:
            return ""
        parts: list[str] = []
        if self.summary:
            parts.append(f"[earlier conversation summary] {self.summary}")
        for t in self.turns:
            parts.append(f"User: {t.user}")
            parts.append(f"Assistant: {t.assistant}")
        return "\n".join(parts)
