# 多模型支持的全栈LangGraph研究代理

这个项目展示了一个使用React前端和LangGraph后端代理的全栈应用程序。代理旨在通过对用户查询进行综合研究，动态生成搜索术语，使用Google搜索查询网络，反思结果以识别知识差距，并迭代优化搜索，直到能够提供带有引用的、有充分支持的答案。此应用程序作为使用LangGraph和多种语言模型构建研究增强型对话AI的示例。

<img src="./app.png" title="多模型全栈LangGraph" alt="多模型全栈LangGraph" width="90%">

## 功能特性

- 💬 **全栈应用**: React前端和LangGraph后端的完整应用
- 🧠 **智能代理**: 由LangGraph代理驱动的高级研究和对话AI
- 🔍 **动态搜索**: 使用多种语言模型动态生成搜索查询
- 🌐 **网络研究**: 通过Google Search API集成网络研究
- 🤔 **反思推理**: 识别知识差距并优化搜索的反思推理
- 📄 **引用答案**: 从收集的来源生成带有引用的答案
- 🔄 **热重载**: 开发期间前端和后端的热重载
- 🎯 **多模型支持**: 支持OpenAI兼容模型、Anthropic Claude和自定义端点
- ⚙️ **动态配置**: 运行时切换不同的模型提供商
- 🔧 **可扩展性**: 易于添加新的模型提供商

## 项目结构

项目分为两个主要目录：

-   `frontend/`: 包含使用Vite构建的React应用程序。
-   `backend/`: 包含LangGraph/FastAPI应用程序，包括研究代理逻辑。

### 详细结构

```
deepresearch-demo/
├── backend/                         # 后端服务
│   ├── src/
│   │   └── agent/
│   │       ├── models/             # 模型管理
│   │       │   ├── __init__.py
│   │       │   ├── base.py         # 基础提供者接口
│   │       │   ├── factory.py      # 模型工厂
│   │       │   └── configuration.py # 配置管理
│   │       ├── graph.py            # LangGraph工作流
│   │       ├── app.py              # FastAPI应用
│   │       └── configuration.py    # 应用配置
│   ├── config/
│   │   └── models.yaml             # 模型配置（已清空）
│   └── requirements.txt
├── frontend/                        # 前端应用
│   ├── src/
│   │   ├── components/
│   │   │   ├── InputForm.tsx       # 输入表单
│   │   │   ├── ResearchResults.tsx # 结果展示
│   │   │   └── ui/                 # UI组件
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## 快速开始：开发和本地测试

按照以下步骤在本地运行应用程序进行开发和测试。

### 1. 系统要求

-   Node.js 和 npm (或 yarn/pnpm)
-   Python 3.11+
-   **API密钥**: 后端代理需要语言模型API密钥

#### 支持的模型提供商

**OpenAI兼容模型 (默认):**
1.  导航到 `backend/` 目录。
2.  通过复制 `backend/.env.example` 文件创建 `.env` 文件。
3.  配置API密钥：
   - 对于OpenAI API：`OPENAI_API_KEY="YOUR_OPENAI_API_KEY"`
   - 对于本地端点（如Ollama、LM Studio等）：`OPENAI_BASE_URL="http://localhost:11434/v1"`
4.  支持的模型包括GPT-4、GPT-3.5-turbo以及任何OpenAI兼容的模型。

**Anthropic Claude:**
1.  在 `.env` 文件中添加：`ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY"`
2.  在 `models.yaml` 中启用Anthropic提供者配置

**AICloud GLM-4.5:**
1.  在 `.env` 文件中添加：`AICLOUD_API_KEY="YOUR_AICLOUD_API_KEY"`
2.  GLM-4.5模型已预配置在 `models.yaml` 中，提供者名称为 `aicloud_glm45`
3.  支持的模型：glm-4.5
4.  模型端点：https://aicloud.oneainexus.cn:30013/inference/aicloud-kouhuashuai/glm4-5/v1

**Web搜索API:**
1.  在 `.env` 文件中添加：`TAVILY_API_KEY="YOUR_TAVILY_API_KEY"`
2.  从 [Tavily](https://tavily.com/) 获取API密钥

### 2. 安装依赖

#### 后端:

```bash
cd backend
pip install .
```

#### 前端:

```bash
cd frontend
npm install
```

### 3. 运行开发服务器

#### 后端和前端同时运行:

```bash
make dev
```
这将运行后端和前端开发服务器。在浏览器中打开前端开发服务器URL（例如 `http://localhost:5173/app`）。

#### 分别运行:

**后端:**
在 `backend/` 目录中打开终端并运行 `langgraph dev`。后端API将在 `http://127.0.0.1:2024` 可用。它还会在浏览器中打开LangGraph UI。

**前端:**
在 `frontend/` 目录中打开终端并运行 `npm run dev`。前端将在 `http://localhost:5173` 可用。

### 4. 模型配置

**注意：所有模型提供商配置已被删除。**

`backend/config/models.yaml` 文件现在为空：

```yaml
providers:
  # 所有提供商配置已被移除
```

### 5. 测试模型系统

**注意：由于所有模型提供商已被删除，模型系统测试将无法正常工作。**

## 后端代理工作原理（高级概述）

后端的核心是在 `backend/src/agent/graph.py` 中定义的LangGraph代理。它遵循以下步骤：

<img src="./agent.png" title="代理流程" alt="代理流程" width="50%">

1.  **生成初始查询:** 基于您的输入，使用配置的语言模型生成一组初始搜索查询。
2.  **网络研究:** 对于每个查询，使用Tavily Search API查找相关网页。
3.  **反思与知识差距分析:** 代理分析搜索结果以确定信息是否充分或是否存在知识差距。它使用配置的模型进行此反思过程。
4.  **迭代优化:** 如果发现差距或信息不足，它会生成后续查询并重复网络研究和反思步骤（达到配置的最大循环次数）。
5.  **最终答案:** 一旦研究被认为充分，代理会将收集的信息合成为一个连贯的答案，包括来自网络来源的引用，使用配置的模型。

### 多模型架构

代理现在支持多种语言模型，通过模型提供者系统实现：

- **模型工厂**: 统一管理所有模型提供商实例
- **抽象接口**: 为所有模型提供商提供统一的接口
- **动态选择**: 运行时根据配置选择不同的模型
- **能力检测**: 自动检测模型是否支持结构化输出和工具使用

### 支持的模型提供商

#### OpenAI兼容模型
- **模型**: gpt-4, gpt-3.5-turbo, 以及任何OpenAI兼容的模型
- **特色**: 结构化输出，工具使用，支持自定义端点（如Ollama、LM Studio等）
- **配置**: `OPENAI_API_KEY` 和可选的 `OPENAI_BASE_URL` 环境变量

#### Anthropic Claude
- **模型**: claude-3-sonnet, claude-3-opus等
- **特色**: 高性能推理，结构化输出，工具使用
- **配置**: `ANTHROPIC_API_KEY` 环境变量（需要在models.yaml中启用）

#### AICloud GLM-4.5
- **模型**: glm-4.5
- **特色**: 智能对话，结构化输出，工具使用，中文优化
- **配置**: `AICLOUD_API_KEY` 环境变量，已预配置在models.yaml中
- **端点**: https://aicloud.oneainexus.cn:30013/inference/aicloud-kouhuashuai/glm4-5/v1

## CLI示例

对于快速的一次性问题，您可以从命令行执行代理。脚本 `backend/examples/cli_research.py` 运行LangGraph代理并打印最终答案：

```bash
cd backend
python examples/cli_research.py "可再生能源的最新趋势是什么？"
```

### 使用特定模型

您可以通过设置环境变量来使用特定的模型提供商：

```bash
# 使用OpenAI模型（默认）
export OPENAI_API_KEY="your-openai-api-key"
python examples/cli_research.py "人工智能的发展历史"

# 使用自定义端点（如Ollama）
export OPENAI_API_KEY="not-needed"  # Ollama通常不需要API密钥
export OPENAI_BASE_URL="http://localhost:11434/v1"  # Ollama默认端口
python examples/cli_research.py "量子计算的最新进展"

# 使用AICloud GLM-4.5模型
export AICLOUD_API_KEY="your-aicloud-api-key"
python examples/cli_research.py "人工智能的发展历史" --reasoning-model aicloud_glm45/glm-4.5
```


## 部署

在生产环境中，后端服务器提供优化的静态前端构建。LangGraph需要Redis实例和Postgres数据库。Redis用作发布-订阅代理，以实现从后台运行的流式实时输出。Postgres用于存储助手、线程、运行、持久化线程状态和长期记忆，并以"精确一次"的语义管理后台任务队列的状态。有关如何部署后端服务器的更多详细信息，请查看[LangGraph文档](https://langchain-ai.github.io/langgraph/concepts/deployment_options/)。下面是如何构建包含优化的前端构建和后端服务器的Docker镜像并通过`docker-compose`运行它的示例。

_注意：对于docker-compose.yml示例，您需要LangSmith API密钥，可以从[LangSmith](https://smith.langchain.com/settings)获取。_

_注意：如果您不运行docker-compose.yml示例或不将后端服务器暴露给公共互联网，您应该将`frontend/src/App.tsx`文件中的`apiUrl`更新为您的主机。当前`apiUrl`设置为`http://localhost:8123`用于docker-compose或`http://localhost:2024`用于开发。_

### 1. 构建Docker镜像

   从**项目根目录**运行以下命令：
   ```bash
   docker build -t multi-model-langgraph -f Dockerfile .
   ```

### 2. 运行生产服务器

   ```bash
   OPENAI_API_KEY=<your_openai_api_key> OPENAI_BASE_URL=<your_openai_base_url> TAVILY_API_KEY=<your_tavily_api_key> LANGSMITH_API_KEY=<your_langsmith_api_key> docker-compose up
   ```

在浏览器中导航到 `http://localhost:8123/app/` 查看应用程序。API将在 `http://localhost:8123` 可用。

### 多模型生产配置

在生产环境中，您可以通过环境变量配置多个模型提供商：

```bash
# OpenAI兼容配置
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1

# 自定义端点配置（可选）
# OPENAI_BASE_URL=http://localhost:11434/v1  # Ollama

# Web搜索配置
TAVILY_API_KEY=your_tavily_key

# 可选：自定义模型配置文件路径
MODEL_CONFIG_PATH=/app/config/custom-models.yaml
```

### 配置文件挂载

您可以在生产环境中挂载自定义的模型配置：

```yaml
# docker-compose.yml 补充
volumes:
  - ./config/models.yaml:/app/config/models.yaml:ro
```

### 健康检查

应用程序包含健康检查端点：

```bash
# 检查模型系统状态
curl http://localhost:8123/api/models/providers

# 检查默认模型配置
curl http://localhost:8123/api/models/default
```

## 使用的技术栈

### 前端技术
- [React](https://reactjs.org/) (配合 [Vite](https://vitejs.dev/)) - 前端用户界面
- [Tailwind CSS](https://tailwindcss.com/) - 样式框架
- [Shadcn UI](https://ui.shadcn.com/) - UI组件库
- [TypeScript](https://www.typescriptlang.org/) - 类型安全
- [Lucide React](https://lucide.dev/) - 图标库

### 后端技术
- [LangGraph](https://github.com/langchain-ai/langgraph) - 构建后端研究代理
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能Web框架
- [Python](https://www.python.org/) - 后端编程语言
- [Pydantic](https://docs.pydantic.dev/) - 数据验证和设置管理
- [PyYAML](https://pyyaml.org/) - YAML配置文件处理

### 语言模型集成
- [OpenAI](https://openai.com/) - GPT模型支持和OpenAI兼容API
- [LangChain](https://python.langchain.com/) - 语言模型框架
  - `langchain-core` - 核心抽象
  - `langchain-openai` - OpenAI集成
  - `langchain-anthropic` - Anthropic Claude集成
- [Tavily](https://tavily.com/) - Web搜索API

### 基础设施
- [Docker](https://www.docker.com/) - 容器化部署
- [Redis](https://redis.io/) - 发布-订阅消息传递
- [PostgreSQL](https://www.postgresql.org/) - 数据持久化
- [Uvicorn](https://www.uvicorn.org/) - ASGI服务器

## 许可证

本项目采用Apache License 2.0许可。详情请参见[LICENSE](LICENSE)文件。

## 贡献

欢迎贡献！请阅读[CUSTOM_MODELS.md](CUSTOM_MODELS.md)了解如何添加新的模型提供商或改进现有功能。

## 支持

如果您遇到问题或有疑问，请：

1. 查看[CUSTOM_MODELS.md](CUSTOM_MODELS.md)文档
2. 运行 `python test_models.py` 测试模型系统
3. 检查配置文件和环境变量设置
4. 查看后端日志以获取详细错误信息

## 更新日志

### v3.0.0 - OpenAI兼容架构更新
- ✨ 移除Gemini依赖，专注于OpenAI兼容架构
- 🔧 移除本地模型逻辑，支持自定义OpenAI标准端点
- 🎯 集成Tavily Web搜索API，所有提供者统一使用
- ⚙️ 简化配置，支持Ollama、LM Studio等本地端点
- 📱 更新前端UI和图标
- 📚 重构文档，专注于OpenAI兼容配置

### v2.0.0 - 多模型支持
- ✨ 添加了多模型提供商支持
- 🔧 实现了模型抽象层和工厂模式
- 🎯 支持Google Gemini和OpenAI兼容模型
- ⚙️ 动态模型配置和选择
- 📱 更新前端UI支持模型选择
- 📚 添加了详细的文档和示例

### v1.0.0 - 初始版本
- 🚀 基本的LangGraph研究代理
- 💬 React前端界面
- 🔍 Google Search API集成
- 📄 引用和答案生成
