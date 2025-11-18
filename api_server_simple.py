import os
import sys
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 导入我们的简化版向量数据库工具
from vector_db_utils_simple import get_vector_db_utils

# 定义API请求和响应模型
class AskRequest(BaseModel):
    question: str
    chat_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)

class AskResponse(BaseModel):
    answer: str
    sources: List[str]
    is_real_time: bool

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

# 请求计数器
request_counter = {
    "total": 0,
    "success": 0,
    "error": 0
}
request_counter_lock = threading.Lock()

# 初始化FastAPI应用
app = FastAPI(
    title="江西工业工程职业技术学院 AI 问答系统",
    description="轻量级智能问答系统API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# 配置CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
if "*" in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"]
)

# 请求跟踪中间件
@app.middleware("http")
async def request_tracker(request: Request, call_next):
    start_time = time.time()
    path = request.url.path
    
    # 跳过文档路径
    if path in ["/api/docs", "/api/redoc", "/api/openapi.json"]:
        response = await call_next(request)
        return response
    
    try:
        # 增加总请求数
        with request_counter_lock:
            request_counter["total"] += 1
        
        # 执行请求
        response = await call_next(request)
        
        # 增加成功请求数
        if response.status_code < 400:
            with request_counter_lock:
                request_counter["success"] += 1
        else:
            with request_counter_lock:
                request_counter["error"] += 1
        
        # 添加处理时间头
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    except Exception as e:
        # 增加错误请求数
        with request_counter_lock:
            request_counter["error"] += 1
        
        logger.error(f"请求处理异常: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "服务器内部错误"}
        )

# 初始化向量数据库工具
vector_db_utils = None
try:
    vector_db_utils = get_vector_db_utils()
    logger.info("向量数据库工具初始化完成")
except Exception as e:
    logger.error(f"向量数据库工具初始化失败: {str(e)}")

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查接口"""
    db_status = "initialized" if vector_db_utils and vector_db_utils.is_initialized() else "not initialized"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "db_status": db_status,
        "request_stats": request_counter
    }

# 简单的问答生成函数
def generate_simple_answer(question: str, context_docs: List[Dict[str, Any]]) -> str:
    """
    基于问题和检索到的文档生成简单回答
    """
    if not context_docs:
        return f"抱歉，我无法找到关于'{question}'的相关信息。请尝试使用其他关键词或联系学校相关部门获取帮助。"
    
    # 简单地拼接文档内容作为回答
    context_texts = [doc["content"] for doc in context_docs[:3]]  # 只使用前3个文档
    context_summary = "\n".join(context_texts)
    
    # 生成回答
    answer = f"根据我找到的信息：\n\n{context_summary}\n\n希望以上信息对您有所帮助！"
    return answer

# 问答端点
@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """
    智能问答接口
    """
    try:
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="问题不能为空")
        
        logger.info(f"收到问题: {question}")
        
        # 从向量数据库搜索相关文档
        search_results = []
        if vector_db_utils and vector_db_utils.is_initialized():
            search_results = vector_db_utils.search_similar_documents(question, top_k=5)
            logger.info(f"向量数据库搜索到 {len(search_results)} 个相关文档")
        
        # 生成回答
        answer = generate_simple_answer(question, search_results)
        
        # 提取来源信息
        sources = [f"文档 {i+1}" for i in range(len(search_results[:3]))]
        
        return AskResponse(
            answer=answer,
            sources=sources,
            is_real_time=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理问答请求时出错: {str(e)}")
        raise HTTPException(status_code=500, detail="处理请求时发生错误")

# 获取请求统计信息的端点
@app.get("/stats")
async def get_stats():
    """获取请求统计信息"""
    return request_counter

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "江西工业工程职业技术学院 AI 问答系统 API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/health"
    }

# 启动时的初始化
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的初始化操作"""
    logger.info("应用启动中...")
    logger.info(f"CORS 允许的源: {ALLOWED_ORIGINS}")
    logger.info("应用启动完成")

# 创建Mangum处理器
try:
    import mangum
    handler = mangum.Mangum(app)
except ImportError:
    logger.warning("mangum未安装，跳过AWS Lambda处理器配置")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )