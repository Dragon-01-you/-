import requests
import json

# 测试历史发展问题的完整回答
def test_history_question():
    """测试学校历史发展问题的完整回答"""
    
    # API端点
    url = "http://localhost:8000/ask"
    
    # 测试问题
    questions = [
        "江西工业工程职业技术学院的历史发展过程是怎样的？",
        "学校的创办历史是什么？",
        "江西工业工程职业技术学院的发展历程？"
    ]
    
    for question in questions:
        print(f"\n{'='*60}")
        print(f"测试问题: {question}")
        print(f"{'='*60}")
        
        # 准备请求数据
        data = {
            "question": question,
            "chat_history": []
        }
        
        # 发送请求
        try:
            response = requests.post(url, json=data)
            response_data = response.json()
            
            # 打印完整回答
            print(f"\n完整回答:")
            print(f"{'='*40}")
            print(response_data['answer'])
            print(f"{'='*40}")
            
            # 打印其他信息
            print(f"\n来源: {', '.join(response_data['sources'])}")
            print(f"是否实时数据: {response_data['is_real_time']}")
            
            # 检查是否包含历史发展的关键点
            has_key_points = all(keyword in response_data['answer'] for keyword in [
                "1956", "萍乡煤矿学校", "1999", "江西省工业工程学校", "2002", "高等职业技术学院"
            ])
            print(f"\n包含所有历史关键点: {'✅' if has_key_points else '❌'}")
            
            # 检查格式是否优化
            has_bullet_points = '•' in response_data['answer']
            print(f"使用了优化的列表格式: {'✅' if has_bullet_points else '❌'}")
            
        except Exception as e:
            print(f"请求失败: {str(e)}")

if __name__ == "__main__":
    print("开始测试学校历史发展问题的完整回答...")
    test_history_question()
    print("\n测试完成！")