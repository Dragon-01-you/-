import requests
import json
import time

class AITestClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.chat_history = []
    
    def health_check(self):
        """测试健康检查端点"""
        print("===== 健康检查测试 =====")
        try:
            url = f"{self.base_url}/health"
            response = requests.get(url, timeout=5)
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"系统状态: {data.get('status', '未知')}")
                print(f"向量数据库状态: {data.get('vector_db_status', '未知')}")
                return True
            return False
        except Exception as e:
            print(f"健康检查失败: {str(e)}")
            return False
    
    def ask_question(self, question, use_history=True):
        """发送问题并获取回答"""
        print(f"\n===== 测试问题: {question} =====")
        try:
            url = f"{self.base_url}/ask"
            
            if use_history:
                history = self.chat_history.copy()
            else:
                history = []
            
            payload = {
                "question": question,
                "chat_history": history
            }
            
            headers = {"Content-Type": "application/json"}
            
            start_time = time.time()
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            end_time = time.time()
            
            print(f"状态码: {response.status_code}")
            print(f"响应时间: {end_time - start_time:.2f}秒")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n回答: {data.get('answer', '无回答')}")
                print(f"是否实时搜索: {data.get('is_real_time', False)}")
                print(f"来源数量: {len(data.get('sources', []))}")
                if data.get('sources'):
                    print(f"来源列表: {', '.join(data.get('sources', []))}")
                
                # 更新对话历史
                if use_history:
                    self.chat_history.append({"role": "user", "content": question})
                    self.chat_history.append({"role": "assistant", "content": data.get('answer', '')})
                    print(f"\n当前对话历史长度: {len(self.chat_history)}")
                
                return data
            else:
                print(f"错误响应: {response.text}")
                return None
        
        except requests.Timeout:
            print("请求超时")
            return None
        except Exception as e:
            print(f"请求异常: {str(e)}")
            return None
    
    def test_multiturn_conversation(self):
        """测试多轮对话"""
        print("\n" + "="*50)
        print("开始多轮对话测试")
        print("="*50)
        
        # 清空对话历史
        self.chat_history = []
        
        # 第一轮对话
        self.ask_question("学校有多少个学院？")
        
        # 第二轮对话（依赖第一轮）
        self.ask_question("计算机学院有哪些专业？")
        
        # 第三轮对话
        self.ask_question("学校的地址在哪里？")
        
        print("\n多轮对话测试完成！")
    
    def test_different_types(self):
        """测试不同类型的问题"""
        print("\n" + "="*50)
        print("测试不同类型的问题")
        print("="*50)
        
        # 学校基本信息
        self.ask_question("学校什么时候成立的？", use_history=False)
        
        # 学生服务相关
        self.ask_question("奖学金申请条件是什么？", use_history=False)
        
        # 教学相关
        self.ask_question("图书馆开放时间？", use_history=False)
        
        # 可能需要实时搜索的问题
        self.ask_question("今年的招生计划是什么？", use_history=False)
        
        print("\n不同类型问题测试完成！")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始进行全面的API测试...\n")
        
        # 1. 健康检查
        health_ok = self.health_check()
        if not health_ok:
            print("\n健康检查失败，API服务可能未正常运行！")
            return
        
        # 2. 简单问答测试
        self.ask_question("学校的全称是什么？", use_history=False)
        
        # 3. 多轮对话测试
        self.test_multiturn_conversation()
        
        # 4. 不同类型问题测试
        self.test_different_types()
        
        print("\n" + "="*50)
        print("🎉 所有测试完成！")
        print("="*50)

if __name__ == "__main__":
    client = AITestClient()
    client.run_all_tests()