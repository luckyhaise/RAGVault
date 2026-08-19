"""HTTP client for API route tests.

Shadows the parent `client` fixture with a working ASGI transport and
`AsyncSessionMaker()` session (parent override is broken / outdated for httpx).
"""

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
import pytest_asyncio

from app.core.config import settings
from app.db.database import get_db
from app.main import app

_async_engine = create_async_engine(url=str(settings.postgres_url))
_AsyncSessionMaker = async_sessionmaker(
    bind=_async_engine,
    autoflush=False,
    expire_on_commit=False,
)


async def _override_get_db():
    async with _AsyncSessionMaker() as session:
        yield session


@pytest_asyncio.fixture()
async def client():
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
