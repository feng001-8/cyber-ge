---
title: "Harness Engineering：给 AI 套上缰绳"
description: "围绕 AI 模型的外部驾驭系统——系统提示、技能模块、工具扩展、子代理和钩子——定义了五个可直接调整的配置点。同一模型通过优化 Harness 可实现近 2 倍性能提升。"
pubDate: "2026-03-27"
tags: ["AI", "开发工具", "方法论", "Agent"]
hexagram: "䷂"
element: "metal"
---

**TL;DR:** AI 模型是「大脑」，但光有大脑不够——它需要一套外部系统来约束行为、管理上下文、自动验证结果。这套系统叫 Harness，由五个组件构成：系统提示、Skills、MCP 工具、子代理和 Hooks。优化 Harness 比换模型更有效。

> **前置知识**：本文假设读者使用过 Claude Code、Cursor 等 AI 编程助手，了解基本的 prompt 工程概念。如果对 AI 协作方法论不熟悉，建议先阅读 [Spec 驱动开发](/blog/spec-driven-development)。

---

## 从一个实验说起

同一个 AI 模型，同一套编码基准测试，第一次得分 42%，第二次 78%。唯一变量不是提示词、不是模型、不是温度设置——是模型外面那套系统。

Mitchell Hashimoto（Terraform 作者）把这个现象总结得很直接：

> "When the AI makes a mistake, don't pray for a better model—design a system that makes it impossible for the AI to make that mistake again."

他不是在说理论。LangChain 团队靠改 Harness（不是换模型）大幅提升了 Agent 表现。OpenAI Codex 团队的经验类似。历史上没有任何一次模型升级能带来接近 2 倍的编码性能提升——但 Harness 优化做到了。

这背后的逻辑不复杂：模型已经接近商品化，Claude、GPT、Gemini 人人都能用。但你的 Harness 是基于你的代码库、你的团队规范、你踩过的坑构建的——这才是差异化的来源。

---

## Harness 是什么

Harness 是围绕 AI 模型的一整套外部配置：规则文件、技能模块、工具连接、子代理、自动检查脚本。

用计算机系统来类比：

- **Model** = CPU——原始算力
- **Context Window** = RAM——有限的工作内存
- **Harness** = 操作系统——管理上下文、调度工具、验证 I/O
- **Agent** = 应用程序——在 OS 之上跑的业务逻辑

大多数人盯着 CPU（模型）看，但真正决定体验的往往是 OS。同样的硬件，调度好和调度差，效果完全不同。

---

## 五个可调整的组件

Harness 不是抽象概念，它由五个具体的、可以独立改的组件构成。

### 系统提示（CLAUDE.md / AGENTS.md）

仓库根目录下的 Markdown 文件，每轮会话自动注入上下文。这是基础层。

**写什么**：技术栈、测试命令、硬性禁忌。控制在 60 行以内。

```markdown
# 项目规则

## 技术栈
- TypeScript + Next.js 14 (App Router)
- PostgreSQL + Drizzle ORM
- 测试：Vitest + Testing Library

## 硬性禁忌
- 不使用 `any` 类型
- 不在客户端组件中直接导入服务端模块
- 不跳过测试

## 命令
- 测试：`pnpm test`
- 构建：`pnpm build`
- Lint：`pnpm lint`
```

**不要写什么**：目录结构（AI 可以自己探索）、条件逻辑（if X then Y）、过时的架构描述。

经验法则：如果你的 CLAUDE.md 超过 100 行，大概率塞了不该放的东西。上下文窗口是有限资源，冗长的系统提示会挤压实际工作空间。

另一个容易犯的错：让 AI 生成 CLAUDE.md。AI 倾向于写冗长、充满条件分支的规则。人类手写的反而更简洁有效。

### Skills（技能模块）

按需加载的独立指令文件。CLAUDE.md 每次会话都注入，Skills 只在需要时加载。

一个中等规模的项目可能涉及数据库迁移规范、API 设计约定、前端组件规范等十几个知识领域。全塞进 CLAUDE.md，上下文就爆了。

```
.claude/skills/
├── db-migration.md       # 数据库迁移规范
├── api-endpoint.md       # API 端点创建规范
├── frontend-component.md # 前端组件规范
└── deploy.md             # 部署流程
```

每个 Skill 文件只管一个领域。当你说「创建一个新的 API 端点」时，Harness 加载 `api-endpoint.md`，AI 获得这个领域的知识，其他领域不占用上下文。

这和 [Spec 驱动开发](/blog/spec-driven-development) 中的分层加载思路一致——都是通过按需加载来管理有限的上下文窗口。

### MCP 服务器（工具扩展）

Model Context Protocol 让 AI 连接外部系统：Linear、Sentry、数据库、GitHub 等。

工具让 AI 从「闭卷考试」变成「开卷考试」。没有工具的 AI 只能基于训练数据猜；有工具的 AI 可以查真实数据、拿实时状态。

但工具不是越多越好。每加一个工具，AI 做决策时要多考虑一个选项，决策质量反而可能下降——这叫「工具混乱」。经验法则是：只加当前工作流真正需要的，别加你认为将来可能需要的。

### 子代理

子代理解决的是上下文防火墙问题。核心思想：把耗上下文的任务扔到独立代理里执行，只返回最终结果给主代理。

具体场景：你需要 AI 分析一个 50 个文件的代码库，然后基于分析结果重构。如果主代理直接做，分析过程会吃掉大量上下文，留给重构的空间不够了。

```
主代理：「分析 src/ 目录的架构模式」
  → 子代理（独立上下文）：遍历文件、分析依赖、总结模式
  → 返回：300 字的架构摘要
主代理：基于摘要进行重构（上下文几乎没消耗）
```

上下文越满，AI 推理能力越差。子代理让主代理始终有足够「工作内存」来做核心任务。

### Hooks

Hooks 是确定性控制点——在特定事件触发时自动执行的检查脚本。给非确定性的 AI 加上确定性的护栏。

最常用的：pre-commit hook，提交前自动跑 linter + 测试，失败就阻止提交。

```bash
#!/bin/bash
# .claude/hooks/pre-commit.sh
pnpm lint && pnpm test
if [ $? -ne 0 ]; then
  echo "Lint 或测试失败，阻止提交"
  exit 1
fi
```

其他常见用法：任务完成后自动验证需求规格、编辑文件前自动备份。

你不需要信任 AI 的自律性。AI 可能「忘记」跑测试，但 Hook 不会。

---

## 实践建议

### 应该做的

**从失败中提炼规则**。AI 犯了错，不要手动修完就完了。问自己：这条规则应该放哪？通用规则加到 CLAUDE.md，领域规则写成 Skill，能自动检查的写成 Hook。花 5 分钟编码，这个错误就不会再发生。

**定期复盘**。每周五花 15 分钟回顾本周 AI 犯的错误，把它们转化为 Harness 规则。一个季度后你会积累几十条「免疫规则」——每条都是从真实失败中来的。

**保持简洁**。CLAUDE.md 控制在 60 行以内，单个 Skill 控制在 40 行以内。规则越少，AI 越不容易困惑。

**用代码而不是口头约定**。「不要用 any」写在 CLAUDE.md 里比口头告诉 AI 有效 100 倍。因为下一轮会话 AI 就不记得你说过什么了。

### 应该避免的

**一次加太多规则**。CLAUDE.md 有 200 条规则，AI 会变得过于保守，只敢做你明确允许的事情。Harness 是护栏，不是牢笼。

**把目录结构写进 CLAUDE.md**。AI 可以自己跑 `ls` 和 `find`，不需要你帮它记目录。这纯粹浪费上下文。

**给 AI 生成系统提示**。AI 写的规则通常冗长且充满条件分支。人手写的反而简洁有效。

**在探索性开发中过度约束**。如果你还不知道要做什么，Harness 的限制反而碍事。Harness 最适合需求明确、需要稳定产出的场景。

---

## 局限性与权衡

**前期投入**。写 CLAUDE.md、创建 Skills、配置 Hooks 都要时间。短期内看不到明显提升。Harness 的价值是累积性的——每多一条规则，AI 就少犯一类错误。

**模型升级的兼容性**。换模型（比如从 Claude 3.5 到 Claude 4）时，某些规则可能不再适用。不同模型有不同的能力和盲区，Harness 要跟着调。

**规则膨胀**。如果不定期清理，Harness 会越来越臃肿。建议每季度审视一次，删除不再适用的规则。

**不适合所有场景**。原型和探索性开发中，Harness 的约束可能适得其反。大部分工程工作是需求明确的——这正是 Harness 发挥作用的地方。

---

## 快速开始

```
# 1. 创建 CLAUDE.md（技术栈 + 命令 + 3-5 条禁忌，40 行以内）
touch CLAUDE.md

# 2. 创建第一个 Skill（针对你项目中最常重复的模式）
mkdir -p .claude/skills
touch .claude/skills/api-endpoint.md

# 3. 添加 pre-commit hook
mkdir -p .claude/hooks
# 写入 lint + test 的检查脚本
```

不需要额外工具，不需要付费订阅。

---

## 进一步阅读

- [Claude Code CLAUDE.md 最佳实践](https://docs.anthropic.com/en/docs/claude-code/memory) — 系统提示的官方指南
- [Mitchell Hashimoto: AI Coding Agents](https://mitchellh.com/writing/ai-coding-agents) — Harness 思想的原始阐述
- [Spec 驱动开发](/blog/spec-driven-development) — 相关的 AI 协作方法论，侧重需求到代码的结构化流程
- [LangChain Agent Architecture](https://python.langchain.com/docs/concepts/agents/) — Agent 系统的工具调用与状态管理
- [Model Context Protocol Specification](https://modelcontextprotocol.io/) — MCP 工具扩展协议的完整规范
