import asyncio

from app.services.build_runtime.planner import MultiPageDetector


class DummyDoc:
    def __init__(self, page_plan=None, content_structure=None):
        self.page_plan = page_plan or {}
        self.content_structure = content_structure or {}


def run(coro):
    return asyncio.run(coro)


def test_product_doc_page_plan_priority():
    detector = MultiPageDetector()
    doc = DummyDoc(
        page_plan={
            "pages": [
                {"name": "Home"},
                {"name": "About"},
            ]
        }
    )
    decision = run(detector.detect(doc, ""))
    assert decision.is_multi_page is True
    assert "Home" in decision.pages


def test_explicit_request_detection():
    detector = MultiPageDetector()
    decision = run(detector.detect(None, "We need multiple pages: about and contact"))
    assert decision.is_multi_page is True
    assert "About" in decision.pages
    assert "Contact" in decision.pages


def test_content_complexity_detection():
    detector = MultiPageDetector()
    sections = [{"name": f"Section {i}", "priority": "low"} for i in range(7)]
    doc = DummyDoc(content_structure={"sections": sections})
    decision = run(detector.detect(doc, ""))
    assert decision.is_multi_page is True


def test_default_single_page():
    detector = MultiPageDetector()
    doc = DummyDoc(content_structure={"sections": [{"name": "Hero", "priority": "high"}]})
    decision = run(detector.detect(doc, "Single page site"))
    assert decision.is_multi_page is False
