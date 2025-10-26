import requests
import json
import time

def test_ask_endpoint(question):
    """测试ask端点的响应"""
    url = "http://localhost:8000/ask"
    payload = {"question": question}
    headers = {"Content-Type": "application/json"}
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, headers=headers)
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n=== 问题: {question} ===")
            print(f"回答: {data.get('answer', '无回答')}")
            print(f"来源: {data.get('sources', [])}")
            print(f"响应时间: {end_time - start_time:.2f}秒")
            
            # 验证回答包含小尤学长标识
            if "小尤学长" in data.get('answer', ''):
                print("✓ 回答包含'小尤学长'标识")
            else:
                print("✗ 回答缺少'小尤学长'标识")
                
            # 检查身份问题是否正确处理
            if any(keyword in question.lower() for keyword in ["你是谁", "你叫什么"]):
                if "智能问答助手" in data.get('answer', '') and "江西工业工程职业技术学院" in data.get('answer', ''):
                    print("✓ 身份问题处理正确")
                else:
                    print("✗ 身份问题处理不正确")
            # 检查是否包含具体查找建议而非笼统建议
            elif "访问学校官网查看最新公告和通知" in data.get('answer', ''):
                print("✗ 仍包含笼统建议")
            elif any(specific_advice in data.get('answer', '') for specific_advice in [
                "访问学校官网的'", "联系", "关注", "咨询", "拨打"
            ]):
                print("✓ 包含具体查找建议")
                
            return True, data.get('answer', '')
        else:
            print(f"错误: 响应状态码 {response.status_code}")
            return False, None
    except Exception as e:
        print(f"异常: {str(e)}")
        return False, None

def test_health_check():
    """测试健康检查端点"""
    url = "http://localhost:8000/health"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("✓ 健康检查通过")
            return True
        else:
            print(f"✗ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 健康检查异常: {str(e)}")
        return False

def main():
    """运行所有测试"""
    print("开始测试智能问答系统优化...")
    
    # 健康检查
    print("\n1. 健康检查测试")
    health_ok = test_health_check()
    
    # 测试用例
    test_cases = [
        "你是谁",  # 身份问题测试
        "学校有哪些专业",  # 专业问题测试
        "招生分数线是多少",  # 招生问题测试
        "宿舍条件怎么样",  # 生活问题测试
        "奖学金如何申请",  # 奖助学金测试
        "校园活动有哪些",  # 活动问题测试
        "期末考试时间",  # 考试问题测试
        "就业情况怎么样"  # 就业问题测试
    ]
    
    print("\n2. 功能测试")
    success_count = 0
    total_time = 0
    
    for question in test_cases:
        success, _ = test_ask_endpoint(question)
        if success:
            success_count += 1
    
    # 统计结果
    print("\n=== 测试总结 ===")
    print(f"总测试用例数: {len(test_cases)}")
    print(f"成功测试用例数: {success_count}")
    print(f"成功率: {(success_count / len(test_cases)) * 100:.1f}%")
    print(f"健康检查状态: {'通过' if health_ok else '失败'}")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()