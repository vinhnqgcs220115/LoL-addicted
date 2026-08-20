from __future__ import annotations

from src.archetypes import (
    ARCHETYPES,
    BUILD_DEPENDENT,
    BUILD_DEPENDENT_LABEL,
    CHAMPION_ARCHETYPES,
    UNCLASSIFIED,
    champion_archetype,
    is_verdict_eligible,
)


def test_every_mapped_archetype_is_in_the_vocabulary() -> None:
    """A typo in an archetype name must not silently create a new bucket."""
    unknown = sorted(set(CHAMPION_ARCHETYPES.values()) - set(ARCHETYPES))
    assert unknown == []


def test_build_dependent_champions_are_not_also_mapped() -> None:
    """A champion held out for build dependence must not carry a static label."""
    overlap = sorted(BUILD_DEPENDENT & CHAMPION_ARCHETYPES.keys())
    assert overlap == []


def test_lookup_degrades_instead_of_raising() -> None:
    """An unseen champion shows up as unclassified rather than breaking a page."""
    assert champion_archetype("Ahri") == "Burst Mages"
    assert champion_archetype("Sylas") == BUILD_DEPENDENT_LABEL
    assert champion_archetype("NotAChampion") == UNCLASSIFIED


def test_only_real_archetypes_carry_a_verdict() -> None:
    """Held-out and unmapped groupings are reference only, never a verdict."""
    assert is_verdict_eligible("Assassins")
    assert not is_verdict_eligible(BUILD_DEPENDENT_LABEL)
    assert not is_verdict_eligible(UNCLASSIFIED)


def test_dropped_taxonomy_labels_stay_dropped() -> None:
    """Bruisers and Fighters overlap Divers/Juggernauts/Skirmishers by definition.

    They were removed by user decision; re-adding one would let two champions
    with the same playstyle land in different buckets.
    """
    assert "Bruisers" not in ARCHETYPES
    assert "Fighters" not in ARCHETYPES
    assert {"Divers", "Juggernauts", "Skirmishers"} <= set(ARCHETYPES)
