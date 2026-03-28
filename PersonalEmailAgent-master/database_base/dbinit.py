from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = "postgresql+asyncpg://postgres:123456@127.0.0.1:5432/EmailAgent"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
