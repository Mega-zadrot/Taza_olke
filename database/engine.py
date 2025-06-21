import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from .models import MyBase
 
engine= create_async_engine(url=os.getenv("DB_PG"),echo=True)

session_maker=async_sessionmaker(bind=engine,expire_on_commit=False,class_=AsyncSession)

async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(MyBase.metadata.create_all)

async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(MyBase.metadata.drop_all)