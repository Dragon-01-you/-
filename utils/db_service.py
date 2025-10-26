import os
import logging
import json
import uuid
import asyncio
import threading
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DatabaseService:
    """
    高性能本地JSON文件数据库服务类，支持高并发操作和异步访问
    无需外部MongoDB，使用本地文件存储所有数据，添加线程安全保护
    """
    
    def __init__(self):
        """
        初始化数据库服务
        """
        # 本地文件存储路径
        self.storage_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # 数据集合
        self.users_collection = {}
        self.sessions_collection = {}
        self.chat_history_collection = []
        self.vector_db_collection = []
        
        # 线程安全锁
        self._users_lock = threading.RLock()  # 可重入锁用于用户数据
        self._sessions_lock = threading.RLock()  # 可重入锁用于会话数据
        self._chat_history_lock = threading.RLock()  # 可重入锁用于聊天历史
        self._vector_db_lock = threading.RLock()  # 可重入锁用于向量数据库元数据
        self._file_lock = threading.RLock()  # 可重入锁用于文件IO操作
        
        # 性能统计指标
        self._operation_count = {
            "read": 0,
            "write": 0,
            "error": 0
        }
        self._last_write_time = time.time()
        self._pending_writes = False  # 标记是否有待保存的写入操作
        
        # 批量写入配置
        self._max_batch_size = 100  # 最大批量保存的聊天记录数
        self._auto_save_interval = 5  # 自动保存间隔（秒）
        
        # 加载本地数据
        self._load_local_data()
        
        # 初始化默认用户（如果没有用户数据）
        if not self.users_collection:
            self._init_default_users()
    
    def _load_local_data(self):
        """
        从本地JSON文件加载数据
        """
        logger.info("📁 正在加载本地数据文件...")
        
        # 加载用户数据
        users_file = os.path.join(self.storage_dir, "users.json")
        try:
            if os.path.exists(users_file):
                with open(users_file, "r", encoding="utf-8") as f:
                    self.users_collection = json.load(f)
                logger.info(f"✅ 已加载用户数据，共 {len(self.users_collection)} 条记录")
            else:
                logger.info("⚠️ 用户数据文件不存在，初始化为空")
        except Exception as e:
            logger.error(f"❌ 加载用户数据失败: {str(e)}")
            self.users_collection = {}
        
        # 加载会话数据
        sessions_file = os.path.join(self.storage_dir, "sessions.json")
        try:
            if os.path.exists(sessions_file):
                with open(sessions_file, "r", encoding="utf-8") as f:
                    self.sessions_collection = json.load(f)
                logger.info(f"✅ 已加载会话数据，共 {len(self.sessions_collection)} 条记录")
            else:
                logger.info("⚠️ 会话数据文件不存在，初始化为空")
        except Exception as e:
            logger.error(f"❌ 加载会话数据失败: {str(e)}")
            self.sessions_collection = {}
        
        # 加载聊天历史数据
        chat_history_file = os.path.join(self.storage_dir, "chat_history.json")
        try:
            if os.path.exists(chat_history_file):
                with open(chat_history_file, "r", encoding="utf-8") as f:
                    self.chat_history_collection = json.load(f)
                logger.info(f"✅ 已加载聊天历史数据，共 {len(self.chat_history_collection)} 条记录")
            else:
                logger.info("⚠️ 聊天历史数据文件不存在，初始化为空")
        except Exception as e:
            logger.error(f"❌ 加载聊天历史数据失败: {str(e)}")
            self.chat_history_collection = []
        
        # 加载向量数据库元数据
        vector_db_file = os.path.join(self.storage_dir, "vector_db_metadata.json")
        try:
            if os.path.exists(vector_db_file):
                with open(vector_db_file, "r", encoding="utf-8") as f:
                    self.vector_db_collection = json.load(f)
                logger.info(f"✅ 已加载向量数据库元数据")
            else:
                logger.info("⚠️ 向量数据库元数据文件不存在，初始化为空")
        except Exception as e:
            logger.error(f"❌ 加载向量数据库元数据失败: {str(e)}")
            self.vector_db_collection = []
    
    def _save_chat_history_to_file(self):
        """
        仅保存聊天历史到文件（线程安全版本）
        用于异步操作和增量保存
        """
        try:
            with self._file_lock:
                chat_history_file = os.path.join(self.storage_dir, "chat_history.json")
                
                # 先获取数据副本，避免长时间持有锁
                with self._chat_history_lock:
                    # 保存前进行数据清理，只保留最近的聊天记录
                    if len(self.chat_history_collection) > 100000:
                        self.chat_history_collection = self.chat_history_collection[-100000:]
                        logger.info(f"💬 聊天历史过多，已清理至最近100000条")
                    
                    # 创建数据副本
                    history_copy = self.chat_history_collection.copy()
                
                # 写入文件（不再持有数据锁）
                with open(chat_history_file, "w", encoding="utf-8") as f:
                    json.dump(history_copy, f, ensure_ascii=False, indent=2)
                
                self._last_write_time = time.time()
                self._pending_writes = False
                self._operation_count["write"] += 1
                
                logger.debug(f"💾 聊天历史保存到文件成功，共 {len(history_copy)} 条记录")
        except Exception as e:
            self._operation_count["error"] += 1
            logger.error(f"❌ 保存聊天历史到文件失败: {str(e)}")
            
    def _save_local_data(self):
        """
        线程安全保存所有数据到本地JSON文件
        """
        logger.debug("💾 正在保存所有数据到本地文件...")
        
        try:
            with self._file_lock:
                # 获取各集合的副本，最小化锁持有时间
                with self._users_lock:
                    users_copy = self.users_collection.copy()
                
                with self._sessions_lock:
                    sessions_copy = self.sessions_collection.copy()
                
                with self._chat_history_lock:
                    history_copy = self.chat_history_collection.copy()
                
                with self._vector_db_lock:
                    vector_db_copy = self.vector_db_collection.copy()
                
                # 保存用户数据
                users_file = os.path.join(self.storage_dir, "users.json")
                with open(users_file, "w", encoding="utf-8") as f:
                    json.dump(users_copy, f, ensure_ascii=False, indent=2, default=str)
                
                # 保存会话数据
                sessions_file = os.path.join(self.storage_dir, "sessions.json")
                with open(sessions_file, "w", encoding="utf-8") as f:
                    json.dump(sessions_copy, f, ensure_ascii=False, indent=2, default=str)
                
                # 保存聊天历史数据
                chat_history_file = os.path.join(self.storage_dir, "chat_history.json")
                with open(chat_history_file, "w", encoding="utf-8") as f:
                    json.dump(history_copy, f, ensure_ascii=False, indent=2, default=str)
                
                # 保存向量数据库元数据
                vector_db_file = os.path.join(self.storage_dir, "vector_db_metadata.json")
                with open(vector_db_file, "w", encoding="utf-8") as f:
                    json.dump(vector_db_copy, f, ensure_ascii=False, indent=2, default=str)
                
                self._last_write_time = time.time()
                self._pending_writes = False
                self._operation_count["write"] += 1
                
                logger.debug("✅ 数据保存成功")
        except Exception as e:
            self._operation_count["error"] += 1
            logger.error(f"❌ 保存数据到本地文件失败: {str(e)}")
    
    def is_connected(self):
        """
        检查数据库连接状态（本地模式始终返回True）
        """
        return True  # 本地存储模式始终返回连接成功
    
    def _init_default_users(self):
        """
        初始化默认用户数据
        """
        try:
            # 创建默认测试用户
            default_users = {
                "student1": {"username": "student1", "password": "password123", "role": "student"},
                "teacher1": {"username": "teacher1", "password": "teacher123", "role": "teacher"},
                "admin": {"username": "admin", "password": "admin123", "role": "admin"}
            }
            
            # 合并到用户集合
            self.users_collection.update(default_users)
            
            # 保存到文件
            self._save_local_data()
            
            logger.info("✅ 默认用户数据初始化完成")
            logger.info("📝 可用账号：")
            logger.info("  - 学生账号: student1/password123")
            logger.info("  - 教师账号: teacher1/teacher123")
            logger.info("  - 管理员账号: admin/admin123")
        except Exception as e:
            logger.error(f"❌ 初始化默认用户失败: {str(e)}")
    
    # 用户相关操作
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        同步根据用户名获取用户信息（线程安全）
        """
        try:
            with self._users_lock:
                user = self.users_collection.get(username)
                self._operation_count["read"] += 1
                logger.debug(f"👤 获取用户信息: {username} - {'找到' if user else '未找到'}")
                return user.copy() if user else None  # 返回副本避免外部修改
        except Exception as e:
            self._operation_count["error"] += 1
            logger.error(f"❌ 获取用户信息失败: {str(e)}")
            return None
    
    async def get_user_async(self, username: str) -> Optional[Dict[str, Any]]:
        """
        异步根据用户名获取用户信息
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self.get_user, username
        )
    
    def create_user(self, username: str, password: str, role: str = "student") -> bool:
        """
        同步创建新用户（线程安全）
        """
        try:
            with self._users_lock:
                # 检查用户是否已存在
                if username in self.users_collection:
                    logger.warning(f"⚠️ 用户已存在: {username}")
                    return False
                
                # 创建用户数据
                user_data = {
                    "username": username,
                    "password": password,  # 注意：生产环境应该哈希密码
                    "role": role,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                # 添加到用户集合
                self.users_collection[username] = user_data
                
                # 标记有待保存的写入
                self._pending_writes = True
            
            # 保存到文件（在锁外进行IO操作）
            self._save_local_data()
            
            logger.info(f"✅ 创建用户成功: {username}")
            return True
        except Exception as e:
            self._operation_count["error"] += 1
            logger.error(f"❌ 创建用户失败: {str(e)}")
            return False
    
    async def create_user_async(self, username: str, password: str, role: str = "student") -> bool:
        """
        异步创建新用户
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self.create_user, username, password, role
        )
    
    # 会话相关操作
    def create_session(self, username: str) -> str:
        """
        同步创建用户会话并返回会话令牌（线程安全）
        """
        try:
            # 生成会话令牌
            session_token = str(uuid.uuid4())
            
            # 计算过期时间（24小时后）
            expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
            
            # 创建会话数据
            session_data = {
                "session_token": session_token,
                "username": username,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at
            }
            
            with self._sessions_lock:
                # 添加到会话集合
                self.sessions_collection[session_token] = session_data
                
                # 标记有待保存的写入
                self._pending_writes = True
            
            # 保存到文件（在锁外进行IO操作）
            self._save_local_data()
            
            logger.info(f"✅ 创建会话成功: {username} - {session_token[:8]}...")
            return session_token
        except Exception as e:
            self._operation_count["error"] += 1
            logger.error(f"❌ 创建会话失败: {str(e)}")
            return ""
    
    async def create_session_async(self, username: str) -> str:
        """
        异步创建用户会话并返回会话令牌
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self.create_session, username
        )
    
    def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        同步根据会话令牌获取会话信息（线程安全）
        """
        try:
            with self._sessions_lock:
                session = self.sessions_collection.get(session_token)
                self._operation_count["read"] += 1
                
                if session and "expires_at" in session:
                    # 检查会话是否过期
                    try:
                        expires_at = datetime.fromisoformat(session["expires_at"])
                        if datetime.utcnow() > expires_at:
                            # 会话已过期，删除它
                            del self.sessions_collection[session_token]
                            self._pending_writes = True
                            
                            # 在锁外保存，避免长时间持有锁
                            session_to_delete = session_token
                            
                            # 复制有效会话数据（如果有）
                            result = None
                        else:
                            # 返回副本避免外部修改
                            result = session.copy()
                    except (ValueError, TypeError):
                        # 如果时间格式错误，视为有效会话
                        result = session.copy() if session else None
                else:
                    result = session.copy() if session else None
            
            # 如果有过期会话需要删除，保存更改
            if 'session_to_delete' in locals():
                self._save_local_data()
                logger.info(f"⏰ 会话已过期并删除: {session_to_delete[:8]}...")
            
            return result
        except Exception as e:
            self._operation_count["error"] += 1
            logger.error(f"❌ 获取会话信息失败: {str(e)}")
            return None
    
    async def get_session_async(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        异步根据会话令牌获取会话信息
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self.get_session, session_token
        )
    
    def delete_session(self, session_token: str) -> bool:
        """
        同步删除会话（线程安全）
        """
        try:
            with self._sessions_lock:
                if session_token in self.sessions_collection:
                    del self.sessions_collection[session_token]
                    self._pending_writes = True
                    
                    # 在锁外保存，避免长时间持有锁
                    self._save_local_data()
                    
                    logger.info(f"❌ 删除会话成功: {session_token[:8]}...")
                    return True
                logger.warning(f"⚠️ 会话不存在: {session_token[:8]}...")
                return False
        except Exception as e:
            self._operation_count["error"] += 1
            logger.error(f"❌ 删除会话失败: {str(e)}")
            return False
    
    async def delete_session_async(self, session_token: str) -> bool:
        """
        异步删除会话
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self.delete_session, session_token
        )
    
    # 聊天历史相关操作
    def save_chat_history(self, username: str, question: str, answer: str, 
                          sources: List[str], is_real_time: bool = False) -> bool:
        """
        保存聊天历史（同步版本）
        """
        try:
            # 创建聊天记录
            chat_record = {
                "id": str(uuid.uuid4()),
                "username": username,
                "question": question,
                "answer": answer,
                "sources": sources or [],
                "is_real_time": is_real_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 添加到历史记录
            self.chat_history_collection.append(chat_record)
            
            # 调用同步保存方法
            self._save_chat_history_to_file()
            
            logger.info(f"💬 保存聊天历史成功: {username} - {chat_record['id'][:12]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存聊天历史失败: {str(e)}")
            return False
            
    async def save_chat_history_async(self, username: str, question: str, answer: str, 
                                     sources: List[str], is_real_time: bool = False):
        """
        异步保存聊天历史（优化版本，支持批量写入）
        用于高并发场景，不阻塞主线程
        """
        try:
            # 创建聊天记录
            chat_record = {
                "id": str(uuid.uuid4()),
                "username": username,
                "question": question,
                "answer": answer,
                "sources": sources or [],
                "is_real_time": is_real_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 线程安全地添加到内存中的历史记录
            with self._chat_history_lock:
                self.chat_history_collection.append(chat_record)
                self._pending_writes = True
                
                # 检查是否需要立即保存（批量大小或时间间隔触发）
                current_time = time.time()
                chat_count = len(self.chat_history_collection)
                
                should_save_now = (chat_count % self._max_batch_size == 0 or 
                                 current_time - self._last_write_time > self._auto_save_interval)
            
            # 如果需要保存，执行异步保存
            if should_save_now:
                # 使用线程池执行文件IO操作，避免阻塞事件循环
                await asyncio.get_event_loop().run_in_executor(
                    None, self._save_chat_history_to_file
                )
            
            logger.debug(f"💬 异步保存聊天历史成功: {username}")
            
        except Exception as e:
            self._operation_count["error"] += 1
            logger.error(f"❌ 异步保存聊天历史失败: {str(e)}")
    
    def get_user_chat_history(self, username: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        同步获取用户的聊天历史记录（线程安全）
        """
        try:
            with self._chat_history_lock:
                self._operation_count["read"] += 1
                
                # 从本地列表中获取用户的聊天历史（创建副本）
                user_history = [h.copy() for h in self.chat_history_collection if h.get("username") == username]
                
                # 按时间戳倒序排序（最新的在前面）
                user_history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                
                logger.info(f"📜 获取聊天历史: {username} - {len(user_history)}条记录")
                return user_history[:limit]
        except Exception as e:
            self._operation_count["error"] += 1
            logger.error(f"❌ 获取聊天历史失败: {str(e)}")
            return []
    
    async def get_user_chat_history_async(self, username: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        异步获取用户的聊天历史记录
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self.get_user_chat_history, username, limit
        )
    
    # 向量数据库元数据操作
    def save_vector_db_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        同步保存向量数据库元数据（线程安全）
        """
        try:
            # 更新或添加元数据
            metadata_with_timestamp = {
                **metadata,
                "updated_at": datetime.utcnow().isoformat(),
                "_id": "vector_db_metadata"
            }
            
            with self._vector_db_lock:
                # 查找并更新现有元数据
                updated = False
                for i, item in enumerate(self.vector_db_collection):
                    if item.get("_id") == "vector_db_metadata":
                        self.vector_db_collection[i] = metadata_with_timestamp
                        updated = True
                        break
                
                # 如果不存在则添加
                if not updated:
                    self.vector_db_collection.append(metadata_with_timestamp)
                
                # 标记有待保存的写入
                self._pending_writes = True
            
            # 保存到文件（在锁外进行IO操作）
            self._save_local_data()
            
            logger.info("📊 保存向量数据库元数据成功")
            return True
        except Exception as e:
            self._operation_count["error"] += 1
            logger.error(f"❌ 保存向量数据库元数据失败: {str(e)}")
            return False
    
    async def save_vector_db_metadata_async(self, metadata: Dict[str, Any]) -> bool:
        """
        异步保存向量数据库元数据
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self.save_vector_db_metadata, metadata
        )
    
    def get_vector_db_metadata(self) -> Optional[Dict[str, Any]]:
        """
        同步获取向量数据库元数据（线程安全）
        """
        try:
            with self._vector_db_lock:
                self._operation_count["read"] += 1
                for item in self.vector_db_collection:
                    if item.get("_id") == "vector_db_metadata":
                        return item.copy()  # 返回副本避免外部修改
                return None
        except Exception as e:
            self._operation_count["error"] += 1
            logger.error(f"❌ 获取向量数据库元数据失败: {str(e)}")
            return None
    
    async def get_vector_db_metadata_async(self) -> Optional[Dict[str, Any]]:
        """
        异步获取向量数据库元数据
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self.get_vector_db_metadata
        )
    
    def close(self):
        """
        关闭数据库服务，保存所有数据（线程安全）
        """
        try:
            # 确保所有待处理的写入都被保存
            if self._pending_writes:
                self._save_local_data()
            logger.info("✅ 数据库服务已关闭，数据已保存")
        except Exception as e:
            self._operation_count["error"] += 1
            logger.error(f"❌ 关闭数据库服务失败: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取数据库服务统计信息
        """
        try:
            with self._users_lock:
                users_count = len(self.users_collection)
            
            with self._sessions_lock:
                sessions_count = len(self.sessions_collection)
            
            with self._chat_history_lock:
                chat_history_count = len(self.chat_history_collection)
            
            with self._vector_db_lock:
                vector_db_count = len(self.vector_db_collection)
            
            return {
                "users_count": users_count,
                "sessions_count": sessions_count,
                "chat_history_count": chat_history_count,
                "vector_db_metadata_count": vector_db_count,
                "operation_stats": self._operation_count.copy(),
                "last_write_time": self._last_write_time,
                "pending_writes": self._pending_writes,
                "storage_dir": self.storage_dir
            }
        except Exception as e:
            logger.error(f"❌ 获取数据库统计信息失败: {str(e)}")
            return {"error": str(e)}
    
    async def get_stats_async(self) -> Dict[str, Any]:
        """
        异步获取数据库服务统计信息
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self.get_stats
        )

# 创建全局数据库服务实例
db_service = DatabaseService()