import requests
import json
import time

# 测试实时信息搜索和回答长度
def test_realtime_information():
    """测试API是否能获取网上实时信息并验证回答长度改进"""
    
    # API端点
    url = "http://localhost:8000/ask"
    
    # 测试问题列表，包含需要实时信息的问题
    questions = [
        "2024年江西工业工程职业技术学院的最新分数线是多少？",
        "学校今年有哪些新开设的专业？",
        "最近学校有哪些重要新闻或活动？",
        "江西工业工程职业技术学院2024年的就业率是多少？"
    ]
    
    for question in questions:
        print(f"\n{'='*70}")
        print(f"测试问题: {question}")
        print(f"{'='*70}")
        
        # 准备请求数据
        data = {
            "question": question,
            "chat_history": []
        }
        
        # 发送请求
        try:
            start_time = time.time()
            response = requests.post(url, json=data)
            end_time = time.time()
            
            response_data = response.json()
            
            # 打印完整回答
            print(f"\n完整回答:")
            print(f"{'='*50}")
            print(response_data['answer'])
            print(f"{'='*50}")
            
            # 统计回答字数和信息
            answer_length = len(response_data['answer'])
            has_real_time = response_data['is_real_time']
            sources = response_data['sources']
            
            print(f"\n回答统计:")
            print(f"- 回答字数: {answer_length} 字")
            print(f"- 是否标记为实时数据: {'✅ 是' if has_real_time else '❌ 否'}")
            print(f"- 信息来源: {', '.join(sources)}")
            print(f"- 响应时间: {round(end_time - start_time, 2)} 秒")
            
            # 检查是否包含改进的结尾
            has_improved_ending = any(phrase in response_data['answer'] for phrase in [
                "小尤学长期待能为你提供更多帮助", 
                "如果以上信息还不够全面",
                "随时欢迎你提出更多问题"
            ])
            print(f"- 是否包含改进的结尾: {'✅ 是' if has_improved_ending else '❌ 否'}")
            
            # 检查是否有数据类型标记
            has_data_type_marker = "【" in response_data['answer'] and "】" in response_data['answer']
            print(f"- 是否包含数据类型标记: {'✅ 是' if has_data_type_marker else '❌ 否'}")
            
            # 检查回答是否完整（没有被截断）
            is_complete = "..." not in response_data['answer'] or response_data['answer'].rfind("...") < len(response_data['answer']) - 10
            print(f"- 回答是否完整（未被截断）: {'✅ 是' if is_complete else '❌ 否'}")
            
        except Exception as e:
            print(f"请求失败: {str(e)}")
    
    # 测试一个长问题来验证长回答的处理
    print(f"\n{'='*70}")
    print("测试长回答处理")
    print(f"{'='*70}")
    
    # 构造一个复杂的长问题
    complex_question = "详细介绍江西工业工程职业技术学院的历史发展、专业设置、师资力量、校园设施、招生政策、就业情况以及近年的发展成就，越详细越好。"
    
    try:
        data = {
            "question": complex_question,
            "chat_history": []
        }
        
        response = requests.post(url, json=data)
        response_data = response.json()
        
        print(f"\n长回答字数: {len(response_data['answer'])} 字")
        print(f"是否包含详细结尾建议: {'✅ 是' if '如果以上信息还不够全面' in response_data['answer'] else '❌ 否'}")
        
    except Exception as e:
        print(f"长问题测试失败: {str(e)}")

if __name__ == "__main__":
    print("开始测试实时信息搜索和回答长度改进...")
    test_realtime_information()
    print("\n测试完成！")