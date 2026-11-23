"""Verify version 1 canonical names for operational and laboratory points."""

import pytest

from tssource.domain.naming.convention import CanonicalName
from tssource.domain.time.site_zone import SiteCode


@pytest.mark.ac("PBI-004-02:AC1")
@pytest.mark.parametrize(
    ("text", "site"),
    [
        ("ORN.A200.R201.TIC-2011.PV", SiteCode.BRAZIL),
        ("GUL.A100.P104.PIC-1040.SP", SiteCode.US_GULF_COAST),
        ("BEL.LAB.A200.AH207.PH", SiteCode.BELGIUM),
        ("CHN.LAB.A100.AH109.H2O", SiteCode.CHINA),
        ("IND.A100.T102.LIC-1020.MODE", SiteCode.INDIA),
    ],
)
def test_canonical_round_trip(text: str, site: SiteCode) -> None:
    """Preserve the supplied grammar and resolve its site abbreviation."""
    parsed = CanonicalName.parse(text)
    assert parsed.site_code is site
    assert parsed.render() == text


@pytest.mark.parametrize(
    "text",
    [
        "",
        "XX.A200.R201.TIC-2011.PV",
        "orn.A200.R201.TIC-2011.PV",
        " ORN.A200.R201.TIC-2011.PV",
        "ORN.A20.R201.TIC-2011.PV",
        "ORN.A200.R201.XYZ-2011.PV",
        "ORN.A200.R201.TIC-2011.RAW",
        "ORN.A200.R201.TIC-2011.PV.X",
        "ORN.LAB.A200.AH207.ph",
        "ORN.LAB.A200.AH207.PH\n",
    ],
)
def test_parser_rejects_malformed_names(text: str) -> None:
    """Reject aliases, unknown tokens, whitespace and incomplete keys."""
    with pytest.raises(ValueError, match="canonical"):
        CanonicalName.parse(text)
