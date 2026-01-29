from datetime import datetime
from uuid import uuid4

from app.models.db.product_doc import ProductDoc


def test_product_doc_to_dict_defaults():
    doc = ProductDoc(
        id=uuid4(),
        project_id=uuid4(),
        overview="Test overview",
        content_structure={"sections": []},
        page_plan={"pages": []},
        interview_answers=[],
        generation_count=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    data = doc.to_dict()

    assert data["overview"] == "Test overview"
    assert data["target_users"] == []
    assert data["content_structure"] == {"sections": []}
    assert data["page_plan"] == {"pages": []}
    assert data["interview_answers"] == []
    assert data["generation_count"] == 1
    assert data["last_generated_at"] is None
