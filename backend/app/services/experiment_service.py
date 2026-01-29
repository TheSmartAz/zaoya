"""Experiments service for A/B testing functionality.

This service manages:
- Experiment CRUD operations
- Variant management
- Traffic assignment (deterministic hashing)
- Conversion tracking
- Statistical analysis (Z-test, confidence intervals)
- Experiment lifecycle (draft -> running -> paused -> completed)
"""

import hashlib
from datetime import datetime, date
from typing import Optional, Literal
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, or_, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.db.experiment import (
    Experiment,
    ExperimentVariant,
    ExperimentResult,
    ExperimentAssignment,
    ExperimentConversion,
    ExperimentAuditLog,
)
from app.models.db import Snapshot, Page
from app.services.cache import get_cache, CacheKeys, CacheTTL
from app.models.db import Project


class ExperimentService:
    """Service for managing A/B testing experiments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Experiment CRUD
    # ============================================================

    async def create_experiment(
        self,
        project_id: UUID,
        name: str,
        traffic_split: list[float],
        conversion_goal: dict,
        created_by_id: UUID,
    ) -> Experiment:
        """
        Create a new A/B testing experiment.

        Args:
            project_id: Project UUID
            name: Experiment name
            traffic_split: List of percentages (e.g., [50, 50] for 50/50 split)
            conversion_goal: Dict defining success metric
                {"type": "page_view", "url": "/thank-you"}
                {"type": "cta_click", "element_id": "signup-btn"}
                {"type": "form_submit", "form_id": "contact"}
            created_by_id: User UUID who created the experiment

        Returns:
            Created experiment
        """
        # Validate traffic split sums to 100
        if abs(sum(traffic_split) - 100) > 0.01:
            raise ValueError("Traffic split must sum to 100")

        experiment = Experiment(
            id=uuid4(),
            project_id=project_id,
            name=name,
            status="draft",
            traffic_split=traffic_split,
            conversion_goal=conversion_goal,
            created_at=datetime.utcnow(),
            created_by_id=created_by_id,
        )

        self.db.add(experiment)

        # Log creation
        await self._log_action(
            experiment_id=experiment.id,
            action="created",
            new_status="draft",
            created_by_id=created_by_id,
        )

        await self.db.commit()
        await self.db.refresh(experiment)
        return experiment

    async def get_experiment(self, experiment_id: UUID) -> Experiment | None:
        """Get an experiment by ID."""
        result = await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        return result.scalar_one_or_none()

    async def list_experiments(
        self,
        project_id: UUID,
        status: Optional[str] = None,
    ) -> list[Experiment]:
        """List experiments for a project, optionally filtered by status."""
        query = select(Experiment).where(Experiment.project_id == project_id)
        if status:
            query = query.where(Experiment.status == status)
        query = query.order_by(Experiment.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_experiment(
        self,
        experiment_id: UUID,
        name: str | None = None,
        traffic_split: list[float] | None = None,
        conversion_goal: dict | None = None,
    ) -> Experiment:
        """Update an experiment (only allowed in draft status)."""
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError("Experiment not found")

        if experiment.status != "draft":
            raise ValueError("Can only update experiments in draft status")

        if name:
            experiment.name = name
        if traffic_split:
            if abs(sum(traffic_split) - 100) > 0.01:
                raise ValueError("Traffic split must sum to 100")
            experiment.traffic_split = traffic_split
        if conversion_goal:
            experiment.conversion_goal = conversion_goal

        await self.db.commit()
        await self._invalidate_results_cache(experiment_id)
        await self.db.refresh(experiment)
        return experiment

    async def delete_experiment(self, experiment_id: UUID) -> None:
        """Delete an experiment (only allowed in draft status)."""
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError("Experiment not found")

        if experiment.status != "draft":
            raise ValueError("Can only delete experiments in draft status")

        await self.db.delete(experiment)
        await self.db.commit()
        await self._invalidate_results_cache(experiment_id)

    # ============================================================
    # Variant Management
    # ============================================================

    async def add_variant(
        self,
        experiment_id: UUID,
        name: str,
        is_control: bool = False,
        snapshot_id: UUID | None = None,
        page_content: dict | None = None,
    ) -> ExperimentVariant:
        """
        Add a variant to an experiment.

        Args:
            experiment_id: Experiment UUID
            name: Variant name (e.g., "Control", "Variant A")
            is_control: Whether this is the control variant
            snapshot_id: Optional snapshot ID to use as content
            page_content: Optional page content dict (overrides snapshot)
        """
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError("Experiment not found")

        # Check control constraint
        if is_control:
            existing = await self.db.execute(
                select(ExperimentVariant).where(
                    ExperimentVariant.experiment_id == experiment_id,
                    ExperimentVariant.is_control == True
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError("Experiment already has a control variant")

        resolved_content = page_content
        if snapshot_id and page_content is None:
            snapshot_result = await self.db.execute(
                select(Snapshot).where(Snapshot.id == snapshot_id)
            )
            snapshot = snapshot_result.scalar_one_or_none()
            if snapshot:
                page_result = await self.db.execute(
                    select(Page)
                    .where(Page.snapshot_id == snapshot.id)
                    .order_by(Page.is_home.desc(), Page.display_order.asc())
                )
                page = page_result.scalar_one_or_none()
                if page:
                    resolved_content = {
                        "html": page.html or "",
                        "js": page.js,
                    }

        variant = ExperimentVariant(
            id=uuid4(),
            experiment_id=experiment_id,
            name=name,
            is_control=is_control,
            snapshot_id=snapshot_id,
            page_content=resolved_content,
            created_at=datetime.utcnow(),
        )

        self.db.add(variant)

        # Create result record
        result = ExperimentResult(
            id=uuid4(),
            experiment_id=experiment_id,
            variant_id=variant.id,
            visitors=0,
            conversions=0,
            conversion_rate=None,
            updated_at=datetime.utcnow(),
        )
        self.db.add(result)

        await self.db.commit()
        await self._invalidate_results_cache(experiment_id)
        await self.db.refresh(variant)
        return variant

    async def get_variants(self, experiment_id: UUID) -> list[ExperimentVariant]:
        """Get all variants for an experiment."""
        result = await self.db.execute(
            select(ExperimentVariant)
            .where(ExperimentVariant.experiment_id == experiment_id)
            .order_by(ExperimentVariant.is_control.desc())
        )
        return list(result.scalars().all())

    async def update_variant(
        self,
        variant_id: UUID,
        name: str | None = None,
        page_content: dict | None = None,
    ) -> ExperimentVariant:
        """Update a variant (only in draft status)."""
        result = await self.db.execute(
            select(ExperimentVariant).where(ExperimentVariant.id == variant_id)
        )
        variant = result.scalar_one_or_none()
        if not variant:
            raise ValueError("Variant not found")

        # Check experiment status
        experiment = await self.get_experiment(variant.experiment_id)
        if experiment.status != "draft":
            raise ValueError("Can only update variants in draft status")

        if name:
            variant.name = name
        if page_content is not None:
            variant.page_content = page_content

        await self.db.commit()
        await self._invalidate_results_cache(experiment_id)
        await self.db.refresh(variant)
        return variant

    async def delete_variant(self, variant_id: UUID) -> None:
        """Delete a variant (only in draft status)."""
        result = await self.db.execute(
            select(ExperimentVariant).where(ExperimentVariant.id == variant_id)
        )
        variant = result.scalar_one_or_none()
        if not variant:
            raise ValueError("Variant not found")

        # Check experiment status
        experiment = await self.get_experiment(variant.experiment_id)
        if experiment.status != "draft":
            raise ValueError("Can only delete variants in draft status")

        # Ensure at least one variant remains
        count_result = await self.db.execute(
            select(func.count())
            .select_from(ExperimentVariant)
            .where(ExperimentVariant.experiment_id == variant.experiment_id)
        )
        if count_result.scalar() <= 1:
            raise ValueError("Experiment must have at least one variant")

        await self.db.delete(variant)
        await self.db.commit()
        await self._invalidate_results_cache(variant.experiment_id)

    # ============================================================
    # Experiment Lifecycle
    # ============================================================

    async def start_experiment(
        self,
        experiment_id: UUID,
        started_by_id: UUID,
    ) -> Experiment:
        """Start an experiment (draft -> running)."""
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError("Experiment not found")

        if experiment.status != "draft":
            raise ValueError("Can only start experiments in draft status")

        # Verify at least 2 variants exist
        variants = await self.get_variants(experiment_id)
        if len(variants) < 2:
            raise ValueError("Experiment must have at least 2 variants to start")

        control_count = sum(1 for v in variants if v.is_control)
        if control_count != 1:
            raise ValueError("Experiment must have exactly one control variant")

        # Verify traffic split matches variant count and totals 100%
        if experiment.traffic_split:
            if len(experiment.traffic_split) != len(variants):
                raise ValueError("Traffic split must match number of variants")
            if abs(sum(experiment.traffic_split) - 100) > 0.01:
                raise ValueError("Traffic split must total 100%")

        old_status = experiment.status
        experiment.status = "running"
        experiment.start_date = datetime.utcnow()

        await self._log_action(
            experiment_id=experiment_id,
            action="started",
            old_status=old_status,
            new_status="running",
            created_by_id=started_by_id,
        )

        await self.db.commit()
        await self.db.refresh(experiment)
        return experiment

    async def pause_experiment(
        self,
        experiment_id: UUID,
        paused_by_id: UUID,
    ) -> Experiment:
        """Pause a running experiment."""
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError("Experiment not found")

        if experiment.status != "running":
            raise ValueError("Can only pause running experiments")

        old_status = experiment.status
        experiment.status = "paused"

        await self._log_action(
            experiment_id=experiment_id,
            action="paused",
            old_status=old_status,
            new_status="paused",
            created_by_id=paused_by_id,
        )

        await self.db.commit()
        await self.db.refresh(experiment)
        return experiment

    async def resume_experiment(
        self,
        experiment_id: UUID,
        resumed_by_id: UUID,
    ) -> Experiment:
        """Resume a paused experiment."""
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError("Experiment not found")

        if experiment.status != "paused":
            raise ValueError("Can only resume paused experiments")

        old_status = experiment.status
        experiment.status = "running"

        await self._log_action(
            experiment_id=experiment_id,
            action="resumed",
            old_status=old_status,
            new_status="running",
            created_by_id=resumed_by_id,
        )

        await self.db.commit()
        await self.db.refresh(experiment)
        return experiment

    async def complete_experiment(
        self,
        experiment_id: UUID,
        completed_by_id: UUID,
        winner_variant_id: UUID | None = None,
    ) -> Experiment:
        """
        Complete an experiment and optionally declare a winner.

        Performs final statistical analysis and stores results.
        """
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError("Experiment not found")

        if experiment.status not in ("running", "paused"):
            raise ValueError("Can only complete running or paused experiments")

        # Calculate final statistics
        results = await self._calculate_all_statistics(experiment_id)

        # Find winner if not specified
        if winner_variant_id is None and results:
            # Pick variant with highest conversion rate
            winner = max(results, key=lambda r: r.conversion_rate or 0)
            winner_variant_id = winner.variant_id

        old_status = experiment.status
        experiment.status = "completed"
        experiment.end_date = datetime.utcnow()
        experiment.winner_variant_id = winner_variant_id

        # Calculate winner confidence
        if winner_variant_id:
            winner_result = next(
                (r for r in results if r.variant_id == winner_variant_id), None
            )
            if winner_result and winner_result.confidence_level is not None:
                experiment.winner_confidence = winner_result.confidence_level

        await self._log_action(
            experiment_id=experiment_id,
            action="completed",
            old_status=old_status,
            new_status="completed",
            audit_data={
                "winner_variant_id": str(winner_variant_id) if winner_variant_id else None,
                "final_results": [
                    {
                        "variant_id": str(r.variant_id),
                        "visitors": r.visitors,
                        "conversions": r.conversions,
                        "conversion_rate": float(r.conversion_rate) if r.conversion_rate else None,
                        "is_significant": r.is_significant,
                    }
                    for r in results
                ],
            },
            created_by_id=completed_by_id,
        )

        await self.db.commit()
        await self.db.refresh(experiment)
        return experiment

    # ============================================================
    # Traffic Assignment
    # ============================================================

    def _assign_variant(
        self,
        visitor_id: str,
        experiment_id: UUID,
        variants: list[ExperimentVariant],
        traffic_split: list[float],
    ) -> ExperimentVariant:
        """
        Assign a visitor to a variant using deterministic hashing.

        The same visitor will always get the same variant.
        """
        # Use consistent hash to pick variant
        hash_input = f"{visitor_id}:{experiment_id}"
        hash_value = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)

        # Map hash to traffic split buckets
        total = sum(traffic_split)
        bucket = hash_value % total

        cumulative = 0
        for i, weight in enumerate(traffic_split):
            cumulative += weight
            if bucket < cumulative:
                return variants[i]

        # Fallback to last variant
        return variants[-1]

    async def get_or_assign_variant(
        self,
        experiment_id: UUID,
        visitor_id: str,
    ) -> tuple[ExperimentVariant, bool]:
        """
        Get existing variant assignment or create a new one.

        Returns:
            (variant, is_new_assignment)
        """
        # Check for existing assignment
        result = await self.db.execute(
            select(ExperimentAssignment).where(
                ExperimentAssignment.experiment_id == experiment_id,
                ExperimentAssignment.visitor_id == visitor_id
            )
        )
        assignment = result.scalar_one_or_none()

        if assignment:
            # Get the variant
            variant_result = await self.db.execute(
                select(ExperimentVariant).where(
                    ExperimentVariant.id == assignment.variant_id
                )
            )
            variant = variant_result.scalar_one_or_none()
            if variant:
                return variant, False

        # Get experiment and variants
        experiment = await self.get_experiment(experiment_id)
        if not experiment or experiment.status != "running":
            raise ValueError("Experiment not found or not running")

        variants = await self.get_variants(experiment_id)
        if not variants:
            raise ValueError("No variants found for experiment")

        # Assign new variant
        selected = self._assign_variant(
            visitor_id=visitor_id,
            experiment_id=experiment_id,
            variants=variants,
            traffic_split=experiment.traffic_split,
        )

        # Store assignment
        new_assignment = ExperimentAssignment(
            id=uuid4(),
            experiment_id=experiment_id,
            variant_id=selected.id,
            visitor_id=visitor_id,
            assigned_at=datetime.utcnow(),
        )
        self.db.add(new_assignment)

        # Increment visitor count in results
        await self._increment_visitors(experiment_id, selected.id)
        await self.db.commit()
        return selected, True

    # ============================================================
    # Conversion Tracking
    # ============================================================

    async def track_conversion(
        self,
        experiment_id: UUID,
        visitor_id: str,
        goal_type: str,
        goal_metadata: dict | None = None,
    ) -> bool:
        """
        Track a conversion event for a visitor.

        Returns:
            True if conversion was tracked (first time for this variant)
        """
        # Get visitor's assignment
        result = await self.db.execute(
            select(ExperimentAssignment).where(
                ExperimentAssignment.experiment_id == experiment_id,
                ExperimentAssignment.visitor_id == visitor_id
            )
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            return False

        # Check if already converted (unique constraint)
        existing = await self.db.execute(
            select(ExperimentConversion).where(
                ExperimentConversion.experiment_id == experiment_id,
                ExperimentConversion.variant_id == assignment.variant_id,
                ExperimentConversion.visitor_id == visitor_id
            )
        )
        if existing.scalar_one_or_none():
            return False  # Already counted

        # Record conversion
        conversion = ExperimentConversion(
            id=uuid4(),
            experiment_id=experiment_id,
            variant_id=assignment.variant_id,
            visitor_id=visitor_id,
            goal_type=goal_type,
            goal_metadata=goal_metadata,
            converted_at=datetime.utcnow(),
        )
        self.db.add(conversion)

        # Increment conversion count
        await self._increment_conversions(experiment_id, assignment.variant_id)
        await self.db.commit()
        return True

    async def _increment_visitors(
        self,
        experiment_id: UUID,
        variant_id: UUID,
    ) -> None:
        """Increment visitor count for a variant."""
        result = await self.db.execute(
            select(ExperimentResult).where(
                ExperimentResult.experiment_id == experiment_id,
                ExperimentResult.variant_id == variant_id
            )
        )
        result_record = result.scalar_one_or_none()
        if result_record:
            result_record.visitors += 1
            result_record.updated_at = datetime.utcnow()
            await self._invalidate_results_cache(experiment_id)

    async def _increment_conversions(
        self,
        experiment_id: UUID,
        variant_id: UUID,
    ) -> None:
        """Increment conversion count and recalculate rate for a variant."""
        result = await self.db.execute(
            select(ExperimentResult).where(
                ExperimentResult.experiment_id == experiment_id,
                ExperimentResult.variant_id == variant_id
            )
        )
        result_record = result.scalar_one_or_none()
        if result_record:
            result_record.conversions += 1
            if result_record.visitors > 0:
                result_record.conversion_rate = (
                    result_record.conversions / result_record.visitors * 100
                )
            result_record.updated_at = datetime.utcnow()
            await self._invalidate_results_cache(experiment_id)

    async def _invalidate_results_cache(self, experiment_id: UUID) -> None:
        """Invalidate cached experiment results after data changes."""
        cache = get_cache()
        await cache.delete(CacheKeys.experiment_results(str(experiment_id)))

    # ============================================================
    # Statistical Analysis
    # ============================================================

    async def _calculate_all_statistics(
        self,
        experiment_id: UUID,
    ) -> list[ExperimentResult]:
        """Recalculate statistics for all variants in an experiment."""
        results = await self.db.execute(
            select(ExperimentResult).where(
                ExperimentResult.experiment_id == experiment_id
            )
        )
        all_results = list(results.scalars().all())

        # Get control variant for comparison
        control_result = None
        for r in all_results:
            variant = await self.db.execute(
                select(ExperimentVariant).where(ExperimentVariant.id == r.variant_id)
            )
            variant_obj = variant.scalar_one_or_none()
            if variant_obj and variant_obj.is_control:
                control_result = r
                break

        for result in all_results:
            if result.visitors > 0:
                result.conversion_rate = (
                    result.conversions / result.visitors * 100
                )

            # Calculate statistical significance against control
            if control_result and result.variant_id != control_result.variant_id:
                result.is_significant, result.p_value = self._z_test(
                    control_conversions=control_result.conversions,
                    control_visitors=control_result.visitors,
                    treatment_conversions=result.conversions,
                    treatment_visitors=result.visitors,
                )

                # Calculate confidence level
                if result.is_significant:
                    result.confidence_level = (1 - result.p_value) * 100 if result.p_value else None

            result.updated_at = datetime.utcnow()

        await self.db.commit()
        return all_results

    def _z_test(
        self,
        control_conversions: int,
        control_visitors: int,
        treatment_conversions: int,
        treatment_visitors: int,
    ) -> tuple[bool, float | None]:
        """
        Perform two-proportion Z-test for statistical significance.

        Returns:
            (is_significant, p_value)
        """
        if control_visitors == 0 or treatment_visitors == 0:
            return False, None

        p1 = control_conversions / control_visitors
        p2 = treatment_conversions / treatment_visitors

        # Pooled proportion
        p_pooled = (control_conversions + treatment_conversions) / (
            control_visitors + treatment_visitors
        )

        # Standard error
        se = (p_pooled * (1 - p_pooled) * (
            1 / control_visitors + 1 / treatment_visitors
        )) ** 0.5

        if se == 0:
            return False, None

        # Z-score
        z = (p2 - p1) / se

        # Calculate p-value (two-tailed)
        import math
        p_value = 2 * (1 - self._normal_cdf(abs(z)))

        # Significant at 95% confidence (p < 0.05)
        return p_value < 0.05, p_value

    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Standard normal CDF approximation."""
        import math
        sqrt2 = math.sqrt(2)
        return 0.5 * (1 + math.erf(x / sqrt2))

    # ============================================================
    # Results & Reporting
    # ============================================================

    async def get_experiment_results(
        self,
        experiment_id: UUID,
    ) -> dict:
        """
        Get comprehensive results for an experiment.

        Returns:
            Dict with experiment info, variant results, and statistics.
        """
        cache = get_cache()
        cache_key = CacheKeys.experiment_results(str(experiment_id))
        cached = await cache.get(cache_key)
        if cached:
            return cached

        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError("Experiment not found")

        variants = await self.get_variants(experiment_id)

        results_data = []
        for variant in variants:
            result = await self.db.execute(
                select(ExperimentResult).where(
                    ExperimentResult.experiment_id == experiment_id,
                    ExperimentResult.variant_id == variant.id
                )
            )
            result_record = result.scalar_one_or_none()

            if result_record:
                results_data.append({
                    "variant_id": str(variant.id),
                    "variant_name": variant.name,
                    "is_control": variant.is_control,
                    "visitors": result_record.visitors,
                    "conversions": result_record.conversions,
                    "conversion_rate": float(result_record.conversion_rate) if result_record.conversion_rate else 0,
                    "is_significant": result_record.is_significant,
                    "p_value": float(result_record.p_value) if result_record.p_value else None,
                    "confidence_level": float(result_record.confidence_level) if result_record.confidence_level else None,
                })

        # Get audit log
        audit_result = await self.db.execute(
            select(ExperimentAuditLog)
            .where(ExperimentAuditLog.experiment_id == experiment_id)
            .order_by(ExperimentAuditLog.created_at.desc())
        )
        audit_log = list(audit_result.scalars().all())

        results_payload = {
            "experiment": {
                "id": str(experiment.id),
                "name": experiment.name,
                "status": experiment.status,
                "traffic_split": experiment.traffic_split,
                "conversion_goal": experiment.conversion_goal,
                "start_date": experiment.start_date.isoformat() if experiment.start_date else None,
                "end_date": experiment.end_date.isoformat() if experiment.end_date else None,
                "winner_variant_id": str(experiment.winner_variant_id) if experiment.winner_variant_id else None,
                "winner_confidence": float(experiment.winner_confidence) if experiment.winner_confidence else None,
            },
            "variants": results_data,
            "audit_log": [
                {
                    "action": log.action,
                    "old_status": log.old_status,
                    "new_status": log.new_status,
                    "created_at": log.created_at.isoformat(),
                    "audit_data": log.audit_data,
                }
                for log in audit_log
            ],
        }
        await cache.set(cache_key, results_payload, ttl=CacheTTL.MEDIUM)
        return results_payload

    # ============================================================
    # Audit Logging
    # ============================================================

    async def _log_action(
        self,
        experiment_id: UUID,
        action: str,
        created_by_id: UUID,
        old_status: str | None = None,
        new_status: str | None = None,
        audit_data: dict | None = None,
    ) -> ExperimentAuditLog:
        """Log an experiment action for audit trail."""
        log = ExperimentAuditLog(
            id=uuid4(),
            experiment_id=experiment_id,
            action=action,
            old_status=old_status,
            new_status=new_status,
            audit_data=audit_data,
            created_at=datetime.utcnow(),
            created_by_id=created_by_id,
        )
        self.db.add(log)
        return log

    async def get_audit_log(
        self,
        experiment_id: UUID,
    ) -> list[ExperimentAuditLog]:
        """Get audit log for an experiment."""
        result = await self.db.execute(
            select(ExperimentAuditLog)
            .where(ExperimentAuditLog.experiment_id == experiment_id)
            .order_by(ExperimentAuditLog.created_at.desc())
        )
        return list(result.scalars().all())
