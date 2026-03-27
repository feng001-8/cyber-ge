---
title: "Harness Engineering：别再换模型了，给 AI 套上缰绳"
description: "同一模型、同一基准测试，仅通过优化外部驾驭系统即可实现近 2 倍性能提升。Harness Engineering 定义了围绕 AI 模型的五大配置杠杆——系统提示、技能模块、工具扩展、子代理和钩子——让非确定性 AI 产出确定性可靠的代码。"
pubDate: "2026-03-27"
tags: ["AI", "开发工具", "方法论", "Agent"]
hexagram: "䷂"
element: "metal"
---

**TL;DR:** AI 模型只是「大脑」，它需要一套外部驾驭系统才能高效、可控地工作。Harness Engineering（马具工程）定义了五个可直接调整的配置点——系统提示、技能模块、MCP 工具、子代理和钩子——通过优化这些「缰绳」，同一模型可以实现接近 2 倍的性能提升。模型已经商品化，但针对你代码库和团队模式的自定义 Harness 是无法复制的竞争壁垒。

> **前置知识**：本文假设读者使用过 Claude Code、Cursor 等 AI 编程助手，了解基本的 prompt 工程概念。如果对 AI 协作方法论不熟悉，建议先阅读 [Spec 驱动开发](/blog/spec-driven-development)。

---

## 一个反直觉的实验

同一个 AI 模型，同一套编码基准测试，第一次得分 42%，第二次飙升到 78%。唯一变量不是提示词、不是模型、不是温度设置——是「harness」。

Harness 是围绕 AI 模型的一整套外部系统：规则、工具、技能、记忆文件和反馈循环。它就像马具之于马——马有力量，但没有缰绳、鞍座和马嚼子，力量就是失控的。

Mitchell Hashimoto（Terraform 作者）说过一句话精准地概括了这个理念：

> "When the AI makes a mistake, don't pray for a better model—design a system that makes it impossible for the AI to make that mistake again."
>
> 当 AI 犯错时，不要祈求更好的模型，而是设计一个让它永远不再犯这个错的系统。

这不是理论。LangChain 团靠优化 Harness 而非换模型大幅提升 Agent 表现。OpenAI Codex 团队的经验类似。历史上没有任何一次模型升级能带来接近 2 倍的编码性能提升——但 Harness 优化做到了。

---

## 计算机系统的类比

理解 Harness Engineering 最直观的方式是类比计算机系统：

- **Model（模型）** = CPU——原始算力，负责推理和生成
- **Context Window（上下文窗口）** = RAM——有限的工作内存，用完就丢
- **Agent Harness（驾驭系统）** = 操作系统——负责管理上下文生命周期、工具调度、I/O 验证
- **Agent（代理）** = 应用程序——在操作系统之上运行的具体业务逻辑

大多数人把注意力放在 CPU（模型）上——哪个模型更强、哪个 benchmark 得分更高。但真正决定系统性能的，往往是操作系统。同样的 CPU，一个调度良好的 OS 和一个混乱的 OS，用户体验天差地别。

AI 领域正在经历同样的认知转变。Prompt Engineering（2023）教你如何写好一句话。Context Engineering（2025）教你如何管理有限的上下文窗口。而 Harness Engineering（2026）教你如何设计一整套让 AI 可靠工作的外部系统。

---

## 五大杠杆：可直接调整的配置点

Harness 不是一个抽象概念，它由五个具体的、可独立调整的组件构成。

### 杠杆一：系统提示（CLAUDE.md / AGENTS.md）

仓库根目录下的 Markdown 文件，每轮会话自动注入 AI 的上下文。这是 Harness 的基础层。

关键原则：

**简洁至上**。控制在 60 行以内。上下文窗口是有限资源，冗长的系统提示会挤压实际工作空间。如果你的 CLAUDE.md 超过 100 行，大概率包含了很多不该放的内容。

**人类手写**。不要让 AI 生成你的系统提示。AI 倾向于写冗长、充满条件逻辑的规则，而人类能写出简洁、通用的约束。

**只写通用规则**：

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

**不要写的内容**：目录结构（AI 可以自己探索）、条件逻辑（if X then Y）、过时的架构描述。

### 杠杆二：Skills（技能模块）

按需加载的独立指令文件。与系统提示不同，Skills 不是每次会话都注入的——只有当任务需要时才加载。

这解决了一个核心问题：你不能把所有知识都塞进上下文窗口。一个中等规模的项目可能涉及数据库迁移规范、API 设计约定、前端组件规范、部署流程等十几个知识领域。如果全部写进 CLAUDE.md，上下文就爆了。

Skills 的设计模式：

```
.claude/skills/
├── db-migration.md      # 数据库迁移规范
├── api-endpoint.md      # API 端点创建规范
├── frontend-component.md # 前端组件规范
└── deploy.md            # 部署流程
```

每个 Skill 文件只包含一个领域的知识。当你说「创建一个新的 API 端点」时，Harness 自动加载 `api-endpoint.md`，AI 获得这个领域的专业知识，同时保持其他知识不占用上下文。

对比 [Spec 驱动开发](/blog/spec-driven-development) 中的分层加载策略——理念相通，都是通过按需加载来管理有限的上下文窗口。

### 杠杆三：MCP 服务器（工具扩展）

Model Context Protocol 让 AI 能够连接外部系统：Linear（项目管理）、Sentry（错误监控）、数据库、GitHub 等。

工具的价值在于让 AI 从「闭卷考试」变成「开卷考试」。不用工具的 AI 只能基于训练数据猜测；有工具的 AI 可以查询真实数据、获取实时状态。

但工具不是越多越好。每增加一个工具，AI 需要在决策时考虑更多选项，这会降低决策质量——称为「工具混乱」（tool confusion）。经验法则是：只添加当前工作流真正需要的工具，而不是你认为将来可能需要的。

### 杠杆四：Sub-agents（子代理）

子代理用于上下文防火墙。核心思想是：把消耗大量上下文的任务隔离到独立的代理中执行，只返回最终结果给主代理。

想象一个场景：你需要 AI 分析一个包含 50 个文件的代码库，然后基于分析结果重构代码。如果让主代理直接做，分析过程会消耗大量上下文，留给重构的空间就不够了。

用子代理解决：

```
主代理：「分析 src/ 目录的架构模式」
  → 子代理（独立上下文）：遍历文件、分析依赖、总结模式
  → 返回：300 字的架构摘要
主代理：基于摘要进行重构（上下文几乎没消耗）
```

子代理保持了主代理的「聪明状态」——上下文越满，AI 的推理能力越差。通过隔离耗上下文的任务，主代理始终有足够的「工作内存」来执行核心任务。

### 杠杆五：Hooks（钩子）

Hooks 是确定性控制点——在特定事件触发时自动执行的检查脚本。它们给非确定性的 AI 加上了确定性的护栏。

常见的 Hook 配置：

**Pre-commit hook**：AI 提交代码前，自动运行 linter + 测试。如果失败，阻止提交。

```bash
# .claude/hooks/pre-commit.sh
#!/bin/bash
pnpm lint && pnpm test
if [ $? -ne 0 ]; then
  echo "Lint 或测试失败，阻止提交"
  exit 1
fi
```

**Post-task hook**：任务完成后，自动验证是否满足需求规格。

**Pre-edit hook**：编辑文件前，自动备份或检查权限。

Hooks 的价值在于：你不需要信任 AI 的自律性，而是用代码强制执行规则。AI 可能会「忘记」运行测试，但 Hook 不会。

---

## 从失败中迭代：Harness 的演进方法论

Harness 不是一次性搭建好的，它是从失败中迭代出来的。

核心心态转变：**AI 出错时，不要手动修复，而是问「怎么让它永远不再犯这个错」，然后把方案编码进 Harness。**

具体流程：

1. AI 犯了一个错误（比如生成了使用 `any` 类型的代码）
2. 你发现后手动修复
3. 问自己：这条规则应该放在哪里？
   - 如果是通用规则 → 加到 CLAUDE.md
   - 如果是领域特定规则 → 创建或更新 Skill
   - 如果是可自动检查的规则 → 写一个 Hook
4. 花 5 分钟编码这条规则
5. 这个错误永远不会再发生

每周五花 15 分钟复盘本周的 AI 失败案例，把它们转化为 Harness 规则。一个季度后，你的 Harness 就积累了几十条「免疫规则」——每一条都是从真实失败中提炼的。

这就是为什么自定义 Harness 是无法复制的竞争壁垒。别人的 Harness 是基于他们的失败模式构建的，你的 Harness 是基于你的代码库、你的团队模式、你的领域特例构建的。模型人人可用，但 Harness 各有不同。

---

## 局限性与权衡

Harness Engineering 不是银弹，有几个需要正视的局限：

**前期投入**。搭建 Harness 需要时间。写 CLAUDE.md、创建 Skills、配置 Hooks——这些工作在短期内不会带来明显的性能提升。Harness 的价值是累积性的：每多一条规则，AI 就少犯一类错误。但你需要耐心等待复利效应。

**过度约束的风险**。规则太多会限制 AI 的创造力。如果你的 CLAUDE.md 有 200 条规则，AI 可能会变得过于保守，只敢做你明确允许的事情。Harness 应该是护栏，不是牢笼。定期审视规则，删除不再适用的。

**模型升级的兼容性**。当你切换模型（比如从 Claude 3.5 到 Claude 4），某些 Harness 规则可能不再适用或反而有害。不同模型有不同的能力和盲区，Harness 需要随模型演进而调整。

**不适用于探索性工作**。如果你在做原型或探索性开发，Harness 的约束可能适得其反。Harness 最适合需求相对明确、需要稳定产出的场景——而这恰恰是大部分工程工作的状态。

---

## 立刻上手：五步启动清单

不需要额外工具，不需要付费订阅，你现在就可以开始：

**第一步：写一个简洁的 CLAUDE.md**。包含技术栈、测试命令、3-5 条硬性禁忌。控制在 40 行以内。

**第二步：建第一个 Skill 文件**。找出你项目中最常重复的模式（API 创建？组件开发？数据库迁移？），写一个 20 行的 Skill 文件。

**第三步：加一个 Hook**。最简单的开始：pre-commit hook 运行 `pnpm lint && pnpm test`。

**第四步：用 Sub-agents 拆解长任务**。下次让 AI 分析代码库时，先派一个子代理去收集信息，再让主代理基于结果行动。

**第五步：每周五复盘**。回顾本周 AI 犯的错误，每个错误花 5 分钟转化为一条 Harness 规则。

---

## 进一步阅读

- [Claude Code CLAUDE.md 最佳实践](https://docs.anthropic.com/en/docs/claude-code/memory) — 系统提示的官方指南
- [Mitchell Hashimoto: AI Coding Agents](https://mitchellh.com/writing/ai-coding-agents) — Terraform 作者关于 Harness 思想的原始阐述
- [Spec 驱动开发](/blog/spec-driven-development) — 本文相关的 AI 协作方法论，侧重需求到代码的结构化流程
- [LangChain Agent Architecture](https://python.langchain.com/docs/concepts/agents/) — Agent 系统的工具调用与状态管理
- [Model Context Protocol Specification](https://modelcontextprotocol.io/) — MCP 工具扩展协议的完整规范
