"""Intent detection for ProductDoc editing."""

from __future__ import annotations

import json
import re
from typing import Optional, Dict, Any

from app.services.ai_service import generate_response, resolve_available_model


class ProductDocEditIntent:
    """Detect and parse ProductDoc edit requests."""

    EDIT_PATTERNS = [
        r"修改.*(概述|overview).*为",
        r"更新.*(目标用户|target)",
        r"添加.*页面",
        r"删除.*页面",
        r"修改.*设计.*要求",
        r"更改.*风格",
        r"添加.*约束",
        r"添加.*区块",
        r"更新.*内容.*结构",
    ]

    FIELD_MAP = {
        "概述": "overview",
        "overview": "overview",
        "目标用户": "target_users",
        "target": "target_users",
        "风格": "design_requirements.style",
        "配色": "design_requirements.colors",
        "字体": "design_requirements.typography",
        "氛围": "design_requirements.mood",
        "页面": "page_plan.pages",
        "区块": "content_structure.sections",
        "约束": "technical_constraints",
    }

    async def detect(self, message: str) -> Optional[Dict[str, Any]]:
        for pattern in self.EDIT_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                return await self._parse_edit_request(message)
        return None

    async def _parse_edit_request(self, message: str) -> Optional[Dict[str, Any]]:
        model_id = resolve_available_model(None)
        if model_id:
            try:
                response = await generate_response(
                    messages=[{"role": "user", "content": self._build_prompt(message)}],
                    model=model_id,
                    temperature=0.1,
                )
                payload_text = _extract_json(response)
                payload = json.loads(payload_text)
                if payload.get("field") and payload.get("action"):
                    return payload
            except Exception:
                pass
        return _parse_edit_request_fallback(message)

    def _build_prompt(self, message: str) -> str:
        return (
            "你是产品文档编辑助手。根据用户输入，提取结构化的修改指令。\n"
            "只输出 JSON，格式如下：\n"
            "{\"field\": \"overview\", \"action\": \"update\", \"value\": \"新的概述\"}\n"
            "可选 field:\n"
            "- overview\n"
            "- target_users\n"
            "- content_structure.sections\n"
            "- design_requirements.style\n"
            "- design_requirements.colors\n"
            "- design_requirements.typography\n"
            "- design_requirements.mood\n"
            "- page_plan.pages\n"
            "- technical_constraints\n"
            "action 仅使用 update/add/remove。\n"
            f"用户输入: {message}"
        )


def _parse_edit_request_fallback(message: str) -> Optional[Dict[str, Any]]:
    overview_match = re.search(r"(?:修改|更新|改).*?(概述|overview).*?为(.+)", message)
    if overview_match:
        return {
            "type": "product_doc_edit",
            "field": "overview",
            "action": "update",
            "value": overview_match.group(2).strip(),
        }

    target_match = re.search(r"(?:更新|修改|添加).*?(目标用户|target).*?(?:为)?(.+)", message)
    if target_match:
        return {
            "type": "product_doc_edit",
            "field": "target_users",
            "action": "update" if "更新" in message or "修改" in message else "add",
            "value": target_match.group(2).strip(),
        }

    constraint_match = re.search(r"添加.*?约束.*?(?:为)?(.+)", message)
    if constraint_match:
        return {
            "type": "product_doc_edit",
            "field": "technical_constraints",
            "action": "add",
            "value": constraint_match.group(1).strip(),
        }

    page_match = re.search(r"(?:添加|新增).*页面[:：]?\s*(.+)", message)
    if page_match:
        return {
            "type": "product_doc_edit",
            "field": "page_plan.pages",
            "action": "add",
            "value": page_match.group(1).strip(),
        }

    delete_page_match = re.search(r"(?:删除|移除).*页面[:：]?\s*(.+)", message)
    if delete_page_match:
        return {
            "type": "product_doc_edit",
            "field": "page_plan.pages",
            "action": "remove",
            "value": delete_page_match.group(1).strip(),
        }

    design_match = re.search(r"(?:更改|修改).*风格.*?(?:为)?(.+)", message)
    if design_match:
        return {
            "type": "product_doc_edit",
            "field": "design_requirements.style",
            "action": "update",
            "value": design_match.group(1).strip(),
        }

    return None


def _extract_json(text: str) -> str:
    if not text:
        return "{}"
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced[0]
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return "{}"
