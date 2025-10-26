#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试数据库服务和用户认证功能
"""

import os
import sys
import json
import requests
import time
from datetime import datetime

# 配置日志
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API基础URL
BASE_URL = "http://localhost:8000"

class APITester:
    """API测试工具类"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.auth_token = None
        self.test_username = "test_user_" + str(int(time.time()))
        self.test_password = "test_password_123"
        self.test_email = f"{self.test_username}@example.com"
    
    def test_health_check(self):
        """测试健康检查端点"""
        logger.info("测试健康检查端点...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            logger.info(f"健康检查响应状态码: {response.status_code}")
            logger.info(f"健康检查响应内容: {response.json()}")
            
            # 验证数据库连接状态
            data = response.json()
            if data.get("status") == "healthy":
                logger.info("✅ 健康检查成功，服务运行正常")
                if data.get("database_connected", False):
                    logger.info("✅ 数据库连接正常")
                else:
                    logger.warning("⚠️  数据库连接状态未检测到")
                return True
            else:
                logger.error(f"❌ 健康检查失败: {data}")
                return False
        except Exception as e:
            logger.error(f"❌ 健康检查出错: {str(e)}")
            return False
    
    def test_user_registration(self):
        """测试用户注册功能"""
        logger.info(f"测试用户注册功能，用户名: {self.test_username}")
        try:
            payload = {
                "username": self.test_username,
                "password": self.test_password,
                "email": self.test_email
            }
            
            response = self.session.post(f"{self.base_url}/register", json=payload)
            logger.info(f"注册响应状态码: {response.status_code}")
            logger.info(f"注册响应内容: {response.json()}")
            
            if response.status_code == 200:
                logger.info("✅ 用户注册成功")
                return True
            else:
                logger.error(f"❌ 用户注册失败: {response.json()}")
                return False
        except Exception as e:
            logger.error(f"❌ 用户注册出错: {str(e)}")
            return False
    
    def test_user_login(self):
        """测试用户登录功能"""
        logger.info(f"测试用户登录功能，用户名: {self.test_username}")
        try:
            payload = {
                "username": self.test_username,
                "password": self.test_password
            }
            
            response = self.session.post(f"{self.base_url}/login", json=payload)
            logger.info(f"登录响应状态码: {response.status_code}")
            logger.info(f"登录响应内容: {response.json()}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                logger.info(f"✅ 用户登录成功，获取到令牌: {self.auth_token[:10]}...")
                # 设置认证头
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                return True
            else:
                logger.error(f"❌ 用户登录失败: {response.json()}")
                return False
        except Exception as e:
            logger.error(f"❌ 用户登录出错: {str(e)}")
            return False
    
    def test_ask_question(self):
        """测试提问功能"""
        logger.info("测试提问功能...")
        
        if not self.auth_token:
            logger.error("❌ 请先登录获取认证令牌")
            return False
        
        try:
            payload = {
                "question": "你好，这个系统能做什么？",
                "chat_history": []
            }
            
            response = self.session.post(f"{self.base_url}/ask", json=payload)
            logger.info(f"提问响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 提问成功，获得回答")
                logger.info(f"回答内容: {data.get('answer', '')[:100]}...")
                logger.info(f"来源信息: {data.get('sources', [])}")
                logger.info(f"聊天ID: {data.get('chat_id')}")
                return True
            else:
                logger.error(f"❌ 提问失败: {response.json() if response.content else '未知错误'}")
                return False
        except Exception as e:
            logger.error(f"❌ 提问出错: {str(e)}")
            return False
    
    def test_get_chat_history(self):
        """测试获取聊天历史功能"""
        logger.info("测试获取聊天历史功能...")
        
        if not self.auth_token:
            logger.error("❌ 请先登录获取认证令牌")
            return False
        
        try:
            response = self.session.get(f"{self.base_url}/chat_history?limit=10")
            logger.info(f"获取聊天历史响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                history_count = len(data.get('chat_history', []))
                logger.info(f"✅ 获取聊天历史成功，共 {history_count} 条记录")
                
                if history_count > 0:
                    first_chat = data['chat_history'][0]
                    logger.info(f"第一条聊天记录: ID={first_chat.get('chat_id')}, 问题={first_chat.get('question', '')[:50]}...")
                
                return True
            else:
                logger.error(f"❌ 获取聊天历史失败: {response.json() if response.content else '未知错误'}")
                return False
        except Exception as e:
            logger.error(f"❌ 获取聊天历史出错: {str(e)}")
            return False
    
    def test_user_logout(self):
        """测试用户登出功能"""
        logger.info("测试用户登出功能...")
        
        if not self.auth_token:
            logger.error("❌ 请先登录获取认证令牌")
            return False
        
        try:
            response = self.session.post(f"{self.base_url}/logout")
            logger.info(f"登出响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ 用户登出成功")
                # 清除认证头
                self.session.headers.pop("Authorization", None)
                self.auth_token = None
                return True
            else:
                logger.error(f"❌ 用户登出失败: {response.json() if response.content else '未知错误'}")
                return False
        except Exception as e:
            logger.error(f"❌ 用户登出错: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("="*60)
        logger.info("开始数据库和用户认证功能测试")
        logger.info("="*60)
        
        results = {
            "health_check": self.test_health_check(),
            "user_registration": self.test_user_registration(),
            "user_login": self.test_user_login(),
            "ask_question": self.test_ask_question(),
            "get_chat_history": self.test_get_chat_history(),
            "user_logout": self.test_user_logout()
        }
        
        logger.info("\n" + "="*60)
        logger.info("测试结果汇总")
        logger.info("="*60)
        
        all_passed = True
        for test_name, passed in results.items():
            status = "✅ 成功" if passed else "❌ 失败"
            logger.info(f"{test_name}: {status}")
            all_passed = all_passed and passed
        
        logger.info("\n" + "="*60)
        if all_passed:
            logger.info("🎉 所有测试通过！数据库和用户认证功能工作正常。")
        else:
            logger.error("⚠️  部分测试失败，请检查相关功能。")
        logger.info("="*60)
        
        return all_passed

if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()