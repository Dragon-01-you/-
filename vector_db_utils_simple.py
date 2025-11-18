import os
import logging
import random
import hashlib
import threading
import time
from typing import List, Dict, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleEmbeddings:
    """
    简单的嵌入模型替代类，用于在无法加载HuggingFace模型时提供基本功能
    """
    
    def __init__(self, dimension: int = 1024):
        """
        初始化简单嵌入模型
        
        Args:
            dimension: 嵌入向量维度
        """
        self.dimension = dimension
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        为文档列表生成嵌入向量
        
        Args:
            texts: 文档文本列表
            
        Returns:
            嵌入向量列表
        """
        embeddings = []
        for text in texts:
            # 使用文本的哈希值作为随机种子，确保相同文本生成相同向量
            seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % 1000000
            random.seed(seed)
            # 生成随机向量
            embedding = [random.uniform(-1, 1) for _ in range(self.dimension)]
            embeddings.append(embedding)
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """
        为查询文本生成嵌入向量
        
        Args:
            text: 查询文本
            
        Returns:
            嵌入向量
        """
        # 使用与embed_documents相同的方法生成向量
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % 1000000
        random.seed(seed)
        return [random.uniform(-1, 1) for _ in range(self.dimension)]

class SimpleDocument:
    """
    简化的Document类，替代langchain_core.document.Document
    """
    def __init__(self, page_content: str, metadata: Dict = None):
        self.page_content = page_content
        self.metadata = metadata or {}

class SimpleVectorDB:
    """
    简化的向量数据库类，只包含基本的搜索功能
    """
    def __init__(self, embedding_function):
        self.embedding_function = embedding_function
        self.documents = []
        self.embeddings = []
        self.metadata = []
        
    def add_documents(self, documents: List[SimpleDocument]):
        """
        添加文档到向量数据库
        """
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        # 生成嵌入向量
        new_embeddings = self.embedding_function.embed_documents(texts)
        
        # 添加到数据库
        self.documents.extend(texts)
        self.embeddings.extend(new_embeddings)
        self.metadata.extend(metadatas)
        
        logger.info(f"添加了 {len(documents)} 个文档到向量数据库")
        return [f"doc_{i}" for i in range(len(self.documents) - len(documents), len(self.documents))]
    
    def similarity_search(self, query: str, k: int = 3) -> List[SimpleDocument]:
        """
        执行相似性搜索
        """
        # 生成查询向量
        query_embedding = self.embedding_function.embed_query(query)
        
        # 计算余弦相似度
        similarities = []
        for i, doc_embedding in enumerate(self.embeddings):
            # 简化的余弦相似度计算
            dot_product = sum(q * d for q, d in zip(query_embedding, doc_embedding))
            norm_q = sum(q * q for q in query_embedding) ** 0.5
            norm_d = sum(d * d for d in doc_embedding) ** 0.5
            
            if norm_q > 0 and norm_d > 0:
                similarity = dot_product / (norm_q * norm_d)
            else:
                similarity = 0.0
            
            similarities.append((i, similarity))
        
        # 按相似度排序并返回前k个结果
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = []
        
        for i, _ in similarities[:k]:
            results.append(SimpleDocument(
                page_content=self.documents[i],
                metadata=self.metadata[i]
            ))
        
        return results

class SimpleChroma:
    """
    模拟Chroma向量数据库的简单类
    """
    def __init__(self, persist_directory=None, embedding_function=None):
        self.persist_directory = persist_directory
        self.embedding_function = embedding_function
        self.vector_db = SimpleVectorDB(embedding_function)
        
        # 尝试从持久化目录加载（简化版，实际不会加载）
        if persist_directory and os.path.exists(persist_directory):
            logger.info(f"检测到向量数据库目录: {persist_directory}")
        
    def add_documents(self, documents, ids=None):
        return self.vector_db.add_documents(documents)
    
    def similarity_search(self, query, k=3):
        return self.vector_db.similarity_search(query, k)

class VectorDBUtils:
    """
    简化版向量数据库工具类，只包含必要的功能
    """
    
    def __init__(self, persist_directory: str = "./vector_db", cache_size: int = 100):
        """
        初始化向量数据库工具
        
        Args:
            persist_directory: 向量数据库持久化目录
            cache_size: 查询缓存大小
        """
        self.persist_directory = persist_directory
        self.cache_size = cache_size
        self._local_cache = {}
        self._cache_lock = threading.RLock()
        self._initialized = False
        
        # 使用SimpleEmbeddings，维度为1024
        logger.info("使用SimpleEmbeddings作为嵌入模型，设置维度为1024")
        self.embeddings = SimpleEmbeddings(dimension=1024)
        
        # 初始化向量存储
        self.vector_db = None
        try:
            self.vector_db = SimpleChroma(
                persist_directory=persist_directory,
                embedding_function=self.embeddings
            )
            self._initialized = True
            logger.info("向量数据库初始化成功")
        except Exception as e:
            logger.error(f"初始化向量数据库失败: {str(e)}")
        
        # 常用查询缓存
        self._common_queries = [
            "学校地址在哪里",
            "图书馆开放时间",
            "奖学金申请条件",
            "如何注册账号",
            "就业指导中心联系方式"
        ]
    
    def search_similar_documents(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            
        Returns:
            相似文档列表
        """
        # 检查缓存
        with self._cache_lock:
            cache_key = f"search:{query}:{top_k}"
            if cache_key in self._local_cache:
                logger.debug(f"缓存命中: {query}")
                return self._local_cache[cache_key]
        
        # 执行搜索
        results = []
        try:
            if self.vector_db and self._initialized:
                docs = self.vector_db.similarity_search(query, k=top_k)
                for doc in docs:
                    results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    })
            else:
                logger.warning("向量数据库未初始化，返回空结果")
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
        
        # 更新缓存
        with self._cache_lock:
            self._local_cache[cache_key] = results
            # 简单的缓存管理
            if len(self._local_cache) > self.cache_size:
                # 删除最旧的缓存项
                oldest_key = next(iter(self._local_cache.keys()))
                del self._local_cache[oldest_key]
        
        return results
    
    def is_initialized(self) -> bool:
        """
        检查向量数据库是否初始化成功
        """
        return self._initialized

# 创建全局实例
vector_db_utils = None

def get_vector_db_utils() -> VectorDBUtils:
    """
    获取向量数据库工具实例
    """
    global vector_db_utils
    if vector_db_utils is None:
        vector_db_utils = VectorDBUtils(persist_directory="./vector_db")
    return vector_db_utils

# 初始化向量数据库工具
try:
    vector_db_utils = get_vector_db_utils()
    logger.info("向量数据库工具初始化完成")
except Exception as e:
    logger.error(f"初始化向量数据库工具失败: {str(e)}")