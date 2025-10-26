import requests
import json

def test_ask_endpoint(question):
    """测试/ask端点"""
    url = "http://localhost:8000/ask"
    payload = {
        "question": question,
        "chat_history": []
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response
    except Exception as e:
        print(f"请求异常: {str(e)}")
        return None

def print_response_details(response):
    """打印响应详情"""
    if not response:
        print("无响应数据")
        return
    
    print(f"状态码: {response.status_code}")
    try:
        data = response.json()
        print(f"回答: {data.get('answer', '无回答')}")
        print(f"是否实时搜索: {data.get('is_realtime', False)}")
        print(f"来源数量: {len(data.get('sources', []))}")
        
        # 打印前几个来源
        print("来源列表:")
        sources = data.get('sources', [])
        for i, source in enumerate(sources[:3]):
            if isinstance(source, dict):
                print(f"  {i+1}. {source.get('source_name', '未知来源')} - {source.get('content', '')[:50]}...")
            else:
                print(f"  {i+1}. {str(source)[:100]}...")
    except json.JSONDecodeError:
        print("响应内容不是有效的JSON格式")
        print(f"原始内容: {response.text}")
    print("-" * 50)

def main():
    """运行测试"""
    print("开始测试本地回答生成功能...")
    print("=" * 50)
    
    # 测试问题列表
    test_questions = [
        "学校的历史是什么？",
        "图书馆的开放时间是什么时候？",
        "奖学金申请需要什么条件？",
        "学校有哪些专业？"
    ]
    
    # 对每个问题进行测试
    for i, question in enumerate(test_questions):
        print(f"\n问题 {i+1}/{len(test_questions)}: {question}")
        response = test_ask_endpoint(question)
        print_response_details(response)
    
    print("测试完成！")

if __name__ == "__main__":
    main()