# LangChain Study Notes

这个目录保留的是我学习 LangChain Essentials 时实际会阅读、运行和修改的 Python 内容。

## 说明

- notebook 以官方教程为基础，并加入了我自己的中文注释
- `env_utils.py` 补强了环境变量和依赖检查
- `l5_local_mcp_server.py` 用本地 MCP 服务替换了已经过时的官方 MCP 示例
- 部分官方图片资源没有继续保留，不影响 notebook 代码运行

## 环境准备

建议使用 Python `3.11` 到 `3.13`。

### 1. 创建 `.env`

```bash
cp example.env .env
```

然后填入你自己的模型和 LangSmith 配置。

### 2. 安装依赖

这个目录保留 `pyproject.toml` 作为环境入口，推荐直接用 `uv`：

```bash
uv sync
```

如果你使用别的包管理方式，也可以按 `pyproject.toml` 中的依赖自行安装。

### 3. 运行 notebook

```bash
uv run jupyter lab
```

## Lessons

- `L1_fast_agent.ipynb`: 用 `create_agent` 快速搭建 agent
- `L2_messages.ipynb`: 理解消息在 agent 中的流转
- `L3_streaming.ipynb`: 学习流式输出
- `L4_tools.ipynb`: 学习工具调用
- `L5_tools_with_mcp.ipynb`: 学习 MCP 接入，配套本地服务为 `l5_local_mcp_server.py`
- `L6_memory.ipynb`: 学习记忆与状态管理
- `L7_structuredOutput.ipynb`: 学习结构化输出
- `L8_dynamic.ipynb`: 学习动态系统提示词
- `L9_HITL.ipynb`: 学习 Human-in-the-Loop

## Studio

`studio/` 目录保留了 SQL agent 的实战示例：

- `langgraph.json`
- `sql_agent1.py`
- `sql_agent2.py`
- `env_utils.py`
- `Chinook.db`

运行前先把根目录下准备好的 `.env` 复制到 `studio/`，再启动：

```bash
cd studio
uv run langgraph dev
```
