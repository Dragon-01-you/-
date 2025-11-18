import sys
import os

# 添加项目目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 确保使用正确的Python版本 (PythonAnywhere配置为Python 3.11)
print(f"Python版本: {sys.version}")

# 从优化的API服务器导入应用
from api_server_pythonanywhere import app

# PythonAnywhere需要的application变量
application = app