"""Heuristic prefilter — catches obvious jailbreak/injection patterns before
the LLM sees them. Saves an API call on the easy attacks. Conservative on
purpose: false negatives are fine (the prompt+context still defend), false
positives on legitimate Harry Potter questions are not.
"""

import re

from .prompts import REFUSAL

# Patterns we refuse outright. Each is a regex applied case-insensitively to
# the raw user message. Keep tight enough that "what is the system of Hogwarts
# houses?" does not trigger the system-prompt rule.
_JAILBREAK_PATTERNS = [
    r"\bignore (all |the |your )?(previous|prior|above|earlier) (instructions?|rules?|prompts?)\b",
    r"\bdisregard (all |the |your )?(previous|prior|above|earlier) (instructions?|rules?|prompts?)\b",
    r"\bforget (everything|all) (you|that you) (know|were told)\b",
    r"\b(reveal|show|print|output|tell me|repeat|leak) (your |the )?(system |initial |hidden )?(prompt|instructions?|rules?)\b",
    r"\bwhat (are|is) your (system )?(prompt|instructions?|rules?)\b",
    r"\bi am (the )?(admin|administrator|developer|owner|root|sudo)\b",
    r"\b(act|behave|pretend|roleplay) as (?!.*(harry|hermione|ron|dumbledore|hagrid|voldemort|snape))",
    r"\byou are (now|no longer) (?!hp-bot)",
    r"\bdan mode\b|\bdeveloper mode\b|\bjailbreak\b",
    r"\bwrite (me )?(a |some )?(python|javascript|code|script|program)\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _JAILBREAK_PATTERNS]


def is_jailbreak(message: str) -> bool:
    """True if the message matches a known jailbreak/injection pattern."""
    return any(p.search(message) for p in _COMPILED)


def guard(message: str) -> str | None:
    """Return refusal string if the message should be blocked, else None."""
    if is_jailbreak(message):
        return REFUSAL
    return None
