from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import *
from fastapi import Depends, FastAPI
from sqlalchemy import *

DATABASE_URL = "mysql+asyncmy://root:123456@127.0.0.1:3306/test?charset=utf8mb4"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db():
    async with SessionLocal() as session:
        yield session

class Base(DeclarativeBase):
    pass

class Tb2(Base):
    __tablename__ = "tb2"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="this is id")
    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, comment="username!")

app = FastAPI()

@app.get("/ping-db")
async def ping_db(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tb2))
    return {"ok": True, "result": result.scalar()}
