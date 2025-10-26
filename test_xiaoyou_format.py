import requests
import time
import json

BASE_URL = "http://localhost:8000"

# 测试函数 - 发送请求到/ask端点
def test_ask_endpoint(question):
    """测试/ask端点并返回响应"""
    url = f"{BASE_URL}/ask"
    payload = {
        "question": question,
        "chat_history": []
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response_time = time.time() - start_time
        return response, response_time
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return None, 0

# 打印响应详情
def print_response_details(question, response, response_time):
    """打印响应的详细信息"""
    if not response or response.status_code != 200:
        print(f"❌ 测试失败 - 问题: '{question}'")
        print(f"  状态码: {response.status_code if response else '无响应'}")
        return False
    
    try:
        data = response.json()
        print(f"✅ 测试成功 - 问题: '{question}'")
        print(f"  响应时间: {response_time:.2f}秒")
        print(f"  回答内容: ")
        print(f"  {data.get('answer', '无回答内容')}")
        print(f"  来源数量: {len(data.get('sources', []))}")
        print(f"  来源列表: {data.get('sources', [])}")
        print(f"  实时搜索: {data.get('is_real_time', False)}")
        print()
        
        # 检查'小尤学长'标识是否存在
        has_xiaoyou = '小尤学长' in data.get('answer', '')
        print(f"  ✅ '小尤学长'标识: {'已包含' if has_xiaoyou else '未包含'}")
        
        return True
    except json.JSONDecodeError:
        print(f"❌ 响应格式错误 - 问题: '{question}'")
        print(f"  原始响应: {response.text}")
        return False

# 测试健康检查端点
def test_health_check():
    """测试健康检查端点"""
    url = f"{BASE_URL}/health"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("✅ 健康检查成功")
            return True
        else:
            print(f"❌ 健康检查失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("===== 小尤学长智能问答格式测试 =====")
    print(f"测试服务器: {BASE_URL}")
    print()
    
    # 先测试健康检查
    if not test_health_check():
        print("服务器未启动或不可访问，请先启动API服务器。")
        exit(1)
    
    print()
    print("开始测试问答功能...")
    print("="*50)
    
    # 测试用例
    test_cases = [
        # 1. 测试有知识库内容的问题（应该包含小尤学长标识和友好建议）
        "学校的历史是怎样的？",
        
        # 2. 测试有知识库内容的问题 - 图书馆
        "图书馆开放时间是什么时候？",
        
        # 3. 测试知识库不足的情况（应该包含搜索结果和指定的提示格式）
        "学校附近有哪些好吃的餐厅？",
        
        # 4. 测试实时搜索问题
        "最近有什么校园活动？",
        
        # 5. 测试明确询问小尤学长身份
        "你是谁？"
    ]
    
    success_count = 0
    total_time = 0
    
    for i, question in enumerate(test_cases, 1):
        print(f"测试用例 {i}/{len(test_cases)}: {question}")
        response, response_time = test_ask_endpoint(question)
        total_time += response_time
        if print_response_details(question, response, response_time):
            success_count += 1
        print("-"*50)
    
    # 测试总结
    print("\n===== 测试总结 =====")
    print(f"总测试用例: {len(test_cases)}")
    print(f"成功用例: {success_count}")
    print(f"失败用例: {len(test_cases) - success_count}")
    print(f"平均响应时间: {total_time / len(test_cases):.2f}秒")
    print(f"成功率: {success_count / len(test_cases) * 100:.1f}%")
    print()
    
    if success_count == len(test_cases):
        print("🎉 所有测试用例通过！小尤学长智能问答功能正常工作。")
    else:
        print("⚠️  部分测试用例失败，请检查API服务器配置。")