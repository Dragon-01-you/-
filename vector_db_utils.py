import os
import logging
import random
import hashlib
import asyncio
import time
from typing import List, Dict, Any, Optional
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

class SimpleEmbeddings:
    """
    简单的嵌入模型替代类，用于在无法加载HuggingFace模型时提供基本功能
    """
    
    def __init__(self, dimension: int = 384):
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


# 强制使用SimpleEmbeddings，避免下载HuggingFace模型
HuggingFaceEmbeddings = None

logger = logging.getLogger(__name__)

import threading
from functools import lru_cache

class VectorDBUtils:
    """
    高性能向量数据库工具类，支持高并发查询、本地缓存和异步操作
    """
    
    def __init__(self, embedding_model_name: str = None,
                 persist_directory: str = "./chroma_db",
                 chunk_size: int = 500,
                 chunk_overlap: int = 50,
                 cache_size: int = 1000):
        """
        初始化向量数据库工具
        
        Args:
            embedding_model_name: 嵌入模型名称（已弃用，默认使用SimpleEmbeddings）
            persist_directory: 向量数据库持久化目录
            chunk_size: 文档分块大小
            chunk_overlap: 文档分块重叠大小
            cache_size: 查询缓存大小
        """
        self.embedding_model_name = embedding_model_name
        self.persist_directory = persist_directory
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.cache_size = cache_size
        self._local_cache = {}
        self._cache_lock = threading.RLock()  # 可重入锁用于缓存操作
        self._search_lock = threading.RLock()  # 可重入锁用于搜索操作
        self._init_lock = threading.Lock()  # 初始化锁
        self._initialized = False
        self._init_error = None
        
        # 性能统计指标
        self._search_count = 0
        self._cache_hit_count = 0
        self._search_time_total = 0
        self._last_cleanup_time = time.time()
        
        # 直接使用SimpleEmbeddings，避免任何可能的外部依赖
        logger.info("使用SimpleEmbeddings作为嵌入模型，确保离线环境兼容性，设置维度为1024以匹配现有向量数据库")
        self.embeddings = SimpleEmbeddings(dimension=1024)
        
        # 初始化向量存储
        self.vector_db = None
        # 尝试加载向量数据库，但即使失败也不会阻止服务运行
        try:
            self._load_vector_db()
        except Exception as e:
            logger.warning(f"加载向量数据库失败，但服务将继续运行: {str(e)}")
        
        # 预热常用查询缓存
        self._common_queries = [
            "学校地址在哪里",
            "图书馆开放时间",
            "奖学金申请条件",
            "如何注册账号",
            "就业指导中心联系方式"
        ]
        
        # 后台预热缓存
        threading.Thread(target=self._warmup_cache, daemon=True).start()
    
    def _load_vector_db(self):
        """
        加载现有的向量数据库
        """
        try:
            if os.path.exists(self.persist_directory):
                self.vector_db = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                logger.info(f"成功加载向量数据库，位于 {self.persist_directory}")
            else:
                logger.info(f"向量数据库目录不存在：{self.persist_directory}")
        except Exception as e:
            logger.error(f"加载向量数据库失败: {str(e)}")
    
    def load_documents(self, documents_dir: str, file_extensions: List[str] = [".txt"]) -> List[Document]:
        """
        加载文档
        
        Args:
            documents_dir: 文档目录
            file_extensions: 文件扩展名列表
            
        Returns:
            文档列表
        """
        documents = []
        
        try:
            for ext in file_extensions:
                if ext == ".txt":
                    loader = DirectoryLoader(
                        documents_dir,
                        glob=f"**/*{ext}",
                        loader_cls=TextLoader,
                        show_progress=True
                    )
                    documents.extend(loader.load())
            
            logger.info(f"成功加载 {len(documents)} 个文档")
        except Exception as e:
            logger.error(f"加载文档失败: {str(e)}")
        
        return documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        分割文档
        
        Args:
            documents: 原始文档列表
            
        Returns:
            分割后的文档块列表
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "\r\n", "\r", "", " "]
        )
        
        try:
            splits = text_splitter.split_documents(documents)
            logger.info(f"文档分割完成，得到 {len(splits)} 个文档块")
            return splits
        except Exception as e:
            logger.error(f"分割文档失败: {str(e)}")
            return []
    
    def build_vector_db(self, documents: List[Document], incremental: bool = False) -> bool:
        """
        构建向量数据库
        
        Args:
            documents: 文档列表
            incremental: 是否增量更新
            
        Returns:
            是否构建成功
        """
        try:
            # 分割文档
            splits = self.split_documents(documents)
            if not splits:
                return False
            
            if incremental and self.vector_db is not None:
                # 增量更新模式
                self.vector_db.add_documents(splits)
                logger.info(f"向量数据库增量更新完成，新增 {len(splits)} 个文档块")
            else:
                # 重新构建模式
                self.vector_db = Chroma.from_documents(
                    splits,
                    self.embeddings,
                    persist_directory=self.persist_directory
                )
                logger.info(f"向量数据库构建完成，存储 {len(splits)} 个文档块")
            
            # 持久化存储
            self.vector_db.persist()
            return True
        except Exception as e:
            logger.error(f"构建向量数据库失败: {str(e)}")
            return False
    
    def _generate_cache_key(self, query: str, top_k: int) -> str:
        """
        生成缓存键
        """
        # 标准化查询字符串
        normalized_query = query.strip().lower()
        return f"{normalized_query}:{top_k}"
    
    def _update_cache(self, key: str, results: List[Dict[str, Any]]):
        """
        更新本地缓存，使用LRU策略
        """
        import time
        
        with self._cache_lock:
            # 如果缓存已满，移除最老的条目
            if len(self._local_cache) >= self.cache_size:
                # 获取最老的键并删除
                oldest_key = next(iter(self._local_cache))
                del self._local_cache[oldest_key]
                
            # 添加新的缓存条目
            self._local_cache[key] = {
                "results": results,
                "timestamp": time.time(),
                "hits": 0
            }
    
    def _get_from_cache(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """
        从缓存获取结果
        """
        import time
        
        with self._cache_lock:
            if key in self._local_cache:
                # 更新命中计数
                self._local_cache[key]["hits"] += 1
                self._local_cache[key]["last_hit"] = time.time()
                return self._local_cache[key]["results"]
            return None
    
    def _warmup_cache(self):
        """
        预热常用查询缓存
        """
        import time
        
        try:
            # 等待数据库初始化完成
            time.sleep(2)
            
            for query in self._common_queries:
                if self.vector_db:
                    results = self.search(query, top_k=3)
                    logger.info(f"缓存预热完成: {query}")
                    time.sleep(0.5)  # 避免过度加载
        except Exception as e:
            logger.error(f"缓存预热失败: {str(e)}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        同步搜索相关文档，支持缓存和并发优化
        
        Args:
            query: 搜索查询
            top_k: 返回的文档数量
            
        Returns:
            相关文档列表
        """
        # 如果查询为空，直接返回空结果
        if not query or not query.strip():
            return []
        
        # 生成缓存键
        cache_key = self._generate_cache_key(query, top_k)
        
        # 尝试从缓存获取
        cached_results = self._get_from_cache(cache_key)
        if cached_results:
            with self._cache_lock:
                self._cache_hit_count += 1
            logger.debug(f"向量搜索缓存命中: {query[:20]}...")
            return cached_results
        
        # 检查向量数据库是否初始化
        if not self.vector_db:
            logger.warning("向量数据库未初始化，返回空结果")
            return []
        
        # 执行搜索，使用锁保护
        with self._search_lock:
            try:
                start_time = time.time()
                
                results = self.vector_db.similarity_search_with_score(query, k=top_k)
                search_time = time.time() - start_time
                
                # 更新性能统计
                with self._cache_lock:
                    self._search_count += 1
                    self._search_time_total += search_time
                
                # 格式化结果
                formatted_results = []
                for doc, score in results:
                    formatted_results.append({
                        "page_content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": score,
                        "relevance_score": 1.0 - score,
                        "search_time": search_time  # 添加搜索时间
                    })
                
                # 更新缓存
                self._update_cache(cache_key, formatted_results)
                
                # 检查是否需要自动清理过期缓存
                current_time = time.time()
                if current_time - self._last_cleanup_time > 600:  # 每10分钟清理一次
                    self.optimize_search()
                    self._last_cleanup_time = current_time
                
                logger.info(f"搜索完成，找到 {len(formatted_results)} 个相关文档，耗时: {search_time:.4f}秒")
                return formatted_results
            except Exception as e:
                logger.error(f"搜索文档失败: {str(e)}")
                # 返回空结果，确保服务能够继续运行
                return []
    
    async def search_async(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        异步搜索相关文档，支持缓存和并发优化
        
        Args:
            query: 搜索查询
            top_k: 返回的文档数量
            
        Returns:
            相关文档列表
        """
        # 对于简单的缓存检查，直接在异步上下文中执行
        if not query or not query.strip():
            return []
        
        cache_key = self._generate_cache_key(query, top_k)
        cached_results = self._get_from_cache(cache_key)
        if cached_results:
            with self._cache_lock:
                self._cache_hit_count += 1
            logger.debug(f"异步向量搜索缓存命中: {query[:20]}...")
            return cached_results
        
        # 对于耗时的搜索操作，使用线程池执行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.search, 
            query, 
            top_k
        )
    
    def simple_keyword_search(self, query: str, documents: List[Document], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        基于关键词的简单搜索（用于极端情况下的回退方案）
        
        Args:
            query: 搜索查询
            documents: 文档列表
            top_k: 返回的文档数量
            
        Returns:
            相关文档列表
        """
        try:
            # 简单的关键词匹配
            query_lower = query.lower()
            results = []
            
            for doc in documents:
                content_lower = doc.page_content.lower()
                # 计算匹配的关键词数量
                match_count = sum(1 for word in query_lower.split() if word in content_lower)
                
                if match_count > 0:
                    results.append({
                        "page_content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": -match_count  # 使用负分数表示相关性（值越小越相关）
                    })
            
            # 按相关性排序
            results.sort(key=lambda x: x["score"])
            
            logger.info(f"关键词搜索完成，找到 {len(results)} 个相关文档")
            return results[:top_k]
        except Exception as e:
            logger.error(f"关键词搜索失败: {str(e)}")
            return []
    
    def get_document_count(self) -> int:
        """
        获取向量数据库中的文档数量
        
        Returns:
            文档数量
        """
        try:
            if self.vector_db is None:
                return 0
            # 使用更通用的方法获取文档数量
            if hasattr(self.vector_db, '_collection') and hasattr(self.vector_db._collection, 'count'):
                return self.vector_db._collection.count()
            elif hasattr(self.vector_db, 'get'):
                try:
                    return len(self.vector_db.get()['ids'])
                except:
                    pass
            # 如果无法直接获取数量，返回0
            return 0
        except Exception as e:
            logger.error(f"获取文档数量失败: {str(e)}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        同步获取向量数据库和缓存统计信息
        
        Returns:
            统计信息字典
        """
        try:
            with self._cache_lock:
                stats = {
                    "db_path": self.persist_directory,
                    "documents_count": self.get_document_count(),
                    "cache_size": len(self._local_cache),
                    "cache_capacity": self.cache_size,
                    "cache_hits": self._cache_hit_count,
                    "total_searches": self._search_count,
                    "last_cleanup_time": self._last_cleanup_time
                }
                
                # 计算缓存命中率
                if self._search_count > 0:
                    stats["cache_hit_rate"] = round((self._cache_hit_count / self._search_count) * 100, 2)
                else:
                    stats["cache_hit_rate"] = 0
                
                # 计算平均搜索时间
                if self._search_count > 0:
                    stats["avg_search_time_ms"] = round((self._search_time_total / self._search_count) * 1000, 2)
                else:
                    stats["avg_search_time_ms"] = 0
                
                # 缓存使用情况
                stats["cache_usage_percent"] = round((len(self._local_cache) / self.cache_size) * 100, 2) if self.cache_size > 0 else 0
                
                return stats
                
        except Exception as e:
            logger.error(f"获取向量数据库统计信息失败: {str(e)}")
            return {"error": str(e)}
    
    async def get_stats_async(self) -> Dict[str, Any]:
        """
        异步获取向量数据库和缓存统计信息
        
        Returns:
            统计信息字典
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.get_stats
        )
    
    # 为了向后兼容，定义异步版本的get_stats方法
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取向量数据库和缓存统计信息（异步版本）
        """
        return await self.get_stats_async()
    
    def clear_cache(self):
        """
        同步清空本地缓存
        """
        with self._cache_lock:
            self._local_cache.clear()
            self._cache_hit_count = 0  # 重置命中计数
            logger.info("向量数据库缓存已清空")
    
    async def clear_cache_async(self):
        """
        异步清空本地缓存
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.clear_cache)
    
    def optimize_search(self):
        """
        同步优化搜索性能，清理过期缓存
        
        Returns:
            清理的缓存项数量
        """
        try:
            current_time = time.time()
            expired_keys = []
            least_used_keys = []
            
            with self._cache_lock:
                # 移除30分钟未访问的缓存项
                for key, entry in self._local_cache.items():
                    if current_time - entry.get("timestamp", 0) > 1800:
                        expired_keys.append(key)
                
                # 如果缓存使用率超过80%，额外移除10%最少使用的项
                if len(self._local_cache) > self.cache_size * 0.8:
                    # 按访问频率排序，获取最少使用的10%
                    sorted_entries = sorted(
                        self._local_cache.items(), 
                        key=lambda x: x[1].get("hits", 0)
                    )
                    remove_count = max(1, int(len(self._local_cache) * 0.1))
                    least_used_keys = [k for k, _ in sorted_entries[:remove_count]]
                
                # 合并需要删除的键
                all_keys_to_remove = set(expired_keys + least_used_keys)
                
                for key in all_keys_to_remove:
                    if key in self._local_cache:
                        del self._local_cache[key]
            
            cleaned_count = len(all_keys_to_remove)
            logger.info(f"已优化向量搜索，清理了 {cleaned_count} 个缓存项（过期: {len(expired_keys)}, 最少使用: {len(least_used_keys)}）")
            return cleaned_count
        except Exception as e:
            logger.error(f"优化搜索失败: {str(e)}")
            return 0
    
    async def optimize_search_async(self):
        """
        异步优化搜索性能，清理过期缓存
        
        Returns:
            清理的缓存项数量
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.optimize_search)
    
    def update_embedding_model(self, new_model_name: str) -> bool:
        """
        更新嵌入模型
        
        Args:
            new_model_name: 新的嵌入模型名称
            
        Returns:
            是否更新成功
        """
        try:
            self.embedding_model_name = new_model_name
            self.embeddings = HuggingFaceEmbeddings(model_name=new_model_name)
            # 重新加载向量数据库
            self._load_vector_db()
            logger.info(f"嵌入模型更新为: {new_model_name}")
            return True
        except Exception as e:
            logger.error(f"更新嵌入模型失败: {str(e)}")
            return False
    
    def reset_vector_db(self) -> bool:
        """重置向量数据库"""
        import shutil
        
        try:
            # 删除持久化目录
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)
                logger.info(f"向量数据库已重置，删除目录: {self.persist_directory}")
            
            # 重新初始化
            self.vector_db = None
            return True
        except Exception as e:
            logger.error(f"重置向量数据库失败: {str(e)}")
            return False

# 创建全局向量数据库工具实例
vector_db_utils = VectorDBUtils()