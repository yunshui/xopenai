# 经验教训

## 设计阶段

- 使用 brainstorming 技能明确了需求
- 设计文档经过3轮审查才最终批准
- 模型映射、认证、错误处理等关键功能需要在设计中明确

## 计划阶段

- 实现计划经过2轮审查
- 主要问题：导入错误、缺少字段、测试不完整
- 修复所有问题后才获得批准

## 执行阶段

- 使用 subagent-driven-development 技能执行
- Task 1 执行顺利，审查流程有效
- Task 2 开始后被中断
- Task 3 修复：将 RotatingFileHandler 改为 TimedRotatingFileHandler 以实现每日轮转，而非基于文件大小轮转

## 日志设计

- **结构化日志格式**：使用自定义 StructuredFormatter 统一输出格式，包含时间戳、级别、模块:行号、客户端IP、请求ID
- **追踪性**：每个请求分配 UUID，在所有日志中记录 request_id，便于跨请求链路追踪和问题排查
- **每日轮转**：使用 TimedRotatingFileHandler 按日轮转（而非按大小），保留7天，文件格式 xopenai-YYYY-MM-DD.log
- **灵活配置**：通过 LOG_LEVEL 环境变量配置级别（DEBUG/INFO/WARNING/ERROR）
- **双输出**：同时输出到控制台和文件，控制台使用 stdout

## 技术决策

| 决策 | 选择 | 原因 |
|------|------|------|
| Web 框架 | FastAPI | 异步、高性能、自动文档 |
| HTTP 客户端 | httpx | 异步、连接池 |
| 配置管理 | pydantic-settings | 类型安全、环境变量支持 |
| 测试框架 | pytest + pytest-asyncio | 异步测试支持 |
| HTTP Mocking | respx | 支持流式响应 |
| 指标 | prometheus-client | 标准指标格式 |