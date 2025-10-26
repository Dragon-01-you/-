import time
import asyncio
from typing import Dict, List, Optional, Any
import logging
import threading
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from functools import wraps

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    高性能令牌桶限流中间件
    支持IP级别和用户级别的限流
    线程安全，支持异步操作
    """
    
    def __init__(self, tokens_per_minute: int = 60, burst_limit: int = 10):
        """
        初始化限流器
        
        Args:
            tokens_per_minute: 每分钟允许的请求数
            burst_limit: 突发请求限制
        """
        self.tokens_per_minute = tokens_per_minute
        self.tokens_per_second = tokens_per_minute / 60.0
        self.burst_limit = burst_limit
        self.ip_buckets: Dict[str, Dict] = {}
        self.user_buckets: Dict[str, Dict] = {}
        self.global_last_refill = time.time()
        self.global_tokens = burst_limit
        # 添加线程锁确保线程安全
        self.lock = threading.RLock()
        # 添加统计计数器
        self.total_requests = 0
        self.limited_requests = 0
        logger.info(f"限流器初始化完成，每分钟{tokens_per_minute}个请求，突发限制{burst_limit}")
    
    def _get_ip_address(self, request: Request) -> str:
        """从请求中获取IP地址"""
        # 优先从X-Forwarded-For获取，适用于代理环境
        x_forwarded_for = request.headers.get('X-Forwarded-For')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        # 直接从客户端地址获取
        client_host = request.client.host if request.client else 'unknown'
        return client_host
    
    def _get_or_create_bucket(self, buckets: Dict[str, Dict], key: str) -> Dict:
        """获取或创建令牌桶"""
        if key not in buckets:
            buckets[key] = {
                'tokens': self.burst_limit,
                'last_refill': time.time()
            }
        return buckets[key]
    
    def _refill_tokens(self, bucket: Dict):
        """填充令牌"""
        now = time.time()
        time_passed = now - bucket['last_refill']
        
        # 计算新增令牌
        new_tokens = time_passed * self.tokens_per_second
        if new_tokens > 0:
            bucket['tokens'] = min(self.burst_limit, bucket['tokens'] + new_tokens)
            bucket['last_refill'] = now
    
    def check_rate_limit(self, request: Request, username: Optional[str] = None) -> bool:
        """
        同步检查请求是否超过速率限制
        
        Args:
            request: FastAPI请求对象
            username: 用户名（可选）
            
        Returns:
            True表示允许请求，False表示拒绝请求
        """
        try:
            with self.lock:
                self.total_requests += 1
                
                # 获取IP地址
                ip_address = self._get_ip_address(request)
                
                # 全局限流检查
                self._refill_tokens({'tokens': self.global_tokens, 'last_refill': self.global_last_refill})
                if self.global_tokens < 1:
                    self.limited_requests += 1
                    logger.warning(f"全局限流触发，IP: {ip_address}")
                    return False
                
                # IP级别限流
                ip_bucket = self._get_or_create_bucket(self.ip_buckets, ip_address)
                self._refill_tokens(ip_bucket)
                
                # 用户级别限流（如果提供了用户名）
                if username:
                    user_bucket = self._get_or_create_bucket(self.user_buckets, username)
                    self._refill_tokens(user_bucket)
                    
                    if user_bucket['tokens'] < 1:
                        self.limited_requests += 1
                        logger.warning(f"用户限流触发: {username}, IP: {ip_address}")
                        return False
                    
                    user_bucket['tokens'] -= 1
                
                if ip_bucket['tokens'] < 1:
                    self.limited_requests += 1
                    logger.warning(f"IP限流触发: {ip_address}")
                    return False
                
                # 消耗令牌
                ip_bucket['tokens'] -= 1
                self.global_tokens -= 1
                
                return True
        
        except Exception as e:
            logger.error(f"限流检查失败: {str(e)}")
            # 出错时默认允许请求，避免影响正常服务
            return True
    
    async def check_rate_limit_async(self, request: Request, username: Optional[str] = None) -> bool:
        """
        异步检查请求是否超过速率限制
        
        Args:
            request: FastAPI请求对象
            username: 用户名（可选）
            
        Returns:
            True表示允许请求，False表示拒绝请求
        """
        # 使用默认线程池执行同步方法
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            self.check_rate_limit, 
            request, 
            username
        )
    
    def middleware(self):
        """创建FastAPI中间件"""
        async def rate_limit_middleware(request: Request, call_next):
            # 跳过静态资源和健康检查路径
            if request.url.path in ['/health', '/favicon.ico'] or \
               request.url.path.startswith('/static/') or \
               request.url.path.startswith('/assets/') or \
               request.url.path.startswith('/stats/'):
                return await call_next(request)
            
            # 检查速率限制
            if not await self.check_rate_limit_async(request):
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "请求过于频繁，请稍后再试",
                        "retry_after": 10,  # 建议10秒后重试
                        "timestamp": time.time()
                    },
                    headers={"X-RateLimit-Limit": str(self.tokens_per_minute)}
                )
            
            # 添加速率限制头信息
            with self.lock:
                headers = {
                    "X-RateLimit-Limit": str(self.tokens_per_minute),
                    "X-RateLimit-Remaining": str(round(self.global_tokens))
                }
            
            response = await call_next(request)
            
            # 添加响应头
            for key, value in headers.items():
                response.headers[key] = value
            
            return response
        
        return rate_limit_middleware
    
    def get_rate_limit_dependency(self, username: Optional[str] = None):
        """创建速率限制依赖项，用于特定端点"""
        async def rate_limit_dependency(request: Request):
            if not await self.check_rate_limit_async(request, username):
                raise HTTPException(
                    status_code=429,
                    detail="请求过于频繁，请稍后再试",
                    headers={"Retry-After": "10"}
                )
        
        return rate_limit_dependency
    
    def get_stats(self) -> Dict[str, Any]:
        """同步获取限流统计信息"""
        with self.lock:
            total = self.total_requests
            limited = self.limited_requests
            allowed = total - limited
            limit_rate = (limited / total * 100) if total > 0 else 0
            
            return {
                'global_tokens': round(self.global_tokens, 2),
                'global_capacity': self.burst_limit,
                'ip_buckets_count': len(self.ip_buckets),
                'user_buckets_count': len(self.user_buckets),
                'tokens_per_minute': self.tokens_per_minute,
                'total_requests': total,
                'allowed_requests': allowed,
                'limited_requests': limited,
                'limit_rate': round(limit_rate, 2),
                'rate_per_second': self.tokens_per_second
            }
    
    async def get_stats_async(self) -> Dict[str, Any]:
        """异步获取限流统计信息"""
        # 使用默认线程池执行同步方法
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            self.get_stats
        )
    
    # 为了向后兼容，定义异步版本的get_stats方法
    async def get_stats(self) -> Dict[str, Any]:
        """获取限流统计信息（异步版本）"""
        return await self.get_stats_async()
    
    def clear_expired_buckets(self):
        """同步清理长时间未使用的令牌桶"""
        with self.lock:
            now = time.time()
            expired_threshold = now - 300  # 5分钟未活动
            
            # 清理IP桶
            expired_ips = [ip for ip, bucket in self.ip_buckets.items() 
                          if bucket['last_refill'] < expired_threshold]
            for ip in expired_ips:
                del self.ip_buckets[ip]
            
            # 清理用户桶
            expired_users = [user for user, bucket in self.user_buckets.items() 
                            if bucket['last_refill'] < expired_threshold]
            for user in expired_users:
                del self.user_buckets[user]
            
            if expired_ips or expired_users:
                logger.debug(f"清理了 {len(expired_ips)} 个IP桶和 {len(expired_users)} 个用户桶")
                return len(expired_ips) + len(expired_users)
            return 0
    
    async def clear_expired_buckets_async(self):
        """异步清理长时间未使用的令牌桶"""
        # 使用默认线程池执行同步方法
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            self.clear_expired_buckets
        )

# 创建全局限流器实例
# 针对高并发场景，提高默认限制
rate_limiter = RateLimiter(tokens_per_minute=1000, burst_limit=100)