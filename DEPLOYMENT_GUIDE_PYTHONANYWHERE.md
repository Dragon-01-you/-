# PythonAnywhere 部署指南

## 1. 准备工作

### 1.1 确保本地项目文件完整

在部署前，确保你的项目包含以下关键文件：

- `api_server_simple.py`: 轻量级后端服务
- `vector_db_utils_simple.py`: 简化版向量数据库工具
- `wsgi.py`: WSGI配置文件
- `minimal_requirements.txt`: 最小依赖列表
- `.env`: 环境变量配置文件（如需要）
- `江西工业工程职业技术学院_数据仓库`: 数据文件夹（如需要）

### 1.2 检查依赖文件

确保`minimal_requirements.txt`包含以下内容：

```
fastapi==0.104.1
uvicorn==0.24.0.post1
python-multipart==0.0.6
pydantic==2.5.2
pydantic-settings==2.1.0
```

## 2. 创建PythonAnywhere账户

1. 访问 [PythonAnywhere](https://www.pythonanywhere.com/)
2. 点击"Sign Up"
3. 选择"Beginner Account"（免费版）
4. 填写注册信息并创建账户

## 3. 设置PythonAnywhere

### 3.1 创建虚拟环境

登录后，按照以下步骤操作：

1. 点击顶部导航栏的"Consoles"
2. 选择"Bash"
3. 在bash控制台中运行以下命令创建虚拟环境：

```bash
python3 -m venv myenv
source myenv/bin/activate  # 激活虚拟环境
```

### 3.2 上传项目文件

方法一：通过Web界面上传

1. 点击顶部导航栏的"Files"
2. 点击"Upload a file"
3. 选择并上传以下文件：
   - `api_server_simple.py`
   - `vector_db_utils_simple.py`
   - `wsgi.py`
   - `minimal_requirements.txt`
   - `.env`（如需要）

方法二：通过Git克隆（如果代码已上传到GitHub）

1. 在bash控制台中运行：
```bash
git clone https://github.com/你的用户名/你的仓库名.git
to your home directory and then work from there.
```

### 3.3 安装依赖

在bash控制台中激活虚拟环境并安装依赖：

```bash
source myenv/bin/activate
pip install -r minimal_requirements.txt
```

## 4. 配置Web应用

1. 点击顶部导航栏的"Web"
2. 点击"Add a new web app"
3. 选择"Manual configuration"
4. 选择合适的Python版本（推荐3.8+）
5. 点击"Next"完成设置

### 4.1 配置WSGI文件

在Web配置页面中：

1. 找到"Code"部分的"WSGI configuration file"
2. 点击链接编辑WSGI文件
3. 确保文件内容如下：

```python
import sys
import os

# 添加项目目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 从api_server_simple导入handler
from api_server_simple import handler

# 这是PythonAnywhere需要的变量名
application = handler
```

4. 保存文件

### 4.2 配置虚拟环境路径

在Web配置页面中：

1. 找到"Virtualenv"部分
2. 输入虚拟环境路径，例如：
   `/home/你的用户名/myenv`
3. 点击"OK"

### 4.3 设置静态文件（如需要）

如果你的应用需要提供静态文件：

1. 在Web配置页面的"Static files"部分
2. 设置URL路径和对应的本地文件路径
3. 点击"Reload"应用更改

## 5. 配置环境变量

### 5.1 在PythonAnywhere中设置环境变量

1. 在Web配置页面中找到"Environment variables"
2. 添加所需的环境变量
3. 常见环境变量：
   - `PYTHONPATH`: `/home/你的用户名`
   - 其他特定于你的应用的环境变量

### 5.2 使用.env文件（备选）

确保`.env`文件已上传，并且在`api_server_simple.py`中正确加载：

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 你的设置...
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## 6. 初始化向量数据库

如果你的应用需要初始化向量数据库：

1. 在bash控制台中运行：

```bash
source myenv/bin/activate
python -c "from vector_db_utils_simple import initialize_vector_db; initialize_vector_db()"
```

## 7. 启动Web应用

1. 返回"Web"配置页面
2. 点击绿色的"Reload [你的用户名].pythonanywhere.com"按钮
3. 等待几秒钟

## 8. 测试应用

1. 访问你的应用URL：`https://你的用户名.pythonanywhere.com`
2. 测试健康检查端点：`https://你的用户名.pythonanywhere.com/health`
3. 测试问答端点：`https://你的用户名.pythonanywhere.com/ask`

## 9. 查看日志

如果遇到问题，可以查看日志：

1. 在"Web"配置页面中找到"Log files"
2. 点击"Error log"或"Server log"查看详细日志

## 10. 定期维护

### 10.1 重启应用

在代码更新或环境变量更改后，需要重启应用：

1. 访问"Web"配置页面
2. 点击"Reload [你的用户名].pythonanywhere.com"

### 10.2 更新依赖

```bash
source myenv/bin/activate
pip install -r minimal_requirements.txt --upgrade
```

## 11. 故障排除

### 11.1 常见错误及解决方案

- **502 Bad Gateway**: 检查WSGI配置和应用代码
- **ModuleNotFoundError**: 确保依赖已正确安装，检查PYTHONPATH
- **内存使用过高**: 优化代码，减少依赖，考虑使用更简化的实现
- **磁盘空间不足**: 删除不必要的文件，清理临时文件

### 11.2 资源限制

注意，PythonAnywhere免费版有以下限制：
- 每月CPU时间有限（约100秒）
- 磁盘空间有限（约512MB）
- 每小时请求次数有限

如果需要更多资源，考虑升级到付费计划。

---

完成以上步骤后，你的后端服务应该已经成功部署在PythonAnywhere上并正常运行。