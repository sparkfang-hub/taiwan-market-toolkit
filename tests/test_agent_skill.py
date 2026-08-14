from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".agents" / "skills" / "taiwan-market-research"
SKILL_FILE = SKILL_DIR / "SKILL.md"
COMMAND_MAP = SKILL_DIR / "references" / "command-map.md"


def test_agent_skill_has_required_frontmatter_and_reference():
    text = SKILL_FILE.read_text(encoding="utf-8")

    assert text.startswith("---\n")
    frontmatter, body = text[4:].split("\n---\n", 1)
    assert "name: taiwan-market-research" in frontmatter
    assert "description:" in frontmatter
    assert "references/command-map.md" in body
    assert COMMAND_MAP.is_file()


def test_agent_skill_routes_to_existing_public_interfaces():
    text = COMMAND_MAP.read_text(encoding="utf-8")

    for command in (
        "tw-market company",
        "tw-market quote",
        "tw-market valuation",
        "tw-market overview",
        "tw-market market-snapshot",
        "tw-market history",
        "tw-market calendar",
        "tw-market validate",
        "tw-market analyze",
        "tw-market archive-quotes",
    ):
        assert command in text

    assert "find_corporate_actions" in text
    assert "fetch_corporate_actions" in text
    assert "filter_corporate_actions" in text


def test_agent_skill_keeps_market_data_safety_boundaries_explicit():
    text = SKILL_FILE.read_text(encoding="utf-8")

    assert "Historical prices are unadjusted" in text
    assert "Do not convert `None`" in text
    assert "Do not place, cancel, simulate, or prepare orders" in text
    assert "Do not fabricate official exchange values" in text
