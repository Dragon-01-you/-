from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import mangum

# 创建FastAPI应用实例
app = FastAPI(title="江西工业智能问答API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 根路径
@app.get("/")
async def root():
    return {"message": "江西工业智能问答API服务正在运行"}

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 简单的查询端点
@app.get("/api/query")
async def query(request: Request):
    query_text = request.query_params.get("q", "")
    return {
        "query": query_text,
        "response": "这是一个简化版API响应",
        "status": "success"
    }

# 创建Mangum处理器
handler = mangum.Mangum(app)