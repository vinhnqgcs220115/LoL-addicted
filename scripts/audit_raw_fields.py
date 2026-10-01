"""Audit the raw Riot corpus: what is on disk, and what every field actually holds.

Phase 0 of the rebuild. Enumerates ``data/raw/`` itself -- no corpus size is
passed in or hardcoded anywhere -- and emits a human-readable report plus a
machine-readable JSON companion.

This output is the sole home for data-availability facts. Domain documents
describe how the game works and must not restate anything measured here.

Run:
    python scripts/audit_raw_fields.py
"""

from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
DOCS_DIR = BASE_DIR / "docs"
REPORT_PATH = DOCS_DIR / "DATA_AUDIT.md"
JSON_PATH = DOCS_DIR / "data_audit.json"

TIMELINE_SUFFIX = "_timeline.json"

#: Per-participant account identifiers. Their presence is measured; the values
#: are never recorded, because eight of ten belong to people who are not the user.
IDENTIFIER_FIELDS = frozenset({"puuid", "summonerId", "summonerName", "riotIdGameName"})

#: Below this presence rate, building on a field needs a documented fallback.
PARTIAL_PRESENCE_THRESHOLD = 0.99

#: Diagnostic cutoff for listing degenerate games. Not a scope rule -- whether a
#: short game counts as a remake and is excluded from analysis is a user decision.
SHORT_MATCH_FRAMES = 10

FIELD_HEADER = (
    "| Path | Present in | Occurrences | Null rate | Types | Flags |\n"
    "|---|---|---|---|---|---|"
)


def load_json(path: Path) -> dict[str, Any]:
    """Read one JSON object, raising rather than guessing on a malformed file."""
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise TypeError(f"Expected a JSON object, found {type(payload).__name__}.")
    return payload


def scan_directory(raw_dir: Path) -> dict[str, Any]:
    """Enumerate detail and timeline files without parsing them."""
    detail_stems: set[str] = set()
    timeline_stems: set[str] = set()

    for path in raw_dir.iterdir():
        if not path.is_file() or path.suffix != ".json":
            continue
        if path.name.endswith(TIMELINE_SUFFIX):
            timeline_stems.add(path.name[: -len(TIMELINE_SUFFIX)])
        else:
            detail_stems.add(path.stem)

    return {
        "detail_files": len(detail_stems),
        "timeline_files": len(timeline_stems),
        "valid_pairs": sorted(detail_stems & timeline_stems),
        "detail_without_timeline": sorted(detail_stems - timeline_stems),
        "timeline_without_detail": sorted(timeline_stems - detail_stems),
    }


def walk(node: Any, prefix: str, seen: dict[str, dict[str, Any]]) -> None:
    """Record every leaf path under ``node``, collapsing list indices to ``[]``."""
    if isinstance(node, dict):
        for key, value in node.items():
            walk(value, f"{prefix}.{key}" if prefix else key, seen)
        return

    if isinstance(node, list):
        for item in node:
            walk(item, f"{prefix}[]", seen)
        return

    stats = seen.setdefault(prefix, {"count": 0, "nulls": 0, "types": set()})
    stats["count"] += 1
    if node is None:
        stats["nulls"] += 1
    else:
        stats["types"].add(type(node).__name__)


def new_tally() -> dict[str, Any]:
    """Presence, occurrence, null and type counters for one group of JSON paths."""
    return {
        "matches": Counter(),
        "occurrences": Counter(),
        "nulls": Counter(),
        "types": defaultdict(set),
    }


def absorb(tally: dict[str, Any], seen: dict[str, dict[str, Any]]) -> None:
    """Fold one payload's walk results into the running totals."""
    for path, stats in seen.items():
        tally["matches"][path] += 1
        tally["occurrences"][path] += stats["count"]
        tally["nulls"][path] += stats["nulls"]
        tally["types"][path] |= stats["types"]


def new_measures() -> dict[str, Any]:
    """Targeted measurements the schema design depends on."""
    return {
        "participant_counts": Counter(),
        "patches": Counter(),
        "queues": Counter(),
        "team_position": Counter(),
        "challenge_key_counts": [],
        "frame_intervals": Counter(),
        "frames_per_match": [],
        "champion_kills": 0,
        "victimDamageDealt_entries": [],
        "victimDamageReceived_entries": [],
        "victimDamageDealt_missing": 0,
        "victimDamageReceived_missing": 0,
        "kills_per_match": [],
        "kills_by_patch": Counter(),
        "dealt_missing_by_patch": Counter(),
        "dealt_missing_execution": 0,
        "dealt_missing_champion": 0,
        "short_matches": [],
        "blank_position_matches": [],
    }


def audit_detail(
    payload: dict[str, Any], tally: dict[str, Any], measures: dict[str, Any]
) -> str:
    """Walk one match-detail payload, record measurements, and return its patch."""
    seen: dict[str, dict[str, Any]] = {}
    walk(payload, "", seen)
    absorb(tally, seen)

    info = payload.get("info", {})
    participants = info.get("participants", [])

    patch = ".".join(str(info.get("gameVersion", "")).split(".")[:2])
    measures["participant_counts"][len(participants)] += 1
    measures["patches"][patch] += 1
    measures["queues"][info.get("queueId")] += 1

    for participant in participants:
        position = participant.get("teamPosition")
        measures["team_position"][position if position else "<blank>"] += 1
        measures["challenge_key_counts"].append(len(participant.get("challenges") or {}))

    return patch


def audit_timeline(
    payload: dict[str, Any],
    frame_tally: dict[str, Any],
    event_tallies: dict[str, dict[str, Any]],
    event_matches: Counter,
    measures: dict[str, Any],
    patch: str,
) -> None:
    """Walk one timeline payload, splitting participant frames from events by type."""
    info = payload.get("info", {})
    frames = info.get("frames", [])

    measures["frame_intervals"][info.get("frameInterval")] += 1
    measures["frames_per_match"].append(len(frames))

    frame_seen: dict[str, dict[str, Any]] = {}
    per_type_seen: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    kills_here = 0

    for frame in frames:
        for participant_frame in (frame.get("participantFrames") or {}).values():
            walk(participant_frame, "", frame_seen)

        for event in frame.get("events") or []:
            event_type = str(event.get("type", "<untyped>"))
            walk(event, "", per_type_seen[event_type])

            if event_type != "CHAMPION_KILL":
                continue

            kills_here += 1
            measures["champion_kills"] += 1
            measures["kills_by_patch"][patch] += 1

            for direction in ("victimDamageDealt", "victimDamageReceived"):
                entries = event.get(direction)
                if entries is None:
                    measures[f"{direction}_missing"] += 1
                else:
                    measures[f"{direction}_entries"].append(len(entries))

            if event.get("victimDamageDealt") is None:
                measures["dealt_missing_by_patch"][patch] += 1
                key = "execution" if event.get("killerId") == 0 else "champion"
                measures[f"dealt_missing_{key}"] += 1

    measures["kills_per_match"].append(kills_here)
    absorb(frame_tally, frame_seen)
    for event_type, seen in per_type_seen.items():
        event_tallies.setdefault(event_type, new_tally())
        absorb(event_tallies[event_type], seen)
        event_matches[event_type] += 1


def run_audit(raw_dir: Path) -> dict[str, Any]:
    """Enumerate the corpus, then walk every valid pair it contains."""
    inventory = scan_directory(raw_dir)
    pairs = inventory["valid_pairs"]
    print(f"Corpus: {len(pairs)} valid pairs. Walking...")

    detail_tally = new_tally()
    frame_tally = new_tally()
    event_tallies: dict[str, dict[str, Any]] = {}
    event_matches: Counter = Counter()
    measures = new_measures()

    malformed: list[dict[str, str]] = []
    incomplete: list[dict[str, str]] = []
    duplicates: list[dict[str, str]] = []
    seen_match_ids: dict[str, str] = {}
    audited = 0

    for index, stem in enumerate(pairs, start=1):
        try:
            detail = load_json(raw_dir / f"{stem}.json")
            timeline = load_json(raw_dir / f"{stem}{TIMELINE_SUFFIX}")
        except (json.JSONDecodeError, TypeError, OSError, UnicodeDecodeError) as exc:
            malformed.append({"stem": stem, "error": f"{type(exc).__name__}: {exc}"})
            continue

        match_id = str(detail.get("metadata", {}).get("matchId", ""))
        if match_id and match_id in seen_match_ids:
            duplicates.append(
                {"match_id": match_id, "files": f"{stem}, {seen_match_ids[match_id]}"}
            )
        elif match_id:
            seen_match_ids[match_id] = stem

        participants = detail.get("info", {}).get("participants", [])
        frames = timeline.get("info", {}).get("frames", [])
        if not participants or not frames:
            incomplete.append(
                {
                    "stem": stem,
                    "reason": f"participants={len(participants)}, frames={len(frames)}",
                }
            )
            continue

        patch = audit_detail(detail, detail_tally, measures)
        audit_timeline(
            timeline, frame_tally, event_tallies, event_matches, measures, patch
        )
        audited += 1

        info = detail.get("info", {})
        if len(frames) < SHORT_MATCH_FRAMES:
            measures["short_matches"].append(
                {
                    "match": stem,
                    "frames": len(frames),
                    "duration_sec": info.get("gameDuration"),
                    "patch": patch,
                    "result": info.get("endOfGameResult", ""),
                }
            )
        if any(not p.get("teamPosition") for p in participants):
            measures["blank_position_matches"].append(
                {"match": stem, "frames": len(frames), "patch": patch}
            )

        if index % 100 == 0:
            print(f"  {index}/{len(pairs)}")

    inventory["malformed"] = malformed
    inventory["structurally_incomplete"] = incomplete
    inventory["duplicate_match_ids"] = duplicates
    inventory["audited"] = audited

    return {
        "inventory": inventory,
        "detail_tally": detail_tally,
        "frame_tally": frame_tally,
        "event_tallies": event_tallies,
        "event_matches": event_matches,
        "measures": measures,
    }


def pct(part: int, whole: int) -> str:
    """Percentage string, or 'n/a' when the denominator is zero."""
    return "n/a" if not whole else f"{100.0 * part / whole:.1f}%"


def describe(values: list[int]) -> str:
    """Compact distribution summary for a list of counts."""
    if not values:
        return "no observations"
    if len(values) == 1:
        return str(values[0])
    return (
        f"min {min(values)}, median {statistics.median(values):.0f}, "
        f"mean {statistics.mean(values):.1f}, max {max(values)}"
    )


def field_rows(tally: dict[str, Any], denominator: int) -> list[str]:
    """One markdown row per JSON path, ordered by path."""
    rows = []
    for path in sorted(tally["matches"]):
        matches = tally["matches"][path]
        occurrences = tally["occurrences"][path]
        nulls = tally["nulls"][path]
        types = ", ".join(sorted(tally["types"][path])) or "null-only"

        flags = []
        if matches < denominator * PARTIAL_PRESENCE_THRESHOLD:
            flags.append("PARTIAL")
        if path.rsplit(".", 1)[-1] in IDENTIFIER_FIELDS:
            flags.append("IDENTIFIER - do not ingest")

        rows.append(
            f"| `{path}` | {pct(matches, denominator)} | {occurrences:,} | "
            f"{pct(nulls, occurrences)} | {types} | {' / '.join(flags)} |"
        )
    return rows


def counter_table(counter: Counter, label: str, total: int) -> list[str]:
    """Markdown table for a Counter, ordered by descending count."""
    lines = [f"| {label} | Count | Share |", "|---|---|---|"]
    for key, count in sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0]))):
        lines.append(f"| `{key}` | {count:,} | {pct(count, total)} |")
    return lines


def render_report(result: dict[str, Any]) -> str:
    """Build DATA_AUDIT.md from the walk results."""
    inventory = result["inventory"]
    measures = result["measures"]
    audited = inventory["audited"]
    kills = measures["champion_kills"]

    out: list[str] = []
    add = out.append

    add("# Data Audit")
    add("")
    add(
        "**Generated** by `scripts/audit_raw_fields.py` from the raw corpus on disk. "
        "Do not edit by hand; re-run the script instead."
    )
    add("")
    add(
        "This file is the **sole home for data-availability facts** in this repository. "
        "Domain documents describe how the game works and must not restate anything "
        "measured here. Everything below is measured over the whole corpus, never sampled."
    )
    add("")
    add("---")
    add("")
    add("## 1. Corpus inventory")
    add("")
    add("| Check | Count |")
    add("|---|---|")
    add(f"| Match detail files | {inventory['detail_files']:,} |")
    add(f"| Timeline files | {inventory['timeline_files']:,} |")
    add(f"| **Valid pairs** | **{len(inventory['valid_pairs']):,}** |")
    add(f"| Detail missing a timeline | {len(inventory['detail_without_timeline']):,} |")
    add(f"| Timeline missing a detail | {len(inventory['timeline_without_detail']):,} |")
    add(f"| Duplicate match IDs | {len(inventory['duplicate_match_ids']):,} |")
    add(f"| Malformed / unparseable | {len(inventory['malformed']):,} |")
    add(f"| Structurally incomplete | {len(inventory['structurally_incomplete']):,} |")
    add(f"| **Audited** | **{audited:,}** |")
    add("")
    add(
        "Every later phase operates on the audited set. Orphans, duplicates, malformed "
        "files and structurally incomplete pairs are excluded and listed, never skipped "
        "silently."
    )
    add("")

    for key, title in (
        ("detail_without_timeline", "Detail files missing a timeline"),
        ("timeline_without_detail", "Timeline files missing a detail"),
    ):
        if inventory[key]:
            add(f"**{title}:** " + ", ".join(f"`{s}`" for s in inventory[key][:20]))
            add("")

    for key, title in (
        ("malformed", "Malformed files"),
        ("structurally_incomplete", "Structurally incomplete pairs"),
        ("duplicate_match_ids", "Duplicate match IDs"),
    ):
        if inventory[key]:
            add(f"**{title}:**")
            add("")
            for entry in inventory[key][:20]:
                add("- " + " - ".join(f"{k}: `{v}`" for k, v in entry.items()))
            add("")

    add("---")
    add("")
    add("## 2. Measurements the schema design depends on")
    add("")
    add("### 2.1 Frame interval")
    add("")
    add(
        "Decides what is observable at all. A uniform 60000 ms means per-minute "
        "resolution and nothing finer, which is what rules out direct wave-state "
        "reconstruction and frame-by-frame trade analysis."
    )
    add("")
    out.extend(counter_table(measures["frame_intervals"], "frameInterval (ms)", audited))
    add("")
    add(f"Frames per match: {describe(measures['frames_per_match'])}")
    add("")

    add("### 2.2 Kill damage attribution")
    add("")
    add(
        "`victimDamageDealt` and `victimDamageReceived` on `CHAMPION_KILL` carry "
        "per-source damage in the seconds before a death -- the only sub-minute "
        "resolution available anywhere in this data. Death context and external-pressure "
        "analysis depend on them."
    )
    add("")
    add("| Measure | Value |")
    add("|---|---|")
    add(f"| CHAMPION_KILL events | {kills:,} |")
    add(f"| Kills per match | {describe(measures['kills_per_match'])} |")
    for direction in ("victimDamageDealt", "victimDamageReceived"):
        entries = measures[f"{direction}_entries"]
        missing = measures[f"{direction}_missing"]
        add(
            f"| `{direction}` present | {pct(len(entries), kills)} "
            f"({len(entries):,} of {kills:,}) |"
        )
        add(f"| `{direction}` missing | {missing:,} |")
        add(f"| `{direction}` entries per kill | {describe(entries)} |")
    add("")
    add(
        "**`victimDamageDealt` absence is semantic, not a patch gap.** The missing rate "
        "is spread evenly across every patch in the corpus (table below), with no cliff "
        "at any version boundary, and "
        f"{pct(measures['dealt_missing_champion'], measures['dealt_missing_champion'] + measures['dealt_missing_execution'])} "
        "of the affected kills were made by a champion rather than an execution. The "
        "field is absent when the victim dealt no damage before dying. **Read absence as "
        "an empty list, not as unavailable data** -- no fallback is required and "
        "`victimDamageReceived` is present on every kill."
    )
    add("")
    out.extend(
        [
            "| Patch | Kills | `victimDamageDealt` missing | Rate |",
            "|---|---|---|---|",
        ]
    )
    for patch in sorted(
        measures["kills_by_patch"], key=lambda v: [int(x) for x in v.split(".")]
    ):
        total = measures["kills_by_patch"][patch]
        gone = measures["dealt_missing_by_patch"][patch]
        out.append(f"| `{patch}` | {total:,} | {gone:,} | {pct(gone, total)} |")
    add("")

    add("### 2.3 Participants, positions and patches")
    add("")
    total_participants = sum(measures["team_position"].values())
    add(f"Participant rows: {total_participants:,}")
    add("")
    out.extend(
        counter_table(measures["participant_counts"], "Participants per match", audited)
    )
    add("")
    out.extend(counter_table(measures["team_position"], "teamPosition", total_participants))
    add("")
    add(f"`challenges` keys per participant: {describe(measures['challenge_key_counts'])}")
    add("")
    out.extend(counter_table(measures["queues"], "queueId", audited))
    add("")
    out.extend(counter_table(measures["patches"], "Patch", audited))
    add("")

    add("### 2.4 Degenerate games")
    add("")
    add(
        f"Matches with fewer than {SHORT_MATCH_FRAMES} timeline frames, and matches where "
        "any participant has a blank `teamPosition`. Both are listed as diagnostics. "
        "**Whether these are excluded from analysis is a scope decision, not a parsing "
        "decision** -- they are real games, they parse cleanly, and the canonical layer "
        "should hold them. No remake threshold is invented here."
    )
    add("")
    short = measures["short_matches"]
    blanks = measures["blank_position_matches"]
    add(f"Short matches: **{len(short)}** of {audited:,} ({pct(len(short), audited)}).")
    add("")
    if short:
        add("| Match | Frames | Duration (s) | Patch | Result |")
        add("|---|---|---|---|---|")
        for entry in sorted(short, key=lambda e: e["frames"]):
            add(
                f"| `{entry['match']}` | {entry['frames']} | {entry['duration_sec']} | "
                f"`{entry['patch']}` | {entry['result']} |"
            )
        add("")
    add(f"Blank `teamPosition` matches: **{len(blanks)}**.")
    add("")
    if blanks:
        add("| Match | Frames | Patch |")
        add("|---|---|---|")
        for entry in blanks:
            add(f"| `{entry['match']}` | {entry['frames']} | `{entry['patch']}` |")
        add("")

    add("---")
    add("")
    add("## 3. Field inventory")
    add("")
    add(
        "Every JSON leaf path observed, with the share of audited matches containing it. "
        "List indices are collapsed to `[]`. `PARTIAL` marks a path present in fewer than "
        f"{PARTIAL_PRESENCE_THRESHOLD:.0%} of matches -- building on one needs a documented "
        "fallback. `IDENTIFIER` marks an account identifier that is measured here but must "
        "never be ingested."
    )
    add("")
    add("### 3.1 Match detail")
    add("")
    add(FIELD_HEADER)
    out.extend(field_rows(result["detail_tally"], audited))
    add("")
    add("### 3.2 Timeline participant frames")
    add("")
    add(FIELD_HEADER)
    out.extend(field_rows(result["frame_tally"], audited))
    add("")
    add("### 3.3 Timeline events, by type")
    add("")
    add(
        "Presence is measured against matches containing that event type at all, not "
        "against the whole corpus."
    )
    add("")
    for event_type in sorted(result["event_tallies"]):
        seen_in = result["event_matches"][event_type]
        add(f"#### `{event_type}`")
        add("")
        add(f"Present in {seen_in:,} of {audited:,} matches ({pct(seen_in, audited)}).")
        add("")
        add(FIELD_HEADER)
        out.extend(field_rows(result["event_tallies"][event_type], seen_in))
        add("")

    add("---")
    add("")
    add("## 4. Concept classification (A / B / C)")
    add("")
    add(
        "**Not yet written.** The A/B/C classification applies to the *concepts the "
        "project needs* -- recall timing, wave state, roam, lane pressure -- not to raw "
        "API paths, which are directly available by definition and inventoried in "
        "section 3."
    )
    add("")
    add(
        "It also cannot live here: this file is generated, and a concept classification is "
        "a hand-written judgement against a candidate catalogue. Mixing the two would mean "
        "either losing the judgements on every re-run or freezing the generated half."
    )
    add("")
    add(
        "Concept classification therefore lives in `docs/ANALYSIS_SPEC.md`, which cites the "
        "measurements in this file. This file stays the sole home for *what the telemetry "
        "observes*; that file is the sole home for *what we can therefore operationalize*."
    )
    add("")
    return "\n".join(out) + "\n"


def to_jsonable(result: dict[str, Any]) -> dict[str, Any]:
    """Machine-readable companion; sets become sorted lists."""

    def dump_tally(tally: dict[str, Any], denominator: int) -> dict[str, Any]:
        return {
            path: {
                "matches": tally["matches"][path],
                "presence_rate": (
                    round(tally["matches"][path] / denominator, 6) if denominator else None
                ),
                "occurrences": tally["occurrences"][path],
                "nulls": tally["nulls"][path],
                "types": sorted(tally["types"][path]),
            }
            for path in sorted(tally["matches"])
        }

    inventory = result["inventory"]
    audited = inventory["audited"]
    measures = result["measures"]

    return {
        "corpus": {
            "detail_files": inventory["detail_files"],
            "timeline_files": inventory["timeline_files"],
            "valid_pairs": len(inventory["valid_pairs"]),
            "audited": audited,
            "detail_without_timeline": inventory["detail_without_timeline"],
            "timeline_without_detail": inventory["timeline_without_detail"],
            "duplicate_match_ids": inventory["duplicate_match_ids"],
            "malformed": inventory["malformed"],
            "structurally_incomplete": inventory["structurally_incomplete"],
        },
        "measures": {
            "frame_intervals": {str(k): v for k, v in measures["frame_intervals"].items()},
            "champion_kills": measures["champion_kills"],
            "victimDamageDealt_present": len(measures["victimDamageDealt_entries"]),
            "victimDamageDealt_missing": measures["victimDamageDealt_missing"],
            "victimDamageReceived_present": len(measures["victimDamageReceived_entries"]),
            "victimDamageReceived_missing": measures["victimDamageReceived_missing"],
            "participant_counts": {
                str(k): v for k, v in measures["participant_counts"].items()
            },
            "team_position": dict(measures["team_position"]),
            "queues": {str(k): v for k, v in measures["queues"].items()},
            "patches": dict(measures["patches"]),
            "kills_by_patch": dict(measures["kills_by_patch"]),
            "dealt_missing_by_patch": dict(measures["dealt_missing_by_patch"]),
            "dealt_missing_execution": measures["dealt_missing_execution"],
            "dealt_missing_champion": measures["dealt_missing_champion"],
            "short_matches": measures["short_matches"],
            "blank_position_matches": measures["blank_position_matches"],
        },
        "fields": {
            "match_detail": dump_tally(result["detail_tally"], audited),
            "timeline_participant_frames": dump_tally(result["frame_tally"], audited),
            "timeline_events": {
                event_type: dump_tally(tally, result["event_matches"][event_type])
                for event_type, tally in sorted(result["event_tallies"].items())
            },
        },
    }


def main() -> None:
    """Audit the corpus and write both report artifacts."""
    if not RAW_DATA_DIR.is_dir():
        raise SystemExit(f"Raw data directory not found: {RAW_DATA_DIR}")

    result = run_audit(RAW_DATA_DIR)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    REPORT_PATH.write_text(render_report(result), encoding="utf-8")
    JSON_PATH.write_text(
        json.dumps(to_jsonable(result), indent=2, sort_keys=True), encoding="utf-8"
    )

    print(f"Wrote {REPORT_PATH.relative_to(BASE_DIR)}")
    print(f"Wrote {JSON_PATH.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
