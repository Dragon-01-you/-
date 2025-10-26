import requests
import json
import time

# 直接复制API配置信息，绕过HTTP层直接测试
MODEL_CONFIG = {
    "api_base": "https://api-inference.huggingface.co/models/THUDM/chatglm-6b",
    "api_key": "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",
    "model_name": "chatglm-6b",
    "timeout": 100
}

# 测试问题列表
TEST_QUESTIONS = [
    "江西工业工程职业技术学院的历史有多久了？",
    "图书馆的开放时间是什么时候？",
    "奖学金申请需要什么条件？",
    "学校有哪些著名的教师？"
]

def call_llm_api_direct(prompt):
    """直接调用大模型API的函数，绕过HTTP服务器"""
    try:
        # 构建消息
        messages = []
        
        # 添加系统提示
        system_prompt = """
        你是江西工业工程职业技术学院的智能问答助手。
        请根据提供的上下文信息和对话历史，用自然、友好的语言回答用户问题。
        如果你不知道答案，请坦率表示，并建议用户联系学校相关部门。
        回答要简洁明了，重点突出。
        """
        messages.append({"role": "system", "content": system_prompt})
        
        # 添加当前问题
        messages.append({"role": "user", "content": prompt})
        
        # 构建请求数据
        payload = {
            "model": MODEL_CONFIG["model_name"],
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # 发送请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MODEL_CONFIG['api_key']}"
        }
        
        print(f"正在调用ChatGLM-6B API...")
        start_time = time.time()
        response = requests.post(
            MODEL_CONFIG["api_base"],
            headers=headers,
            json=payload,
            timeout=MODEL_CONFIG["timeout"]
        )
        
        end_time = time.time()
        print(f"API调用完成，耗时: {(end_time - start_time):.2f}秒")
        
        if response.status_code != 200:
            print(f"❌ API调用失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False, f"API调用失败: {response.status_code}"
        
        # 解析响应
        result = response.json()
        if "choices" in result and result["choices"]:
            answer = result["choices"][0]["message"]["content"]
            print(f"✅ 成功获取回答")
            print(f"回答内容: {answer}")
            return True, answer
        else:
            print(f"❌ API返回格式异常")
            print(f"响应内容: {result}")
            return False, "API返回数据格式异常"
            
    except Exception as e:
        print(f"❌ API调用异常: {str(e)}")
        return False, f"API调用异常: {str(e)}"

def main():
    print("=== ChatGLM-6B API直接测试工具 ===")
    print(f"API端点: {MODEL_CONFIG['api_base']}")
    print(f"模型名称: {MODEL_CONFIG['model_name']}")
    print()
    
    success_count = 0
    
    for i, question in enumerate(TEST_QUESTIONS):
        print(f"\n问题 {i+1}/{len(TEST_QUESTIONS)}: {question}")
        print("-" * 60)
        
        success, answer = call_llm_api_direct(question)
        if success:
            success_count += 1
        
        print("=" * 60)
    
    # 总结
    print(f"\n测试总结:")
    print(f"总问题数: {len(TEST_QUESTIONS)}")
    print(f"成功数: {success_count}")
    print(f"成功率: {(success_count / len(TEST_QUESTIONS) * 100):.1f}%")
    
    if success_count == len(TEST_QUESTIONS):
        print("\n🎉 ChatGLM-6B API调用测试成功！")
    else:
        print("\n⚠️ 部分API调用失败，请检查配置和网络连接。")

if __name__ == "__main__":
    main()