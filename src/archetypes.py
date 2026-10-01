"""Champion archetype taxonomy for mid-lane matchup analysis.

Domain constants only. This module reads nothing and computes nothing; it maps
champion names to the archetype vocabulary defined in ARCHETYPES below so
matchup analysis can group opponents into buckets large enough to support a
verdict. Pair-level slices in this dataset run 2-9 games and never will.

Assignments here are domain judgments and are owned by the user. Riot's Data
Dragon `tags` are deliberately not used as the source: they conflate "can be
played support" with class identity (it returns Mage/Support for Hwei and
Orianna) and carry no burst-versus-control distinction, which is the exact
split mid-lane matchup analysis depends on.

Correct a champion by editing CHAMPION_ARCHETYPES. Nothing else needs to change.
"""

from __future__ import annotations

# The original product spec listed Bruisers and Fighters alongside Divers,
# Juggernauts, and Skirmishers. Riot's Fighter class *is* Divers plus
# Juggernauts and "bruiser" is colloquial for the same group, so the redundant
# labels are dropped per the user's decision: only the specific subclasses are
# used, and no champion can be ambiguous between a class and its own subclass.
ARCHETYPES: tuple[str, ...] = (
    "Burst Mages",
    "Control Mages",
    "Artillery",
    "Assassins",
    "Skirmishers",
    "Divers",
    "Juggernauts",
    "Tanks",
    "Marksmen",
    "Enchanters",
    "Catchers",
    "Specialists",
)

UNCLASSIFIED: str = "Unclassified"

#: Archetype depends on the build taken in that specific game, so a static
#: champion-level label would be wrong. These are excluded from archetype
#: aggregates rather than forced into a bucket they would distort; they keep
#: their own champion-level verdict, which is unaffected by this question.
#: Resolving them properly needs per-game item data. Items are present in the
#: raw match JSON and are not parsed into DuckDB yet; parsing item buys is
#: part of the per-game timeline work (ROADMAP.md, M2).
BUILD_DEPENDENT: frozenset[str] = frozenset({"Sylas"})

BUILD_DEPENDENT_LABEL: str = "Build-dependent"

CHAMPION_ARCHETYPES: dict[str, str] = {
    # --- Burst Mages: front-loaded damage in a single combo window
    "Ahri": "Burst Mages",
    "Annie": "Burst Mages",
    "Aurora": "Burst Mages",
    "Brand": "Burst Mages",
    "Lissandra": "Burst Mages",
    "Lux": "Burst Mages",
    "Mel": "Burst Mages",
    "Orianna": "Burst Mages",
    "Syndra": "Burst Mages",
    "Veigar": "Burst Mages",
    "Vex": "Burst Mages",
    "Zoe": "Burst Mages",
    # --- Control Mages: sustained damage and zone denial, scale with items
    "Anivia": "Control Mages",
    "AurelionSol": "Control Mages",
    "Cassiopeia": "Control Mages",
    "Hwei": "Control Mages",
    "Malzahar": "Control Mages",
    "Rumble": "Control Mages",
    "Ryze": "Control Mages",
    "Swain": "Control Mages",
    "Taliyah": "Control Mages",
    "Viktor": "Control Mages",
    "Vladimir": "Control Mages",
    # --- Artillery: damage from outside the opponent's threat range
    "Xerath": "Artillery",
    # --- Assassins: mobility onto a single priority target
    "Akali": "Assassins",
    "Diana": "Assassins",
    "Ekko": "Assassins",
    "Fizz": "Assassins",
    "Kassadin": "Assassins",
    "Katarina": "Assassins",
    "Khazix": "Assassins",
    "Leblanc": "Assassins",
    "Locke": "Assassins",
    "Naafiri": "Assassins",
    "Pyke": "Assassins",
    "Qiyana": "Assassins",
    "Talon": "Assassins",
    "Zed": "Assassins",
    # --- Skirmishers: sustained melee duelling, no hard engage
    "Irelia": "Skirmishers",
    "Tryndamere": "Skirmishers",
    "Yasuo": "Skirmishers",
    "Yone": "Skirmishers",
    # --- Divers: commit onto a target and survive the follow-up
    "Renekton": "Divers",
    # --- Juggernauts: no mobility, immense close-range threat
    "Singed": "Juggernauts",
    "Sion": "Juggernauts",
    # --- Tanks
    "Galio": "Tanks",
    "Nunu": "Tanks",
    # --- Marksmen: sustained ranged auto-attack damage
    "Ezreal": "Marksmen",
    "Kaisa": "Marksmen",
    "KogMaw": "Marksmen",
    "Quinn": "Marksmen",
    "Smolder": "Marksmen",
    "Tristana": "Marksmen",
    "Yunara": "Marksmen",
    # --- Enchanters
    "Sona": "Enchanters",
    "Zilean": "Enchanters",
    # --- Catchers: land a hard point of crowd control to start a fight
    "Morgana": "Catchers",
    # --- Specialists: kits that do not fit the classes above
    "Azir": "Specialists",
    "Jayce": "Specialists",
    "Kayle": "Specialists",
    "TwistedFate": "Specialists",
}


def champion_archetype(champion_name: str) -> str:
    """Return the archetype for a champion.

    Build-dependent champions return ``BUILD_DEPENDENT_LABEL`` and unknown
    champions return ``UNCLASSIFIED``. Neither raises: a champion appearing for
    the first time must not break the dashboard, it must show up as unclassified
    so it can be added deliberately.
    """
    if champion_name in BUILD_DEPENDENT:
        return BUILD_DEPENDENT_LABEL
    return CHAMPION_ARCHETYPES.get(champion_name, UNCLASSIFIED)


def is_verdict_eligible(archetype: str) -> bool:
    """Whether an archetype bucket may carry a directional verdict.

    Build-dependent and unclassified groupings are reference only: the first
    mixes playstyles that a single label misrepresents, the second is a bag of
    whatever has not been mapped yet.
    """
    return archetype in ARCHETYPES
