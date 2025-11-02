import os
import sys
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading
import random
import hashlib

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

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

# 简化版向量数据库工具（内联实现，减少文件依赖）
class SimpleVectorDB:
    """简化的向量数据库实现，专为资源受限环境设计"""
    
    def __init__(self):
        self.dimension = 128  # 降低维度以减少内存使用
        self.documents = []
        self.embeddings = []
        self.metadata = []
        self._initialized = False
    
    def _generate_embedding(self, text: str) -> List[float]:
        """生成简单的文本嵌入向量"""
        # 使用哈希值作为随机种子
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % 1000000
        random.seed(seed)
        # 生成低维随机向量
        return [random.uniform(-1, 1) for _ in range(self.dimension)]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
        norm1 = sum(v * v for v in vec1) ** 0.5
        norm2 = sum(v * v for v in vec2) ** 0.5
        
        if norm1 > 0 and norm2 > 0:
            return dot_product / (norm1 * norm2)
        return 0.0
    
    def initialize_with_sample_data(self):
        """初始化一些示例数据"""
        try:
            # 预定义的常见问题和答案
            sample_data = [
                {"question": "学校地址在哪里", "answer": "江西工业工程职业技术学院位于江西省萍乡市安源区建设东路268号"},
                {"question": "图书馆开放时间", "answer": "图书馆开放时间为周一至周五 8:00-22:00，周末 9:00-20:00"},
                {"question": "奖学金申请条件", "answer": "奖学金申请条件包括：1. 学习成绩优秀；2. 遵守校规校纪；3. 积极参与课外活动；4. 家庭经济困难学生优先考虑"},
                {"question": "如何注册账号", "answer": "新生可通过学校官网的新生注册系统，使用录取通知书上的学号和初始密码进行注册"},
                {"question": "就业指导中心联系方式", "answer": "就业指导中心联系电话：0799-6351234，办公地点：行政楼2楼"},
                {"question": "宿舍管理规定", "answer": "宿舍开放时间为6:00-23:00，禁止使用大功率电器，保持宿舍卫生整洁"},
                {"question": "食堂就餐时间", "answer": "第一食堂：早餐6:30-8:30，午餐11:00-13:00，晚餐17:00-19:00"},
                {"question": "学生证办理流程", "answer": "新生入学后由辅导员统一收集照片和信息，一周内发放学生证"},
                {"question": "选课系统开放时间", "answer": "每学期开学前两周开放选课系统，请关注教务处通知"},
                {"question": "校园卡服务中心", "answer": "校园卡服务中心位于图书馆一楼大厅，提供办卡、充值、挂失等服务"}
            ]
            
            for i, item in enumerate(sample_data):
                # 存储问题和答案
                self.documents.append(f"问题: {item['question']} 答案: {item['answer']}")
                # 生成嵌入向量
                self.embeddings.append(self._generate_embedding(item['question']))
                # 添加元数据
                self.metadata.append({"id": i, "category": "common_question"})
            
            self._initialized = True
            logger.info(f"向量数据库初始化完成，加载了 {len(sample_data)} 条示例数据")
        except Exception as e:
            logger.error(f"初始化示例数据失败: {str(e)}")
    
    def search_similar(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        if not self._initialized or not self.documents:
            return []
        
        # 生成查询向量
        query_embedding = self._generate_embedding(query)
        
        # 计算相似度
        similarities = []
        for i, doc_embedding in enumerate(self.embeddings):
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append((i, similarity))
        
        # 按相似度排序并返回结果
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = []
        
        for i, score in similarities[:top_k]:
            if score > 0.3:  # 设置最低相似度阈值
                results.append({
                    "content": self.documents[i],
                    "metadata": self.metadata[i],
                    "score": score
                })
        
        return results
    
    def is_initialized(self) -> bool:
        """检查是否初始化完成"""
        return self._initialized

# 初始化向量数据库
simple_vector_db = SimpleVectorDB()
simple_vector_db.initialize_with_sample_data()

# 定义API请求和响应模型
class AskRequest(BaseModel):
    question: str
    chat_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)

class AskResponse(BaseModel):
    answer: str
    sources: List[str]
    is_real_time: bool

# 请求计数器
request_counter = {
    "total": 0,
    "success": 0,
    "error": 0
}
request_counter_lock = threading.Lock()

# 查询缓存，减少重复计算
query_cache = {}
cache_lock = threading.RLock()
MAX_CACHE_SIZE = 50  # 限制缓存大小

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

# 简单的问答生成函数
def generate_answer(question: str, search_results: List[Dict[str, Any]]) -> str:
    """基于问题和检索到的文档生成回答"""
    if not search_results:
        return f"抱歉，我无法找到关于'{question}'的相关信息。请尝试使用其他关键词或联系学校相关部门获取帮助。"
    
    # 从检索结果中提取答案部分
    answers = []
    for result in search_results:
        content = result["content"]
        if "答案:" in content:
            # 提取答案部分
            answer_part = content.split("答案:", 1)[1].strip()
            answers.append(answer_part)
        else:
            # 如果没有明确的答案格式，使用整个内容
            answers.append(content)
    
    # 生成最终回答
    if answers:
        return f"{answers[0]}\n\n希望以上信息对您有所帮助！"
    else:
        return "抱歉，暂时无法为您提供相关信息。"

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查接口"""
    db_status = "initialized" if simple_vector_db.is_initialized() else "not initialized"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "db_status": db_status,
        "request_stats": request_counter
    }

# 问答端点
@app.post("/api/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """
    智能问答接口 - 专为PythonAnywhere优化的轻量级版本
    """
    try:
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="问题不能为空")
        
        logger.info(f"收到问题: {question}")
        
        # 检查缓存
        cache_key = f"search:{question}"
        with cache_lock:
            if cache_key in query_cache:
                logger.info(f"缓存命中: {question}")
                search_results = query_cache[cache_key]
            else:
                # 从向量数据库搜索相关文档
                search_results = simple_vector_db.search_similar(question, top_k=3)
                logger.info(f"向量数据库搜索到 {len(search_results)} 个相关文档")
                
                # 更新缓存
                query_cache[cache_key] = search_results
                # 如果缓存过大，删除最旧的项
                if len(query_cache) > MAX_CACHE_SIZE:
                    oldest_key = next(iter(query_cache.keys()))
                    del query_cache[oldest_key]
        
        # 生成回答
        answer = generate_answer(question, search_results)
        
        # 提取来源信息
        sources = [f"文档 {i+1}" for i in range(len(search_results))]
        
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

# 为PythonAnywhere创建handler
handler = app

# 如果需要AWS Lambda支持，可以取消下面的注释
# try:
#     import mangum
#     handler = mangum.Mangum(app)
# except ImportError:
#     logger.warning("mangum未安装，使用默认handler")
#     handler = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server_pythonanywhere:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )