# PythonAnywhere 部署步骤指南

本文档提供在 PythonAnywhere 平台部署江西工业工程职业技术学院 AI 问答系统的详细步骤。

## 1. 项目准备

### 1.1 必要文件
确保以下关键文件已正确配置：

- `api_server_pythonanywhere.py` - 优化的轻量级 API 服务器
- `wsgi.py` - PythonAnywhere WSGI 配置文件
- `pythonanywhere_requirements.txt` - 最小化依赖列表

### 1.2 文件上传方法

在 PythonAnywhere 控制面板中，通过以下方式上传文件：

1. 登录 PythonAnywhere 账户 (dragon01@pythonanywhere.com)
2. 点击顶部导航栏中的 "文件"
3. 选择目标目录 (通常为 `/home/dragon01`)
4. 使用 "上传文件" 功能上传必要文件
5. 或者使用 Git 克隆仓库（如果已托管在代码仓库）

## 2. 虚拟环境设置

### 2.1 创建虚拟环境

在 PythonAnywhere 控制台中执行：

```bash
python3.11 -m venv venv
```

### 2.2 激活虚拟环境

```bash
source venv/bin/activate
```

### 2.3 安装依赖

```bash
pip install -r pythonanywhere_requirements.txt
```

## 3. Web 应用配置

### 3.1 创建/编辑 Web 应用

1. 在 PythonAnywhere 控制面板中，点击 "Web"
2. 点击 "Add a new web app"
3. 选择 "Manual configuration"
4. 选择 Python 3.11
5. 点击 "Next" 完成基本设置

### 3.2 WSGI 配置

在 Web 应用配置页面：

1. **代码部分**：
   - 确保 "Source code" 指向正确的项目目录
   - WSGI 配置文件路径：`/var/www/dragon01_pythonanywhere_com_wsgi.py`

2. **WSGI 配置文件内容**：

```python
# This file contains the WSGI configuration required to serve up your
# web application at http://dragon01.pythonanywhere.com/ 
# It works by setting the variable 'application' to a WSGI handler of some
# description. 

import os
import sys

# add your project directory to the sys.path
sys.path.insert(0, '/home/dragon01')

# import flask app but need to call it "application" for WSGI to work
from api_server_pythonanywhere import app as application

# Uncomment the lines below if you use a virtual environment
activate_this = '/home/dragon01/venv/bin/activate_this.py'
exec(open(activate_this).read(), dict(__file__=activate_this))
```

### 3.3 虚拟环境配置

在 Web 应用配置页面，找到 "Virtualenv" 部分：

- 虚拟环境路径：`/home/dragon01/venv`
- 点击 "Reload dragon01.pythonanywhere.com" 应用配置

### 3.4 静态文件配置

如果需要提供静态文件（如前端页面）：

1. 在 "Static files" 部分添加：
   - URL: `/static/`
   - 目录: `/home/dragon01/static/`

2. 确保 `/home/dragon01/static/` 目录存在并包含所需静态文件

## 4. 环境变量配置

在 Web 应用配置页面，找到 "Environment variables" 部分：

```
ALLOWED_ORIGINS=*
```

## 5. 应用启动与测试

### 5.1 重新加载应用

配置完成后，点击页面顶部的 "Reload dragon01.pythonanywhere.com"

### 5.2 测试 API 端点

- **健康检查**：`http://dragon01.pythonanywhere.com/health`
- **API 文档**：`http://dragon01.pythonanywhere.com/api/docs`
- **问答接口**：`http://dragon01.pythonanywhere.com/api/ask`

### 5.3 测试请求示例

使用 curl 或其他 HTTP 客户端测试：

```bash
curl -X POST "http://dragon01.pythonanywhere.com/api/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "学校地址在哪里", "chat_history": []}'
```

## 6. 日志查看

在 PythonAnywhere 控制台中，可以通过以下命令查看应用日志：

```bash
cat /var/log/dragon01.pythonanywhere.com.error.log
cat /var/log/dragon01.pythonanywhere.com.server.log
```

或者在 Web 应用配置页面的 "Log files" 部分查看。

## 7. 定期维护

- 定期检查日志文件查找错误
- 监控请求统计信息：`http://dragon01.pythonanywhere.com/stats`
- 如需要更新应用，上传新文件后记得重新加载 Web 应用

## 8. 注意事项

1. PythonAnywhere 免费版有资源限制，请确保应用优化资源使用
2. 免费版应用在不活跃时会进入休眠状态
3. 定期备份关键数据
4. 监控应用性能，必要时进行进一步优化

## 9. 故障排除

### 常见问题及解决方案

1. **502 Bad Gateway 错误**
   - 检查 WSGI 配置是否正确
   - 查看错误日志中的具体错误信息
   - 确保虚拟环境中的依赖已正确安装

2. **导入错误**
   - 检查 Python 路径配置
   - 确认相关模块已安装
   - 验证文件权限

3. **应用无法启动**
   - 检查代码语法错误
   - 确认端口配置正确
   - 查看详细错误日志