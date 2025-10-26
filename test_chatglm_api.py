import requests
import json
import time

# API端点
API_URL = "http://localhost:8000/ask"

# 测试问题列表 - 包含不同类型的问题
TEST_QUESTIONS = [
    "学校的历史有多久了？",
    "图书馆的开放时间是什么时候？",
    "奖学金申请需要什么条件？",
    "今年有哪些新开设的专业？",
    "学校有哪些著名的教师？",
    "如何申请入学？",
    "校园里有哪些体育设施？"
]

def test_api():
    print("开始测试ChatGLM-6B API调用...\n")
    print("=" * 60)
    
    success_count = 0
    failure_count = 0
    
    for i, question in enumerate(TEST_QUESTIONS):
        print(f"问题 {i+1}/{len(TEST_QUESTIONS)}: {question}")
        print("-" * 60)
        
        try:
            # 准备请求数据
            payload = {
                "question": question,
                "chat_history": []
            }
            
            # 发送请求
            start_time = time.time()
            response = requests.post(
                API_URL,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=60  # 设置较长的超时时间
            )
            end_time = time.time()
            
            # 检查响应状态
            if response.status_code == 200:
                success_count += 1
                result = response.json()
                print(f"✅ 成功获取回答 (响应时间: {(end_time - start_time):.2f}秒)")
                print(f"回答: {result['answer']}")
                print(f"来源数: {len(result['sources'])}")
                print(f"来源列表: {', '.join(result['sources'])}")
                print(f"是否实时搜索: {result['is_real_time']}")
            else:
                failure_count += 1
                print(f"❌ API调用失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except Exception as e:
            failure_count += 1
            print(f"❌ 发生异常: {str(e)}")
            
        print("=" * 60)
        print()  # 空行分隔不同问题的结果
    
    # 输出测试总结
    print("\n测试总结:")
    print(f"总问题数: {len(TEST_QUESTIONS)}")
    print(f"成功数: {success_count}")
    print(f"失败数: {failure_count}")
    print(f"成功率: {(success_count / len(TEST_QUESTIONS) * 100):.1f}%")
    
    if failure_count > 0:
        print("\n注意: API调用可能存在问题，请检查服务器状态和配置。")
    else:
        print("\n🎉 所有API调用测试成功！")

if __name__ == "__main__":
    print("ChatGLM-6B API调用测试脚本")
    print(f"测试目标: {API_URL}")
    print()
    
    # 先检查服务器是否可访问
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ 服务器健康检查通过")
            test_api()
        else:
            print("❌ 服务器不可用，状态码:", health_response.status_code)
            print("请先启动后端服务: python api_server.py")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        print("请先启动后端服务: python api_server.py")
    except Exception as e:
        print(f"❌ 检查服务器状态时发生错误: {str(e)}")