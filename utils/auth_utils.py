import os
import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from fastapi import HTTPException, Header

logger = logging.getLogger(__name__)

# 导入数据库服务
from .db_service import db_service

class AuthUtils:
    """
    认证工具类，用于处理API密钥验证和用户认证
    """
    
    def __init__(self):
        """
        初始化认证工具
        """
        # 从环境变量或默认值初始化
        self.api_key_secret = os.environ.get("API_KEY_SECRET", "your-secret-key-change-in-production")
        self.api_keys_storage = {}
        self._load_api_keys()
    
    def _load_api_keys(self):
        """
        加载API密钥配置
        这里使用硬编码的测试密钥，实际生产环境中应从安全的存储中加载
        """
        # 设置默认的测试API密钥（实际应用中应该从环境变量或数据库加载）
        default_key = os.environ.get("DEFAULT_API_KEY", "test_key_2024")
        
        # 添加默认API密钥
        self.api_keys_storage[default_key] = {
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(days=365),  # 有效期一年
            "description": "Default test API key",
            "usage_count": 0
        }
        
        logger.info("API密钥配置加载完成")
    
    def generate_api_key(self, description: str = "", expiration_days: int = 365) -> Dict[str, str]:
        """
        生成新的API密钥
        
        Args:
            description: 密钥描述
            expiration_days: 有效期（天）
            
        Returns:
            包含新密钥和信息的字典
        """
        try:
            # 生成32字节的随机密钥
            key = secrets.token_urlsafe(32)
            
            # 计算密钥的哈希值用于存储（实际生产环境中应使用更安全的方法）
            key_hash = hashlib.sha256(f"{key}{self.api_key_secret}".encode()).hexdigest()
            
            # 保存密钥信息
            expires_at = datetime.now() + timedelta(days=expiration_days)
            self.api_keys_storage[key] = {
                "created_at": datetime.now(),
                "expires_at": expires_at,
                "description": description,
                "usage_count": 0,
                "key_hash": key_hash
            }
            
            logger.info(f"新API密钥生成: {description}")
            
            return {
                "api_key": key,
                "expires_at": expires_at.isoformat(),
                "description": description
            }
        except Exception as e:
            logger.error(f"生成API密钥失败: {str(e)}")
            raise
    
    def verify_api_key(self, api_key: str) -> Dict[str, any]:
        
        """
        验证API密钥
        
        Args:
            api_key: 待验证的API密钥
            
        Returns:
            包含验证结果的字典
        """
        try:
            # 检查密钥是否存在
            if api_key not in self.api_keys_storage:
                logger.warning(f"未知API密钥验证尝试")
                return {
                    "valid": False,
                    "message": "API密钥无效",
                    "expiration_date": None
                }
            
            key_info = self.api_keys_storage[api_key]
            
            # 检查密钥是否过期
            if datetime.now() > key_info["expires_at"]:
                logger.warning(f"过期API密钥验证尝试: {api_key[:8]}...")
                return {
                    "valid": False,
                    "message": "API密钥已过期",
                    "expiration_date": key_info["expires_at"]
                }
            
            # 更新使用计数
            key_info["usage_count"] += 1
            logger.info(f"API密钥验证成功: {api_key[:8]}..., 使用次数: {key_info['usage_count']}")
            
            return {
                "valid": True,
                "message": "API密钥有效",
                "expiration_date": key_info["expires_at"],
                "usage_count": key_info["usage_count"],
                "description": key_info["description"]
            }
        except Exception as e:
            logger.error(f"验证API密钥失败: {str(e)}")
            return {
                "valid": False,
                "message": f"验证过程出错: {str(e)}",
                "expiration_date": None
            }
    
    def revoke_api_key(self, api_key: str) -> bool:
        """
        撤销API密钥
        
        Args:
            api_key: 要撤销的API密钥
            
        Returns:
            是否成功撤销
        """
        try:
            if api_key in self.api_keys_storage:
                del self.api_keys_storage[api_key]
                logger.info(f"API密钥已撤销: {api_key[:8]}...")
                return True
            return False
        except Exception as e:
            logger.error(f"撤销API密钥失败: {str(e)}")
            return False
    
    def get_api_key_info(self, api_key: str) -> Optional[Dict[str, any]]:
        """
        获取API密钥信息
        
        Args:
            api_key: API密钥
            
        Returns:
            密钥信息字典，如果不存在则返回None
        """
        return self.api_keys_storage.get(api_key)
    
    def list_api_keys(self, show_usage: bool = False) -> List[Dict[str, any]]:
        """
        列出所有API密钥信息
        
        Args:
            show_usage: 是否显示使用统计
            
        Returns:
            API密钥信息列表
        """
        keys_info = []
        
        for key, info in self.api_keys_storage.items():
            key_info = {
                "key_prefix": key[:8] + "...",
                "created_at": info["created_at"].isoformat(),
                "expires_at": info["expires_at"].isoformat(),
                "description": info["description"],
                "is_expired": datetime.now() > info["expires_at"]
            }
            
            if show_usage:
                key_info["usage_count"] = info.get("usage_count", 0)
            
            keys_info.append(key_info)
        
        return keys_info
    
    def check_rate_limit(self, api_key: str, limit: int = 100, window_hours: int = 24) -> bool:
        """
        检查API调用频率限制
        
        Args:
            api_key: API密钥
            limit: 时间窗口内的最大调用次数
            window_hours: 时间窗口大小（小时）
            
        Returns:
            是否允许调用
        """
        try:
            key_info = self.api_keys_storage.get(api_key)
            if not key_info:
                return False
            
            usage_count = key_info.get("usage_count", 0)
            
            # 简单的基于计数的限制（实际应用中应使用更精确的滑动窗口方法）
            if usage_count > limit:
                logger.warning(f"API密钥超出限制: {api_key[:8]}..., 当前: {usage_count}, 限制: {limit}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"检查速率限制失败: {str(e)}")
            return False

# 数据库服务已在各函数中直接使用，不需要全局变量

# 创建全局认证工具实例
_auth_utils = AuthUtils()

# 用户认证相关函数
async def login(username: str, password: str) -> Dict[str, str]:
    """
    用户登录函数
    
    Args:
        username: 用户名
        password: 密码
        sessions: 会话字典
    
    Returns:
        包含访问令牌的字典
    """
    try:
        # 从数据库获取用户信息
        user = db_service.get_user(username)
        
        if not user:
            logger.warning(f"登录失败: 用户不存在 - {username}")
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 验证密码（这里使用明文密码比较，生产环境应使用哈希）
        if user["password"] != password:
            logger.warning(f"登录失败: 密码错误 - {username}")
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 创建会话
        session_token = db_service.create_session(username)
        
        if not session_token:
            raise HTTPException(status_code=500, detail="创建会话失败")
        
        logger.info(f"用户登录成功: {username}")
        
        return {
            "access_token": session_token,
            "token_type": "bearer",
            "username": username,
            "role": user.get("role", "user")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录过程出错: {str(e)}")
        raise HTTPException(status_code=500, detail="登录过程出错")

async def logout(authorization: Optional[str] = None) -> Dict[str, str]:
    """
    用户登出函数
    
    Args:
        authorization: Authorization头
        sessions: 会话字典
    
    Returns:
        登出结果字典
    """
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="无效的认证令牌")
        
        # 提取令牌
        session_token = authorization.split(" ")[1]
        
        # 从数据库删除会话
        success = db_service.delete_session(session_token)
        
        if success:
            logger.info("用户登出成功")
            return {"message": "登出成功"}
        else:
            logger.warning(f"登出失败: 会话不存在 - {session_token[:8]}...")
            raise HTTPException(status_code=401, detail="无效的会话令牌")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登出过程出错: {str(e)}")
        raise HTTPException(status_code=500, detail="登出过程出错")

async def verify_user_session(authorization: Optional[str] = Header(None)) -> str:
    """
    验证用户会话
    
    Args:
        authorization: Authorization头
    
    Returns:
        用户名
    """
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="未提供认证令牌")
        
        # 提取令牌
        session_token = authorization.split(" ")[1]
        
        # 从数据库获取会话信息
        session = db_service.get_session(session_token)
        
        if not session:
            logger.warning(f"会话验证失败: 会话不存在 - {session_token[:8]}...")
            raise HTTPException(status_code=401, detail="无效或已过期的会话令牌")
        
        # 会话是否过期的检查已在db_service.get_session中完成
        
        logger.info(f"会话验证成功: {session['username']}")
        return session["username"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"会话验证过程出错: {str(e)}")
        raise HTTPException(status_code=500, detail="会话验证过程出错")

# API密钥验证函数
def verify_api_key(api_key: str) -> Dict[str, any]:
    return _auth_utils.verify_api_key(api_key)

# 确保api_server.py能正确导入
verify_user_session = verify_user_session