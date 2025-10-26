import requests
import json

# API端点URL
url = "http://localhost:8000/ask"

# 测试问题
question = "江西工业工程职业技术学院的历史发展过程是怎样的？"

# 准备请求数据
data = {
    "question": question,
    "chat_history": []
}

# 发送请求
print(f"发送问题: {question}")
try:
    response = requests.post(url, json=data)
    response_data = response.json()
    
    # 打印完整回答
    print("\n完整回答:")
    print(response_data["answer"])
    print("\n来源:", response_data["sources"])
    print("是否实时数据:", response_data["is_real_time"])
    
except Exception as e:
    print(f"请求失败: {e}")