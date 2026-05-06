# xopenai

生产就绪的 HTTP 代理，转换 Anthropic API 请求到 OpenAI 格式。

## 功能

- 流式和非流式响应
- 工具调用
- 重试逻辑
- Prometheus 指标
- 速率限制
- 结构化日志（每日轮转）
- 请求大小限制
- 可选认证

## 快速开始

```bash
# 复制示例配置文件
cp conf/settings.json.example conf/settings.json

# 编辑 settings.json 添加 API 密钥
# 或使用环境变量
export OPENAI__API_KEY=your-key

uvicorn app.main:app --reload
```

## API

- `POST /v1/messages` - 发送消息
- `GET /v1/models` - 列出模型
- `GET /health` - 健康检查
- `GET /metrics` - Prometheus 指标

## 配置

代理使用 `conf/settings.json` 进行配置。首次使用：

```bash
cp conf/settings.json.example conf/settings.json
```

然后编辑 `conf/settings.json` 配置：

- **OpenAI API**：默认使用 Qwen OpenAI 兼容 API (`https://coding.dashscope.aliyuncs.com/v1`)
- **模型映射**：将 Anthropic 模型名称映射到后端模型（默认：`claude-3-5-sonnet-20241022` → `qwen3.6-plus`）
- **安全配置**：可选 API 密钥认证
- **代理设置**：重试、超时、速率限制

环境变量覆盖配置：
```bash
OPENAI__API_KEY=sk-dashscope-your-key
OPENAI__API_ENDPOINT=https://coding.dashscope.aliyuncs.com/v1
```

查看 `.env.example` 了解所有可用环境变量。

## 日志

日志存储在 `logs/` 目录中，采用结构化 JSON 格式。日志文件每天午夜轮转，保留 7 天。日志格式：

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [module:line] message | {"extra": "fields"}
```

## 测试

```bash
pytest tests/
```

## Docker 部署

```bash
docker-compose up
```

## 许可证

MIT