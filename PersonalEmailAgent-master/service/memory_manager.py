from llama_index.core import VectorStoreIndex, Document, StorageContext
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import Settings
from typing import List, Dict, Optional
import json
from datetime import datetime
import os
import dashscope
from llama_index.core.vector_stores import VectorStoreQuery

_memory_manager=None

def get_memory_manager():
    global _memory_manager
    if _memory_manager is None:
        _memory_manager=MemoryManager()
    return _memory_manager

class MemoryManager:
    def __init__(self):
        """初始化记忆管理器"""
        # 初始化 DashScope
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY", "your_dashscope_api_key")

        # 设置 PostgreSQL 向量存储
        self.vector_store = PGVectorStore.from_params(
            database="EmailAgent",
            host="127.0.0.1",
            password="123456",
            port="5432",
            user="postgres",
            table_name="agent_memories",
            embed_dim=1024  # Qwen-embedding-text-v4 的维度
        )
        
        '''
        # 创建存储上下文
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
        # 创建索引
        self.index = VectorStoreIndex.from_documents(
            [], 
            storage_context=self.storage_context
        )
        '''
    
    async def get_embedding(self, text: str) -> List[float]:
        """获取 Qwen 嵌入向量"""
        response = dashscope.TextEmbedding.call(
            model="text-embedding-v4",
            input=text,
            text_type="document"
        )
        
        if response.status_code == 200:
            return response.output["embeddings"][0]["embedding"]
        else:
            raise Exception(f"Embedding API 错误: {response.message}")
    
    async def store_memory(self, agent_id: str, content: str) -> str:
        """存储记忆"""
        # 获取嵌入向量
        embedding = await self.get_embedding(content)
        
        doc = Document(
            text=content,
            embedding=embedding,
            metadata={
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
                "type": "memory"
            }
        )
        
        await self.vector_store.async_add([doc])
        
        return f"记忆已存储: {content[:50]}..."
    
    async def search_memories(self, agent_id: str, query: str, limit: int = 5) -> Dict:
        """RAG 搜索记忆，越靠前的记忆越新"""
        # 获取查询嵌入
        query_embedding = await self.get_embedding(query)
        
        
        # 创建向量查询
        vector_query = VectorStoreQuery(
            query_embedding=query_embedding,
            similarity_top_k=limit*2
        )
        
        # 执行向量搜索
        query_result = await self.vector_store.aquery(vector_query)
        
        # 处理搜索结果
        relevant_memories = []
        for node in query_result.nodes:
            metadata = node.metadata
            if metadata.get("agent_id") == agent_id:
                relevant_memories.append({
                    "content": node.text,
                    "timestamp": metadata.get("timestamp")
                })

        relevant_memories.sort(
            key=lambda x: datetime.fromisoformat(x["timestamp"]) if x.get("timestamp") else datetime.min,
            reverse=True,  # 新的记忆在前
        )
        
        return {
            "query": query,
            "response": f"找到 {len(relevant_memories)} 条相关记忆",
            "relevant_memories": relevant_memories[:limit],
            "total_sources": len(query_result.nodes)
        }