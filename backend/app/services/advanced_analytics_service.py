"""Advanced analytics service for funnels, cohorts, and insights.

This service extends the base analytics service with:
- Funnel analysis (drop-off rates, time to convert)
- Cohort analysis (retention by cohort)
- Insights and anomalies detection
- Segment comparison
"""

from datetime import date, datetime, timedelta
from typing import Optional, Literal
from collections import defaultdict
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, case, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.db.analytics import (
    AnalyticsEvent,
    AnalyticsSession,
    AnalyticsDaily,
    AnalyticsFunnel,
    AnalyticsCohort,
)


class AdvancedAnalyticsService:
    """Service for advanced analytics features."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Funnel Analysis
    # ============================================================

    async def create_funnel(
        self,
        project_id: UUID,
        name: str,
        steps: list[dict],
        created_by_id: UUID | None = None,
    ) -> AnalyticsFunnel:
        """
        Create a conversion funnel for analysis.

        Steps format:
        [
            {"name": "Visit", "event_type": "page_view", "filters": {"url": "/"}},
            {"name": "View Product", "event_type": "page_view", "filters": {"url": "/product"}},
            {"name": "Add to Cart", "event_type": "cta_click", "filters": {"element_id": "add-to-cart"}},
            {"name": "Purchase", "event_type": "form_submit", "filters": {"form_id": "checkout"}},
        ]
        """
        funnel = AnalyticsFunnel(
            id=uuid4(),
            project_id=project_id,
            name=name,
            steps=steps,
            created_at=datetime.utcnow(),
            created_by_id=created_by_id,
        )
        self.db.add(funnel)
        await self.db.commit()
        await self.db.refresh(funnel)
        return funnel

    async def analyze_funnel(
        self,
        project_id: UUID,
        funnel_def: dict,
        start_date: date | None = None,
        end_date: date | None = None,
        segment_by: str | None = None,
    ) -> dict:
        """
        Analyze a conversion funnel.

        Returns step-by-step conversion rates, drop-off, and time analysis.
        """
        end_date = end_date or date.today()
        start_date = start_date or (end_date - timedelta(days=30))

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        steps = funnel_def.get("steps", [])
        results = []

        # Base query - all visitors in the period
        base_visitors = await self._get_unique_visitors(
            project_id, start_dt, end_dt
        )

        cumulative_users = None  # Users who completed all previous steps

        for i, step in enumerate(steps):
            event_type = step.get("event_type")
            filters = step.get("filters", {})

            # Get users who completed this step
            step_users = await self._get_step_users(
                project_id, event_type, filters, start_dt, end_dt
            )

            # For first step, use all visitors as base
            if i == 0:
                cumulative_users = step_users
                conversion_rate = (step_users / base_visitors * 100) if base_visitors > 0 else 0
                dropped_from = 0
                dropped_from_pct = 0
            else:
                prev_users = results[-1]["step_users"]
                conversion_rate = (step_users / prev_users * 100) if prev_users > 0 else 0
                dropped_from = prev_users - step_users
                dropped_from_pct = ((prev_users - step_users) / prev_users * 100) if prev_users > 0 else 0

            # Calculate average time from previous step
            avg_time = None
            if i > 0 and step_users > 0:
                avg_time = await self._get_avg_time_between_steps(
                    project_id,
                    steps[i - 1],
                    step,
                    start_dt,
                    end_dt,
                )

            results.append({
                "step": i + 1,
                "name": step.get("name", f"Step {i + 1}"),
                "event_type": event_type,
                "step_users": step_users,
                "cumulative_pct": (step_users / base_visitors * 100) if base_visitors > 0 else 0,
                "conversion_rate": round(conversion_rate, 2),
                "dropped_from": dropped_from,
                "dropped_from_pct": round(dropped_from_pct, 2),
                "avg_time_seconds": avg_time,
            })

        # Overall completion rate
        completion_rate = (results[-1]["step_users"] / base_visitors * 100) if base_visitors > 0 else 0

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_visitors": base_visitors,
            "completion_rate": round(completion_rate, 2),
            "steps": results,
        }

    async def _get_unique_visitors(
        self,
        project_id: UUID,
        start_dt: datetime,
        end_dt: datetime,
    ) -> int:
        """Get count of unique visitors in a period."""
        result = await self.db.execute(
            select(func.count(func.distinct(AnalyticsEvent.visitor_id)))
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.timestamp >= start_dt,
                    AnalyticsEvent.timestamp <= end_dt,
                )
            )
        )
        return result.scalar() or 0

    async def _get_step_users(
        self,
        project_id: UUID,
        event_type: str,
        filters: dict,
        start_dt: datetime,
        end_dt: datetime,
    ) -> int:
        """Get count of unique users who completed a step."""
        query = select(func.count(func.distinct(AnalyticsEvent.visitor_id)))
        query = query.select_from(AnalyticsEvent).where(
            and_(
                AnalyticsEvent.project_id == project_id,
                AnalyticsEvent.event_type == event_type,
                AnalyticsEvent.timestamp >= start_dt,
                AnalyticsEvent.timestamp <= end_dt,
            )
        )

        # Apply filters on properties JSONB
        for key, value in filters.items():
            if isinstance(value, str):
                query = query.where(AnalyticsEvent.properties[key].astext == value)
            else:
                query = query.where(AnalyticsEvent.properties[key].astext == str(value))

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _get_avg_time_between_steps(
        self,
        project_id: UUID,
        step_from: dict,
        step_to: dict,
        start_dt: datetime,
        end_dt: datetime,
    ) -> float | None:
        """
        Calculate average time for users to go from step A to step B.

        This is complex - we need to find pairs of events from the same visitor.
        For now, return a simplified calculation.
        """
        # Simplified: get timestamps of both events and calculate difference
        # In production, this would use window functions or multiple queries
        return None  # TODO: Implement with proper time-to-convert analysis

    # ============================================================
    # Cohort Analysis
    # ============================================================

    async def create_cohort(
        self,
        project_id: UUID,
        cohort_type: Literal["signup", "first_visit", "acquisition_channel"],
        cohort_date: date,
        initial_size: int,
        period_data: dict,
    ) -> AnalyticsCohort:
        """
        Create or update a cohort analysis record.

        cohort_type:
        - signup: Users who signed up on a given date
        - first_visit: Users who first visited on a given date
        - acquisition_channel: Users acquired via a specific channel

        period_data: {"day_0": N, "day_7": M, "day_30": P, ...}
        """
        cohort_label = f"{cohort_type}_{cohort_date.isoformat()}"

        # Check if exists
        result = await self.db.execute(
            select(AnalyticsCohort).where(
                and_(
                    AnalyticsCohort.project_id == project_id,
                    AnalyticsCohort.cohort_type == cohort_type,
                    AnalyticsCohort.cohort_date == cohort_date,
                )
            )
        )
        cohort = result.scalar_one_or_none()

        if cohort:
            # Update
            cohort.initial_size = initial_size
            cohort.period_data = period_data
        else:
            # Create
            cohort = AnalyticsCohort(
                id=uuid4(),
                project_id=project_id,
                cohort_type=cohort_type,
                cohort_date=cohort_date,
                cohort_label=cohort_label,
                initial_size=initial_size,
                period_data=period_data,
                created_at=datetime.utcnow(),
            )
            self.db.add(cohort)

        await self.db.commit()
        await self.db.refresh(cohort)
        return cohort

    async def calculate_retention_cohort(
        self,
        project_id: UUID,
        start_date: date | None = None,
        periods: int = 8,
        period_days: int = 7,
    ) -> list[dict]:
        """
        Calculate retention by signup week cohort.

        Returns a matrix showing what % of each cohort is still active.
        """
        start_date = start_date or (date.today() - timedelta(weeks=periods))

        cohorts = []

        # Get weekly signup cohorts from daily aggregates
        for week in range(periods):
            cohort_start = start_date + timedelta(weeks=week)
            cohort_end = cohort_start + timedelta(days=6)

            # Sum users who signed up this week
            result = await self.db.execute(
                select(func.sum(AnalyticsDaily.unique_visitors))
                .where(
                    and_(
                        AnalyticsDaily.project_id == project_id,
                        AnalyticsDaily.date >= cohort_start,
                        AnalyticsDaily.date <= cohort_end,
                    )
                )
            )
            cohort_size = result.scalar() or 0

            if cohort_size == 0:
                continue

            # Calculate retention for subsequent periods
            retention_data = {
                "cohort": cohort_start.isoformat(),
                "size": cohort_size,
                "periods": [],
            }

            for period in range(periods - week):
                period_start = cohort_start + timedelta(days=period * period_days)
                period_end = period_start + timedelta(days=period_days - 1)

                # Get unique visitors in this period (retained users)
                result = await self.db.execute(
                    select(func.sum(AnalyticsDaily.unique_visitors))
                    .where(
                        and_(
                            AnalyticsDaily.project_id == project_id,
                            AnalyticsDaily.date >= period_start,
                            AnalyticsDaily.date <= period_end,
                        )
                    )
                )
                retained = result.scalar() or 0

                retention_pct = (retained / cohort_size * 100) if cohort_size > 0 else 0

                retention_data["periods"].append({
                    "period": period,
                    "start_date": period_start.isoformat(),
                    "end_date": period_end.isoformat(),
                    "retained": retained,
                    "retention_pct": round(retention_pct, 1),
                })

            cohorts.append(retention_data)

        return cohorts

    async def get_channel_cohorts(
        self,
        project_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """
        Analyze cohorts by acquisition channel (UTM source).

        Shows performance of different traffic sources.
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        # Get visitors by UTM source
        result = await self.db.execute(
            select(
                AnalyticsEvent.utm_source,
                func.count(func.distinct(AnalyticsEvent.visitor_id)).label("visitors"),
                func.count(AnalyticsEvent.id).label("events"),
            )
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.timestamp >= start_dt,
                    AnalyticsEvent.timestamp <= end_dt,
                    AnalyticsEvent.utm_source.isnot(None),
                )
            )
            .group_by(AnalyticsEvent.utm_source)
            .order_by(func.count(func.distinct(AnalyticsEvent.visitor_id)).desc())
        )

        channels = []
        for row in result:
            source = row.utm_source or "Direct"

            # Get conversion rate for this channel
            cta_result = await self.db.execute(
                select(func.count(AnalyticsEvent.id))
                .where(
                    and_(
                        AnalyticsEvent.project_id == project_id,
                        AnalyticsEvent.event_type == "cta_click",
                        AnalyticsEvent.utm_source == source,
                        AnalyticsEvent.timestamp >= start_dt,
                        AnalyticsEvent.timestamp <= end_dt,
                    )
                )
            )
            ctas = cta_result.scalar() or 0

            conversion_rate = (ctas / row.visitors * 100) if row.visitors > 0 else 0

            channels.append({
                "source": source,
                "visitors": row.visitors,
                "events": row.events,
                "avg_events_per_visitor": round(row.events / row.visitors, 1) if row.visitors > 0 else 0,
                "conversions": ctas,
                "conversion_rate": round(conversion_rate, 2),
            })

        return channels

    # ============================================================
    # Insights & Anomalies
    # ============================================================

    async def get_insights(
        self,
        project_id: UUID,
        days: int = 30,
    ) -> dict:
        """
        Generate actionable insights from analytics data.

        Detects:
        - Traffic spikes/drops
        - Conversion rate changes
        - Best performing pages
        - Traffic source trends
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        prev_start = start_date - timedelta(days=days)

        # Get current and previous period data
        current_data = await self._get_period_summary(project_id, start_date, end_date)
        previous_data = await self._get_period_summary(project_id, prev_start, start_date)

        insights = []
        trends = {}

        # Compare metrics
        for metric in ["views", "unique_visitors", "cta_clicks", "form_submissions"]:
            current = current_data.get(metric, 0)
            previous = previous_data.get(metric, 0)

            if previous > 0:
                change_pct = ((current - previous) / previous) * 100
                trends[metric] = {
                    "current": current,
                    "previous": previous,
                    "change_pct": round(change_pct, 1),
                }

                # Generate insight for significant changes
                if abs(change_pct) >= 20:
                    if change_pct > 0:
                        insights.append({
                            "type": "positive",
                            "metric": metric,
                            "message": f"{metric.replace('_', ' ').title()} increased by {change_pct:.1f}% vs previous period",
                        })
                    else:
                        insights.append({
                            "type": "negative",
                            "metric": metric,
                            "message": f"{metric.replace('_', ' ').title()} decreased by {abs(change_pct):.1f}% vs previous period",
                        })

        # Best performing pages
        top_pages = await self._get_top_pages(project_id, start_date, end_date, limit=5)

        # Traffic source breakdown
        sources = await self._get_traffic_sources(project_id, start_date, end_date)

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days,
            },
            "insights": insights,
            "trends": trends,
            "top_pages": top_pages,
            "traffic_sources": sources,
        }

    async def _get_period_summary(
        self,
        project_id: UUID,
        start_date: date,
        end_date: date,
    ) -> dict:
        """Get aggregated metrics for a date range."""
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        # Sum from daily aggregates
        result = await self.db.execute(
            select(
                func.sum(AnalyticsDaily.views).label("views"),
                func.sum(AnalyticsDaily.unique_visitors).label("unique_visitors"),
                func.sum(AnalyticsDaily.cta_clicks).label("cta_clicks"),
                func.sum(AnalyticsDaily.form_submissions).label("form_submissions"),
            )
            .where(
                and_(
                    AnalyticsDaily.project_id == project_id,
                    AnalyticsDaily.date >= start_date,
                    AnalyticsDaily.date <= end_date,
                )
            )
        )

        row = result.one()
        return {
            "views": row.views or 0,
            "unique_visitors": row.unique_visitors or 0,
            "cta_clicks": row.cta_clicks or 0,
            "form_submissions": row.form_submissions or 0,
        }

    async def _get_top_pages(
        self,
        project_id: UUID,
        start_date: date,
        end_date: date,
        limit: int = 5,
    ) -> list[dict]:
        """Get most visited pages from event properties."""
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        result = await self.db.execute(
            select(
                AnalyticsEvent.properties["url"].astext.label("url"),
                func.count(AnalyticsEvent.id).label("views"),
            )
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.event_type == "page_view",
                    AnalyticsEvent.timestamp >= start_dt,
                    AnalyticsEvent.timestamp <= end_dt,
                    AnalyticsEvent.properties["url"].isnot(None),
                )
            )
            .group_by(AnalyticsEvent.properties["url"].astext)
            .order_by(func.count(AnalyticsEvent.id).desc())
            .limit(limit)
        )

        return [{"url": row.url, "views": row.views} for row in result]

    async def _get_traffic_sources(
        self,
        project_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """Get breakdown by traffic source."""
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        result = await self.db.execute(
            select(
                func.coalesce(AnalyticsEvent.utm_source, "Direct").label("source"),
                func.count(func.distinct(AnalyticsEvent.visitor_id)).label("visitors"),
            )
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.timestamp >= start_dt,
                    AnalyticsEvent.timestamp <= end_dt,
                )
            )
            .group_by(func.coalesce(AnalyticsEvent.utm_source, "Direct"))
            .order_by(func.count(func.distinct(AnalyticsEvent.visitor_id)).desc())
        )

        total_visitors = sum(row.visitors for row in result)

        return [
            {
                "source": row.source,
                "visitors": row.visitors,
                "percentage": round((row.visitors / total_visitors * 100), 1) if total_visitors > 0 else 0,
            }
            for row in result
        ]

    # ============================================================
    # Real-time and Session Analytics
    # ============================================================

    async def get_active_sessions(
        self,
        project_id: UUID,
        minutes: int = 5,
    ) -> list[dict]:
        """
        Get currently active sessions.

        Returns sessions with activity in the last N minutes.
        """
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)

        result = await self.db.execute(
            select(
                AnalyticsSession.id,
                AnalyticsSession.visitor_id,
                AnalyticsSession.started_at,
                AnalyticsSession.page_views,
                AnalyticsSession.entry_page,
                AnalyticsSession.device_type,
            )
            .where(
                and_(
                    AnalyticsSession.project_id == project_id,
                    AnalyticsSession.started_at >= cutoff,
                    AnalyticsSession.ended_at.is_(None),
                )
            )
            .order_by(AnalyticsSession.started_at.desc())
        )

        sessions = []
        for row in result:
            # Calculate duration (in progress)
            duration_seconds = int((datetime.utcnow() - row.started_at).total_seconds())

            sessions.append({
                "session_id": row.id,
                "visitor_id": row.visitor_id,
                "started_at": row.started_at.isoformat(),
                "duration_seconds": duration_seconds,
                "page_views": row.page_views,
                "entry_page": row.entry_page,
                "device_type": row.device_type,
            })

        return sessions

    async def get_session_recording(
        self,
        session_id: str,
    ) -> dict | None:
        """
        Get detailed session recording (events timeline).

        Useful for replaying user journeys.
        """
        result = await self.db.execute(
            select(AnalyticsSession).where(AnalyticsSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            return None

        # Get all events for this session
        events_result = await self.db.execute(
            select(AnalyticsEvent)
            .where(
                and_(
                    AnalyticsEvent.session_id == session_id,
                )
            )
            .order_by(AnalyticsEvent.timestamp)
        )

        events = []
        for event in events_result.scalars():
            events.append({
                "type": event.event_type,
                "name": event.event_name,
                "properties": event.properties,
                "timestamp": event.timestamp.isoformat(),
            })

        return {
            "session_id": session.id,
            "visitor_id": session.visitor_id,
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "duration_seconds": session.duration_seconds,
            "page_views": session.page_views,
            "events": session.events,
            "entry_page": session.entry_page,
            "exit_page": session.exit_page,
            "device_type": session.device_type,
            "timeline": events,
        }

    # ============================================================
    # Attribution & Heatmaps
    # ============================================================

    async def get_attribution(
        self,
        project_id: UUID,
        start_date: date,
        end_date: date,
        model: Literal["first_touch", "last_touch", "linear"] = "first_touch",
    ) -> list[dict]:
        """
        Calculate attribution by traffic source.

        Uses form_submit events as conversions.
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        # Fetch touchpoints
        touchpoints_result = await self.db.execute(
            select(
                AnalyticsEvent.visitor_id,
                AnalyticsEvent.utm_source,
                AnalyticsEvent.utm_medium,
                AnalyticsEvent.timestamp,
            )
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.timestamp >= start_dt,
                    AnalyticsEvent.timestamp <= end_dt,
                    AnalyticsEvent.utm_source.isnot(None),
                )
            )
            .order_by(AnalyticsEvent.visitor_id, AnalyticsEvent.timestamp)
        )

        touchpoints_by_visitor: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for row in touchpoints_result:
            touchpoints_by_visitor[row.visitor_id].append(
                (row.utm_source or "Direct", row.utm_medium or "")
            )

        # Fetch conversions
        conversions_result = await self.db.execute(
            select(
                AnalyticsEvent.visitor_id,
                func.count(AnalyticsEvent.id).label("conversions"),
            )
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.event_type == "form_submit",
                    AnalyticsEvent.timestamp >= start_dt,
                    AnalyticsEvent.timestamp <= end_dt,
                )
            )
            .group_by(AnalyticsEvent.visitor_id)
        )
        conversions = {row.visitor_id: row.conversions for row in conversions_result}

        attribution: dict[tuple[str, str], float] = defaultdict(float)

        for visitor_id, conversion_count in conversions.items():
            touches = touchpoints_by_visitor.get(visitor_id, [])
            if not touches:
                continue

            if model == "first_touch":
                source, medium = touches[0]
                attribution[(source, medium)] += conversion_count
            elif model == "last_touch":
                source, medium = touches[-1]
                attribution[(source, medium)] += conversion_count
            else:
                weight = conversion_count / len(touches)
                for source, medium in touches:
                    attribution[(source, medium)] += weight

        total = sum(attribution.values()) or 0

        return [
            {
                "source": source,
                "medium": medium,
                "conversions": round(value, 2),
                "attributed_value": round((value / total) * 100, 2) if total > 0 else 0,
            }
            for (source, medium), value in sorted(
                attribution.items(), key=lambda item: item[1], reverse=True
            )
        ]

    async def get_heatmap(
        self,
        project_id: UUID,
        page_url: str,
        start_date: date,
        end_date: date,
        grid: int = 20,
    ) -> dict:
        """
        Aggregate click events into a heatmap grid.
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        result = await self.db.execute(
            select(AnalyticsEvent.properties)
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.event_type == "click",
                    AnalyticsEvent.timestamp >= start_dt,
                    AnalyticsEvent.timestamp <= end_dt,
                    AnalyticsEvent.properties["url"].astext == page_url,
                )
            )
        )

        bucket_counts: dict[tuple[int, int], int] = defaultdict(int)
        bucket_size = 100 / grid if grid > 0 else 5

        for row in result:
            props = row.properties or {}
            try:
                x = float(props.get("x", 0))
                y = float(props.get("y", 0))
            except (TypeError, ValueError):
                continue

            x_bucket = min(grid - 1, max(0, int(x // bucket_size)))
            y_bucket = min(grid - 1, max(0, int(y // bucket_size)))
            bucket_counts[(x_bucket, y_bucket)] += 1

        points = []
        for (x_bucket, y_bucket), count in bucket_counts.items():
            points.append({
                "x": round((x_bucket + 0.5) * bucket_size, 2),
                "y": round((y_bucket + 0.5) * bucket_size, 2),
                "intensity": count,
            })

        return {
            "page_url": page_url,
            "grid": grid,
            "points": points,
            "total": sum(bucket_counts.values()),
        }
