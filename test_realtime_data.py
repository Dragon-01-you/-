import requests
import json
import time

BASE_URL = "http://localhost:8000"

# 测试用例
test_cases = [
    {
        "name": "1. 实时招生数据查询",
        "question": "2025年江西工业工程职业技术学院的招生计划是多少？",
        "keywords": ["实时数据", "2025年", "招生计划"]
    },
    {
        "name": "2. 历年分数线查询（需要近几年数据）",
        "question": "江西工业工程职业技术学院近三年的录取分数线是多少？",
        "keywords": ["近年数据", "近三年", "分数线"]
    },
    {
        "name": "3. 最新就业情况查询",
        "question": "江西工业工程职业技术学院最新的就业率是多少？",
        "keywords": ["实时数据", "最新", "就业率"]
    },
    {
        "name": "4. 近年专业设置查询",
        "question": "江西工业工程职业技术学院近四年开设了哪些专业？",
        "keywords": ["近年数据", "近四年", "专业"]
    },
    {
        "name": "5. 最新校园活动查询",
        "question": "江西工业工程职业技术学院最近有什么校园活动？",
        "keywords": ["实时数据", "最近", "校园活动"]
    },
    {
        "name": "6. 历年校企合作查询",
        "question": "江西工业工程职业技术学院过去几年有哪些校企合作项目？",
        "keywords": ["近年数据", "过去几年", "校企合作"]
    },
    {
        "name": "7. 2024年专业课程查询",
        "question": "2024年江西工业工程职业技术学院机械专业的课程设置是什么？",
        "keywords": ["实时数据", "2024年", "课程设置"]
    },
    {
        "name": "8. 学校历史发展查询（无需实时数据）",
        "question": "江西工业工程职业技术学院的历史发展过程是怎样的？",
        "keywords": ["近年数据", "历史发展", "学校概况"]
    }
]

def test_health_check():
    """测试健康检查接口"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ 健康检查通过")
            print(f"   状态: {data.get('status')}")
            print(f"   时间: {data.get('timestamp')}")
            return True
        else:
            print(f"❌ 健康检查失败: 状态码 {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {str(e)}")
        return False

def test_realtime_data_query(test_case):
    """测试实时数据查询"""
    question = test_case["question"]
    
    try:
        # 构建请求数据
        request_data = {
            "question": question,
            "chat_history": []
        }
        
        # 发送请求
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/ask", json=request_data)
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            
            # 验证回答是否包含必要的信息
            contains_identity = "小尤学长" in answer
            
            # 检查是否包含关键词
            contains_keywords = any(keyword in answer for keyword in test_case["keywords"])
            
            # 检查是否有数据类型标记
            has_data_type = "实时数据" in answer or "近年数据" in answer
            
            # 打印测试结果
            print(f"\n{test_case['name']}:")
            print(f"   ✅ 查询成功")
            print(f"   问题: {question}")
            print(f"   响应时间: {end_time - start_time:.2f} 秒")
            print(f"   包含'小尤学长': {'✅' if contains_identity else '❌'}")
            print(f"   包含关键词: {'✅' if contains_keywords else '❌'}")
            print(f"   有数据类型标记: {'✅' if has_data_type else '❌'}")
            print(f"   回答摘要: {answer[:100]}...")
            
            return contains_identity and contains_keywords and has_data_type
        else:
            print(f"\n{test_case['name']}:")
            print(f"   ❌ 查询失败: 状态码 {response.status_code}")
            return False
    except Exception as e:
        print(f"\n{test_case['name']}:")
        print(f"   ❌ 查询异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("==== 实时数据处理逻辑测试 ====\n")
    
    # 先进行健康检查
    if not test_health_check():
        print("\n❌ 健康检查失败，退出测试")
        return
    
    # 执行测试用例
    passed_count = 0
    total_count = len(test_cases)
    
    print("\n==== 开始执行测试用例 ====\n")
    
    for test_case in test_cases:
        if test_realtime_data_query(test_case):
            passed_count += 1
    
    # 输出测试结果统计
    print("\n==== 测试结果统计 ====")
    print(f"总测试用例: {total_count}")
    print(f"通过测试: {passed_count}")
    print(f"失败测试: {total_count - passed_count}")
    print(f"通过率: {passed_count / total_count * 100:.1f}%")
    
    if passed_count == total_count:
        print("\n🎉 所有测试用例通过！实时数据处理逻辑优化成功！")
    else:
        print("\n❌ 部分测试用例失败，需要进一步调试优化。")

if __name__ == "__main__":
    main()