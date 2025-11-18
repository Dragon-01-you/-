# GitHub 部署江西工业智能问答系统指南

## 一、GitHub 部署可行性分析

该项目支持通过 GitHub 结合第三方平台（如 Vercel、Render、Railway 或 Heroku）进行完整部署。GitHub Pages 仅支持静态网站部署，而该项目包含 Python 后端 API 服务，因此需要额外的后端部署平台。

## 二、完整部署方案

### 方案一：前后端分离部署

#### 1. 前端部署（GitHub Pages）

**步骤：**
1. 将前端文件夹 `OKComputer_江西工业智能问答前端` 单独上传到 GitHub 仓库
2. 在仓库设置中启用 GitHub Pages
3. 将 `index.html` 中所有 API 请求路径从 `/api/ask` 修改为完整的后端 API 地址
4. 确保图标引用路径正确（已修复为相对路径）

**命令：**
```bash
cd OKComputer_江西工业智能问答前端
git init
git add .
git commit -m "initial commit"
git remote add origin <your-repo-url>
git push -u origin main
```

#### 2. 后端部署（Render）

**步骤：**
1. 在 Render 上创建 Web Service
2. 连接 GitHub 仓库
3. 配置构建命令：`pip install -r requirements.txt`
4. 配置启动命令：`uvicorn api_server:app --host 0.0.0.0 --port $PORT`
5. 配置环境变量：
   - MODEL_API_BASE=https://api.siliconflow.cn/v1
   - MODEL_API_KEY=your-key
   - MODEL_NAME=deepseek-ai/DeepSeek-R1-Distill-Qwen-7B

**命令：**
```bash
# 在本地测试后端
pip install -r requirements.txt
python api_server.py
```

### 方案二：单仓库完整部署（Railway）

**步骤：**
1. 将整个项目上传到 GitHub
2. 在 Railway 上创建 Service
3. 配置构建命令：`pip install -r requirements.txt`
4. 配置启动命令：`uvicorn api_server:app --host 0.0.0.0 --port $PORT`
5. 配置环境变量

## 三、常见问题及解决方法

### 问题1：图标显示不上

**原因分析：**
- 图标路径错误
- 静态资源未被正确服务器

**解决方案：**
1. 确保 `index.html` 中图标引用为相对路径：
   ```html
   <link rel="icon" type="image/svg+xml" href="resources/school-logo-final.svg">
   <img src="resources/school-logo-final.svg" alt="江西工业工程职业技术学院校徽" class="logo">
   ```

2. 确保后端正确配置静态文件服务：
   ```python
   app.mount("/static", StaticFiles(directory="./OKComputer_江西工业智能问答前端/resources"), name="static")
   ```

### 问题2：服务暂不可用

**原因分析：**
- 后端服务未启动
- 环境变量配置错误
- CORS 配置问题
- 端口被占用

**解决方案：**
1. 检查后端服务是否正常启动：
   ```bash
   python api_server.py
   ```

2. 检查环境变量配置：
   ```bash
   # 创建 .env 文件
   cp .env.example .env
   # 编辑配置
   vi .env
   ```

3. 检查 CORS 配置是否允许前端域名：
   ```python
   ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
   ```

4. 检查端口是否正确：
   ```bash
   # 默认端口 8000
   uvicorn api_server:app --host 0.0.0.0 --port 8000
   ```

### 问题3：API 请求失败

**原因分析：**
- API 路径错误
- 后端服务未正确响应
- 环境变量未配置

**解决方案：**
1. 确保前端 API 请求路径与后端一致：
   ```javascript
   this.apiUrl = '/api/ask'; // 或完整的后端 API 地址
   ```

2. 检查后端 API 路由是否正确：
   ```python
   @app.post("/api/ask")
   ```

## 四、测试与验证

部署完成后，使用以下方式验证：

1. **前端页面访问**：在浏览器中输入部署后的前端 URL
2. **图标验证**：检查页面左上角校徽是否显示
3. **API 验证**：打开浏览器控制台，查看 API 请求是否成功
4. **功能验证**：输入测试问题，查看是否返回正常响应

## 五、持续集成与自动化部署

使用 GitHub Actions 实现自动化部署：

```yaml
name: Deploy
on: push
jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.8'
      - name: Deploy to Render
        run: |
          curl -X POST "https://api.render.com/v1/services/<service-id>/deploys" \
               -H "Authorization: Bearer ${{ secrets.RENDER_API_KEY }}"
```

## 六、注意事项

1. 敏感信息（如 API 密钥）应通过环境变量配置，不要直接提交到 GitHub
2. 确保部署平台支持 Python 3.8+ 版本
3. 定期更新依赖包以确保安全性
4. 配置适当的日志记录以便排查问题

## 七、总结

通过 GitHub 结合第三方部署平台，可以成功部署江西工业智能问答系统。关键在于正确配置前后端路径、环境变量和 CORS 设置，并确保静态资源能够正确访问。