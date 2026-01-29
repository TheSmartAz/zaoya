# Multi-Page Projects Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform Zaoya from a single-page generator to a multi-page web app studio with draft/snapshot architecture and static HTML publishing.

**Architecture:**
- PostgreSQL database with SQLAlchemy 2.0 async
- Draft snapshot (mutable) → Version snapshot (immutable) flow
- Static HTML files rendered per page at publish time
- Design system shared across pages via CSS variables

**Tech Stack:** PostgreSQL, SQLAlchemy 2.0, Alembic, FastAPI, React, Zustand, dnd-kit

---

## Part 1: Database Foundation

### Task 1: Install Database Dependencies

**Files:**
- Modify: `backend/requirements.txt`

**Step 1: Add SQLAlchemy and async dependencies**

Open `backend/requirements.txt` and add these lines:

```txt
# Database
sqlalchemy[asyncio]==2.0.34
asyncpg==0.29.0
alembic==1.13.0
# Use psycopg2 for alembic migrations (needs sync driver)
psycopg2-binary==2.9.9
```

**Step 2: Install dependencies**

Run: `cd backend && pip install -r requirements.txt`
Expected: No errors, packages installed successfully

**Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "feat: add SQLAlchemy and Alembic dependencies"
```

---

### Task 2: Configure Database Connection

**Files:**
- Modify: `backend/app/config.py`
- Create: `backend/app/db/__init__.py`

**Step 1: Add database settings to config.py**

Open `backend/app/config.py` and add to the `Settings` class (after `pages_url`):

```python
from pydantic import field_validator

class Settings(BaseSettings):
    # ... existing fields ...

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/zaoya"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/zaoya"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
```

**Step 2: Create database module**

Create `backend/app/db/__init__.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

**Step 3: Create sync database module for Alembic**

Create `backend/app/db/sync.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
)

SyncSessionLocal = sessionmaker(bind=sync_engine)
```

**Step 4: Test database connection**

Create test script `backend/test_db.py`:

```python
import asyncio
from app.db import engine

async def test_connection():
    async with engine.begin() as conn:
        result = await conn.execute("SELECT 1")
        print("Database connected!", result.scalar())

if __name__ == "__main__":
    asyncio.run(test_connection())
```

Run: `cd backend && python test_db.py`
Expected: "Database connected! 1" (or error if DB not running)

**Step 5: Clean up**

```bash
rm backend/test_db.py
```

**Step 6: Commit**

```bash
git add backend/app/config.py backend/app/db/ backend/requirements.txt
git commit -m "feat: configure SQLAlchemy async database connection"
```

---

### Task 3: Initialize Alembic

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/.gitkeep`

**Step 1: Initialize Alembic**

Run: `cd backend && alembic init alembic`
Expected: Creates `alembic/` directory and `alembic.ini`

**Step 2: Configure alembic.ini**

Open `backend/alembic.ini` and modify the sqlalchemy.url line:

```ini
# Use the sync URL for Alembic
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/zaoya
```

**Step 3: Configure env.py for SQLAlchemy 2.0**

Open `backend/alembic/env.py` and replace contents:

```python
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.db.sync import sync_engine
from app.db import Base

# Import all models here for autogenerate
from app.models import user, project, snapshot, page  # We'll create these

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = sync_engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 4: Create versions directory**

```bash
mkdir -p backend/alembic/versions && touch backend/alembic/versions/.gitkeep
```

**Step 5: Commit**

```bash
git add backend/alembic/ backend/alembic.ini
git commit -m "feat: initialize Alembic for database migrations"
```

---

### Task 4: Create ORM Models

**Files:**
- Create: `backend/app/models/db/__init__.py`
- Create: `backend/app/models/db/user.py`
- Create: `backend/app/models/db/project.py`
- Create: `backend/app/models/db/snapshot.py`
- Create: `backend/app/models/db/page.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Create user model**

Create `backend/app/models/db/user.py`:

```python
from datetime import datetime
from sqlalchemy import Column, String, Boolean, TEXT
from sqlalchemy.dialects.postgresql import CITEXT, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4, UUID

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(TEXT)
    provider: Mapped[str] = mapped_column(String(20), default="email")
    provider_id: Mapped[str | None] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(CITEXT, unique=True)
    preferences: Mapped[dict] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

**Step 2: Create project model**

Create `backend/app/models/db/project.py`:

```python
from datetime import datetime
from sqlalchemy import Column, String, Boolean, TEXT, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4, UUID

from app.db import Base
from app.models.db.user import User


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    public_id: Mapped[str | None] = mapped_column(String(8), unique=True)
    slug: Mapped[str | None] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_id: Mapped[str | None] = mapped_column(String(50))
    template_inputs: Mapped[dict] = mapped_column(JSONB, default={})
    status: Mapped[str] = mapped_column(String(20), default="draft")
    current_draft_id: Mapped[UUID | None] = mapped_column(ForeignKey("snapshots.id"))
    published_snapshot_id: Mapped[UUID | None] = mapped_column(ForeignKey("snapshots.id"))
    notification_email: Mapped[str | None] = mapped_column(String(255))
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("slug ~ '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'", name="slug_format"),
    )
```

**Step 3: Create snapshot model**

Create `backend/app/models/db/snapshot.py`:

```python
from datetime import datetime
from sqlalchemy import Column, String, TEXT, ForeignKey, ExcludeConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4, UUID

from app.db import Base


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    version_number: Mapped[int] = mapped_column(nullable=False)
    summary: Mapped[str | None] = mapped_column(TEXT)
    design_system: Mapped[dict] = mapped_column(JSONB, default={})
    navigation: Mapped[dict] = mapped_column(JSONB, default={})
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        ExcludeConstraint(("project_id", "="), ("is_draft", "="), where="is_draft = true",
                          name="at_most_one_draft_per_project"),
    )
```

**Step 4: Create page model**

Create `backend/app/models/db/page.py`:

```python
from datetime import datetime
from sqlalchemy import Column, String, TEXT, Boolean, Integer, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4, UUID

from app.db import Base


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    snapshot_id: Mapped[UUID] = mapped_column(ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    html: Mapped[str] = mapped_column(TEXT, nullable=False)
    js: Mapped[str | None] = mapped_column(TEXT)
    metadata: Mapped[dict] = mapped_column(JSONB, default={})
    is_home: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("slug ~ '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'", name="slug_format"),
        Index("uniq_home_per_snapshot", "snapshot_id", unique=True,
              postgresql_where="is_home = true"),
    )
```

**Step 5: Create db models package init**

Create `backend/app/models/db/__init__.py`:

```python
from app.db import Base
from app.models.db.user import User
from app.models.db.project import Project
from app.models.db.snapshot import Snapshot
from app.models.db.page import Page

__all__ = ["Base", "User", "Project", "Snapshot", "Page"]
```

**Step 6: Update models package init**

Modify `backend/app/models/__init__.py`, add at the end:

```python
# ORM models (keep separate from Pydantic models for now)
from app.models.db import Base, User, Project, Snapshot, Page
```

**Step 7: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add ORM models for users, projects, snapshots, pages"
```

---

### Task 5: Create Initial Migration

**Files:**
- Create: `backend/alembic/versions/001_initial.py`

**Step 1: Create migration file manually**

Create `backend/alembic/versions/001_initial_schema.py`:

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create citext extension
    op.execute('CREATE EXTENSION IF NOT EXISTS citext')

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255)),
        sa.Column('name', sa.String(255)),
        sa.Column('avatar_url', sa.Text()),
        sa.Column('provider', sa.String(20), default='email'),
        sa.Column('provider_id', sa.String(255)),
        sa.Column('username', postgresql.CITEXT(), unique=True),
        sa.Column('preferences', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.TIMESTAMP(), default=sa.text('now()')),
        sa.CheckConstraint("username ~ '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'", name='username_format'),
    )

    # Projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('public_id', sa.String(8), unique=True),
        sa.Column('slug', sa.String(100)),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('template_id', sa.String(50)),
        sa.Column('template_inputs', postgresql.JSONB(), default={}),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('current_draft_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('snapshots.id')),
        sa.Column('published_snapshot_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('snapshots.id')),
        sa.Column('notification_email', sa.String(255)),
        sa.Column('notification_enabled', sa.Boolean(), default=False),
        sa.Column('published_at', sa.TIMESTAMP()),
        sa.Column('created_at', sa.TIMESTAMP(), default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(), default=sa.text('now()')),
        sa.UniqueConstraint('user_id', 'slug'),
        sa.CheckConstraint("slug ~ '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'", name='slug_format'),
    )

    # Snapshots table
    op.create_table(
        'snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('summary', sa.Text()),
        sa.Column('design_system', postgresql.JSONB(), default={}),
        sa.Column('navigation', postgresql.JSONB(), default={}),
        sa.Column('is_draft', sa.Boolean(), default=False),
        sa.Column('created_at', sa.TIMESTAMP(), default=sa.text('now()')),
        sa.UniqueConstraint('project_id', 'version_number'),
        postgresql.ExcludeConstraint(('project_id', '='), ('is_draft', '='),
                                      where='is_draft = true',
                                      name='at_most_one_draft_per_project'),
    )

    # Pages table
    op.create_table(
        'pages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('snapshot_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('snapshots.id', ondelete='CASCADE'), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('html', sa.Text(), nullable=False),
        sa.Column('js', sa.Text()),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.Column('is_home', sa.Boolean(), default=False),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.TIMESTAMP(), default=sa.text('now()')),
        sa.UniqueConstraint('snapshot_id', 'slug'),
        sa.CheckConstraint("slug ~ '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'", name='slug_format'),
    )

    # Indexes
    op.create_index('uniq_home_per_snapshot', 'pages', ['snapshot_id'],
                    unique=True, postgresql_where=sa.text('is_home = true'))
    op.create_index('idx_snapshots_project_created', 'snapshots', ['project_id', 'created_at'])
    op.create_index('idx_pages_snapshot_order', 'pages', ['snapshot_id', 'display_order'])
    op.create_index('idx_projects_user_updated', 'projects', ['user_id', 'updated_at'])
    op.create_index('idx_projects_public_id', 'projects', ['public_id'],
                    postgresql_where=sa.text('public_id IS NOT NULL'))


def downgrade():
    op.drop_index('idx_projects_public_id', table_name='projects')
    op.drop_index('idx_projects_user_updated', table_name='projects')
    op.drop_index('idx_pages_snapshot_order', table_name='pages')
    op.drop_index('idx_snapshots_project_created', table_name='snapshots')
    op.drop_index('uniq_home_per_snapshot', table_name='pages')

    op.drop_table('pages')
    op.drop_table('snapshots')
    op.drop_table('projects')
    op.drop_table('users')

    op.execute('DROP EXTENSION IF EXISTS citext')
```

**Step 2: Run migration**

First ensure PostgreSQL is running and database exists:

```bash
# Create database if needed
psql -U postgres -c "CREATE DATABASE zaoya;" 2>/dev/null || echo "Database exists"

# Run migration
cd backend && alembic upgrade head
```

Expected: Output shows migration applied, tables created

**Step 3: Verify tables**

Run: `psql -U postgres -d zaoya -c "\dt"`
Expected: Shows users, projects, snapshots, pages tables

**Step 4: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat: create initial database schema migration"
```

---

## Part 2: Draft and Page CRUD APIs

### Task 6: Create Pydantic Schemas for API

**Files:**
- Create: `backend/app/models/schemas/__init__.py`
- Create: `backend/app/models/schemas/draft.py`
- Create: `backend/app/models/schemas/snapshot.py`
- Create: `backend/app/models/schemas/page.py`

**Step 1: Create draft schemas**

Create `backend/app/models/schemas/draft.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class DesignSystem(BaseModel):
    colors: Dict[str, str] = Field(default_factory=dict)
    typography: Dict[str, str] = Field(default_factory=dict)
    spacing: Dict[str, str] = Field(default_factory=dict)


class NavigationConfig(BaseModel):
    header: Dict[str, Any] = Field(default_factory=dict)
    footer: Dict[str, Any] = Field(default_factory=dict)
    pages: list[Dict[str, Any]] = Field(default_factory=list)


class DraftResponse(BaseModel):
    id: UUID
    project_id: UUID
    version_number: int
    summary: Optional[str] = None
    design_system: DesignSystem
    navigation: NavigationConfig
    created_at: datetime

    class Config:
        from_attributes = True


class DraftUpdate(BaseModel):
    design_system: Optional[DesignSystem] = None
    navigation: Optional[NavigationConfig] = None
    summary: Optional[str] = None
```

**Step 2: Create page schemas**

Create `backend/app/models/schemas/page.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class PageCreate(BaseModel):
    slug: str = Field(..., pattern=r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$')
    title: str
    html: str
    js: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_home: bool = False


class PageUpdate(BaseModel):
    slug: Optional[str] = Field(None, pattern=r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$')
    title: Optional[str] = None
    html: Optional[str] = None
    js: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    display_order: Optional[int] = None


class PageResponse(BaseModel):
    id: UUID
    slug: str
    title: str
    html: str
    js: Optional[str]
    metadata: Dict[str, Any]
    is_home: bool
    display_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReorderPagesRequest(BaseModel):
    page_ids: list[UUID]  # Ordered list of page IDs
```

**Step 3: Create snapshot schemas**

Create `backend/app/models/schemas/snapshot.py`:

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.models.schemas.page import PageResponse
from app.models.schemas.draft import DesignSystem, NavigationConfig


class SnapshotResponse(BaseModel):
    id: UUID
    project_id: UUID
    version_number: int
    summary: Optional[str]
    design_system: DesignSystem
    navigation: NavigationConfig
    is_draft: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SnapshotWithPages(SnapshotResponse):
    pages: List[PageResponse]


class CreateSnapshotRequest(BaseModel):
    summary: Optional[str] = None


class RestoreSnapshotRequest(BaseModel):
    snapshot_id: UUID
```

**Step 4: Create schemas package init**

Create `backend/app/models/schemas/__init__.py`:

```python
from app.models.schemas.draft import DraftResponse, DraftUpdate, DesignSystem, NavigationConfig
from app.models.schemas.page import PageCreate, PageUpdate, PageResponse, ReorderPagesRequest
from app.models.schemas.snapshot import (
    SnapshotResponse,
    SnapshotWithPages,
    CreateSnapshotRequest,
    RestoreSnapshotRequest,
)

__all__ = [
    "DraftResponse",
    "DraftUpdate",
    "DesignSystem",
    "NavigationConfig",
    "PageCreate",
    "PageUpdate",
    "PageResponse",
    "ReorderPagesRequest",
    "SnapshotResponse",
    "SnapshotWithPages",
    "CreateSnapshotRequest",
    "RestoreSnapshotRequest",
]
```

**Step 5: Commit**

```bash
git add backend/app/models/schemas/
git commit -m "feat: add Pydantic schemas for draft, pages, snapshots"
```

---

### Task 7: Create Draft Service

**Files:**
- Create: `backend/app/services/draft_service.py`

**Step 1: Write the draft service**

Create `backend/app/services/draft_service.py`:

```python
from uuid import UUID, uuid4
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Project, Snapshot, Page
from app.models.schemas import DraftUpdate, PageCreate, PageResponse, DraftResponse, DesignSystem, NavigationConfig


class DraftService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_draft(self, project_id: UUID, user_id: UUID) -> Snapshot:
        """Get existing draft or create new one for project."""
        # Verify user owns project
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        # Look for existing draft
        draft_result = await self.db.execute(
            select(Snapshot).where(
                Snapshot.project_id == project_id,
                Snapshot.is_draft == True
            )
        )
        draft = draft_result.scalar_one_or_none()

        if draft:
            return draft

        # Create new draft
        draft = Snapshot(
            id=uuid4(),
            project_id=project_id,
            version_number=0,
            is_draft=True,
            design_system={},
            navigation={},
        )
        self.db.add(draft)
        await self.db.commit()
        await self.db.refresh(draft)

        # Update project's current_draft_id
        project.current_draft_id = draft.id
        await self.db.commit()

        return draft

    async def update_draft(self, project_id: UUID, user_id: UUID, update: DraftUpdate) -> Snapshot:
        """Update draft metadata (design system, navigation, summary)."""
        draft = await self.get_or_create_draft(project_id, user_id)

        if update.design_system is not None:
            draft.design_system = update.design_system.model_dump()
        if update.navigation is not None:
            draft.navigation = update.navigation.model_dump()
        if update.summary is not None:
            draft.summary = update.summary

        await self.db.commit()
        await self.db.refresh(draft)
        return draft

    async def get_draft_pages(self, project_id: UUID, user_id: UUID) -> list[Page]:
        """Get all pages in the draft."""
        draft = await self.get_or_create_draft(project_id, user_id)

        result = await self.db.execute(
            select(Page)
            .where(Page.snapshot_id == draft.id)
            .order_by(Page.display_order)
        )
        return list(result.scalars().all())

    async def add_page(self, project_id: UUID, user_id: UUID, page_data: PageCreate) -> Page:
        """Add a page to the draft."""
        draft = await self.get_or_create_draft(project_id, user_id)

        # Check if home page already exists if adding a home page
        if page_data.is_home:
            existing_home = await self.db.execute(
                select(Page).where(
                    Page.snapshot_id == draft.id,
                    Page.is_home == True
                )
            )
            if existing_home.scalar_one_or_none():
                raise ValueError("Home page already exists")

        # Get next display order
        max_order_result = await self.db.execute(
            select(func.max(Page.display_order)).where(Page.snapshot_id == draft.id)
        )
        max_order = max_order_result.scalar() or 0

        page = Page(
            id=uuid4(),
            snapshot_id=draft.id,
            slug=page_data.slug,
            title=page_data.title,
            html=page_data.html,
            js=page_data.js,
            metadata=page_data.metadata,
            is_home=page_data.is_home,
            display_order=max_order + 1,
        )
        self.db.add(page)
        await self.db.commit()
        await self.db.refresh(page)
        return page

    async def update_page(self, project_id: UUID, user_id: UUID, page_id: UUID, update: dict) -> Page:
        """Update a page in the draft."""
        draft = await self.get_or_create_draft(project_id, user_id)

        result = await self.db.execute(
            select(Page).where(
                Page.id == page_id,
                Page.snapshot_id == draft.id
            )
        )
        page = result.scalar_one_or_none()
        if not page:
            raise ValueError("Page not found")

        for key, value in update.items():
            if value is not None and hasattr(page, key):
                setattr(page, key, value)

        await self.db.commit()
        await self.db.refresh(page)
        return page

    async def delete_page(self, project_id: UUID, user_id: UUID, page_id: UUID) -> None:
        """Delete a page from the draft."""
        draft = await self.get_or_create_draft(project_id, user_id)

        result = await self.db.execute(
            select(Page).where(
                Page.id == page_id,
                Page.snapshot_id == draft.id
            )
        )
        page = result.scalar_one_or_none()
        if not page:
            raise ValueError("Page not found")

        await self.db.delete(page)
        await self.db.commit()

    async def reorder_pages(self, project_id: UUID, user_id: UUID, page_ids: list[UUID]) -> None:
        """Reorder pages in the draft."""
        draft = await self.get_or_create_draft(project_id, user_id)

        # Verify all pages belong to this draft
        result = await self.db.execute(
            select(Page).where(
                Page.id.in_(page_ids),
                Page.snapshot_id == draft.id
            )
        )
        pages = result.scalars().all()
        if len(pages) != len(page_ids):
            raise ValueError("Some pages not found")

        # Update display orders
        page_map = {p.id: p for p in pages}
        for order, page_id in enumerate(page_ids):
            page_map[page_id].display_order = order

        await self.db.commit()
```

**Step 2: Commit**

```bash
git add backend/app/services/draft_service.py
git commit -m "feat: add draft service for multi-page CRUD operations"
```

---

### Task 8: Create Snapshot Service

**Files:**
- Create: `backend/app/services/snapshot_service.py`

**Step 1: Write the snapshot service**

Create `backend/app/services/snapshot_service.py`:

```python
from uuid import UUID, uuid4
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from copy import deepcopy

from app.models.db import Project, Snapshot, Page
from app.models.schemas import CreateSnapshotRequest, RestoreSnapshotRequest, SnapshotWithPages


class SnapshotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_snapshots(self, project_id: UUID, user_id: UUID) -> list[Snapshot]:
        """List all non-draft snapshots for a project."""
        # Verify user owns project
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
        if not project_result.scalar_one_or_none():
            raise ValueError("Project not found")

        result = await self.db.execute(
            select(Snapshot)
            .where(
                Snapshot.project_id == project_id,
                Snapshot.is_draft == False
            )
            .order_by(Snapshot.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_snapshot(
        self,
        project_id: UUID,
        user_id: UUID,
        request: CreateSnapshotRequest
    ) -> Snapshot:
        """Create an immutable snapshot from the current draft."""
        from app.services.draft_service import DraftService

        draft_service = DraftService(self.db)
        draft = await draft_service.get_or_create_draft(project_id, user_id)

        # Get next version number
        max_version_result = await self.db.execute(
            select(func.max(Snapshot.version_number)).where(
                Snapshot.project_id == project_id,
                Snapshot.is_draft == False
            )
        )
        next_version = (max_version_result.scalar() or 0) + 1

        # Copy draft pages to new snapshot
        draft_pages_result = await self.db.execute(
            select(Page).where(Page.snapshot_id == draft.id)
        )
        draft_pages = draft_pages_result.scalars().all()

        # Create snapshot
        snapshot = Snapshot(
            id=uuid4(),
            project_id=project_id,
            version_number=next_version,
            summary=request.summary or f"Version {next_version}",
            design_system=deepcopy(draft.design_system),
            navigation=deepcopy(draft.navigation),
            is_draft=False,
        )
        self.db.add(snapshot)
        await self.db.flush()  # Get the ID

        # Copy pages
        for page in draft_pages:
            new_page = Page(
                id=uuid4(),
                snapshot_id=snapshot.id,
                slug=page.slug,
                title=page.title,
                html=page.html,
                js=page.js,
                metadata=deepcopy(page.metadata),
                is_home=page.is_home,
                display_order=page.display_order,
            )
            self.db.add(new_page)

        await self.db.commit()
        await self.db.refresh(snapshot)
        return snapshot

    async def get_snapshot(self, project_id: UUID, user_id: UUID, snapshot_id: UUID) -> Optional[Snapshot]:
        """Get a specific snapshot."""
        # Verify user owns project
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
        if not project_result.scalar_one_or_none():
            raise ValueError("Project not found")

        result = await self.db.execute(
            select(Snapshot).where(
                Snapshot.id == snapshot_id,
                Snapshot.project_id == project_id
            )
        )
        return result.scalar_one_or_none()

    async def restore_snapshot(self, project_id: UUID, user_id: UUID, snapshot_id: UUID) -> Snapshot:
        """Restore a snapshot to become the new draft."""
        from app.services.draft_service import DraftService

        # Get the snapshot to restore
        snapshot = await self.get_snapshot(project_id, user_id, snapshot_id)
        if not snapshot:
            raise ValueError("Snapshot not found")

        draft_service = DraftService(self.db)

        # Get existing draft
        draft_result = await self.db.execute(
            select(Snapshot).where(
                Snapshot.project_id == project_id,
                Snapshot.is_draft == True
            )
        )
        old_draft = draft_result.scalar_one_or_none()

        # Create new draft from snapshot
        new_draft = Snapshot(
            id=uuid4(),
            project_id=project_id,
            version_number=0,
            summary=f"Restored from version {snapshot.version_number}",
            design_system=snapshot.design_system.copy() if snapshot.design_system else {},
            navigation=snapshot.navigation.copy() if snapshot.navigation else {},
            is_draft=True,
        )
        self.db.add(new_draft)
        await self.db.flush()

        # Copy pages from snapshot
        pages_result = await self.db.execute(
            select(Page).where(Page.snapshot_id == snapshot_id)
        )
        old_pages = pages_result.scalars().all()

        for page in old_pages:
            new_page = Page(
                id=uuid4(),
                snapshot_id=new_draft.id,
                slug=page.slug,
                title=page.title,
                html=page.html,
                js=page.js,
                metadata=page.metadata.copy() if page.metadata else {},
                is_home=page.is_home,
                display_order=page.display_order,
            )
            self.db.add(new_page)

        # Delete old draft
        if old_draft:
            # Old draft's pages will be cascade deleted
            await self.db.delete(old_draft)

        # Update project
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one()
        project.current_draft_id = new_draft.id

        await self.db.commit()
        await self.db.refresh(new_draft)
        return new_draft
```

**Step 2: Commit**

```bash
git add backend/app/services/snapshot_service.py
git commit -m "feat: add snapshot service for version management"
```

---

### Task 9: Create Draft API Endpoints

**Files:**
- Create: `backend/app/api/draft.py`

**Step 1: Write the draft API routes**

Create `backend/app/api/draft.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.user import get_current_user
from app.models.db import User
from app.services.draft_service import DraftService
from app.models.schemas import (
    DraftResponse,
    DraftUpdate,
    PageResponse,
    PageCreate,
    PageUpdate,
    ReorderPagesRequest,
)

router = APIRouter(prefix="/api/projects/{project_id}/draft", tags=["draft"])


async def get_draft_service(project_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> DraftService:
    """Get draft service with ownership verification."""
    return DraftService(db)


@router.get("", response_model=DraftResponse)
async def get_draft(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get or create the current draft for a project."""
    service = DraftService(db)
    draft = await service.get_or_create_draft(project_id, current_user.id)
    return DraftResponse(
        id=draft.id,
        project_id=draft.project_id,
        version_number=draft.version_number,
        summary=draft.summary,
        design_system=draft.design_system or {},
        navigation=draft.navigation or {},
        created_at=draft.created_at,
    )


@router.post("", response_model=DraftResponse)
async def create_draft(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new draft (same as get)."""
    service = DraftService(db)
    draft = await service.get_or_create_draft(project_id, current_user.id)
    return DraftResponse(
        id=draft.id,
        project_id=draft.project_id,
        version_number=draft.version_number,
        summary=draft.summary,
        design_system=draft.design_system or {},
        navigation=draft.navigation or {},
        created_at=draft.created_at,
    )


@router.patch("", response_model=DraftResponse)
async def update_draft(
    project_id: str,
    update: DraftUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update draft design system or navigation."""
    service = DraftService(db)
    draft = await service.update_draft(project_id, current_user.id, update)
    return DraftResponse(
        id=draft.id,
        project_id=draft.project_id,
        version_number=draft.version_number,
        summary=draft.summary,
        design_system=draft.design_system or {},
        navigation=draft.navigation or {},
        created_at=draft.created_at,
    )


@router.get("/pages", response_model=list[PageResponse])
async def get_draft_pages(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all pages in the draft."""
    service = DraftService(db)
    pages = await service.get_draft_pages(project_id, current_user.id)
    return [
        PageResponse(
            id=p.id,
            slug=p.slug,
            title=p.title,
            html=p.html,
            js=p.js,
            metadata=p.metadata or {},
            is_home=p.is_home,
            display_order=p.display_order,
            created_at=p.created_at,
        )
        for p in pages
    ]


@router.post("/pages", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
async def add_page(
    project_id: str,
    page_data: PageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new page to the draft."""
    service = DraftService(db)
    page = await service.add_page(project_id, current_user.id, page_data)
    return PageResponse(
        id=page.id,
        slug=page.slug,
        title=page.title,
        html=page.html,
        js=page.js,
        metadata=page.metadata or {},
        is_home=page.is_home,
        display_order=page.display_order,
        created_at=page.created_at,
    )


@router.patch("/pages/{page_id}", response_model=PageResponse)
async def update_page(
    project_id: str,
    page_id: str,
    update: PageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a page in the draft."""
    service = DraftService(db)
    page = await service.update_page(
        project_id,
        current_user.id,
        page_id,
        update.model_dump(exclude_unset=True)
    )
    return PageResponse(
        id=page.id,
        slug=page.slug,
        title=page.title,
        html=page.html,
        js=page.js,
        metadata=page.metadata or {},
        is_home=page.is_home,
        display_order=page.display_order,
        created_at=page.created_at,
    )


@router.delete("/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    project_id: str,
    page_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a page from the draft."""
    service = DraftService(db)
    await service.delete_page(project_id, current_user.id, page_id)


@router.post("/pages/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_pages(
    project_id: str,
    request: ReorderPagesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reorder pages in the draft."""
    service = DraftService(db)
    await service.reorder_pages(project_id, current_user.id, request.page_ids)
```

**Step 2: Register router in main.py**

Open `backend/app/main.py` and add the router import and registration:

```python
from app.api.draft import router as draft_router  # Add this import

# After other router registrations:
app.include_router(draft_router)
```

**Step 3: Commit**

```bash
git add backend/app/api/draft.py backend/app/main.py
git commit -m "feat: add draft API endpoints"
```

---

### Task 10: Create Snapshot API Endpoints

**Files:**
- Create: `backend/app/api/snapshots.py`

**Step 1: Write the snapshots API routes**

Create `backend/app/api/snapshots.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.user import get_current_user
from app.models.db import User
from app.services.snapshot_service import SnapshotService
from app.models.schemas import (
    SnapshotResponse,
    SnapshotWithPages,
    CreateSnapshotRequest,
)

router = APIRouter(prefix="/api/projects/{project_id}/snapshots", tags=["snapshots"])


@router.get("", response_model=list[SnapshotResponse])
async def list_snapshots(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all non-draft snapshots for a project."""
    service = SnapshotService(db)
    snapshots = await service.list_snapshots(project_id, current_user.id)
    return [
        SnapshotResponse(
            id=s.id,
            project_id=s.project_id,
            version_number=s.version_number,
            summary=s.summary,
            design_system=s.design_system or {},
            navigation=s.navigation or {},
            is_draft=s.is_draft,
            created_at=s.created_at,
        )
        for s in snapshots
    ]


@router.post("", response_model=SnapshotResponse, status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    project_id: str,
    request: CreateSnapshotRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create an immutable snapshot from the current draft."""
    service = SnapshotService(db)
    snapshot = await service.create_snapshot(project_id, current_user.id, request)
    return SnapshotResponse(
        id=snapshot.id,
        project_id=snapshot.project_id,
        version_number=snapshot.version_number,
        summary=snapshot.summary,
        design_system=snapshot.design_system or {},
        navigation=snapshot.navigation or {},
        is_draft=snapshot.is_draft,
        created_at=snapshot.created_at,
    )


@router.post("/{snapshot_id}/restore", response_model=SnapshotResponse)
async def restore_snapshot(
    project_id: str,
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restore a snapshot to become the new draft."""
    service = SnapshotService(db)
    draft = await service.restore_snapshot(project_id, current_user.id, snapshot_id)
    return SnapshotResponse(
        id=draft.id,
        project_id=draft.project_id,
        version_number=draft.version_number,
        summary=draft.summary,
        design_system=draft.design_system or {},
        navigation=draft.navigation or {},
        is_draft=draft.is_draft,
        created_at=draft.created_at,
    )
```

**Step 2: Register router in main.py**

Open `backend/app/main.py` and add:

```python
from app.api.snapshots import router as snapshots_router  # Add this import

# After other router registrations:
app.include_router(snapshots_router)
```

**Step 3: Commit**

```bash
git add backend/app/api/snapshots.py backend/app/main.py
git commit -m "feat: add snapshots API endpoints"
```

---

## Part 3: Frontend Multi-Page Support

### Task 11: Update Types for Multi-Page

**Files:**
- Modify: `frontend/src/types/project.ts`
- Create: `frontend/src/types/page.ts`
- Create: `frontend/src/types/design.ts`

**Step 1: Create page types**

Create `frontend/src/types/page.ts`:

```typescript
export interface Page {
  id: string;
  slug: string;
  title: string;
  html: string;
  js?: string;
  metadata: Record<string, unknown>;
  is_home: boolean;
  display_order: number;
  created_at: string;
}

export interface PageCreate {
  slug: string;
  title: string;
  html: string;
  js?: string;
  metadata?: Record<string, unknown>;
  is_home?: boolean;
}

export interface PageUpdate {
  slug?: string;
  title?: string;
  html?: string;
  js?: string;
  metadata?: Record<string, unknown>;
  display_order?: number;
}
```

**Step 2: Create design system types**

Create `frontend/src/types/design.ts`:

```typescript
export interface DesignSystem {
  colors: Record<string, string>;
  typography: Record<string, string>;
  spacing: Record<string, string>;
  components?: Record<string, unknown>;
}

export interface NavigationConfig {
  header: {
    enabled?: boolean;
    logo?: string;
    title?: string;
    links?: Array<{ title: string; slug: string }>;
  };
  footer: {
    enabled?: boolean;
    text?: string;
    links?: Array<{ title: string; url: string }>;
  };
}

export interface DraftResponse {
  id: string;
  project_id: string;
  version_number: number;
  summary?: string;
  design_system: DesignSystem;
  navigation: NavigationConfig;
  created_at: string;
}
```

**Step 3: Update project types**

Open `frontend/src/types/project.ts` and add to Project interface:

```typescript
import type { Page, DesignSystem, NavigationConfig } from './page';
import type { DesignSystem as DS, NavigationConfig as NC } from './design';

// Add to Project interface:
export interface Project {
  // ... existing fields ...
  current_draft_id?: string;
  published_snapshot_id?: string;
  slug?: string;
  // Add these:
  pages?: Page[];
  design_system?: DS;
  navigation?: NC;
}
```

**Step 4: Commit**

```bash
git add frontend/src/types/
git commit -m "feat: add types for multi-page projects"
```

---

### Task 12: Update Project Store

**Files:**
- Modify: `frontend/src/stores/projectStore.ts`

**Step 1: Add draft/page CRUD to project store**

Open `frontend/src/stores/projectStore.ts` and add:

```typescript
import { create } from 'zustand';
import type { Project, ProjectCreate } from '@/types/project';
import type { Page, PageCreate, DraftResponse, DesignSystem, NavigationConfig } from '@/types/page';
import type { DesignSystem as DS, NavigationConfig as NC } from '@/types/design';

interface ProjectState {
  // ... existing state ...

  // Multi-page state
  currentDraft: DraftResponse | null;
  pages: Page[];

  // Actions
  loadDraft: (projectId: string) => Promise<DraftResponse>;
  updateDesignSystem: (projectId: string, designSystem: DS) => Promise<void>;
  updateNavigation: (projectId: string, navigation: NC) => Promise<void>;
  addPage: (projectId: string, page: PageCreate) => Promise<Page>;
  updatePage: (projectId: string, pageId: string, updates: Partial<PageCreate>) => Promise<Page>;
  deletePage: (projectId: string, pageId: string) => Promise<void>;
  reorderPages: (projectId: string, pageIds: string[]) => Promise<void>;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  // ... existing code ...

  // New state
  currentDraft: null,
  pages: [],

  loadDraft: async (projectId: string) => {
    const token = localStorage.getItem('zaoya_token');
    const response = await fetch(`/api/projects/${projectId}/draft`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to load draft');
    const draft: DraftResponse = await response.json();

    // Load pages
    const pagesResponse = await fetch(`/api/projects/${projectId}/draft/pages`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const pages: Page[] = await pagesResponse.json();

    set({ currentDraft: draft, pages });
    return draft;
  },

  updateDesignSystem: async (projectId: string, designSystem: DS) => {
    const token = localStorage.getItem('zaoya_token');
    const response = await fetch(`/api/projects/${projectId}/draft`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ design_system: designSystem }),
    });
    if (!response.ok) throw new Error('Failed to update design system');
    const draft: DraftResponse = await response.json();
    set({ currentDraft: draft });
  },

  updateNavigation: async (projectId: string, navigation: NC) => {
    const token = localStorage.getItem('zaoya_token');
    const response = await fetch(`/apiapi/projects/${projectId}/draft`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ navigation }),
    });
    if (!response.ok) throw new Error('Failed to update navigation');
    const draft: DraftResponse = await response.json();
    set({ currentDraft: draft });
  },

  addPage: async (projectId: string, page: PageCreate) => {
    const token = localStorage.getItem('zaoya_token');
    const response = await fetch(`/api/projects/${projectId}/draft/pages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(page),
    });
    if (!response.ok) throw new Error('Failed to add page');
    const newPage: Page = await response.json();
    set((state) => ({ pages: [...state.pages, newPage] }));
    return newPage;
  },

  updatePage: async (projectId: string, pageId: string, updates: Partial<PageCreate>) => {
    const token = localStorage.getItem('zaoya_token');
    const response = await fetch(`/api/projects/${projectId}/draft/pages/${pageId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(updates),
    });
    if (!response.ok) throw new Error('Failed to update page');
    const updated: Page = await response.json();
    set((state) => ({
      pages: state.pages.map((p) => (p.id === pageId ? updated : p)),
    }));
    return updated;
  },

  deletePage: async (projectId: string, pageId: string) => {
    const token = localStorage.getItem('zaoya_token');
    const response = await fetch(`/api/projects/${projectId}/draft/pages/${pageId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to delete page');
    set((state) => ({ pages: state.pages.filter((p) => p.id !== pageId) }));
  },

  reorderPages: async (projectId: string, pageIds: string[]) => {
    const token = localStorage.getItem('zaoya_token');
    const response = await fetch(`/api/projects/${projectId}/draft/pages/reorder`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ page_ids: pageIds }),
    });
    if (!response.ok) throw new Error('Failed to reorder pages');
    set((state) => {
      const pageMap = new Map(state.pages.map((p) => [p.id, p]));
      const reordered = pageIds
        .map((id) => pageMap.get(id))
        .filter((p): p is Page => p !== undefined);
      return { pages: reordered };
    });
  },
}));
```

**Step 2: Commit**

```bash
git add frontend/src/stores/projectStore.ts
git commit -m "feat: add multi-page CRUD to project store"
```

---

### Task 13: Create Project Sidebar Component

**Files:**
- Create: `frontend/src/components/editor/ProjectSidebar.tsx`

**Step 1: Install dnd-kit**

Run: `cd frontend && npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities`

**Step 2: Create ProjectSidebar component**

Create `frontend/src/components/editor/ProjectSidebar.tsx`:

```typescript
import { useEffect } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { FileText, Plus, Settings, Palette, Trash2, GripVertical } from 'lucide-react';
import { useProjectStore } from '@/stores/projectStore';
import type { Page } from '@/types/page';

interface SortablePageProps {
  page: Page;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
}

function SortablePage({ page, isActive, onSelect, onDelete }: SortablePageProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: page.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-colors ${
        isActive ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'
      }`}
    >
      <button
        {...attributes}
        {...listeners}
        className="p-1 hover:bg-gray-200 rounded"
        title="Drag to reorder"
      >
        <GripVertical size={16} />
      </button>
      <FileText size={16} />
      <span className="flex-1 truncate" onClick={onSelect}>
        {page.title}
      </span>
      {page.is_home && <span className="text-xs text-gray-500">Home</span>}
      <button
        onClick={onDelete}
        className="p-1 hover:bg-red-100 text-red-500 rounded opacity-0 group-hover:opacity-100"
        title="Delete page"
      >
        <Trash2 size={14} />
      </button>
    </div>
  );
}

interface ProjectSidebarProps {
  projectId: string;
  selectedPageId: string | null;
  onPageSelect: (pageId: string) => void;
  onAddPage: () => void;
  onOpenDesign: () => void;
  onOpenSettings: () => void;
}

export function ProjectSidebar({
  projectId,
  selectedPageId,
  onPageSelect,
  onAddPage,
  onOpenDesign,
  onOpenSettings,
}: ProjectSidebarProps) {
  const { pages, loadDraft, reorderPages, deletePage } = useProjectStore();

  useEffect(() => {
    loadDraft(projectId);
  }, [projectId, loadDraft]);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = pages.findIndex((p) => p.id === active.id);
    const newIndex = pages.findIndex((p) => p.id === over.id);
    const newPageIds = arrayMove(pages, oldIndex, newIndex).map((p) => p.id);

    reorderPages(projectId, newPageIds);
  };

  const handleDeletePage = async (pageId: string) => {
    if (confirm('Are you sure you want to delete this page?')) {
      await deletePage(projectId, pageId);
    }
  };

  return (
    <div className="w-64 bg-white border-r flex flex-col h-full">
      {/* Project name header */}
      <div className="p-4 border-b">
        <h2 className="font-semibold truncate">My Project</h2>
      </div>

      {/* Pages list */}
      <div className="flex-1 overflow-y-auto p-2 group">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext items={pages.map((p) => p.id)} strategy={verticalListSortingStrategy}>
            {pages.map((page) => (
              <SortablePage
                key={page.id}
                page={page}
                isActive={selectedPageId === page.id}
                onSelect={() => onPageSelect(page.id)}
                onDelete={() => handleDeletePage(page.id)}
              />
            ))}
          </SortableContext>
        </DndContext>

        <button
          onClick={onAddPage}
          className="w-full mt-2 p-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-blue-400 hover:text-blue-500 transition-colors flex items-center justify-center gap-2"
        >
          <Plus size={16} />
          Add Page
        </button>
      </div>

      {/* Bottom actions */}
      <div className="p-2 border-t">
        <button
          onClick={onOpenDesign}
          className="w-full p-2 text-left hover:bg-gray-100 rounded-lg flex items-center gap-2"
        >
          <Palette size={16} />
          Design
        </button>
        <button
          onClick={onOpenSettings}
          className="w-full p-2 text-left hover:bg-gray-100 rounded-lg flex items-center gap-2"
        >
          <Settings size={16} />
          Settings
        </button>
      </div>
    </div>
  );
}
```

**Step 3: Commit**

```bash
git add frontend/src/components/editor/ProjectSidebar.tsx frontend/package.json frontend/package-lock.json
git commit -m "feat: add ProjectSidebar component with drag-reorder"
```

---

### Task 14: Update EditorPage to use 3-panel layout

**Files:**
- Modify: `frontend/src/pages/EditorPage.tsx`

**Step 1: Update EditorPage layout**

Open `frontend/src/pages/EditorPage.tsx` and restructure:

```typescript
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { ProjectSidebar } from '@/components/editor/ProjectSidebar';
import { ChatPanel } from '@/components/chat/ChatPanel';
import { PreviewPanel } from '@/components/preview/PreviewPanel';
import { PageCreationModal } from '@/components/editor/PageCreationModal';
import { useProjectStore } from '@/stores/projectStore';

export function EditorPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { currentProject, loadProject } = useProjectStore();

  const [selectedPageId, setSelectedPageId] = useState<string | null>(null);
  const [showAddPage, setShowAddPage] = useState(false);
  const [showDesign, setShowDesign] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    if (projectId) {
      loadProject(projectId);
    }
  }, [projectId, loadProject]);

  if (!currentProject) {
    return <div>Loading...</div>;
  }

  return (
    <div className="flex h-screen">
      {/* Left sidebar */}
      <ProjectSidebar
        projectId={projectId!}
        selectedPageId={selectedPageId}
        onPageSelect={setSelectedPageId}
        onAddPage={() => setShowAddPage(true)}
        onOpenDesign={() => setShowDesign(true)}
        onOpenSettings={() => setShowSettings(true)}
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {/* Top: Preview */}
        <div className="flex-1 p-4">
          <PreviewPanel />
        </div>

        {/* Bottom: Chat */}
        <div className="h-80 border-t">
          <ChatPanel projectId={projectId!} />
        </div>
      </div>

      {/* Modals */}
      {showAddPage && (
        <PageCreationModal
          projectId={projectId!}
          onClose={() => setShowAddPage(false)}
        />
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/pages/EditorPage.tsx
git commit -m "feat: update EditorPage to 3-panel layout with sidebar"
```

---

## End of Multi-Page Implementation Plan

This completes Part 1 of the implementation. Remaining parts:
- Part 4: Static HTML Publishing
- Part 5: Vanity URLs
- Part 6: Model Selector
- Part 7: Bilingual UI

Continue with remaining parts in separate plan files to keep tasks bite-sized.
