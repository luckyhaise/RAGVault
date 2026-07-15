from sqlalchemy.ext.asyncio import async_sessionmaker , create_async_engine
from sqlalchemy import create_engine
from app.core.config import settings


engine = create_async_engine(str(settings.postgres_url),echo=False)
SessionLocal = async_sessionmaker(bind=engine,autoflush=False,expire_on_commit=False)
async def get_db():
    session =  SessionLocal()
    try:
     yield session
    except Exception:
       await session.rollback()
       raise 
    finally:
        await session.close()
      


