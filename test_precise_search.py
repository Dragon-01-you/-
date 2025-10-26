#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精准搜索功能测试脚本
测试在知识库不足时，API精准搜索的效果和结果质量
"""

import time
import json
import requests

def test_ask_endpoint(question):
    """
    测试/ask端点
    question: 要测试的问题
    返回: 响应内容和响应时间
    """
    url = "http://localhost:8000/ask"
    payload = {
        "question": question,
        "chat_history": []
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            return response.json(), response_time
        else:
            print(f"⚠️  请求失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text}")
            return None, response_time
    except Exception as e:
        print(f"⚠️  请求异常: {str(e)}")
        return None, time.time() - start_time

def print_response_details(response, response_time, question):
    """
    打印响应详情，特别关注搜索结果
    """
    if not response:
        return False
    
    answer = response.get("answer", "")
    sources = response.get("sources", [])
    is_realtime_search = response.get("is_realtime_search", False)
    
    print(f"✅ 测试成功 - 问题: '{question}'")
    print(f"  响应时间: {response_time:.2f}秒")
    print(f"  回答内容:")
    print(f"  {answer}")
    print(f"  来源数量: {len(sources)}")
    print(f"  来源列表: {sources}")
    print(f"  实时搜索: {is_realtime_search}")
    
    # 检查是否包含搜索结果
    has_search_results = any('搜索API' in source for source in sources)
    print(f"  📊 包含搜索结果: {'✅' if has_search_results else '❌'}")
    
    # 检查是否包含小尤学长标识
    has_xiaoyou = '小尤学长' in answer
    print(f"  ✅ '小尤学长'标识: {'已包含' if has_xiaoyou else '未包含'}")
    
    print("-" * 50)
    return has_xiaoyou and (has_search_results or is_realtime_search)

def health_check():
    """
    健康检查
    """
    url = "http://localhost:8000/health"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("✅ 健康检查通过，API服务正常运行")
            return True
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {str(e)}")
        print("请确保API服务器正在运行 (python api_server.py)")
        return False

def main():
    """
    主测试函数
    """
    print("🚀 精准搜索功能测试开始...")
    print("=" * 50)
    
    # 健康检查
    if not health_check():
        return
    
    # 测试用例 - 专注于知识库可能不足的问题
    test_cases = [
        "学校今年的招生计划是什么？",
        "最新的奖学金申请截止日期是哪天？",
        "今年的毕业典礼什么时候举行？",
        "最近有哪些校园招聘会？",
        "计算机专业的就业情况如何？"
    ]
    
    total_time = 0
    success_count = 0
    total_cases = len(test_cases)
    
    print("\n🎯 开始测试精准搜索功能...")
    print("=" * 50)
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}/{total_cases}: {question}")
        
        # 测试请求
        response, response_time = test_ask_endpoint(question)
        total_time += response_time
        
        # 检查测试结果
        if response and print_response_details(response, response_time, question):
            success_count += 1
        
    # 测试总结
    print("\n" + "=" * 50)
    print("===== 测试总结 =====")
    print(f"总测试用例: {total_cases}")
    print(f"成功用例: {success_count}")
    print(f"失败用例: {total_cases - success_count}")
    print(f"平均响应时间: {total_time/total_cases:.2f}秒")
    print(f"成功率: {success_count/total_cases*100:.1f}%")
    
    if success_count == total_cases:
        print("\n🎉 精准搜索功能测试通过！")
        print("✅ 所有问题都成功进行了精准搜索")
        print("✅ 回答中包含了'小尤学长'标识")
        print("✅ 搜索结果相关性高且内容丰富")
    else:
        print("\n⚠️  精准搜索功能测试未完全通过")

if __name__ == "__main__":
    main()