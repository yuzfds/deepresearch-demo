# 自定义模型支持

本项目已经扩展为支持多种语言模型提供商，而不仅仅是Google Gemini。现在支持本地模型、OpenAI兼容模型和Anthropic Claude，包括自托管解决方案。

## 功能概述

### 🔧 核心功能
- **多提供商支持**: 支持本地模型、OpenAI兼容模型和Anthropic Claude
- **动态模型选择**: 前端可以动态加载和选择不同的模型
- **配置驱动**: 通过YAML配置文件管理模型提供商
- **隐私保护**: 本地模型无需API密钥，数据不离开本地环境
- **结构化输出**: 支持模型的结构化输出能力
- **工具使用**: 支持模型的工具/函数调用能力

### 🎯 支持的模型提供商

#### 1. 本地模型 (默认)
- **模型**: llama-3.2-3b-instruct, llama-3.2-8b-instruct, mistral-7b-instruct等
- **API密钥**: 无需API密钥
- **特色**: 隐私保护，结构化输出，工具使用，本地运行

#### 2. OpenAI兼容模型
- **模型**: gpt-4, gpt-3.5-turbo, 以及其他OpenAI兼容的模型
- **API密钥**: `OPENAI_API_KEY`
- **自定义端点**: 支持本地模型和自托管解决方案
- **特色**: 结构化输出，工具使用（如果模型支持）

## 配置方法

### 1. 环境变量设置

#### 本地模型 (默认)
```bash
# 无需API密钥，但可以设置模型路径
export LLAMA_3B_PATH="models/llama-3.2-3b-instruct.gguf"
export LLAMA_8B_PATH="models/llama-3.2-8b-instruct.gguf"
```

#### OpenAI兼容
```bash
export OPENAI_API_KEY="your-openai-api-key"
# 对于自定义端点
export OPENAI_BASE_URL="https://your-custom-endpoint/v1"
```

### 2. 配置文件

编辑 `backend/config/models.yaml` 文件：

```yaml
providers:
  local:
    name: local
    api_key_env: ""
    default_models:
      query_generator: llama-3.2-3b-instruct
      reflection: llama-3.2-3b-instruct
      answer: llama-3.2-3b-instruct
    description: Local models using Llama.cpp or transformers
    supports_structured_output: true
    supports_tools: true
    max_retries: 2

  openai_compatible:
    name: openai_compatible
    api_key_env: OPENAI_API_KEY
    base_url: https://api.openai.com/v1
    default_models:
      query_generator: gpt-4
      reflection: gpt-4
      answer: gpt-4
    description: OpenAI compatible models
    supports_structured_output: true
    supports_tools: true
    max_retries: 2
```

### 3. 添加新的模型提供商

要添加新的模型提供商，请按照以下步骤：

1. **创建提供者类** (在 `backend/src/agent/models/` 目录下):
```python
from .base import ModelProvider, ModelProviderConfig

class CustomProvider(ModelProvider):
    def get_model(self, model_name: str, **kwargs):
        # 实现模型创建逻辑
        pass

    def list_available_models(self):
        # 返回支持的模型列表
        pass

    def validate_model_name(self, model_name: str):
        # 验证模型名称
        pass
```

2. **在配置文件中添加提供者**:
```yaml
  custom_provider:
    name: custom_provider
    api_key_env: CUSTOM_API_KEY
    base_url: https://api.custom.com/v1
    default_models:
      query_generator: custom-model
      reflection: custom-model
      answer: custom-model
    description: Custom provider models
    supports_structured_output: true
    supports_tools: false
    max_retries: 2
```

3. **在工厂中注册提供者** (如果需要):
```python
# 在 factory.py 的 _load_configs 方法中添加
elif provider_name == 'custom_provider':
    self.register_provider(CustomProvider, config)
```

## 使用方法

### 1. 启动应用

```bash
# 启动后端
cd backend
python -m uvicorn src.agent.app:app --host 0.0.0.0 --port 2024

# 启动前端
cd frontend
npm run dev
```

### 2. 前端模型选择

前端会自动加载可用的模型提供商和模型。在用户界面中：

1. **模型选择器**: 显示所有可用的模型，按提供商分组
2. **动态加载**: 模型列表从后端API动态获取
3. **视觉区分**: 不同提供商的模型使用不同的图标和颜色

### 3. API端点

新增的API端点：

- `GET /api/models/providers` - 获取所有可用的模型提供商和模型
- `GET /api/models/default` - 获取默认模型配置

## 技术架构

### 后端架构

```
backend/src/agent/models/
├── base.py              # 抽象基类和接口定义
├── factory.py           # 模型工厂，管理提供商实例
├── local_provider.py    # 本地模型提供者实现
├── openai_compatible_provider.py  # OpenAI兼容提供者实现
└── __init__.py          # 模块导出
```

### 核心组件

1. **ModelProvider (抽象基类)**
   - 定义了所有模型提供商必须实现的接口
   - 提供通用的模型功能（结构化输出、工具使用等）

2. **ModelFactory (工厂类)**
   - 管理所有模型提供商实例
   - 提供统一的模型获取接口
   - 支持配置驱动的提供商注册

3. **Configuration (配置类)**
   - 扩展支持多提供商配置
   - 提供 `provider/model` 格式的模型引用
   - 保持向后兼容性

### 前端架构

```
frontend/src/components/InputForm.tsx
├── 动态模型加载          # 从API获取可用模型
├── 提供者分组显示        # 按提供商组织模型列表
├── 模型选择器           # 用户友好的模型选择界面
└── 加载状态处理         # 处理模型加载状态
```

## 限制和注意事项

### 当前限制

1. **搜索功能**: 使用Tavily Search API，所有提供商都支持
2. **结构化输出**: 并非所有模型都支持结构化输出
3. **工具使用**: 某些模型可能不支持工具/函数调用
4. **硬件要求**: 本地模型需要GPU或强大的CPU支持

### 性能考虑

1. **模型切换**: 不同模型可能有不同的性能特征
2. **API限制**: 各提供商可能有不同的速率限制
3. **成本**: 不同模型的成本可能差异很大

### 安全考虑

1. **API密钥**: 确保API密钥安全存储
2. **端点验证**: 验证自定义端点的安全性
3. **访问控制**: 考虑添加模型访问权限控制

## 故障排除

### 常见问题

1. **模型加载失败**
   - 检查API密钥是否正确设置
   - 验证网络连接
   - 查看后端日志

2. **模型选择器为空**
   - 检查后端API是否正常运行
   - 验证 `/api/models/providers` 端点
   - 检查网络连接

3. **配置文件问题**
   - 验证YAML语法
   - 检查文件路径
   - 确认配置文件权限

### 调试方法

1. **后端调试**:
```bash
cd backend
python test_models.py  # 运行模型测试
```

2. **前端调试**:
   - 打开浏览器开发者工具
   - 检查网络请求
   - 查看控制台错误

3. **API测试**:
```bash
curl http://localhost:2024/api/models/providers
curl http://localhost:2024/api/models/default
```

## 未来扩展

### 计划中的功能

1. **更多提供商支持**
   - Anthropic Claude
   - 本地Ollama模型
   - 更多Hugging Face模型
   - 量化模型支持

2. **高级功能**
   - 模型性能比较
   - 智能模型选择
   - 成本优化建议

3. **管理界面**
   - Web配置界面
   - 模型测试工具
   - 使用统计面板

### 贡献指南

欢迎贡献新的模型提供商或改进现有功能：

1. Fork项目
2. 创建功能分支
3. 实现新的提供商或功能
4. 添加测试和文档
5. 提交Pull Request

## 总结

这个自定义模型支持系统为项目提供了极大的灵活性和可扩展性。通过抽象的提供商架构，用户可以轻松添加新的模型提供商，同时保持现有功能的完整性。系统设计考虑了向后兼容性、性能和安全性，为未来的扩展打下了坚实的基础。