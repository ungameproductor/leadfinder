from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.entities import Lead
from app.schemas import PlaceCandidate
from app.services.enrichment.dedupe import find_existing_lead
from app.services.enrichment.normalize import normalize_phone


def _lead(**kwargs) -> Lead:
    defaults = dict(name="Panificio del Corso", source_provider="mock")
    defaults.update(kwargs)
    return Lead(**defaults)


def test_dedupe_by_external_id(db: Session):
    db.add(_lead(source_external_id="mock-1", phone="+39111"))
    db.commit()
    candidate = PlaceCandidate(external_id="mock-1", name="Altro", provider="mock")
    found, conf = find_existing_lead(db, candidate)
    assert found is not None
    assert conf == 1.0


def test_dedupe_by_phone(db: Session):
    db.add(_lead(source_external_id="a", phone=normalize_phone("0831 111001")))
    db.commit()
    candidate = PlaceCandidate(
        external_id="b",
        name="Panificio",
        phone="0831 111001",
        provider="mock",
    )
    found, conf = find_existing_lead(db, candidate)
    assert found is not None
    assert conf == 0.9


def test_dedupe_by_name_address_not_name_only(db: Session):
    db.add(_lead(source_external_id="a", address="Corso Roma 12, 72100 Brindisi"))
    db.commit()
    similar_name = PlaceCandidate(
        external_id="c",
        name="Panificio del Corso",
        address="Via Nuova 99, 72100 Brindisi",
        provider="mock",
    )
    found, _ = find_existing_lead(db, similar_name)
    assert found is None

    same = PlaceCandidate(
        external_id="d",
        name="Panificio del Corso",
        address="Via Roma 12, 72100 Brindisi",
        provider="mock",
    )
    found, conf = find_existing_lead(db, same)
    assert found is not None
    assert conf == 0.7
