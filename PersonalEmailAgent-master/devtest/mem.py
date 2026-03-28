import asyncio
from service.memory_manager import MemoryManager

async def main():
    manager=MemoryManager()

    
    #res=await manager.store_memory("global_agent",
    #"我喜欢吃苹果和香蕉！"

    res=await manager.store_memory("global_agent",
    "我下周六全天有空")
    print(res)
    

    res=await manager.search_memories("global_agent","周六",limit=3)
    print(res)

if __name__=="__main__":
    asyncio.run(main())