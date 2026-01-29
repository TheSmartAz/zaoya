from app.services.intent_detector import _parse_edit_request_fallback


def test_edit_intent_fallback_overview():
    result = _parse_edit_request_fallback("修改概述为新的简介")
    assert result is not None
    assert result["field"] == "overview"
    assert result["action"] == "update"
    assert "新的简介" in result["value"]


def test_edit_intent_fallback_add_page():
    result = _parse_edit_request_fallback("添加页面 关于我们")
    assert result is not None
    assert result["field"] == "page_plan.pages"
    assert result["action"] == "add"
    assert "关于我们" in result["value"]


def test_edit_intent_fallback_delete_page():
    result = _parse_edit_request_fallback("删除页面 /pricing")
    assert result is not None
    assert result["field"] == "page_plan.pages"
    assert result["action"] == "remove"
    assert "/pricing" in result["value"]
