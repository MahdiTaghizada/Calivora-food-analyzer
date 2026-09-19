import pytest

from ai.nutrition import _extract_nutrients


def test_energy_kj_is_converted_to_kcal():
    nutrients = [
        {
            "nutrientName": "Energy",
            "value": 1210,
            "unitName": "KJ",
        }
    ]

    result = _extract_nutrients(nutrients)

    assert result["Energy"] == pytest.approx(
        1210 / 4.184,
        rel=0.01,
    )


def test_energy_kcal_is_kept_as_kcal():
    nutrients = [
        {
            "nutrientName": "Energy",
            "value": 290,
            "unitName": "KCAL",
        }
    ]

    result = _extract_nutrients(nutrients)

    assert result["Energy"] == pytest.approx(290)


def test_kcal_is_preferred_when_both_units_exist():
    nutrients = [
        {
            "nutrientName": "Energy",
            "value": 1210,
            "unitName": "KJ",
        },
        {
            "nutrientName": "Energy",
            "value": 290,
            "unitName": "KCAL",
        },
    ]

    result = _extract_nutrients(nutrients)

    assert result["Energy"] == pytest.approx(290)
