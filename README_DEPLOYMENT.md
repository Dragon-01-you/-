# 江西工业工程职业技术学院 AI 助手后端部署指南

## 项目概述

这是一个简化版的AI助手后端服务，使用FastAPI构建，包含轻量级的向量数据库功能。该项目经过优化，可以在PythonAnywhere等资源受限的环境中运行。

## 主要组件

- **api_server_simple.py**: 轻量级FastAPI后端服务
- **vector_db_utils_simple.py**: 简化版向量数据库工具
- **wsgi.py**: PythonAnywhere WSGI配置文件
- **minimal_requirements.txt**: 最小依赖列表
- **江西工业工程职业技术学院_数据仓库**: 包含系统所需的文档数据

## 部署准备

所有部署所需的文件都已准备就绪，可以通过执行以下命令验证：

```bash
python verify_deployment_files.py
```

## 部署步骤

详细的部署步骤请参考：
- **[DEPLOYMENT_GUIDE_PYTHONANYWHERE.md](./DEPLOYMENT_GUIDE_PYTHONANYWHERE.md)**: PythonAnywhere部署详细指南

## 快速部署摘要

1. 在PythonAnywhere创建账户并登录
2. 创建虚拟环境并激活
3. 上传项目文件
4. 安装依赖: `pip install -r minimal_requirements.txt`
5. 创建Web应用并配置WSGI
6. 设置虚拟环境路径
7. 初始化向量数据库（如果需要）
8. 重启Web应用

## 验证部署

部署完成后，可以通过以下端点测试服务：

- 健康检查: `https://你的用户名.pythonanywhere.com/health`
- 问答接口: `https://你的用户名.pythonanywhere.com/ask`

## 故障排除

如有问题，请查看PythonAnywhere的错误日志，或参考部署指南中的故障排除部分。