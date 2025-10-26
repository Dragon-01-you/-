import os
import sys
import logging
import json
import asyncio
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import threading
import hashlib
from functools import lru_cache, wraps
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv
import requests
from pydantic import BaseModel, Field

# 导入服务和工具
from utils.auth_utils import verify_user_session, login as auth_login, logout as auth_logout
from utils.vector_db_utils import VectorDBUtils
from utils.db_service import db_service
from services.llm_service import generate_answer, is_api_configured
# 导入高性能组件
from utils.cache_service import cache_service
from utils.rate_limiter import rate_limiter
# 暂时注释掉搜索服务导入，避免可能的依赖问题
# from services.search_service import should_use_realtime_search, search_api_integration, optimize_search_query, generate_precise_search_results
# 创建一个最小化的搜索服务替代类
class MinimalSearchService:
    def should_use_realtime_search(self, query):
        return False
    def search_api_integration(self, query, need_realtime=False, vector_docs_count=0):
        return []
# 创建搜索服务实例
search_service = MinimalSearchService()

# 定义API请求和响应模型
class LoginRequest(BaseModel):
    username: str
    password: str

class AskRequest(BaseModel):
    question: str
    chat_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)

class AskResponse(BaseModel):
    answer: str
    sources: List[str]
    is_real_time: bool

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 确保utils模块可以被导入
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 请求计数器
request_counter = {
    "total": 0,
    "success": 0,
    "error": 0,
    "cache_hits": 0,
    "vector_searches": 0
}
request_counter_lock = asyncio.Lock()

# 初始化FastAPI应用
app = FastAPI(
    title="江西工业工程职业技术学院 AI 问答系统",
    description="高并发优化版智能问答系统API",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# 配置静态文件服务
try:
    # 配置静态文件目录
    app.mount("/static", StaticFiles(directory="./OKComputer_江西工业智能问答前端/resources"), name="static")
    logger.info("静态文件服务已配置")
except Exception as e:
    logger.warning(f"配置静态文件服务时出错: {str(e)}")
    # 如果失败，尝试使用当前目录
    try:
        app.mount("/static", StaticFiles(directory="resources"), name="static")
        logger.info("使用备选静态文件目录")
    except Exception as e2:
        logger.error(f"配置静态文件服务失败: {str(e2)}")

# 配置CORS - 支持环境变量和动态配置
# 从环境变量获取允许的源，如果没有设置则使用默认值
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# 处理通配符情况
if "*" in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # 可通过环境变量配置
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "X-Process-Time"]
)

# 请求跟踪和性能监控中间件
@app.middleware("http")
async def request_tracker(request: Request, call_next):
    start_time = time.time()
    path = request.url.path
    
    # 跳过静态文件和文档路径
    if path.startswith("/static/") or path in ["/api/docs", "/api/redoc", "/api/openapi.json"]:
        response = await call_next(request)
        return response
    
    try:
        # 增加总请求数
        async with request_counter_lock:
            request_counter["total"] += 1
        
        # 执行请求
        response = await call_next(request)
        
        # 增加成功请求数
        if response.status_code < 400:
            async with request_counter_lock:
                request_counter["success"] += 1
        else:
            async with request_counter_lock:
                request_counter["error"] += 1
        
        # 添加处理时间头
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    except Exception as e:
        # 增加错误请求数
        async with request_counter_lock:
            request_counter["error"] += 1
        
        logger.error(f"请求处理异常: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "服务器内部错误"}
        )

# 添加速率限制中间件
app.middleware("http")(rate_limiter.middleware())



# 登录端点
@app.post("/login")
async def login(request: LoginRequest):
    """用户登录"""
    return await auth_login(request.username, request.password)



# 初始化向量数据库工具，添加错误处理以确保服务器能够启动
try:
    vector_db = VectorDBUtils()
    logger.info("向量数据库工具初始化完成")
except Exception as e:
    logger.error(f"向量数据库工具初始化失败，但服务器将继续运行: {str(e)}")
    # 创建一个最小化的VectorDBUtils替代类以确保服务能够运行
    class MinimalVectorDB:
        def search(self, query, top_k=5):
            return []
    vector_db = MinimalVectorDB()

# 数据库服务已改为本地JSON存储模式，无需显式初始化
logger.info("数据库服务已准备就绪（本地JSON存储模式）")

# 检查LLM API配置状态
if not is_api_configured():
    logger.warning("LLM API未配置，将使用默认响应")





# 依赖：获取客户端IP
async def get_client_ip(request: Request) -> str:
    # 尝试从代理头获取真实IP
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    
    # 尝试从其他代理头获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 获取远程地址
    client_host = request.client.host if request.client else "unknown"
    return client_host

@app.post("/ask")
async def ask(
    request: AskRequest, 
    username: str = Depends(verify_user_session), 
    request_obj: Request = Request,
    client_ip: str = Depends(get_client_ip)
):
    start_time = time.time()
    # 记录用户提问日志
    logger.info(f"用户 {username} 提问: {request.question[:100]}...")
    
    # 检查用户级别速率限制
    rate_limit_result = await rate_limiter.check_rate_limit(client_ip, username)
    if not rate_limit_result["allowed"]:
        raise HTTPException(
            status_code=429,
            detail="您的请求过于频繁，请稍后再试",
            headers={"Retry-After": str(rate_limit_result["retry_after"])}
        )
    
    try:
        # 检查输入参数
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="问题不能为空")
        
        # 生成缓存键 - 使用问题和最近的聊天历史的哈希值作为键
        history_str = json.dumps(request.chat_history[-3:]) if request.chat_history else ""
        cache_key = hashlib.md5(f"{request.question}:{history_str}".encode()).hexdigest()
        
        # 尝试从缓存获取回答
        cached_response = await cache_service.get(f"ask:{cache_key}")
        if cached_response:
            async with request_counter_lock:
                request_counter["cache_hits"] += 1
            logger.info(f"缓存命中，直接返回回答 (耗时: {time.time() - start_time:.3f}s)")
            
            # 异步保存聊天历史，不阻塞响应
            async def save_history():
                try:
                    await db_service.save_chat_history_async(
                        username=username,
                        question=request.question,
                        answer=cached_response["answer"],
                        sources=cached_response["sources"],
                        is_real_time=False
                    )
                except Exception as e:
                    logger.error(f"异步保存聊天历史失败: {str(e)}")
            
            asyncio.create_task(save_history())
            
            # 返回缓存的响应，添加缓存标记
            result = {**cached_response, "from_cache": True, "process_time": time.time() - start_time}
            return JSONResponse(content=result, headers=rate_limit_result["headers"])
        
        # 从向量数据库检索相关文档（异步执行）
        vector_docs = []
        try:
            vector_docs = await run_in_threadpool(vector_db.search, request.question, top_k=5)
            async with request_counter_lock:
                request_counter["vector_searches"] += 1
            logger.info(f"从向量数据库检索到 {len(vector_docs)} 条文档 (耗时: {time.time() - start_time:.3f}s)")
        except Exception as e:
            logger.warning(f"向量数据库搜索失败: {str(e)}")
            vector_docs = []
        
        # 简化处理，直接生成基本回答（异步执行）
        answer = await run_in_threadpool(
            lambda: f"这是对您问题 '{request.question}' 的回答。系统当前在离线模式下运行。"
        )
        
        # 构建响应
        response = {
            "answer": answer,
            "sources": ["系统提示"] if not vector_docs else [doc.get('metadata', {}).get('source', '向量数据库') for doc in vector_docs[:3]],
            "search_used": False,
            "vector_search_used": len(vector_docs) > 0,
            "token_usage": {},
            "cached": False
        }
        
        # 缓存回答（基于问题频率和复杂度的智能缓存策略）
        cache_ttl = 3600  # 1小时
        question_length = len(request.question)
        
        # 简单常见问题缓存更长时间
        if question_length < 30:
            cache_ttl = 7200  # 2小时
        elif question_length > 200:
            cache_ttl = 1800  # 30分钟（复杂问题可能较少重复）
        
        # 使用异步缓存设置
        await cache_service.set(f"ask:{cache_key}", response, expire_seconds=cache_ttl)
        logger.info(f"回答已缓存 (TTL: {cache_ttl}s)")
        
        # 异步保存聊天历史，不阻塞响应
        async def save_history():
            try:
                await db_service.save_chat_history_async(
                    username=username,
                    question=request.question,
                    answer=answer,
                    sources=response["sources"],
                    is_real_time=False
                )
            except Exception as e:
                logger.error(f"异步保存聊天历史失败: {str(e)}")
        
        asyncio.create_task(save_history())
        
        process_time = time.time() - start_time
        logger.info(f"成功生成回答 (总耗时: {process_time:.3f}s)")
        
        # 返回响应，添加处理时间信息
        result = {**response, "from_cache": False, "process_time": process_time}
        return JSONResponse(content=result, headers=rate_limit_result["headers"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理请求时发生错误: {str(e)}")



@app.post("/logout")
async def logout(
    authorization: Optional[str] = Header(None),
    username: str = Depends(verify_user_session)
):
    """
    用户登出端点
    """
    try:
        # 执行登出操作
        result = await auth_logout(authorization)
        
        # 异步清除用户相关缓存
        async def clear_user_cache():
            try:
                # 清除用户聊天历史缓存
                for limit in [20, 50, 100]:
                    for offset in [0, 50, 100]:
                        cache_key = f"history:{username}:{limit}:{offset}"
                        await cache_service.delete(cache_key)
                logger.info(f"用户缓存已清除 - {username}")
            except Exception as e:
                logger.error(f"清除用户缓存失败: {str(e)}")
        
        asyncio.create_task(clear_user_cache())
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登出失败: {str(e)}")
        raise HTTPException(status_code=500, detail="登出失败")

@app.get("/chat_history")
async def get_chat_history(
    username: str = Depends(verify_user_session),
    limit: int = 50,
    offset: int = 0
):
    """
    获取用户聊天历史
    """
    start_time = time.time()
    try:
        # 生成缓存键
        cache_key = f"history:{username}:{limit}:{offset}"
        
        # 尝试从缓存获取
        cached_history = await cache_service.get(cache_key)
        if cached_history:
            logger.info(f"聊天历史缓存命中 - 用户: {username}")
            return JSONResponse(
                content={**cached_history, "from_cache": True, "process_time": time.time() - start_time}
            )
        
        # 异步获取聊天历史
        history = await run_in_threadpool(db_service.get_user_chat_history, username, limit)
        
        result = {
            "chat_history": history,
            "total": len(history)
        }
        
        # 缓存聊天历史（较短的TTL，因为历史可能会经常更新）
        await cache_service.set(cache_key, result, expire_seconds=180)  # 3分钟
        
        return JSONResponse(
            content={**result, "from_cache": False, "process_time": time.time() - start_time}
        )
    except Exception as e:
        logger.error(f"获取聊天历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取聊天历史失败")

@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    start_time = time.time()
    try:
        # 对于本地JSON存储，我们认为数据库总是可用的
        db_connected = True
        
        # 添加缓存和限流统计
        cache_stats = await cache_service.get_stats()
        rate_limit_stats = await rate_limiter.get_stats()
        
        # 获取请求统计信息
        async with request_counter_lock:
            current_stats = request_counter.copy()
        
        # 计算成功率
        success_rate = current_stats["total"] > 0 \
            and current_stats["success"] / current_stats["total"] \
            or 0
        
        # 计算缓存命中率
        cache_hit_rate = current_stats["total"] > 0 \
            and current_stats["cache_hits"] / current_stats["total"] \
            or 0
        
        return {
            "status": "healthy",
            "database_connected": db_connected,
            "llm_api_configured": is_api_configured(),
            "services": {
                "cache": cache_stats,
                "rate_limit": rate_limit_stats
            },
            "metrics": {
                "total_requests": current_stats["total"],
                "success_requests": current_stats["success"],
                "error_requests": current_stats["error"],
                "cache_hits": current_stats["cache_hits"],
                "vector_searches": current_stats["vector_searches"],
                "success_rate": success_rate,
                "cache_hit_rate": cache_hit_rate
            },
            "timestamp": datetime.now().isoformat(),
            "process_time": time.time() - start_time
        }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/stats/cache")
async def get_cache_stats():
    """
    获取缓存统计信息
    """
    stats = await cache_service.get_stats()
    return {
        "timestamp": datetime.now().isoformat(),
        "stats": stats
    }

@app.get("/stats/rate_limit")
async def get_rate_limit_stats():
    """
    获取速率限制统计信息
    """
    stats = await rate_limiter.get_stats()
    return {
        "timestamp": datetime.now().isoformat(),
        "stats": stats
    }

@app.get("/stats/performance")
async def get_performance_stats():
    """
    获取系统性能统计信息
    """
    async with request_counter_lock:
        current_stats = request_counter.copy()
    
    # 计算成功率和缓存命中率
    success_rate = current_stats["total"] > 0 \
        and current_stats["success"] / current_stats["total"] \
        or 0
    
    cache_hit_rate = current_stats["total"] > 0 \
        and current_stats["cache_hits"] / current_stats["total"] \
        or 0
    
    return {
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "total_requests": current_stats["total"],
            "success_requests": current_stats["success"],
            "error_requests": current_stats["error"],
            "cache_hits": current_stats["cache_hits"],
            "vector_searches": current_stats["vector_searches"],
            "success_rate": success_rate,
            "cache_hit_rate": cache_hit_rate
        }
    }

@app.post("/admin/clear_cache")
async def clear_cache(username: str = Depends(verify_user_session)):
    """
    清空缓存（管理员功能）
    """
    try:
        # 检查是否为管理员
        user = await run_in_threadpool(db_service.get_user, username)
        if not user or user.get('role') != 'admin':
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 清空所有缓存
        await cache_service.clear()
        
        # 清空请求计数器
        async with request_counter_lock:
            request_counter.update({
                "cache_hits": 0,
                "vector_searches": 0
            })
        
        logger.info(f"管理员 {username} 清空了所有缓存")
        return {"message": "缓存已清空", "timestamp": datetime.now().isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清空缓存失败: {str(e)}")
        raise HTTPException(status_code=500, detail="操作失败")

@app.post("/admin/optimize")
async def optimize_services(username: str = Depends(verify_user_session)):
    """
    优化所有服务性能（管理员功能）
    """
    try:
        # 检查是否为管理员
        user = await run_in_threadpool(db_service.get_user, username)
        if not user or user.get('role') != 'admin':
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 清理过期缓存
        expired_count = await cache_service.cleanup_expired()
        
        # 优化向量数据库搜索（如果可用）
        vector_optimized = False
        try:
            if 'vector_db' in globals() and hasattr(vector_db, 'optimize_search'):
                await run_in_threadpool(vector_db.optimize_search)
                vector_optimized = True
        except Exception as e:
            logger.warning(f"向量数据库优化失败: {str(e)}")
        
        logger.info(f"管理员 {username} 执行了服务优化")
        return {
            "message": "服务优化完成",
            "details": {
                "expired_cache_cleaned": expired_count,
                "vector_db_optimized": vector_optimized
            },
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"优化服务失败: {str(e)}")
        raise HTTPException(status_code=500, detail="操作失败")

@app.post("/register")
async def register(request: Request):
    """
    用户注册端点
    """
    try:
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        email = data.get("email", "")
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="用户名和密码不能为空")
        
        # 检查用户是否已存在
        existing_user = db_service.get_user(username)
        if existing_user:
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 创建新用户
        user_created = db_service.create_user(
            username=username,
            password=password,
            role="user"
        )
        
        if user_created:
            logger.info(f"用户注册成功: {username}")
            return {"message": "注册成功", "username": username}
        else:
            raise HTTPException(status_code=500, detail="用户创建失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")

# 定期优化任务
async def start_optimization_task():
    """
    启动定期优化任务
    """
    while True:
        try:
            logger.info("开始定期服务优化...")
            
            # 清理过期缓存
            expired_count = await cache_service.cleanup_expired()
            logger.info(f"清理了 {expired_count} 个过期缓存项")
            
            # 优化向量数据库搜索（如果可用）
            try:
                if 'vector_db' in globals() and hasattr(vector_db, 'optimize_search'):
                    await run_in_threadpool(vector_db.optimize_search)
                    logger.info("向量数据库搜索优化完成")
            except Exception as e:
                logger.warning(f"向量数据库优化失败: {str(e)}")
            
            logger.info("定期服务优化完成")
        except Exception as e:
            logger.error(f"定期优化任务失败: {str(e)}")
        
        # 每15分钟执行一次优化
        await asyncio.sleep(900)

# 缓存预热任务
async def start_warmup_task():
    """
    启动缓存预热任务
    """
    # 常见问题
    common_questions = [
        "学校地址在哪里",
        "图书馆开放时间",
        "奖学金申请条件",
        "如何注册账号",
        "就业指导中心联系方式"
    ]
    
    try:
        logger.info("开始缓存预热...")
        for question in common_questions:
            try:
                # 预热向量搜索
                if 'vector_db' in globals() and hasattr(vector_db, 'search'):
                    await run_in_threadpool(vector_db.search, question, top_k=3)
                logger.info(f"预热完成: {question[:30]}...")
            except Exception as e:
                logger.warning(f"预热失败: {question[:30]}..., 错误: {str(e)}")
            await asyncio.sleep(0.5)
        logger.info("缓存预热完成")
    except Exception as e:
        logger.error(f"缓存预热任务失败: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """
    服务启动事件
    """
    logger.info("江西工业智能问答系统启动中...")
    
    # 立即执行一次缓存清理（不等定期任务）
    try:
        expired_count = await cache_service.cleanup_expired()
        logger.info(f"清理了 {expired_count} 个过期缓存项")
    except Exception as e:
        logger.warning(f"启动时清理缓存失败: {str(e)}")
    
    # 启动定期优化任务
    asyncio.create_task(start_optimization_task())
    
    # 启动缓存预热任务
    asyncio.create_task(start_warmup_task())
    
    logger.info("江西工业智能问答系统启动完成，优化任务已启动")

@app.get("/")
async def root():
    """
    根路径，返回前端页面
    """
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"读取index.html失败: {str(e)}")
        return HTMLResponse(content="<h1>页面加载失败</h1><p>请稍后再试</p>")

@app.get("/login")
async def login_page():
    """
    登录页面
    """
    try:
        with open("login.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.warning(f"读取login.html失败: {str(e)}")
        # 如果login.html不存在，重定向到根路径
        return root()

@app.on_event("shutdown")
async def shutdown_event():
    """
    服务关闭事件
    """
    logger.info("江西工业智能问答系统正在关闭...")
    
    # 保存所有数据
    try:
        if hasattr(db_service, 'save_data'):
            await run_in_threadpool(db_service.save_data)
            logger.info("所有数据已保存")
    except Exception as e:
        logger.error(f"关闭时保存数据失败: {str(e)}")
    
    logger.info("江西工业智能问答系统已关闭")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,
        workers=4,  # 启用多进程处理
        timeout_keep_alive=60,  # 增加超时时间
        access_log=True  # 启用访问日志
    )