# 下一步操作指南

## 一、选择部署方案

根据您的需求，选择以下其中一种部署方案：

### 方案A：前后端分离部署（推荐）
- 前端部署到 GitHub Pages
- 后端部署到 Render 或 Railway

### 方案B：单仓库完整部署
- 将整个项目部署到 Render 或 Railway

## 二、方案A：前后端分离部署

### 1. 前端部署（GitHub Pages）

**需要上传的文件：**
- `OKComputer_江西工业智能问答前端` 文件夹下的所有文件

**步骤：**
1. 创建一个新的 GitHub 仓库（如 `jxiee-ai-frontend`）
2. 将 `OKComputer_江西工业智能问答前端` 文件夹上传到该仓库
3. 在仓库设置中启用 GitHub Pages
4. 等待 GitHub Pages 部署完成（通常需要几分钟）

### 2. 后端部署（Render）

**需要上传的文件：**
- 除 `OKComputer_江西工业智能问答前端` 文件夹外的所有文件

**步骤：**
1. 创建一个新的 GitHub 仓库（如 `jxiee-ai-backend`）
2. 将以下文件上传到该仓库：
   - `api_server.py`
   - `requirements_api.txt`
   - `.env.example`
   - `wsgi.py`
   - `utils/` 文件夹
   - `services/` 文件夹
   - `models/` 文件夹
   - `江西工业工程职业技术学院_数据仓库/` 文件夹
3. 在 Render 上创建 Web Service
4. 连接该 GitHub 仓库
5. 配置环境变量（参考 `.env.example`）
6. 部署完成后获取后端 API 地址

### 3. 连接前后端

**步骤：**
1. 编辑前端仓库中的 `main.js` 文件
2. 将 API URL 从 `/api/ask` 改为后端 API 地址
3. 提交并推送更改

## 三、方案B：单仓库完整部署

### 需要上传的文件：
- 所有项目文件（包括 `OKComputer_江西工业智能问答前端` 文件夹）

### 步骤：
1. 创建一个新的 GitHub 仓库（如 `jxiee-ai-system`）
2. 将所有项目文件上传到该仓库
3. 在 Render 或 Railway 上创建 Web Service
4. 连接该 GitHub 仓库
5. 配置构建命令：`pip install -r requirements_api.txt`
6. 配置启动命令：`uvicorn api_server:app --host 0.0.0.0 --port $PORT`
7. 配置环境变量（参考 `.env.example`）
8. 部署完成后访问应用

## 四、环境变量配置

无论选择哪种方案，都需要配置以下环境变量：

```env
# 大模型API配置
MODEL_API_BASE=https://api.siliconflow.cn/v1
MODEL_API_KEY=sk-xxx
MODEL_NAME=deepseek-ai/DeepSeek-R1-Distill-Qwen-7B
MODEL_TIMEOUT=100

# 应用配置
APP_SECRET_KEY=your_app_secret_key_here
DEBUG=False
```

## 五、验证部署

部署完成后，验证以下内容：
1. 前端页面能正常加载
2. 图标能正常显示
3. API 请求能正常响应
4. 能正常提问和获取回答

## 六、常见问题

### 1. 图标显示问题
- 检查 `index.html` 中的图标引用路径是否正确
- 确保静态文件服务已正确配置

### 2. 服务不可用
- 检查后端服务是否正常运行
- 检查环境变量配置是否正确
- 检查 API 请求路径是否正确

### 3. 回答不正确
- 检查大模型 API 配置是否正确
- 检查数据仓库是否包含相关信息

如果遇到其他问题，请参考 `GITHUB_DEPLOYMENT_GUIDE.md` 中的详细说明。