# 搜索API集成功能说明

本文档详细介绍了江西工业工程职业技术学院智能问答系统中新增的搜索API集成功能。

## 一、功能概述

为了增加数据来源和提高回答的可靠性，我们在系统中集成了多种搜索API选项，包括：

1. **默认模拟搜索API** - 内置的免费搜索功能，提供基础的搜索结果
2. **古谷数据API** - 可选的专业教育数据API，提供大学专业相关信息
3. **SERP API** - 可选的学术搜索API，可连接Google Scholar等学术资源

## 二、配置方法

所有搜索API配置都集中在`api_server.py`文件中的`SEARCH_CONFIG`字典中，用户可以根据需要启用或禁用不同的API：

```python
# 搜索API配置 - 支持多种搜索来源
SEARCH_CONFIG = {
    # 古谷数据API配置（提供大学专业数据）
    "gugudata": {
        "enabled": False,  # 设置为True启用
        "api_key": "",    # 在此处填写您的API密钥
        "endpoint": "https://api.gugudata.com/metadata/ceemajor",
        "timeout": 30
    },
    # 自定义搜索引擎配置（可替换为其他搜索API）
    "custom_search": {
        "enabled": True,  # 设置为True启用
        "search_engine": "mock"  # 可选值: "mock", "serpapi"
    },
    # SERP API配置（用于Google Scholar等搜索，如果需要）
    "serpapi": {
        "enabled": False,  # 设置为True启用
        "api_key": "",    # 在此处填写您的API密钥
        "timeout": 30
    }
}
```

### 2.1 默认模拟搜索API

这是系统默认启用的免费搜索功能，无需额外配置即可使用。系统会根据用户的问题生成相关的模拟搜索结果，增强数据来源。

### 2.2 古谷数据API（可选付费）

古谷数据API提供大学专业相关的详细信息。要启用此功能：

1. 将`SEARCH_CONFIG["gugudata"]["enabled"]`设置为`True`
2. 在`SEARCH_CONFIG["gugudata"]["api_key"]`中填写您的API密钥

> 注意：此API为付费服务，需要在古谷数据官网注册并获取API密钥。

### 2.3 SERP API（可选付费）

SERP API可以连接到Google Scholar等学术资源，提供学术文献搜索功能。要启用此功能：

1. 将`SEARCH_CONFIG["serpapi"]["enabled"]`设置为`True`
2. 在`SEARCH_CONFIG["serpapi"]["api_key"]`中填写您的API密钥
3. 确保`SEARCH_CONFIG["custom_search"]["search_engine"]`设置为`"serpapi"`

> 注意：此API为付费服务，需要在SERP API官网注册并获取API密钥。

## 三、工作原理

搜索API集成功能通过以下方式工作：

1. **自动触发搜索** - 系统会为每个问题自动调用搜索API，无论向量数据库返回的结果如何
2. **增强数据来源** - 搜索结果会与向量数据库的结果合并，丰富回答的上下文信息
3. **优化错误处理** - 当大模型API调用失败时，系统会根据问题类型生成更有针对性的本地回答
4. **智能结果筛选** - 系统会避免重复的来源信息，确保每个来源只显示一次

## 四、测试验证

系统集成了搜索API后，您可以通过运行测试脚本来验证功能：

```bash
python comprehensive_test.py
```

在测试结果中，您应该能看到每个问题的来源列表现在包含了搜索API的结果，例如：

```
来源列表: 模拟文档源 1, 模拟文档源 2, 模拟文档源 3, 搜索API 1, 搜索API 2, 搜索API 3
```

## 五、自定义扩展

如果您想集成其他搜索API，可以按照以下步骤操作：

1. 在`SEARCH_CONFIG`字典中添加新的API配置项
2. 在`search_api_integration`函数中添加相应的API调用逻辑
3. 确保错误处理机制能够优雅地处理API调用失败的情况

## 六、注意事项

1. 使用第三方API时，请注意遵守相关服务的使用条款和限制
2. 付费API需要注意使用成本，建议设置合理的调用频率限制
3. 系统已内置错误处理机制，即使API调用失败，也能提供基本的回答功能
4. 搜索结果的质量取决于API的性能和配置，建议定期测试和评估

## 七、故障排除

如果遇到搜索API相关的问题，可以通过查看系统日志来诊断：

```bash
# 查看API服务器日志
python api_server.py
```

常见问题及解决方案：

1. **API密钥无效** - 检查API密钥是否正确填写，是否过期
2. **API调用超时** - 可以调整`timeout`参数增加超时时间
3. **搜索结果不相关** - 可能需要调整搜索关键词处理逻辑或选择更合适的API

通过合理配置和使用搜索API集成功能，您可以显著提高智能问答系统的数据来源多样性和回答可靠性。