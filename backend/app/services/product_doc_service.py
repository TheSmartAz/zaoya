"""ProductDoc generation and normalization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import re
from typing import Any, List, Optional
from uuid import UUID, uuid4

from app.models.db.product_doc import ProductDoc
from app.services.ai_service import generate_response, resolve_available_model


@dataclass
class ProductDocPayload:
    overview: str
    target_users: list[str]
    content_structure: dict
    design_requirements: Optional[dict]
    page_plan: dict
    technical_constraints: Optional[list[str]]

    def to_dict(self) -> dict:
        return {
            "overview": self.overview,
            "target_users": self.target_users,
            "content_structure": self.content_structure,
            "design_requirements": self.design_requirements,
            "page_plan": self.page_plan,
            "technical_constraints": self.technical_constraints,
        }


class ProductDocService:
    """Generate and normalize ProductDoc content."""

    def __init__(self, model_id: Optional[str] = None):
        self.model_id = model_id

    async def generate_payload(
        self,
        interview_answers: List[dict],
        project_type: Optional[str] = None,
        preferred_model: Optional[str] = None,
    ) -> ProductDocPayload:
        prompt = self._build_generation_prompt(interview_answers, project_type)
        model_id = resolve_available_model(preferred_model or self.model_id)
        payload: dict[str, Any] = {}

        if model_id:
            try:
                response_text = await generate_response(
                    messages=[{"role": "user", "content": prompt}],
                    model=model_id,
                    temperature=0.2,
                )
                payload_text = _extract_json(response_text)
                payload = json.loads(payload_text)
            except Exception:
                payload = {}

        normalized = self._normalize_payload(payload, project_type)
        return ProductDocPayload(**normalized)

    def build_product_doc(
        self,
        project_id: UUID,
        payload: ProductDocPayload,
        interview_answers: List[dict],
        generation_count: int = 1,
    ) -> ProductDoc:
        now = datetime.utcnow()
        return ProductDoc(
            id=uuid4(),
            project_id=project_id,
            overview=payload.overview,
            target_users=payload.target_users,
            content_structure=payload.content_structure,
            design_requirements=payload.design_requirements,
            page_plan=payload.page_plan,
            technical_constraints=payload.technical_constraints,
            interview_answers=interview_answers,
            generation_count=generation_count,
            last_generated_at=now,
        )

    def apply_payload(self, doc: ProductDoc, payload: ProductDocPayload) -> ProductDoc:
        doc.overview = payload.overview
        doc.target_users = payload.target_users
        doc.content_structure = payload.content_structure
        doc.design_requirements = payload.design_requirements
        doc.page_plan = payload.page_plan
        doc.technical_constraints = payload.technical_constraints
        doc.last_generated_at = datetime.utcnow()
        return doc

    def _build_generation_prompt(
        self,
        interview_answers: List[dict],
        project_type: Optional[str] = None,
    ) -> str:
        answers_text = "\n".join(
            [
                f"Q: {answer.get('question', '')}\nA: {answer.get('answer', '')}"
                for answer in interview_answers
            ]
        )
        project_type_label = project_type or "项目"
        return f"""
基于以下用户访谈回答，生成一个完整的产品需求文档 (ProductDoc)。

项目类型: {project_type_label}

访谈内容:
{answers_text}

请生成以下结构的JSON:
{{
    \"overview\": \"项目简介（2-3句话）\",
    \"target_users\": [\"目标用户1\", \"目标用户2\"],
    \"content_structure\": {{
        \"sections\": [
            {{
                \"name\": \"区块名称\",
                \"description\": \"区块描述\",
                \"priority\": \"high/medium/low\",
                \"content_hints\": [\"内容提示1\", \"内容提示2\"]
            }}
        ]
    }},
    \"design_requirements\": {{
        \"style\": \"设计风格\",
        \"colors\": [\"主色\", \"辅色\"],
        \"typography\": \"字体风格\",
        \"mood\": \"整体氛围\"
    }},
    \"page_plan\": {{
        \"pages\": [
            {{
                \"id\": \"page-1\",
                \"name\": \"页面名称\",
                \"path\": \"/path\",
                \"description\": \"页面描述\",
                \"is_main\": true,
                \"sections\": [\"区块引用\"]
            }}
        ]
    }},
    \"technical_constraints\": [\"约束1\", \"约束2\"]
}}

确保:
1. 内容基于用户回答，不要编造信息
2. 页面规划合理，首页标记为 is_main: true
3. 设计要求符合用户偏好
4. 区块优先级反映用户重点
"""

    def _normalize_payload(self, payload: dict, project_type: Optional[str]) -> dict:
        if not isinstance(payload, dict):
            payload = {}

        overview = str(payload.get("overview") or "").strip()
        if not overview:
            overview = f"{project_type or '项目'}需求概述。"

        target_users = payload.get("target_users")
        if not isinstance(target_users, list):
            target_users = []
        target_users = [str(item).strip() for item in target_users if str(item).strip()]

        content_structure = payload.get("content_structure")
        if not isinstance(content_structure, dict):
            content_structure = {}
        raw_sections = content_structure.get("sections")
        if not isinstance(raw_sections, list):
            raw_sections = []
        sections = []
        for idx, section in enumerate(raw_sections):
            if not isinstance(section, dict):
                continue
            name = str(section.get("name") or f"Section {idx + 1}").strip()
            description = str(section.get("description") or "").strip()
            priority = section.get("priority")
            if priority not in {"high", "medium", "low"}:
                priority = "medium"
            content_hints = section.get("content_hints")
            if not isinstance(content_hints, list):
                content_hints = []
            content_hints = [
                str(item).strip() for item in content_hints if str(item).strip()
            ]
            sections.append(
                {
                    "name": name,
                    "description": description,
                    "priority": priority,
                    "content_hints": content_hints,
                }
            )
        content_structure = {"sections": sections}

        design_requirements = payload.get("design_requirements")
        if not isinstance(design_requirements, dict):
            design_requirements = None
        else:
            colors = design_requirements.get("colors")
            if not isinstance(colors, list):
                colors = []
            colors = [str(item).strip() for item in colors if str(item).strip()]
            design_requirements = {
                "style": design_requirements.get("style"),
                "colors": colors,
                "typography": design_requirements.get("typography"),
                "mood": design_requirements.get("mood"),
            }
            if not any(value for value in design_requirements.values()):
                design_requirements = None

        page_plan = payload.get("page_plan")
        if not isinstance(page_plan, dict):
            page_plan = {}
        raw_pages = page_plan.get("pages")
        if not isinstance(raw_pages, list):
            raw_pages = []
        pages = []
        for idx, page in enumerate(raw_pages):
            if not isinstance(page, dict):
                continue
            page_id = page.get("id") or f"page-{uuid4().hex[:8]}"
            name = str(page.get("name") or f"页面 {idx + 1}").strip()
            path = str(page.get("path") or "/").strip()
            description = str(page.get("description") or "").strip()
            is_main = bool(page.get("is_main"))
            sections_ref = page.get("sections")
            if not isinstance(sections_ref, list):
                sections_ref = []
            sections_ref = [
                str(item).strip() for item in sections_ref if str(item).strip()
            ]
            pages.append(
                {
                    "id": str(page_id),
                    "name": name,
                    "path": path,
                    "description": description,
                    "is_main": is_main,
                    "sections": sections_ref,
                }
            )
        if not pages:
            pages = [
                {
                    "id": f"page-{uuid4().hex[:8]}",
                    "name": "首页",
                    "path": "/",
                    "description": "主页面",
                    "is_main": True,
                    "sections": [s["name"] for s in sections],
                }
            ]
        if not any(page.get("is_main") for page in pages):
            pages[0]["is_main"] = True
        page_plan = {"pages": pages}

        technical_constraints = payload.get("technical_constraints")
        if not isinstance(technical_constraints, list):
            technical_constraints = []
        technical_constraints = [
            str(item).strip() for item in technical_constraints if str(item).strip()
        ]
        if not technical_constraints:
            technical_constraints = None

        return {
            "overview": overview,
            "target_users": target_users,
            "content_structure": content_structure,
            "design_requirements": design_requirements,
            "page_plan": page_plan,
            "technical_constraints": technical_constraints,
        }


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
