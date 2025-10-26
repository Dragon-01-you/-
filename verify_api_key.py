import requests
import time
import sys
from api_server import MODEL_CONFIG, is_api_configured, call_llm_api

def verify_api_configuration():
    """
    验证API配置是否正确
    """
    print("开始验证API配置...")
    print("=" * 50)
    
    # 检查是否配置了API
    if not is_api_configured():
        print("❌ API未完全配置！请检查以下字段：")
        
        # 检查每个必需字段
        required_fields = ["api_base", "api_key", "model_name"]
        for field in required_fields:
            value = MODEL_CONFIG.get(field)
            if not value or value == "":
                print(f"  - {field}: 未设置")
            else:
                # 显示部分密钥用于安全
                if field == "api_key":
                    masked_key = value[:4] + "****" + value[-4:]
                    print(f"  - {field}: {masked_key}")
                else:
                    print(f"  - {field}: {value}")
        
        print("\n请在api_server.py文件中更新MODEL_CONFIG字典：")
        print("例如：")
        print("MODEL_CONFIG = {")
        print("    'api_base': '您的API基础URL',")
        print("    'api_key': '您的API密钥',")
        print("    'model_name': '模型名称',")
        print("    'timeout': 100")
        print("}")
        return False
    
    print("✅ API配置已检测到")
    print(f"  - API基础URL: {MODEL_CONFIG['api_base']}")
    print(f"  - API密钥: {MODEL_CONFIG['api_key'][:4]}****{MODEL_CONFIG['api_key'][-4:]}")
    print(f"  - 模型名称: {MODEL_CONFIG['model_name']}")
    print(f"  - 超时设置: {MODEL_CONFIG['timeout']}秒")
    
    return True

def test_api_connection():
    """
    测试API连接是否正常工作
    """
    print("\n开始测试API连接...")
    print("-" * 50)
    
    # 构建一个简单的测试提示
    test_prompt = "你好，请简单介绍一下自己。"
    
    try:
        start_time = time.time()
        print("正在发送测试请求到API...")
        print(f"请求URL: {MODEL_CONFIG['api_base']}")
        
        # 直接测试API调用
        answer = call_llm_api(test_prompt)
        
        end_time = time.time()
        print(f"\n✅ API调用成功！")
        print(f"响应时间: {end_time - start_time:.2f}秒")
        print(f"API返回内容: {answer[:100]}..." if len(answer) > 100 else f"API返回内容: {answer}")
        return True
        
    except Exception as e:
        print(f"❌ API调用失败：")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        
        # 根据错误类型提供建议
        if "ConnectionError" in str(type(e).__name__) or "Timeout" in str(type(e).__name__):
            print("\n可能的原因：")
            print("1. 网络连接问题")
            print("2. API基础URL不正确")
            print("3. API密钥无效")
            print("4. 防火墙阻止了连接")
        elif "Unauthorized" in str(e):
            print("\n可能的原因：")
            print("1. API密钥无效或已过期")
            print("2. API密钥格式不正确")
        else:
            print("\n请检查您的API配置和网络连接")
        
        return False

def main():
    """
    主函数
    """
    print("江西工业工程职业技术学院 - API密钥验证工具")
    print("=" * 50)
    
    # 步骤1：验证API配置
    config_valid = verify_api_configuration()
    if not config_valid:
        print("\n❌ 请先完成API配置，然后再次运行此脚本。")
        sys.exit(1)
    
    # 步骤2：测试API连接
    connection_success = test_api_connection()
    
    # 步骤3：给出最终建议
    print("\n" + "=" * 50)
    if connection_success:
        print("🎉 API配置和连接测试成功！")
        print("您现在可以启动API服务器并开始使用ChatGLM-6B了。")
        print("运行命令: python api_server.py")
    else:
        print("❌ API配置或连接测试失败。")
        print("请检查您的配置和网络连接，修复问题后再次尝试。")

if __name__ == "__main__":
    main()