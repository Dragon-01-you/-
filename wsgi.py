import sys
import os

# 添加项目目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 从api_server_simple导入handler
from api_server_simple import handler

# 这是PythonAnywhere需要的变量名
application = handler