import os
import logging
import requests
import time
import threading
import asyncio
from typing import List, Dict, Optional, Any
from functools import lru_cache
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

class LLMService:
    """
    大语言模型服务类，负责与大模型API的交互，支持缓存和并发优化
    """
    
    def __init__(self, cache_size: int = 500):
        # 从环境变量初始化配置
        self.api_base = os.environ.get("MODEL_API_BASE", "https://api.siliconflow.cn/v1")
        self.api_key = os.environ.get("MODEL_API_KEY", "")
        self.model_name = os.environ.get("MODEL_NAME", "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B")
        self.timeout = int(os.environ.get("MODEL_TIMEOUT", "100"))
        self.cache_size = cache_size
        self.system_prompt = """
        你是江西工业工程职业技术学院的智能问答助手，名字叫小尤学长。
        请以亲切、友好的语气，根据提供的上下文信息和对话历史回答用户问题。
        如果你不知道答案，请坦率表示，并建议用户联系学校相关部门。
        回答要简洁明了，重点突出。
        """
        
        # 初始化线程安全的缓存和锁
        self._response_cache = {}
        self._cache_lock = threading.RLock()
        self._model_lock = threading.RLock()
        
        # 统计信息
        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "total_response_time": 0,
            "failed_requests": 0
        }
        self._stats_lock = threading.RLock()
    
    def _generate_cache_key(self, prompt: str, chat_history: Optional[List[Dict]] = None) -> str:
        """
        生成缓存键
        
        Args:
            prompt: 用户的问题
            chat_history: 对话历史
            
        Returns:
            缓存键字符串
        """
        key = prompt.strip().lower()
        if chat_history:
            # 为对话历史添加一个简单的哈希
            history_str = "|".join(f"{h.get('role')}:{h.get('content', '')[:50]}" for h in chat_history)
            history_hash = str(hash(history_str) % 1000000)
            key = f"{key}:hist:{history_hash}"
        return key
    
    def _update_cache(self, key: str, response: str):
        """
        更新响应缓存，使用LRU策略
        
        Args:
            key: 缓存键
            response: 响应内容
        """
        with self._cache_lock:
            # 如果缓存已满，移除最老的条目
            if len(self._response_cache) >= self.cache_size:
                oldest_key = next(iter(self._response_cache))
                del self._response_cache[oldest_key]
            
            # 添加新的缓存条目
            self._response_cache[key] = {
                "response": response,
                "timestamp": time.time(),
                "hits": 0
            }
    
    def _get_from_cache(self, key: str) -> Optional[str]:
        """
        从缓存获取响应
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的响应或None
        """
        with self._cache_lock:
            if key in self._response_cache:
                # 更新命中计数
                self._response_cache[key]["hits"] += 1
                self._response_cache[key]["last_hit"] = time.time()
                
                # 更新统计信息
                with self._stats_lock:
                    self._stats["cache_hits"] += 1
                
                return self._response_cache[key]["response"]
            return None
    
    def is_configured(self) -> bool:
        """
        检查API配置是否完整
        """
        return all([self.api_base, self.api_key, self.model_name])
    
    def call_llm_api(self, prompt: str, chat_history: Optional[List[Dict]] = None) -> str:
        """
        调用大模型API生成回答，支持缓存和并发优化
        
        Args:
            prompt: 用户的问题
            chat_history: 对话历史
            
        Returns:
            生成的回答文本
        """
        # 更新请求统计
        with self._stats_lock:
            self._stats["total_requests"] += 1
        
        # 生成缓存键
        cache_key = self._generate_cache_key(prompt, chat_history)
        
        # 尝试从缓存获取
        cached_response = self._get_from_cache(cache_key)
        if cached_response:
            logger.debug(f"大模型API响应缓存命中: {prompt[:20]}...")
            return cached_response
        
        if not self.is_configured():
            logger.warning("大模型API未配置，使用默认回答")
            return "大模型API未配置，请检查环境变量配置。"
        
        try:
            start_time = time.time()
            
            # 构建消息历史
            messages = []
            
            # 添加系统提示
            messages.append({"role": "system", "content": self.system_prompt})
            
            # 添加对话历史
            if chat_history:
                messages.extend(chat_history)
            
            # 添加当前问题
            messages.append({"role": "user", "content": prompt})
            
            # 构建请求数据
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            # 设置请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 构建完整API URL
            api_url = f"{self.api_base}/chat/completions"
            
            # 使用锁保护API调用
            with self._model_lock:
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
            
            response_time = time.time() - start_time
            
            # 更新响应时间统计
            with self._stats_lock:
                self._stats["total_response_time"] += response_time
            
            if response.status_code != 200:
                logger.error(f"大模型API调用失败，状态码: {response.status_code}, 响应: {response.text}")
                # 更新失败统计
                with self._stats_lock:
                    self._stats["failed_requests"] += 1
                return f"API调用失败: {response.status_code}"
            
            # 解析响应
            result = response.json()
            if "choices" in result and result["choices"]:
                answer = result["choices"][0]["message"]["content"]
                
                # 更新缓存
                self._update_cache(cache_key, answer)
                
                logger.info(f"大模型API调用成功，用时: {response_time:.2f}秒")
                return answer
            else:
                logger.error(f"大模型API返回格式异常: {result}")
                # 更新失败统计
                with self._stats_lock:
                    self._stats["failed_requests"] += 1
                return "API返回数据格式异常"
                
        except Exception as e:
            logger.error(f"大模型API调用异常: {str(e)}")
            # 更新失败统计
            with self._stats_lock:
                self._stats["failed_requests"] += 1
            return f"API调用异常: {str(e)}"
    
    async def call_llm_api_async(self, prompt: str, chat_history: Optional[List[Dict]] = None) -> str:
        """
        异步调用大模型API生成回答
        
        Args:
            prompt: 用户的问题
            chat_history: 对话历史
            
        Returns:
            生成的回答文本
        """
        # 使用线程池执行同步代码
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,  # 使用默认线程池
            self.call_llm_api, 
            prompt, 
            chat_history
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取LLM服务统计信息
        
        Returns:
            统计信息字典
        """
        with self._stats_lock:
            stats_copy = self._stats.copy()
        
        # 计算平均响应时间
        if stats_copy["total_requests"] - stats_copy["cache_hits"] > 0:
            stats_copy["avg_response_time"] = (
                stats_copy["total_response_time"] / 
                (stats_copy["total_requests"] - stats_copy["cache_hits"])
            )
        else:
            stats_copy["avg_response_time"] = 0
        
        # 计算缓存命中率
        if stats_copy["total_requests"] > 0:
            stats_copy["cache_hit_rate"] = (
                stats_copy["cache_hits"] / stats_copy["total_requests"]
            )
        else:
            stats_copy["cache_hit_rate"] = 0
        
        # 添加基本信息
        stats_copy.update({
            "model_name": self.model_name,
            "api_base": self.api_base,
            "timeout": self.timeout,
            "cache_size": len(self._response_cache),
            "cache_capacity": self.cache_size
        })
        
        return stats_copy
    
    def clear_cache(self):
        """
        清空响应缓存
        """
        with self._cache_lock:
            self._response_cache.clear()
            logger.info("大模型API响应缓存已清空")
    
    def optimize_performance(self):
        """
        优化性能，清理过期缓存
        """
        try:
            current_time = time.time()
            expired_keys = []
            
            with self._cache_lock:
                # 移除1小时未访问的缓存项
                for key, entry in self._response_cache.items():
                    if current_time - entry.get("timestamp", 0) > 3600:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self._response_cache[key]
            
            logger.info(f"已优化大模型API性能，清理了 {len(expired_keys)} 个过期缓存项")
        except Exception as e:
            logger.error(f"优化大模型API性能失败: {str(e)}")

# 创建LLM服务实例
_llm_service = LLMService()

# 模块级别导出，用于方便导入和使用
MODEL_CONFIG = {
    "api_base": _llm_service.api_base,
    "model_name": _llm_service.model_name,
    "timeout": _llm_service.timeout
}

def call_llm_api(prompt: str, chat_history: Optional[List[Dict]] = None) -> str:
    return _llm_service.call_llm_api(prompt, chat_history)

def is_api_configured() -> bool:
    return _llm_service.is_configured()

def generate_answer(prompt: str, search_results: list = None, history: list = None) -> str:
    """
    生成回答的模块级函数
    
    Args:
        prompt: 用户问题
        search_results: 搜索结果列表（可选）
        history: 历史对话（可选）
        
    Returns:
        生成的回答文本
    """
    # 构建完整提示
    full_prompt = prompt
    
    if search_results:
        # 添加搜索结果到提示
        search_info = "参考信息：\n"
        for i, result in enumerate(search_results):
            search_info += f"[{i+1}] {result.get('content', '')}\n"
        full_prompt = f"{prompt}\n\n{search_info}"
    
    if history:
        # 简单添加历史对话
        history_info = "历史对话：\n"
        for turn in history:
            history_info += f"用户: {turn.get('user', '')}\n助手: {turn.get('assistant', '')}\n"
        full_prompt = f"{history_info}\n\n当前问题: {full_prompt}"
    
    # 调用LLM API生成回答
    try:
        result = call_llm_api(full_prompt)
        return result
    except Exception as e:
        # 如果API调用失败，返回简单的错误提示
        return f"生成回答时出现错误: {str(e)}"