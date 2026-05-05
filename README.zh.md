# Anthropic to OpenAI API 代理

生产就绪的 HTTP 代理，转换 Anthropic API 请求到 OpenAI 格式。

## 功能

- 流式和非流式响应
- 工具调用
- 重试逻辑
- Prometheus 指标
- 速率限制
- 结构化日志
- 请求大小限制
- 可选认证

## 快速开始

```bash
export OPENAI_API_KEY=your-key
uvicorn app.main:app --reload
```

## API

- `POST /v1/messages` - 发送消息
- `GET /v1/models` - 列出模型
- `GET /health` - 健康检查
- `GET /metrics` - Prometheus 指标

## 配置

参见 `conf/settings.json`。环境变量覆盖配置。

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