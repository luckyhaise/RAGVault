import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.database import get_db
from app.main import app
from app.models.models import Base

async_engine = create_async_engine(url=str(settings.postgres_url))

AsyncSessionMaker = async_sessionmaker(bind=async_engine,autoflush=False,expire_on_commit=False)



@pytest_asyncio.fixture(scope="session",autouse=True)
async def setup_database():

   async with async_engine.begin() as conn:
      # print(Base.metadata.tables.keys())
      await conn.run_sync(Base.metadata.drop_all)
      await conn.run_sync(Base.metadata.create_all)
   yield 
   async with async_engine.begin() as conn:
      print("tables deleted")
      await conn.run_sync(Base.metadata.drop_all)
   await async_engine.dispose()



@pytest_asyncio.fixture()
async def db_session():
  async with AsyncSessionMaker() as session:
      yield session
    #   print("rollback happened")
      await session.rollback()

async def override_get_db():
   async with AsyncSessionMaker as session:
      yield session


@pytest_asyncio.fixture()
async def client():
   app.dependency_overrides[get_db]  = override_get_db
   async with AsyncClient(app=app,base_url="http://tests",) as client: 
      yield client
   app.dependency_overrides.clear()
