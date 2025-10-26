import requests
import json

# 测试健康检查端点
def test_health_check():
    print("===== 测试健康检查端点 =====")
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.json()}")
    except Exception as e:
        print(f"错误: {str(e)}")

# 测试问答端点
def test_ask_endpoint():
    print("\n===== 测试问答端点 =====")
    try:
        url = "http://localhost:8000/ask"
        payload = {
            "question": "学校有哪些学院？",
            "chat_history": []
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        print(f"状态码: {response.status_code}")
        
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
    
    except Exception as e:
        print(f"请求错误: {str(e)}")

# 测试另一个问题
def test_different_question():
    print("\n===== 测试不同问题 =====")
    try:
        url = "http://localhost:8000/ask"
        payload = {
            "question": "学校的历史是什么？",
            "chat_history": []
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"回答: {data.get('answer', '无回答')}")
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    print("开始测试API服务...\n")
    test_health_check()
    test_ask_endpoint()
    test_different_question()
    print("\n测试完成！")