"""Analytics service using PostgreSQL for persistent storage."""

import hashlib
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select, func, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.db.analytics import (
    AnalyticsEvent,
    AnalyticsSession,
    AnalyticsDaily,
    AnalyticsFunnel,
    AnalyticsCohort,
)
from app.models.db import Project


class AnalyticsService:
    """Service for tracking and querying analytics data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Event Tracking
    # ============================================================

    async def track_event(
        self,
        project_id: UUID,
        visitor_id: str,
        event_type: str,
        properties: dict,
        context: dict | None = None,
    ) -> AnalyticsEvent:
        """
        Track a raw analytics event.

        Args:
            project_id: Project UUID
            visitor_id: Unique visitor identifier (hashed)
            event_type: Event type (page_view, cta_click, form_submit, etc.)
            properties: Event-specific properties
            context: Request context (referrer, UTM params, device, geo)
        """
        timestamp = datetime.utcnow()
        session_id = context.get("session_id") if context else None
        day_start = datetime.combine(timestamp.date(), datetime.min.time())
        day_end = datetime.combine(timestamp.date(), datetime.max.time())

        is_new_visitor = await self._is_new_daily_visitor(
            project_id, visitor_id, day_start, day_end
        )
        is_new_session = False
        if session_id:
            is_new_session = await self._is_new_daily_session(
                project_id, session_id, day_start, day_end
            )

        event = AnalyticsEvent(
            id=uuid4(),
            project_id=project_id,
            visitor_id=visitor_id,
            session_id=session_id,
            event_type=event_type,
            event_name=properties.get("name"),
            properties=properties,
            # Context metadata
            referrer=context.get("referrer") if context else None,
            utm_source=context.get("utm_source") if context else None,
            utm_medium=context.get("utm_medium") if context else None,
            utm_campaign=context.get("utm_campaign") if context else None,
            device_type=context.get("device_type", "desktop") if context else "desktop",
            browser=context.get("browser") if context else None,
            country=context.get("country") if context else None,
            city=context.get("city") if context else None,
            timestamp=timestamp,
        )
        self.db.add(event)

        await self._upsert_daily_metrics(
            project_id=project_id,
            target_date=timestamp.date(),
            event_type=event_type,
            is_new_visitor=is_new_visitor,
            is_new_session=is_new_session,
            timestamp=timestamp,
        )

        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def track_events_batch(
        self,
        project_id: UUID,
        events: list[dict],
    ) -> None:
        """Batch insert analytics events and update daily aggregates."""
        if not events:
            return

        seen_visitors: set[tuple[str, date]] = set()
        seen_sessions: set[tuple[str, date]] = set()
        visitor_cache: dict[tuple[str, date], bool] = {}
        session_cache: dict[tuple[str, date], bool] = {}
        daily_increments: dict[date, dict[str, int]] = {}
        event_rows: list[dict] = []

        for event in events:
            timestamp: datetime = event.get("timestamp") or datetime.utcnow()
            day = timestamp.date()
            day_start = datetime.combine(day, datetime.min.time())
            day_end = datetime.combine(day, datetime.max.time())

            visitor_id = event["visitor_id"]
            session_id = event.get("session_id")

            visitor_key = (visitor_id, day)
            if visitor_key in seen_visitors:
                is_new_visitor = False
            else:
                cached = visitor_cache.get(visitor_key)
                if cached is None:
                    cached = await self._is_new_daily_visitor(
                        project_id, visitor_id, day_start, day_end
                    )
                    visitor_cache[visitor_key] = cached
                is_new_visitor = cached
                seen_visitors.add(visitor_key)

            is_new_session = False
            if session_id:
                session_key = (session_id, day)
                if session_key in seen_sessions:
                    is_new_session = False
                else:
                    cached_session = session_cache.get(session_key)
                    if cached_session is None:
                        cached_session = await self._is_new_daily_session(
                            project_id, session_id, day_start, day_end
                        )
                        session_cache[session_key] = cached_session
                    is_new_session = cached_session
                    seen_sessions.add(session_key)

            increments = daily_increments.setdefault(
                day,
                {
                    "views": 0,
                    "unique_visitors": 0,
                    "sessions": 0,
                    "cta_clicks": 0,
                    "form_submissions": 0,
                },
            )

            event_type = event["event_type"]
            if event_type == "page_view":
                increments["views"] += 1
            elif event_type == "cta_click":
                increments["cta_clicks"] += 1
            elif event_type == "form_submit":
                increments["form_submissions"] += 1

            if is_new_visitor:
                increments["unique_visitors"] += 1
            if is_new_session:
                increments["sessions"] += 1

            context = event.get("context") or {}
            properties = event.get("properties") or {}

            event_rows.append({
                "id": uuid4(),
                "project_id": project_id,
                "visitor_id": visitor_id,
                "session_id": session_id,
                "event_type": event_type,
                "event_name": properties.get("name"),
                "properties": properties,
                "referrer": context.get("referrer"),
                "utm_source": context.get("utm_source"),
                "utm_medium": context.get("utm_medium"),
                "utm_campaign": context.get("utm_campaign"),
                "device_type": context.get("device_type", "desktop"),
                "browser": context.get("browser"),
                "country": context.get("country"),
                "city": context.get("city"),
                "timestamp": timestamp,
            })

        if event_rows:
            await self.db.execute(insert(AnalyticsEvent), event_rows)

        for day, increments in daily_increments.items():
            await self._upsert_daily_metrics_batch(
                project_id=project_id,
                target_date=day,
                increments=increments,
                updated_at=datetime.utcnow(),
            )

        await self.db.commit()

    async def _is_new_daily_visitor(
        self,
        project_id: UUID,
        visitor_id: str,
        day_start: datetime,
        day_end: datetime,
    ) -> bool:
        result = await self.db.execute(
            select(AnalyticsEvent.id)
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.visitor_id == visitor_id,
                    AnalyticsEvent.timestamp >= day_start,
                    AnalyticsEvent.timestamp <= day_end,
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is None

    async def _is_new_daily_session(
        self,
        project_id: UUID,
        session_id: str,
        day_start: datetime,
        day_end: datetime,
    ) -> bool:
        result = await self.db.execute(
            select(AnalyticsEvent.id)
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.session_id == session_id,
                    AnalyticsEvent.timestamp >= day_start,
                    AnalyticsEvent.timestamp <= day_end,
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is None

    async def _upsert_daily_metrics(
        self,
        project_id: UUID,
        target_date: date,
        event_type: str,
        is_new_visitor: bool,
        is_new_session: bool,
        timestamp: datetime,
    ) -> None:
        inc_views = 1 if event_type == "page_view" else 0
        inc_cta = 1 if event_type == "cta_click" else 0
        inc_form = 1 if event_type == "form_submit" else 0
        inc_unique = 1 if is_new_visitor else 0
        inc_sessions = 1 if is_new_session else 0

        if not any([inc_views, inc_cta, inc_form, inc_unique, inc_sessions]):
            return

        stmt = insert(AnalyticsDaily).values(
            id=uuid4(),
            project_id=project_id,
            date=target_date,
            views=inc_views,
            unique_visitors=inc_unique,
            sessions=inc_sessions,
            cta_clicks=inc_cta,
            form_submissions=inc_form,
            created_at=timestamp,
            updated_at=timestamp,
        ).on_conflict_do_update(
            index_elements=["project_id", "date"],
            set_={
                "views": AnalyticsDaily.views + inc_views,
                "unique_visitors": AnalyticsDaily.unique_visitors + inc_unique,
                "sessions": AnalyticsDaily.sessions + inc_sessions,
                "cta_clicks": AnalyticsDaily.cta_clicks + inc_cta,
                "form_submissions": AnalyticsDaily.form_submissions + inc_form,
                "updated_at": timestamp,
            },
        )
        await self.db.execute(stmt)

    async def _upsert_daily_metrics_batch(
        self,
        project_id: UUID,
        target_date: date,
        increments: dict[str, int],
        updated_at: datetime,
    ) -> None:
        if not increments:
            return

        inc_views = increments.get("views", 0)
        inc_unique = increments.get("unique_visitors", 0)
        inc_sessions = increments.get("sessions", 0)
        inc_cta = increments.get("cta_clicks", 0)
        inc_form = increments.get("form_submissions", 0)

        if not any([inc_views, inc_unique, inc_sessions, inc_cta, inc_form]):
            return

        stmt = insert(AnalyticsDaily).values(
            id=uuid4(),
            project_id=project_id,
            date=target_date,
            views=inc_views,
            unique_visitors=inc_unique,
            sessions=inc_sessions,
            cta_clicks=inc_cta,
            form_submissions=inc_form,
            created_at=updated_at,
            updated_at=updated_at,
        ).on_conflict_do_update(
            index_elements=["project_id", "date"],
            set_={
                "views": AnalyticsDaily.views + inc_views,
                "unique_visitors": AnalyticsDaily.unique_visitors + inc_unique,
                "sessions": AnalyticsDaily.sessions + inc_sessions,
                "cta_clicks": AnalyticsDaily.cta_clicks + inc_cta,
                "form_submissions": AnalyticsDaily.form_submissions + inc_form,
                "updated_at": updated_at,
            },
        )
        await self.db.execute(stmt)

    async def track_page_view(
        self,
        project_id: UUID,
        visitor_id: str,
        session_id: str | None,
        page_url: str,
        page_title: str | None = None,
        context: dict | None = None,
    ) -> tuple[AnalyticsEvent, AnalyticsSession | None]:
        """
        Track a page view and update session.

        Returns the event and (optionally) updated session.
        """
        # Create page view event
        event = await self.track_event(
            project_id=project_id,
            visitor_id=visitor_id,
            event_type="page_view",
            properties={"url": page_url, "title": page_title},
            context=context or {},
        )

        # Update session if provided
        session = None
        if session_id:
            session = await self._update_session(
                session_id=session_id,
                visitor_id=visitor_id,
                project_id=project_id,
                page_url=page_url,
                device_type=context.get("device_type", "desktop") if context else "desktop",
                browser=context.get("browser") if context else None,
                country=context.get("country") if context else None,
            )

        return event, session

    async def track_cta_click(
        self,
        project_id: UUID,
        visitor_id: str,
        element_id: str,
        element_text: str | None = None,
        context: dict | None = None,
    ) -> AnalyticsEvent:
        """Track a CTA click event."""
        return await self.track_event(
            project_id=project_id,
            visitor_id=visitor_id,
            event_type="cta_click",
            properties={
                "element_id": element_id,
                "element_text": element_text,
            },
            context=context,
        )

    async def track_form_submit(
        self,
        project_id: UUID,
        visitor_id: str,
        form_id: str,
        form_data: dict | None = None,
        context: dict | None = None,
    ) -> AnalyticsEvent:
        """Track a form submission event."""
        return await self.track_event(
            project_id=project_id,
            visitor_id=visitor_id,
            event_type="form_submit",
            properties={
                "form_id": form_id,
                "form_fields": list(form_data.keys()) if form_data else [],
            },
            context=context,
        )

    # ============================================================
    # Session Management
    # ============================================================

    async def _update_session(
        self,
        session_id: str,
        visitor_id: str,
        project_id: UUID,
        page_url: str,
        device_type: str = "desktop",
        browser: str | None = None,
        country: str | None = None,
    ) -> AnalyticsSession | None:
        """Update an existing session with new page view or create one if missing."""
        result = await self.db.execute(
            select(AnalyticsSession).where(AnalyticsSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if session:
            # Update session stats
            session.page_views += 1
            session.events += 1
            session.exit_page = page_url
            # Duration will be calculated when session ends
        else:
            session = AnalyticsSession(
                id=session_id,
                visitor_id=visitor_id,
                project_id=project_id,
                started_at=datetime.utcnow(),
                entry_page=page_url,
                exit_page=page_url,
                page_views=1,
                events=1,
                device_type=device_type,
                browser=browser,
                country=country,
            )
            self.db.add(session)

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_or_create_session(
        self,
        visitor_id: str,
        project_id: UUID,
        entry_page: str,
        device_type: str = "desktop",
        browser: str | None = None,
        country: str | None = None,
    ) -> AnalyticsSession:
        """
        Get existing active session or create a new one.

        Sessions are considered active if less than 30 minutes old.
        """
        # Look for recent session from this visitor
        cutoff = datetime.utcnow() - timedelta(minutes=30)
        result = await self.db.execute(
            select(AnalyticsSession)
            .where(
                and_(
                    AnalyticsSession.visitor_id == visitor_id,
                    AnalyticsSession.project_id == project_id,
                    AnalyticsSession.started_at >= cutoff,
                    AnalyticsSession.ended_at.is_(None),
                )
            )
            .order_by(AnalyticsSession.started_at.desc())
            .limit(1)
        )
        session = result.scalar_one_or_none()

        if session:
            return session

        # Create new session
        session = AnalyticsSession(
            id=self._generate_session_id(),
            visitor_id=visitor_id,
            project_id=project_id,
            started_at=datetime.utcnow(),
            entry_page=entry_page,
            exit_page=entry_page,
            page_views=1,
            events=1,
            device_type=device_type,
            browser=browser,
            country=country,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def end_session(self, session_id: str) -> None:
        """Mark a session as ended and calculate duration."""
        result = await self.db.execute(
            select(AnalyticsSession).where(AnalyticsSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if session and not session.ended_at:
            session.ended_at = datetime.utcnow()
            if session.started_at:
                session.duration_seconds = int(
                    (session.ended_at - session.started_at).total_seconds()
                )
            await self.db.commit()

    # ============================================================
    # Daily Aggregation
    # ============================================================

    async def get_or_create_daily(
        self, project_id: UUID, date: date
    ) -> AnalyticsDaily:
        """Get or create daily analytics record."""
        result = await self.db.execute(
            select(AnalyticsDaily).where(
                and_(
                    AnalyticsDaily.project_id == project_id,
                    AnalyticsDaily.date == date,
                )
            )
        )
        daily = result.scalar_one_or_none()

        if not daily:
            daily = AnalyticsDaily(
                id=uuid4(),
                project_id=project_id,
                date=date,
                views=0,
                unique_visitors=0,
                sessions=0,
                cta_clicks=0,
                form_submissions=0,
                device_counts={},
                top_pages={},
                traffic_sources={},
            )
            self.db.add(daily)
            await self.db.commit()
            await self.db.refresh(daily)

        return daily

    async def update_daily_aggregates(
        self, project_id: UUID, target_date: date | None = None
    ) -> AnalyticsDaily:
        """
        Recalculate daily aggregates from raw events.

        This is expensive - should be run asynchronously or scheduled.
        """
        target_date = target_date or date.today()

        # Get daily record
        daily = await self.get_or_create_daily(project_id, target_date)

        # Calculate views from raw events
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())

        # Page views
        views_result = await self.db.execute(
            select(func.count())
            .select_from(AnalyticsEvent)
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.event_type == "page_view",
                    AnalyticsEvent.timestamp >= start,
                    AnalyticsEvent.timestamp <= end,
                )
            )
        )
        daily.views = views_result.scalar() or 0

        # Unique visitors
        visitors_result = await self.db.execute(
            select(func.count(func.distinct(AnalyticsEvent.visitor_id)))
            .select_from(AnalyticsEvent)
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.timestamp >= start,
                    AnalyticsEvent.timestamp <= end,
                )
            )
        )
        daily.unique_visitors = visitors_result.scalar() or 0

        # CTA clicks
        cta_result = await self.db.execute(
            select(func.count())
            .select_from(AnalyticsEvent)
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.event_type == "cta_click",
                    AnalyticsEvent.timestamp >= start,
                    AnalyticsEvent.timestamp <= end,
                )
            )
        )
        daily.cta_clicks = cta_result.scalar() or 0

        # Form submissions
        form_result = await self.db.execute(
            select(func.count())
            .select_from(AnalyticsEvent)
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.event_type == "form_submit",
                    AnalyticsEvent.timestamp >= start,
                    AnalyticsEvent.timestamp <= end,
                )
            )
        )
        daily.form_submissions = form_result.scalar() or 0

        # Sessions from today
        sessions_result = await self.db.execute(
            select(func.count())
            .select_from(AnalyticsSession)
            .where(
                and_(
                    AnalyticsSession.project_id == project_id,
                    AnalyticsSession.started_at >= start,
                    AnalyticsSession.started_at <= end,
                )
            )
        )
        daily.sessions = sessions_result.scalar() or 0

        # Device breakdown
        device_result = await self.db.execute(
            select(
                AnalyticsEvent.device_type,
                func.count().label("count"),
            )
            .select_from(AnalyticsEvent)
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.timestamp >= start,
                    AnalyticsEvent.timestamp <= end,
                )
            )
            .group_by(AnalyticsEvent.device_type)
        )
        daily.device_counts = {row.device_type: row.count for row in device_result}

        await self.db.commit()
        await self.db.refresh(daily)

        return daily

    # ============================================================
    # Dashboard Queries
    # ============================================================

    async def get_analytics_dashboard(
        self,
        project_id: UUID,
        days: int = 30,
    ) -> dict:
        """
        Get dashboard data for a project.

        Returns totals, trends, and daily breakdown.
        """
        days = min(90, max(7, days))

        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # Get pre-aggregated daily data
        result = await self.db.execute(
            select(AnalyticsDaily)
            .where(
                and_(
                    AnalyticsDaily.project_id == project_id,
                    AnalyticsDaily.date >= start_date,
                    AnalyticsDaily.date <= end_date,
                )
            )
            .order_by(AnalyticsDaily.date)
        )
        daily_data = list(result.scalars().all())

        # Calculate totals
        totals = {
            "views": sum(d.views for d in daily_data),
            "unique_visitors": sum(d.unique_visitors for d in daily_data),
            "sessions": sum(d.sessions for d in daily_data),
            "cta_clicks": sum(d.cta_clicks for d in daily_data),
            "form_submissions": sum(d.form_submissions for d in daily_data),
        }

        # Calculate trends
        prev_start = start_date - timedelta(days=days)
        prev_end = start_date - timedelta(days=1)
        prev_result = await self.db.execute(
            select(AnalyticsDaily)
            .where(
                and_(
                    AnalyticsDaily.project_id == project_id,
                    AnalyticsDaily.date >= prev_start,
                    AnalyticsDaily.date <= prev_end,
                )
            )
        )
        prev_data = list(prev_result.scalars().all())

        prev_totals = {
            "views": sum(d.views for d in prev_data),
            "unique_visitors": sum(d.unique_visitors for d in prev_data),
        }

        trends = {
            "views": self._calculate_trend(totals["views"], prev_totals["views"]),
            "visitors": self._calculate_trend(
                totals["unique_visitors"], prev_totals["unique_visitors"]
            ),
        }

        # Build daily breakdown
        daily_map = {d.date: d for d in daily_data}
        filled_daily = []
        current = start_date
        while current <= end_date:
            if current in daily_map:
                d = daily_map[current]
                filled_daily.append({
                    "date": d.date.isoformat(),
                    "views": d.views,
                    "visitors": d.unique_visitors,
                    "sessions": d.sessions,
                    "clicks": d.cta_clicks,
                    "submissions": d.form_submissions,
                })
            else:
                filled_daily.append({
                    "date": current.isoformat(),
                    "views": 0,
                    "visitors": 0,
                    "sessions": 0,
                    "clicks": 0,
                    "submissions": 0,
                })
            current += timedelta(days=1)

        # Additional breakdowns for advanced dashboard
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        top_pages = await self._get_top_pages(project_id, start_dt, end_dt, limit=10)
        traffic_sources = await self._get_traffic_sources(project_id, start_dt, end_dt, limit=10)
        device_breakdown = await self._get_device_breakdown(project_id, start_dt, end_dt)
        geo_breakdown = await self._get_geo_breakdown(project_id, start_dt, end_dt)
        bounce_rate = await self._get_bounce_rate(project_id, start_dt, end_dt)
        avg_session_duration = await self._get_avg_session_duration(project_id, start_dt, end_dt)
        realtime = await self.get_realtime_stats(project_id)

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days,
            },
            "totals": totals,
            "trends": trends,
            "daily": filled_daily,
            "kpis": {
                "bounce_rate": bounce_rate,
                "avg_session_duration": avg_session_duration,
            },
            "breakdowns": {
                "top_pages": top_pages,
                "traffic_sources": traffic_sources,
                "device": device_breakdown,
                "geo": geo_breakdown,
            },
            "realtime": realtime,
        }

    async def get_realtime_stats(self, project_id: UUID) -> dict:
        """Get real-time stats for the last 5 minutes."""
        cutoff = datetime.utcnow() - timedelta(minutes=5)

        # Recent page views
        views_result = await self.db.execute(
            select(func.count())
            .select_from(AnalyticsEvent)
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.event_type == "page_view",
                    AnalyticsEvent.timestamp >= cutoff,
                )
            )
        )
        views = views_result.scalar() or 0

        # Current active visitors (with event in last 5 min)
        visitors_result = await self.db.execute(
            select(func.count(func.distinct(AnalyticsEvent.visitor_id)))
            .select_from(AnalyticsEvent)
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.timestamp >= cutoff,
                )
            )
        )
        active_visitors = visitors_result.scalar() or 0

        return {
            "views_last_5m": views,
            "active_visitors": active_visitors,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _get_top_pages(
        self,
        project_id: UUID,
        start_dt: datetime,
        end_dt: datetime,
        limit: int = 10,
    ) -> list[dict]:
        """Get top pages by page views."""
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
        start_dt: datetime,
        end_dt: datetime,
        limit: int = 10,
    ) -> list[dict]:
        """Get traffic sources breakdown."""
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
            .limit(limit)
        )
        total = sum(row.visitors for row in result)
        return [
            {
                "source": row.source,
                "visitors": row.visitors,
                "percentage": round((row.visitors / total * 100), 1) if total > 0 else 0,
            }
            for row in result
        ]

    async def _get_device_breakdown(
        self,
        project_id: UUID,
        start_dt: datetime,
        end_dt: datetime,
    ) -> list[dict]:
        """Get device type breakdown."""
        result = await self.db.execute(
            select(
                AnalyticsEvent.device_type,
                func.count(func.distinct(AnalyticsEvent.visitor_id)).label("visitors"),
            )
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.timestamp >= start_dt,
                    AnalyticsEvent.timestamp <= end_dt,
                )
            )
            .group_by(AnalyticsEvent.device_type)
        )
        total = sum(row.visitors for row in result)
        return [
            {
                "device": row.device_type,
                "visitors": row.visitors,
                "percentage": round((row.visitors / total * 100), 1) if total > 0 else 0,
            }
            for row in result
        ]

    async def _get_geo_breakdown(
        self,
        project_id: UUID,
        start_dt: datetime,
        end_dt: datetime,
    ) -> list[dict]:
        """Get geographic breakdown by country."""
        result = await self.db.execute(
            select(
                func.coalesce(AnalyticsEvent.country, "Unknown").label("country"),
                func.count(func.distinct(AnalyticsEvent.visitor_id)).label("visitors"),
            )
            .where(
                and_(
                    AnalyticsEvent.project_id == project_id,
                    AnalyticsEvent.timestamp >= start_dt,
                    AnalyticsEvent.timestamp <= end_dt,
                )
            )
            .group_by(func.coalesce(AnalyticsEvent.country, "Unknown"))
            .order_by(func.count(func.distinct(AnalyticsEvent.visitor_id)).desc())
        )
        total = sum(row.visitors for row in result)
        return [
            {
                "country": row.country,
                "visitors": row.visitors,
                "percentage": round((row.visitors / total * 100), 1) if total > 0 else 0,
            }
            for row in result
        ]

    async def _get_bounce_rate(
        self,
        project_id: UUID,
        start_dt: datetime,
        end_dt: datetime,
    ) -> float:
        """Calculate bounce rate (% sessions with a single page view)."""
        total_result = await self.db.execute(
            select(func.count())
            .select_from(AnalyticsSession)
            .where(
                and_(
                    AnalyticsSession.project_id == project_id,
                    AnalyticsSession.started_at >= start_dt,
                    AnalyticsSession.started_at <= end_dt,
                )
            )
        )
        total_sessions = total_result.scalar() or 0

        if total_sessions == 0:
            return 0.0

        bounce_result = await self.db.execute(
            select(func.count())
            .select_from(AnalyticsSession)
            .where(
                and_(
                    AnalyticsSession.project_id == project_id,
                    AnalyticsSession.started_at >= start_dt,
                    AnalyticsSession.started_at <= end_dt,
                    AnalyticsSession.page_views <= 1,
                )
            )
        )
        bounces = bounce_result.scalar() or 0
        return round((bounces / total_sessions) * 100, 1)

    async def _get_avg_session_duration(
        self,
        project_id: UUID,
        start_dt: datetime,
        end_dt: datetime,
    ) -> float:
        """Calculate average session duration in seconds."""
        result = await self.db.execute(
            select(func.avg(AnalyticsSession.duration_seconds))
            .where(
                and_(
                    AnalyticsSession.project_id == project_id,
                    AnalyticsSession.started_at >= start_dt,
                    AnalyticsSession.started_at <= end_dt,
                    AnalyticsSession.duration_seconds.isnot(None),
                )
            )
        )
        avg = result.scalar()
        return round(float(avg or 0), 1)

    # ============================================================
    # Funnel Analysis (v1 feature)
    # ============================================================

    async def create_funnel(
        self,
        project_id: UUID,
        name: str,
        steps: list[dict],
        created_by_id: UUID | None = None,
    ) -> AnalyticsFunnel:
        """
        Create a conversion funnel.

        Steps format: [{"event_type": "page_view", "filters": {...}}, ...]
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
        funnel_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        """
        Analyze funnel performance over date range.

        Returns conversion counts for each step.
        """
        result = await self.db.execute(
            select(AnalyticsFunnel).where(AnalyticsFunnel.id == funnel_id)
        )
        funnel = result.scalar_one_or_none()
        if not funnel:
            raise ValueError("Funnel not found")

        end_date = end_date or date.today()
        start_date = start_date or (end_date - timedelta(days=30))

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        steps_data = []
        for i, step in enumerate(funnel.steps):
            # Build query for this step
            query = select(func.count(func.distinct(AnalyticsEvent.visitor_id)))
            query = query.select_from(AnalyticsEvent).where(
                and_(
                    AnalyticsEvent.project_id == funnel.project_id,
                    AnalyticsEvent.event_type == step.get("event_type"),
                    AnalyticsEvent.timestamp >= start_dt,
                    AnalyticsEvent.timestamp <= end_dt,
                )
            )

            # Apply filters if present
            filters = step.get("filters", {})
            for key, value in filters.items():
                query = query.where(
                    AnalyticsEvent.properties[key].astext == str(value)
                )

            count_result = await self.db.execute(query)
            count = count_result.scalar() or 0

            # Calculate conversion rate from first step
            if i == 0:
                conversion_rate = 100.0
            elif steps_data:
                conversion_rate = (
                    (count / steps_data[0]["visitors"]) * 100
                    if steps_data[0]["visitors"] > 0
                    else 0
                )

            steps_data.append({
                "step": i + 1,
                "name": step.get("name", f"Step {i + 1}"),
                "event_type": step.get("event_type"),
                "visitors": count,
                "conversion_rate": round(conversion_rate, 1),
            })

        return steps_data

    # ============================================================
    # Helpers
    # ============================================================

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        import secrets
        import time
        return f"sess_{int(time.time())}_{secrets.token_hex(8)}"

    def _calculate_trend(self, current: int, previous: int) -> float:
        """Calculate percentage trend between two periods."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round((current - previous) / previous * 100, 1)

    @staticmethod
    def hash_visitor(ip: str, user_agent: str | None = None) -> str:
        """
        Hash visitor identifier for privacy-friendly tracking.

        Combines IP and user agent with a daily salt for uniqueness.
        """
        daily_salt = date.today().isoformat()
        data = f"{ip}{user_agent or ''}{daily_salt}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
