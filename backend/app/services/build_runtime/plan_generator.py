"""BuildPlan generator for multi-page builds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID, uuid4

from app.models.db.build_plan import BuildPlan, BuildStatus
from app.services.build_runtime.planner import PageSpec


@dataclass
class TaskTemplate:
    """Template for generating build tasks."""

    name: str
    category: str
    estimated_ms: int
    description: str = ""


@dataclass
class BuildTaskData:
    id: str
    name: str
    description: str
    category: str
    status: str
    page_id: Optional[str] = None
    estimated_ms: int = 0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None


class BuildPlanGenerator:
    """Generate accurate BuildPlans from page specifications."""

    PAGE_TASKS = [
        TaskTemplate("生成 HTML 结构", "generation", 5000, "AI 生成页面 HTML"),
        TaskTemplate("应用样式", "generation", 2000, "Tailwind CSS 样式应用"),
        TaskTemplate("HTML 验证", "validation", 1000, "检查 HTML 结构有效性"),
        TaskTemplate("安全检查", "validation", 1000, "检查 XSS 和注入风险"),
        TaskTemplate("保存页面", "storage", 500, "保存到数据库"),
        TaskTemplate("生成缩略图", "assets", 3000, "渲染页面截图"),
    ]

    PROJECT_TASKS_START = [
        TaskTemplate("创建构建计划", "planning", 500, "规划构建任务"),
        TaskTemplate("解析需求文档", "planning", 1000, "从 ProductDoc 提取信息"),
    ]

    PROJECT_TASKS_END = [
        TaskTemplate("验证跨页面链接", "validation", 1000, "检查页面间导航"),
        TaskTemplate("最终检查", "finalization", 500, "确认构建完成"),
    ]

    def generate(
        self,
        project_id: str,
        pages: List[PageSpec],
        product_doc: object,
        plan_id: Optional[str] = None,
    ) -> BuildPlan:
        """Generate a complete BuildPlan."""
        plan_uuid = UUID(plan_id) if plan_id else uuid4()
        project_uuid = UUID(project_id)

        tasks: List[BuildTaskData] = []
        total_estimated_ms = 0

        for template in self.PROJECT_TASKS_START:
            task = self._create_task(template, page_id=None)
            tasks.append(task)
            total_estimated_ms += template.estimated_ms

        page_summaries = []
        for page in pages:
            page_tasks = []
            for template in self.PAGE_TASKS:
                task = self._create_task(template, page_id=page.id, name_prefix=page.name)
                tasks.append(task)
                page_tasks.append(task)
                total_estimated_ms += template.estimated_ms

            page_summaries.append(
                {
                    "id": page.id,
                    "name": page.name,
                    "path": page.path,
                    "is_main": page.is_main,
                    "task_count": len(page_tasks),
                }
            )

        for template in self.PROJECT_TASKS_END:
            task = self._create_task(template, page_id=None)
            tasks.append(task)
            total_estimated_ms += template.estimated_ms

        return BuildPlan(
            id=plan_uuid,
            project_id=project_uuid,
            pages=page_summaries,
            tasks=[t.__dict__ for t in tasks],
            total_tasks=len(tasks),
            completed_tasks=0,
            failed_tasks=0,
            estimated_duration_ms=total_estimated_ms,
            status=BuildStatus.DRAFT,
        )

    def _create_task(
        self,
        template: TaskTemplate,
        page_id: Optional[str] = None,
        name_prefix: Optional[str] = None,
    ) -> BuildTaskData:
        name = template.name
        if name_prefix:
            name = f"{name_prefix}: {name}"

        return BuildTaskData(
            id=str(uuid4()),
            name=name,
            description=template.description,
            category=template.category,
            status="pending",
            page_id=page_id,
            estimated_ms=template.estimated_ms,
        )
