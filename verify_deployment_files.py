#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署文件验证脚本
用于在部署到PythonAnywhere前验证所有必要的文件和配置
"""

import os
import sys

# 检查Python版本
print("检查Python版本...")
if sys.version_info < (3, 7):
    print("❌ Python版本至少需要3.7")
    sys.exit(1)
else:
    print(f"✅ Python版本: {sys.version}")

# 检查核心文件是否存在
print("\n检查核心文件...")
required_files = [
    "api_server_simple.py",
    "vector_db_utils_simple.py",
    "wsgi.py",
    "minimal_requirements.txt"
]

missing_files = []
for file in required_files:
    if os.path.exists(file):
        print(f"✅ 找到: {file}")
    else:
        print(f"❌ 缺少: {file}")
        missing_files.append(file)

# 检查环境变量文件
print("\n检查环境变量文件...")
if os.path.exists(".env"):
    print("✅ 找到: .env")
else:
    print("⚠️  未找到.env文件，如果应用需要环境变量，请创建它")

# 检查数据目录
print("\n检查数据目录...")
data_directory = "江西工业工程职业技术学院_数据仓库"
if os.path.exists(data_directory) and os.path.isdir(data_directory):
    files_in_data = os.listdir(data_directory)
    print(f"✅ 找到数据目录: {data_directory} (包含 {len(files_in_data)} 个文件)")
else:
    print(f"⚠️  未找到数据目录: {data_directory}")

# 检查minimal_requirements.txt内容
print("\n检查依赖文件内容...")
if "minimal_requirements.txt" not in missing_files:
    required_deps = ["fastapi", "uvicorn", "pydantic"]
    found_deps = []
    with open("minimal_requirements.txt", "r", encoding="utf-8") as f:
        content = f.read().lower()
        
    for dep in required_deps:
        if dep in content:
            found_deps.append(dep)
            print(f"✅ 找到依赖: {dep}")
        else:
            print(f"❌ 缺少依赖: {dep}")
    
    if len(found_deps) != len(required_deps):
        print("⚠️  请确保minimal_requirements.txt包含所有必要的依赖")
else:
    print("❌ 无法检查依赖文件内容")

# 检查wsgi.py配置
print("\n检查WSGI配置...")
if "wsgi.py" not in missing_files:
    with open("wsgi.py", "r", encoding="utf-8") as f:
        wsgi_content = f.read().lower()
        
    if "api_server_simple" in wsgi_content and "application" in wsgi_content:
        print("✅ WSGI配置看起来正确")
    else:
        print("❌ WSGI配置可能不正确，请检查是否正确引用了api_server_simple")
else:
    print("❌ 无法检查WSGI配置")

# 检查api_server_simple.py内容
print("\n检查后端服务文件...")
if "api_server_simple.py" not in missing_files:
    with open("api_server_simple.py", "r", encoding="utf-8") as f:
        api_content = f.read().lower()
        
    if "fastapi" in api_content and "handler" in api_content and "vector_db_utils_simple" in api_content:
        print("✅ 后端服务文件看起来正确配置")
    else:
        print("⚠️  后端服务文件可能缺少必要的配置，请检查是否正确引用了vector_db_utils_simple和创建了handler")
else:
    print("❌ 无法检查后端服务文件")

# 总结
print("\n=== 部署准备检查总结 ===")
if not missing_files:
    print("✅ 所有核心文件都已找到，准备就绪！")
else:
    print(f"❌ 缺少 {len(missing_files)} 个核心文件，请在部署前创建它们")
    for file in missing_files:
        print(f"  - {file}")

print("\n请查看DEPLOYMENT_GUIDE_PYTHONANYWHERE.md了解详细部署步骤")