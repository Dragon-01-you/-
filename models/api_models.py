from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Message(BaseModel):
    """
    消息模型，用于表示用户或助手的消息
    """
    role: str = Field(..., description="消息角色：user或assistant")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="消息时间戳")

class QueryRequest(BaseModel):
    """
    查询请求模型
    """
    query: str = Field(..., description="用户查询内容")
    history: Optional[List[Message]] = Field(default_factory=list, description="历史对话记录")
    use_search: bool = Field(default=True, description="是否使用搜索增强")
    api_key: Optional[str] = Field(None, description="API密钥，用于权限验证")
    user_id: Optional[str] = Field(None, description="用户ID，用于会话管理")
    is_realtime: bool = Field(default=False, description="是否需要实时数据")

class SearchResult(BaseModel):
    """
    搜索结果模型
    """
    content: str = Field(..., description="搜索结果内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据，如来源、类型等")

class QueryResponse(BaseModel):
    """
    查询响应模型
    """
    response: str = Field(..., description="助手回复内容")
    search_results: Optional[List[SearchResult]] = Field(default=None, description="搜索结果列表")
    tokens_used: Optional[Dict[str, int]] = Field(default=None, description="使用的token数量统计")
    response_time: Optional[float] = Field(default=None, description="响应时间（秒）")
    success: bool = Field(default=True, description="是否成功")
    error: Optional[str] = Field(default=None, description="错误信息")

class VerifyKeyRequest(BaseModel):
    """
    API密钥验证请求模型
    """
    api_key: str = Field(..., description="待验证的API密钥")

class VerifyKeyResponse(BaseModel):
    """
    API密钥验证响应模型
    """
    valid: bool = Field(..., description="密钥是否有效")
    message: Optional[str] = Field(default=None, description="验证结果消息")
    expiration_date: Optional[datetime] = Field(default=None, description="密钥过期日期")

class HealthCheckResponse(BaseModel):
    """
    健康检查响应模型
    """
    status: str = Field(default="ok", description="服务状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    components: Dict[str, str] = Field(default_factory=dict, description="各组件状态")

class ChatRequest(BaseModel):
    """
    聊天请求模型（扩展版）
    """
    messages: List[Message] = Field(..., description="消息列表")
    temperature: float = Field(default=0.7, description="生成温度参数")
    max_tokens: int = Field(default=1024, description="最大生成token数")
    use_search: bool = Field(default=True, description="是否使用搜索增强")
    api_key: Optional[str] = Field(None, description="API密钥")
    is_realtime: bool = Field(default=False, description="是否需要实时数据")

class BatchQueryItem(BaseModel):
    """
    批量查询项模型
    """
    id: str = Field(..., description="查询ID")
    query: str = Field(..., description="查询内容")
    use_search: bool = Field(default=True, description="是否使用搜索增强")
    is_realtime: bool = Field(default=False, description="是否需要实时数据")

class BatchQueryRequest(BaseModel):
    """
    批量查询请求模型
    """
    queries: List[BatchQueryItem] = Field(..., description="批量查询列表")
    api_key: Optional[str] = Field(None, description="API密钥")

class BatchQueryResponse(BaseModel):
    """
    批量查询响应模型
    """
    results: List[Dict[str, Any]] = Field(..., description="查询结果列表")
    total_processed: int = Field(..., description="处理的总查询数")
    total_succeeded: int = Field(..., description="成功的查询数")
    total_failed: int = Field(..., description="失败的查询数")