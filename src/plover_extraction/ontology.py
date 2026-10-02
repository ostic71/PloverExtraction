"""Canonical Plover categories, event types, and human-readable definitions."""

from typing import Final, Literal, TypeAlias

PloverCategory: TypeAlias = Literal[
    "THREATEN", "PROTEST", "MOBILIZE", "COERCE", "ASSAULT"
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
}

PLOVER_CATEGORY_DESCRIPTIONS: Final[dict[PloverCategory, str]] = {
    "THREATEN": "Communicate an adverse consequence directed at a target, conditionally or unconditionally, to intimidate or compel. The communication has occurred; the threatened action need not occur. A demand without an adverse consequence, hostile commentary, risk forecast, or announcement of military plans alone is insufficient.",
    "PROTEST": "Carry out public or collective dissent through demonstrations, strikes, hunger strikes, boycotts, obstruction, or riots. A hunger strike may involve one person. Violence integral to a riot remains PROTEST; do not duplicate that same act as ASSAULT. Separately evaluate police violence or arrests. Hunger caused by food deprivation is not a hunger strike.",
    "MOBILIZE": "Actually deploy, reinforce, mobilize, or increase readiness of military, police, armed groups, or military hardware, including exercises already underway. Training fire or simulated attacks are not ASSAULT. A planned exercise, equipment inventory, or existing deployment alone does not establish a new mobilization; actual attacks on real opponents belong to ASSAULT.",
    "COERCE": "Implement coercive control through arrest, detention, seizure, deportation, restrictions, censorship, cyber intrusion, or withholding essentials, below substantial physical violence. An expressly imposed emergency or effective curfew qualifies. An arrest warrant or order alone does not establish an arrest. Beating, torture, kidnapping, hostage-taking, and combat capture belong to ASSAULT.",
    "ASSAULT": "Carry out or physically attempt deliberate violence against people or property: shooting, bombing, shelling, beating, torture, sexual violence, abduction, hostage-taking, or combat capture. Police perpetrators do not make violence COERCE. Distinguish custodial arrest, training simulations, and violence integral to a PROTEST riot. Existing territorial control alone does not establish a new attack.",
}

MODE_DESCRIPTIONS: Final[dict[PloverCategory, dict[str, str]]] = {
    "THREATEN": {
        "Territory": "Threaten occupation or seizure of control over all or part of a territory.",
        "Arrest": "Threaten arrest, detention, or imprisonment; includes an in-absentia arrest not physically enforced.",
        "Relations": "Threaten to suspend relations or ongoing talks, meetings, or negotiations.",
        "Expel": "Threaten expulsion of diplomats, peacekeepers, or NGOs.",
        "Violence": "Threaten physical violence; hostile language alone is insufficient.",
        "Restrict": "Threaten restrictions on movement of people or goods, including boycotts, strikes, blockades, curfews, economic sanctions, tariffs, trade embargoes, or bans on political activity.",
    },
    "PROTEST": {
        "Riot": "Violent collective protest whose participants intend physical injury or property damage.",
        "Demo": "An organized, continuous, largely peaceful public demonstration or rally against an actor or policy.",
        "Strike": "Collective withdrawal of labor or abandonment of workplaces as protest.",
        "Hunger": "Refusal of food as protest; involuntary hunger is insufficient.",
        "Boycott": "Protest through withdrawal of commercial or social relations with an activity, person, country, or organization.",
        "Obstruct": "Protest by physically obstructing passage or access to a location.",
        "Vandalize": "Damage or destroy property as a symbolic protest act rather than destruction incidental to a riot.",
    },
    "MOBILIZE": {
        "Troops": "Mobilize armed personnel or military units without actual combat; distinguish police and non-state militias.",
        "Weapons": "Mobilize or increase readiness of weapon systems, military ships, aircraft, or vehicles.",
        "Militia": "Mobilize or increase readiness of a non-state entity with significant military capability.",
        "Police": "Mobilize or increase readiness of police or security units.",
    },
    "COERCE": {
        "Martial-law": "Impose a state-of-emergency or martial-law regime.",
        "Seize": "Execute a search or raid, or confiscate property.",
        "Restrict": "Impose restrictions on political freedoms or movement.",
        "Arrest": "Arrest, detain, or imprison; excludes combat capture and in-absentia arrest.",
        "Deport": "Expel or deport individuals from a territory.",
        "Withhold": "Withhold public goods or essential physical services.",
        "Cyber": "Conduct a cyberattack or cybercrime.",
        "Censor": "Censor, ban, or restrict access to publications or information.",
        "Curfew": "Impose or enforce a curfew.",
        "Misinformation": "Conduct a specific deception, manipulation, or misinformation operation.",
    },
    "ASSAULT": {
        "Unconventional": "Use chemical, biological, radiological, or nuclear weapons.",
        "Targeted": "Attempt or carry out assassination, execution, or deliberate mass killing of defenseless people.",
        "Suicide-attack": "An individual or vehicle attack explicitly involving the attacker's suicide.",
        "Aerial": "Attack using manned aircraft or helicopters.",
        "Drone": "Attack using unmanned aerial vehicles or drones.",
        "Heavy-weapons": "Attack using artillery, rocket launchers, armored vehicles, tanks, or comparable heavy weapons.",
        "Firearms": "Attack using rifles, pistols, light machine guns, or comparable small arms.",
        "Explosives": "Use explosives outside heavy weapons, including mines, IEDs, and car bombs.",
        "Abduct": "Abduct, kidnap, hijack, or capture enemy combatants during armed conflict.",
        "Torture": "Inflict torture; do not infer it from detention or injury alone.",
        "Sexual": "Commit rape or other sexual violence.",
        "Destroy": "Intentionally destroy property; also applies when the attack method is unknown.",
        "Primitive": "Attack using fire, edged weapons, rocks, farm implements, or blunt instruments.",
        "Beat": "Bodily assault by one-off or repeated blows.",
        "Crowd-control": "Use explicit less-lethal crowd-control weapons or tactics.",
    },
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
