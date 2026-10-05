import pytest
from pydantic import ValidationError

from app.models.scenario import FleetScenarioDocument
from app.models.vessel import Vessel
from app.services.scenario_service import validate_references


def test_demo_round_trip(doc):
    again = FleetScenarioDocument.model_validate_json(doc.model_dump_json())
    assert again == doc
    assert validate_references(doc) == []


def test_all_factors_labelled_synthetic(doc):
    assert all(f.source_ref == "synthetic_demo" and "Not measured" in f.notes for f in doc.fuels)


def _vessel(**kw):
    base = dict(id="V", type="bulk", capacity_mt=1000, draft=10, design_speed_kn=13, min_speed_kn=9,
                max_speed_kn=16, base_efficiency=0.015, fuel_compatibility=["MGO"])
    return Vessel(**{**base, **kw})


def test_invalid_speed_and_capacity_rejected():
    with pytest.raises(ValidationError):
        _vessel(min_speed_kn=17)
    with pytest.raises(ValidationError):
        _vessel(capacity_mt=0)
