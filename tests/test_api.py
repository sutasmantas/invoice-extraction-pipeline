from pathlib import Path

from fastapi.testclient import TestClient

from ledger_lens.config import Settings
from ledger_lens.main import create_app


def test_extract_review_correct_export(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "runtime", review_threshold=0.8)
    with TestClient(create_app(settings)) as client:
        documents = client.get("/api/documents").json()
        assert len(documents) == 4
        assert sum(document["status"] == "needs_review" for document in documents) == 2
        assert sum(document["status"] == "ready" for document in documents) == 2

        document = next(
            document for document in documents if document["filename"] == "sample-invoice.txt"
        )
        flagged = {
            field["name"] for field in document["fields"] if field["status"] == "needs_review"
        }
        assert flagged == {"vat_id"}

        corrected = client.patch(
            f"/api/documents/{document['id']}/fields/vat_id",
            json={"value": "DE278445901"},
        )
        assert corrected.status_code == 200
        vat = next(field for field in corrected.json()["fields"] if field["name"] == "vat_id")
        assert vat["confidence"] == 1.0

        exported = client.get(f"/api/documents/{document['id']}/export").json()
        assert exported["review_complete"] is True
        assert exported["data"]["total"] == 14280.0


def test_text_upload_and_invalid_type(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "runtime")
    with TestClient(create_app(settings)) as client:
        created = client.post(
            "/api/documents",
            files={"file": ("invoice.txt", b"Invoice # AB-9911\nTotal due: $120.00", "text/plain")},
        )
        assert created.status_code == 201
        assert created.json()["filename"] == "invoice.txt"

        invalid = client.post(
            "/api/documents",
            files={"file": ("invoice.csv", b"a,b", "text/csv")},
        )
        assert invalid.status_code == 422
