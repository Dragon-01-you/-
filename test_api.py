import requests
import json
import time

# API服务基本信息
API_BASE_URL = "http://localhost:8000"

# 默认用户凭据（从db_service.py中找到的默认账号）
DEFAULT_CREDENTIALS = {
    "username": "student1",
    "password": "password123"
}

# 存储认证令牌
auth_token = None

# 打印API服务信息
def print_api_info():
    print("""
    ============================================
    API服务信息
    ============================================
    服务地址: {}  
    后端入口文件: api_server.py
    启动命令: python -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
    API文档: {}/api/docs
    默认测试账号: student1/password123
    ============================================
    """.format(API_BASE_URL, API_BASE_URL))

# 用户登录获取认证令牌
def login():
    global auth_token
    print("\n===== 用户登录 =====")
    endpoint = f"{API_BASE_URL}/login"
    print(f"访问端点: {endpoint}")
    print(f"使用默认账号登录: {DEFAULT_CREDENTIALS['username']}/{DEFAULT_CREDENTIALS['password']}")
    
    try:
        payload = DEFAULT_CREDENTIALS
        headers = {"Content-Type": "application/json"}
        
        start_time = time.time()
        response = requests.post(endpoint, json=payload, headers=headers)
        response_time = time.time() - start_time
        
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {response_time:.2f} 秒")
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            print(f"登录成功！获取到访问令牌: {auth_token[:10]}...")
            print(f"用户角色: {data.get('role', 'unknown')}")
            return True
        else:
            print(f"登录失败: {response.text}")
            return False
    except Exception as e:
        print(f"登录错误: {str(e)}")
        return False

# 测试健康检查端点
def test_health_check():
    print("\n===== 测试健康检查端点 =====")
    endpoint = f"{API_BASE_URL}/health"
    print(f"访问端点: {endpoint}")
    
    try:
        start_time = time.time()
        response = requests.get(endpoint)
        response_time = time.time() - start_time
        
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {response_time:.2f} 秒")
        print(f"响应内容: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {str(e)}")
        return False

# 测试问答端点
def test_ask_endpoint():
    global auth_token
    print("\n===== 测试问答端点 =====")
    endpoint = f"{API_BASE_URL}/ask"
    print(f"访问端点: {endpoint}")
    
    if not auth_token:
        print("错误: 未登录或认证令牌无效")
        return False
    
    try:
        payload = {
            "question": "学校有哪些学院？",
            "chat_history": []
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}"
        }
        
        start_time = time.time()
        response = requests.post(endpoint, json=payload, headers=headers)
        response_time = time.time() - start_time
        
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {response_time:.2f} 秒")
        
        # 打印原始响应内容
        print(f"原始响应: {response.text}")
        
        # 尝试解析JSON
        try:
            data = response.json()
            print(f"\n解析后的数据:")
            print(f"回答: {data.get('answer', '无回答')}")
            print(f"是否实时搜索: {data.get('is_realtime', False)}")
            print(f"来源: {data.get('sources', [])}")
        except json.JSONDecodeError as je:
            print(f"JSON解析错误: {str(je)}")
            return False
        return response.status_code == 200
    
    except Exception as e:
        print(f"请求错误: {str(e)}")
        return False

# 测试另一个问题
def test_different_question():
    global auth_token
    print("\n===== 测试不同问题 =====")
    endpoint = f"{API_BASE_URL}/ask"
    print(f"访问端点: {endpoint}")
    
    if not auth_token:
        print("错误: 未登录或认证令牌无效")
        return False
    
    try:
        payload = {
            "question": "学校的历史是什么？",
            "chat_history": []
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}"
        }
        
        start_time = time.time()
        response = requests.post(endpoint, json=payload, headers=headers)
        response_time = time.time() - start_time
        
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {response_time:.2f} 秒")
        
        if response.status_code == 200:
            data = response.json()
            print(f"回答: {data.get('answer', '无回答')}")
            return True
        else:
            print(f"请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"错误: {str(e)}")
        return False

# 测试用户登出
def test_logout():
    global auth_token
    print("\n===== 测试用户登出 =====")
    endpoint = f"{API_BASE_URL}/logout"
    print(f"访问端点: {endpoint}")
    
    if not auth_token:
        print("错误: 未登录或认证令牌无效")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {auth_token}"
        }
        
        start_time = time.time()
        response = requests.post(endpoint, headers=headers)
        response_time = time.time() - start_time
        
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {response_time:.2f} 秒")
        
        if response.status_code == 200:
            print("登出成功！")
            auth_token = None
            return True
        else:
            print(f"登出失败: {response.text}")
            return False
    except Exception as e:
        print(f"登出错误: {str(e)}")
        return False

# 测试API文档可用性
def test_api_docs():
    print("\n===== 测试API文档 =====")
    endpoint = f"{API_BASE_URL}/api/docs"
    print(f"API文档地址: {endpoint}")
    print("请在浏览器中打开此地址查看完整的API文档")
    return True

# 检查API服务状态
def check_api_service_status():
    print("\n===== 检查API服务状态 =====")
    try:
        start_time = time.time()
        response = requests.head(API_BASE_URL, timeout=5)
        response_time = time.time() - start_time
        print(f"API服务正在运行!")
        print(f"响应时间: {response_time:.2f} 秒")
        return True
    except requests.exceptions.ConnectionError:
        print(f"错误: 无法连接到API服务 {API_BASE_URL}")
        print("请确保后端服务已启动")
        return False
    except Exception as e:
        print(f"检查服务状态时出错: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始测试API服务...\n")
    print_api_info()
    
    # 先检查服务状态
    if not check_api_service_status():
        print("\n测试失败: API服务未运行")
        exit(1)
    
    # 必须先登录
    if not login():
        print("\n测试失败: 无法登录，无法继续测试")
        exit(1)
    
    # 运行所有测试
    tests = [
        test_health_check,
        test_ask_endpoint,
        test_different_question,
        test_api_docs
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append((test.__name__, result))
    
    # 最后登出
    test_logout()
    
    # 打印测试结果汇总
    print("\n\n===========================================\n测试结果汇总:")
    for test_name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    if all(success for _, success in results):
        print("\n🎉 所有测试通过！API服务运行正常！")
        print(f"\n您的API地址是: {API_BASE_URL}")
        print(f"您可以访问 {API_BASE_URL}/api/docs 查看完整的API文档")
        print(f"使用默认账号 {DEFAULT_CREDENTIALS['username']}/{DEFAULT_CREDENTIALS['password']} 进行认证访问")
    else:
        print("\n⚠️  部分测试失败，请检查API服务")
    
    print("\n===========================================")
    print("测试完成！")

# 显示API服务信息的函数，可直接调用获取API信息
def show_api_info():
    """
    显示API服务信息，包括地址、认证凭据等
    """
    print("""
    ============================================
    API服务信息
    ============================================
    服务地址: {}
    API文档: {}/api/docs
    API密钥认证: 使用测试密钥 "test_key_2024"
    用户认证: 使用账号 "student1"，密码 "password123"
    ============================================
    """.format(API_BASE_URL, API_BASE_URL))

# 如果直接运行此脚本，会自动执行完整测试
# 如果作为模块导入，可以调用show_api_info()获取API信息