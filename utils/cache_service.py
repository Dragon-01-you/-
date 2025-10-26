import json
import hashlib
import time
import asyncio
from typing import Dict, Any, Optional
import logging
import threading
from contextlib import asynccontextmanager
import concurrent.futures

logger = logging.getLogger(__name__)

class CacheService:
    """
    高性能缓存服务类，用于缓存热门问题回答和会话数据
    支持LRU缓存策略、过期时间管理和内存优化
    同时支持同步和异步操作，并确保线程安全
    """
    
    def __init__(self, max_entries: int = 1000, default_ttl: int = 3600):
        """
        初始化缓存服务
        
        Args:
            max_entries: 最大缓存条目数
            default_ttl: 默认过期时间（秒）
        """
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict] = {}
        self.access_order = []
        self.hit_count = 0
        self.miss_count = 0
        # 添加线程锁确保线程安全
        self.lock = threading.RLock()
        logger.info(f"缓存服务初始化完成，最大条目: {max_entries}，默认过期时间: {default_ttl}秒")
    
    def _generate_key(self, data: Any) -> str:
        """生成缓存键"""
        try:
            if isinstance(data, str):
                content = data
            else:
                content = json.dumps(data, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(content.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"生成缓存键失败: {str(e)}")
            # 即使失败也返回一个有效的默认键
            return hashlib.md5(str(data).encode('utf-8')).hexdigest()
    
    def _is_expired(self, entry: Dict) -> bool:
        """检查缓存是否过期"""
        return entry.get('expires_at', 0) < time.time()
    
    def _evict_oldest(self):
        """移除最老的缓存条目"""
        if self.access_order:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
            logger.debug(f"缓存已满，移除最老条目: {oldest_key}")
    
    def _update_access_order(self, key: str):
        """更新访问顺序"""
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def get_sync(self, key_data: Any) -> Optional[Any]:
        """
        同步获取缓存
        
        Args:
            key_data: 可以是字符串或JSON可序列化对象
            
        Returns:
            缓存的数据，如果不存在或已过期则返回None
        """
        with self.lock:
            key = self._generate_key(key_data)
            
            if key not in self.cache:
                self.miss_count += 1
                return None
            
            entry = self.cache[key]
            
            # 检查是否过期
            if self._is_expired(entry):
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
                self.miss_count += 1
                logger.debug(f"缓存已过期: {key}")
                return None
            
            # 更新访问顺序
            self._update_access_order(key)
            self.hit_count += 1
            logger.debug(f"缓存命中: {key}")
            return entry['data']
    
    # 为了向后兼容保留原方法名
    def get(self, key_data: Any) -> Optional[Any]:
        """
        获取缓存（同步版本，向后兼容）
        
        Args:
            key_data: 可以是字符串或JSON可序列化对象
            
        Returns:
            缓存的数据，如果不存在或已过期则返回None
        """
        return self.get_sync(key_data)
    
    async def get(self, key_data: Any) -> Optional[Any]:
        """
        获取缓存（异步版本）
        
        Args:
            key_data: 可以是字符串或JSON可序列化对象
            
        Returns:
            缓存的数据，如果不存在或已过期则返回None
        """
        # 调用明确的同步方法
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            self.get_sync, 
            key_data
        )
    
    def set_sync(self, key_data: Any, data: Any, ttl: Optional[int] = None) -> bool:
        """
        同步设置缓存
        
        Args:
            key_data: 可以是字符串或JSON可序列化对象
            data: 要缓存的数据
            ttl: 过期时间（秒），None表示使用默认值
            
        Returns:
            是否设置成功
        """
        try:
            with self.lock:
                key = self._generate_key(key_data)
                
                # 如果缓存已满，移除最老的条目
                if len(self.cache) >= self.max_entries and key not in self.cache:
                    self._evict_oldest()
                
                # 设置缓存
                ttl = ttl or self.default_ttl
                self.cache[key] = {
                    'data': data,
                    'expires_at': time.time() + ttl,
                    'created_at': time.time()
                }
                
                # 更新访问顺序
                self._update_access_order(key)
                logger.debug(f"缓存设置成功: {key}")
                return True
        except Exception as e:
            logger.error(f"缓存设置失败: {str(e)}")
            return False
    
    # 为了向后兼容保留原方法名
    def set(self, key_data: Any, data: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存（同步版本，向后兼容）
        
        Args:
            key_data: 可以是字符串或JSON可序列化对象
            data: 要缓存的数据
            ttl: 过期时间（秒），None表示使用默认值
            
        Returns:
            是否设置成功
        """
        return self.set_sync(key_data, data, ttl)
    
    # 为了向后兼容，定义异步版本的set方法
    async def set(self, key_data: Any, data: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存（异步版本）
        
        Args:
            key_data: 可以是字符串或JSON可序列化对象
            data: 要缓存的数据
            ttl: 过期时间（秒），None表示使用默认值
            
        Returns:
            是否设置成功
        """
        # 调用明确的同步方法
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            self.set_sync, 
            key_data, 
            data, 
            ttl
        )
    
    def delete_sync(self, key_data: Any) -> bool:
        """同步删除缓存"""
        try:
            with self.lock:
                key = self._generate_key(key_data)
                if key in self.cache:
                    del self.cache[key]
                    if key in self.access_order:
                        self.access_order.remove(key)
                    logger.debug(f"缓存删除成功: {key}")
                    return True
                return False
        except Exception as e:
            logger.error(f"缓存删除失败: {str(e)}")
            return False
    
    # 为了向后兼容保留原方法名
    def delete(self, key_data: Any) -> bool:
        """
        删除缓存（同步版本，向后兼容）
        """
        return self.delete_sync(key_data)
    
    # 为了向后兼容，定义异步版本的delete方法
    async def delete(self, key_data: Any) -> bool:
        """删除缓存（异步版本）"""
        # 调用明确的同步方法
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            self.delete_sync, 
            key_data
        )
    
    def clear_sync(self):
        """同步清空缓存"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
            logger.info("缓存已清空")
    
    # 为了向后兼容保留原方法名
    def clear(self):
        """
        清空缓存（同步版本，向后兼容）
        """
        self.clear_sync()
    
    # 为了向后兼容，定义异步版本的clear方法
    async def clear(self):
        """清空缓存（异步版本）"""
        # 调用明确的同步方法
        await asyncio.get_event_loop().run_in_executor(
            None, 
            self.clear_sync
        )
    
    def get_stats_sync(self) -> Dict[str, Any]:
        """同步获取缓存统计信息"""
        with self.lock:
            total = self.hit_count + self.miss_count
            hit_rate = (self.hit_count / total * 100) if total > 0 else 0
            
            # 清理过期缓存
            expired_count = self.cleanup_expired_sync()
            
            return {
                'size': len(self.cache),
                'max_size': self.max_entries,
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate': round(hit_rate, 2),
                'total_requests': total,
                'recently_cleaned': expired_count,
                'default_ttl': self.default_ttl
            }
    
    # 为了向后兼容保留原方法名
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息（同步版本，向后兼容）
        """
        return self.get_stats_sync()
    
    # 为了向后兼容，定义异步版本的get_stats方法
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息（异步版本）"""
        # 调用明确的同步方法
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            self.get_stats_sync
        )
    
    def cleanup(self):
        """同步清理过期缓存（兼容性方法）"""
        return self.cleanup_expired_sync()
    
    def cleanup_expired_sync(self) -> int:
        """
        同步清理过期缓存并返回清理的条目数
        
        Returns:
            清理的过期缓存条目数
        """
        with self.lock:
            expired_keys = []
            for key, entry in self.cache.items():
                if self._is_expired(entry):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
            
            if expired_keys:
                logger.debug(f"清理了 {len(expired_keys)} 个过期缓存")
            
            return len(expired_keys)
    
    # 为了向后兼容保留原方法名
    def cleanup_expired(self) -> int:
        """
        清理过期缓存并返回清理的条目数（同步版本，向后兼容）
        
        Returns:
            清理的过期缓存条目数
        """
        return self.cleanup_expired_sync()
    
    # 为了向后兼容，定义异步版本的cleanup_expired方法
    async def cleanup_expired(self) -> int:
        """清理过期缓存并返回清理的条目数（异步版本）"""
        # 调用明确的同步方法
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            self.cleanup_expired_sync
        )

# 创建全局缓存服务实例
cache_service = CacheService(max_entries=5000, default_ttl=7200)