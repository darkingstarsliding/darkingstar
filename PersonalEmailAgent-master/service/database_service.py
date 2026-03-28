from database_base.dbinit import SessionLocal
import asyncio
from sqlalchemy import text

async def load_tag_definitions() -> dict:
    sql = text("""
        SELECT name, values_json, description
        FROM tag_definitions
        WHERE enabled = true
        ORDER BY id
    """)
    async with SessionLocal() as db:
        result = await db.execute(sql)

    tags = {}
    for row in result.mappings():
        tags[row["name"]] = {
            "values": row["values_json"],      # jsonb -> Python list
            "description": row["description"],
        }
    return tags

async def test():
    tags=await load_tag_definitions()
    print(tags)

if __name__=="__main__":
    asyncio.run(test())