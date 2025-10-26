import requests
import json
import time

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
        start_time = time.time()
        response = requests.post(url, json=payload, headers=headers)
        end_time = time.time()
        
        return response, end_time - start_time
    except Exception as e:
        print(f"请求异常: {str(e)}")
        return None, 0

def print_response_details(response, response_time, question):
    """打印响应详情"""
    if not response:
        print("无响应数据")
        return
    
    print(f"问题: {question}")
    print(f"状态码: {response.status_code}")
    print(f"响应时间: {response_time:.2f}秒")
    
    try:
        data = response.json()
        print(f"回答: {data.get('answer', '无回答')}")
        print(f"是否实时搜索: {data.get('is_realtime', False)}")
        print(f"来源数量: {len(data.get('sources', []))}")
        
        # 检查回答中是否包含"小尤学长"标识
        answer = data.get('answer', '')
        if "小尤学长" in answer:
            print("✅ 成功: 回答中包含'小尤学长'标识")
        else:
            print("⚠️ 提示: 回答中未明确包含'小尤学长'标识，但可能已按系统提示工作")
            
    except json.JSONDecodeError:
        print("响应内容不是有效的JSON格式")
        print(f"原始内容: {response.text}")
    print("=" * 80)

def main():
    """
    测试小尤学长智能问答功能
    """
    print("江西工业工程职业技术学院 - 小尤学长智能问答测试")
    print("=" * 80)
    print("正在测试API服务器...")
    
    # 先检查健康状态
    try:
        health_response = requests.get("http://localhost:8000/health")
        print(f"健康检查: {'成功' if health_response.status_code == 200 else '失败'}")
    except Exception as e:
        print(f"健康检查失败: {str(e)}")
        print("请确保API服务器正在运行!")
        return
    
    print("\n开始问答测试...")
    print("=" * 80)
    
    # 测试问题列表
    test_questions = [
        "你好，你叫什么名字？",
        "学校的历史是什么？",
        "图书馆的开放时间是什么时候？",
        "奖学金申请需要什么条件？",
        "介绍一下学校的专业设置"
    ]
    
    success_count = 0
    total_time = 0
    
    # 对每个问题进行测试
    for i, question in enumerate(test_questions):
        print(f"\n测试问题 {i+1}/{len(test_questions)}")
        print(f"问题: {question}")
        print("正在等待响应...")
        
        response, response_time = test_ask_endpoint(question)
        
        if response and response.status_code == 200:
            success_count += 1
            total_time += response_time
        
        print_response_details(response, response_time, question)
    
    # 测试总结
    print("\n测试总结")
    print("=" * 80)
    print(f"总问题数: {len(test_questions)}")
    print(f"成功回答: {success_count}")
    print(f"成功率: {(success_count / len(test_questions)) * 100:.1f}%")
    print(f"平均响应时间: {total_time / success_count:.2f}秒" if success_count > 0 else "无成功响应")
    
    if success_count == len(test_questions):
        print("🎉 所有测试通过！小尤学长智能问答功能正常工作。")
    else:
        print("⚠️ 部分测试未通过，请检查API配置和服务器状态。")

if __name__ == "__main__":
    main()