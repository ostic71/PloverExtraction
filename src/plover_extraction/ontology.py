"""Canonical Plover category/type relationships; descriptions live in YAML."""

from typing import Final, Literal, TypeAlias

PloverCategory: TypeAlias = Literal[
    "THREATEN", "PROTEST", "MOBILIZE", "COERCE", "ASSAULT", "APOLITICAL"
]

PLOVER_ONTOLOGY: Final[dict[PloverCategory, tuple[str | None, ...]]] = {
    "THREATEN": ("Territory", None, "Arrest", "Relations", "Expel", "Violence", "Restrict"),
    "PROTEST": ("Riot", None, "Demo", "Strike", "Hunger", "Boycott", "Obstruct"),
    "MOBILIZE": ("Troops", "Weapons", "Militia", None, "Police"),
    "COERCE": (
        "Martial-law", None, "Seize", "Restrict", "Arrest", "Deport",
        "Withhold", "Cyber", "Censor", "Curfew", "Misinformation",
    ),
    "ASSAULT": (
        "Unconventional", "Targeted", "Suicide-attack", "Aerial", "Drone",
        "Heavy-weapons", None, "Firearms", "Explosives", "Abduct", "Torture",
        "Sexual", "Destroy", "Primitive", "Beat", "Crowd-control",
    ),
    "APOLITICAL": ("natural_disaster", "epidemic"),
}

def validate_event_type(category: str, event_type: str | None) -> None:
    """Raise ``ValueError`` unless category and event type form a valid pair."""
    if category not in PLOVER_ONTOLOGY:
        allowed = ", ".join(PLOVER_ONTOLOGY)
        raise ValueError(f"Unknown category {category!r}; expected one of: {allowed}")
    if event_type not in PLOVER_ONTOLOGY[category]:
        allowed = ", ".join(value or "null" for value in PLOVER_ONTOLOGY[category])
        raise ValueError(
            f"Invalid event_type {event_type!r} for {category}; expected one of: {allowed}"
        )
