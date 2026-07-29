from scripts.fetch_champion_icons import build_icon_mapping


MOCK_CHAMPION_RESPONSE = {
    "data": {
        "AurelionSol": {
            "id": "AurelionSol",
            "name": "Aurelion Sol",
            "image": {"full": "AurelionSol.png"},
        },
        "Kaisa": {
            "id": "Kaisa",
            "name": "Kai'Sa",
            "image": {"full": "Kaisa.png"},
        },
        "MonkeyKing": {
            "id": "MonkeyKing",
            "name": "Wukong",
            "image": {"full": "MonkeyKing.png"},
        },
    }
}


def test_build_icon_mapping_matches_id_and_name_fields() -> None:
    mapping, unmapped = build_icon_mapping(
        ["AurelionSol", "Kaisa", "Wukong"],
        MOCK_CHAMPION_RESPONSE,
    )

    assert mapping == {
        "AurelionSol": "AurelionSol.png",
        "Kaisa": "Kaisa.png",
        "Wukong": "MonkeyKing.png",
    }
    assert unmapped == []


def test_build_icon_mapping_reports_unmapped_name() -> None:
    mapping, unmapped = build_icon_mapping(
        ["AurelionSol", "NotAChampion"],
        MOCK_CHAMPION_RESPONSE,
    )

    assert mapping == {"AurelionSol": "AurelionSol.png"}
    assert unmapped == ["NotAChampion"]
