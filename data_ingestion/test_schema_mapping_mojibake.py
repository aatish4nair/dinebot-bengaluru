"""Tests for encoding repair in data_ingestion.schema_mapping."""
from data_ingestion.schema_mapping import repair_mojibake


def _corrupt(text: str, rounds: int = 1) -> str:
    """Reproduce the damage: UTF-8 bytes read back as Latin-1, `rounds` times."""
    for _ in range(rounds):
        text = text.encode("utf-8").decode("latin-1")
    return text


def test_repairs_single_round_corruption() -> None:
    assert repair_mojibake(_corrupt("Café")) == "Café"


def test_repairs_repeated_corruption() -> None:
    """The source dump carries several layers of the same damage."""
    for rounds in (2, 3, 4):
        assert repair_mojibake(_corrupt("Café", rounds)) == "Café"
        assert repair_mojibake(_corrupt("Piñata", rounds)) == "Piñata"
        assert repair_mojibake(_corrupt("100°C", rounds)) == "100°C"


def test_repairs_cp1252_curly_apostrophe() -> None:
    assert repair_mojibake(_corrupt("McDonald’s", 2)) == "McDonald’s"


def test_leaves_clean_ascii_untouched() -> None:
    for value in ["Cafe Coffee Day", "1/8, 1st Stage, Indiranagar, Bangalore", ""]:
        assert repair_mojibake(value) == value


def test_leaves_correct_non_ascii_untouched() -> None:
    """Already-correct accented text must not be mangled."""
    for value in ["Café Felix", "Piñata", "100°C"]:
        assert repair_mojibake(value) == value


def test_preserves_legitimate_circumflex() -> None:
    """
    'Yauatcha Pâtisserie' is real data in this dataset, not corruption. A
    repair pass that fires on any non-ASCII byte would destroy it.
    """
    assert repair_mojibake("Yauatcha Pâtisserie") == "Yauatcha Pâtisserie"


def test_does_not_normalize_or_rewrite() -> None:
    """Repair is encoding-only: casing, spacing and punctuation are preserved."""
    assert repair_mojibake("  Big   Brewsky  ") == "  Big   Brewsky  "
    assert repair_mojibake("BOX8- Desi Meals") == "BOX8- Desi Meals"
