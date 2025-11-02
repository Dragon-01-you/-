import sys
import os

# 添加项目目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 从优化的API服务器导入handler
from api_server_pythonanywhere import handler

# 这是PythonAnywhere需要的变量名
application = handler