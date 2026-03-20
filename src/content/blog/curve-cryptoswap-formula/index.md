---
title: "Curve CryptoSwap (v2) 公式推导：从稳定币到波动资产"
description: "深入推导 Curve v2 的 CryptoSwap 不变量，理解价值转换、动态 K 参数、Repegging 机制如何让 AMM 支持任意资产对。"
pubDate: "2026-03-01"
tags: ["DeFi", "AMM", "Curve", "数学"]
hexagram: "䷀"
element: "fire"
---

**TL;DR:** Curve v2 CryptoSwap 通过三个核心创新突破了 StableSwap 的局限：(1) 引入内部价格 price_scale 将数量转换为价值，使公式适用于任意资产对；(2) 用 γ 参数调整 K 系数，让曲线在偏离平衡点时更快变陡；(3) Repegging 机制自动追踪市场价格，无需外部预言机。理解这些机制，是理解现代 AMM 设计的关键。

> **前置知识**：本文假设读者已理解 [Curve StableSwap 公式推导](/blog/curve-stableswap-formula)，熟悉动态参数 χ = A × 4xy/D² 的设计思路。如果不熟悉，建议先阅读该文章。

---

## 从 StableSwap 到 CryptoSwap：为什么需要 v2

2020 年 Curve v1 StableSwap 在稳定币交易领域取得了巨大成功。但它有一个根本性的假设：池中资产的价格应该接近 1:1。这个假设对 USDC/USDT/DAI 完美适用，却无法处理 USDT/WBTC/WETH 这样的组合——当 WBTC 价格是 40,000 美元、WETH 是 3,000 美元时，1:1 的假设显然不成立。

2021 年 6 月，Curve CEO Michael Egorov 发布了 CryptoSwap 白皮书，提出了一套全新的机制。核心思想是：既然价格不再是 1:1，就需要引入内部价格来「标准化」不同资产，让它们在价值层面可比较。

这个看似简单的想法，引出了一系列复杂但精妙的设计。

---

## 价值转换：从数量到价值

### 问题的本质

回顾 v1 StableSwap 的核心公式（n = 2）：

$$4A(x+y) + D = 4AD + \frac{D^3}{4xy}$$

这里的 x 和 y 是资产的**数量**。公式能工作的前提是：1 个 USDC 和 1 个 USDT 的价值相等。但如果池子是 USDT-WBTC，1 个 USDT 和 1 个 WBTC 的价值相差 40,000 倍，直接用数量计算毫无意义。

### 引入内部价格

v2 的解决方案是引入**内部缩放价格** price_scale，记为 p。对于 USDT-WBTC-WETH 池：

- USDT 价格：p₀ = 1（作为锚定标的，始终为 1）
- WBTC 价格：p₁ = 40,000（相对于 USDT）
- WETH 价格：p₂ = 3,000（相对于 USDT）

**关键规则**：第一个资产始终作为计价单位，其价格恒为 1。

### 数量与价值的转换

定义两个向量：

- **数量向量** b = (b₀, b₁, b₂, ...)：实际持有的 token 数量
- **价值向量** b' = (b'₀, b'₁, b'₂, ...)：用锚定资产计价的价值

转换公式：

$$b'_i = b_i \cdot p_i$$

举个例子。假设池子状态为：100,000 USDT、2 WBTC、30 WETH。

![价值转换示意图](/images/blog/curve-cryptoswap-formula/value_conversion.svg)

通过价格转换，三种资产可以在同一尺度上比较了。

> **白皮书勘误**：原白皮书中 b 和 b' 的转换公式写反了。正确的形式是 b' = b × p（价值 = 数量 × 价格），而非 b = b' × p。这个错误在代码中已修正。

---

## D 的重新定义

### v1 中的 D

在 v1 StableSwap 中，D 的定义很直观：

$$D = \sum x_i$$

当池子处于平衡状态（所有资产数量相等）时，D 就是资产数量的总和。

### v2 中的 D

v2 中资产价格不同，不能直接用数量求和。D 被重新定义为：

$$D = N \cdot x_{eq}$$

其中 N 是资产数量，x_eq 是平衡点时**每个资产的等价价值**。

理解「平衡点」：当池子处于平衡状态时，每个资产的**价值**相等：

$$b'_0 = b'_1 = b'_2 = \ldots = x_{eq}$$

以 3 个币种为例，如果平衡点时每个资产价值为 90,000 USDT：

$$D = 3 \times 90,000 = 270,000$$

**几何意义的转变**：v1 中 D 是数量的总和，v2 中 D 是价值的总和。这个转变是 CryptoSwap 能处理任意资产对的基础。

---

## K 的动态调整机制

### 回顾 v1 的 χ

v1 StableSwap 的动态参数：

$$\chi = A \times \frac{4xy}{D^2}$$

其中 4xy/D² 是「位置因子」，在平衡点为 1，远离时趋向 0。这让曲线在平衡点附近平坦、远离时弯曲。

### v2 的 K₀

v2 将位置因子推广到 N 个资产：

$$K_0 = \frac{\prod x_i \cdot N^N}{D^N}$$

验证平衡点：当所有 xᵢ = D/N 时：

$$K_0 = \frac{(D/N)^N \cdot N^N}{D^N} = \frac{D^N \cdot N^N}{N^N \cdot D^N} = 1$$

K₀ 的行为与 v1 的位置因子一致：平衡点为 1，偏离时小于 1。

### 引入 γ 调整因子

v2 的核心创新是在 A·K₀ 基础上，再乘以一个调整因子：

$$K = A \cdot K_0 \cdot \frac{\gamma^2}{(\gamma + 1 - K_0)^2}$$

γ（gamma）是一个新参数，控制曲线在偏离平衡点时的「陡峭程度」。

分析这个调整因子的行为：

**在平衡点**（K₀ = 1）：

$$\frac{\gamma^2}{(\gamma + 1 - 1)^2} = \frac{\gamma^2}{\gamma^2} = 1$$

调整因子为 1，不影响 A。

**远离平衡点**（K₀ → 0）：

$$\frac{\gamma^2}{(\gamma + 1)^2} < 1$$

调整因子小于 1，进一步降低 K。

这意味着什么？看一个数值对比（假设 A = 100，γ = 0.01）：

| 位置 | K₀ | v1: χ = A·K₀ | v2: K = A·K₀·调整因子 |
|------|-----|--------------|----------------------|
| 平衡点 | 1.0 | 100 | 100 |
| 轻微偏离 | 0.96 | 96 | 94.1 |
| 严重偏离 | 0.36 | 36 | 26.3 |

**结论**：γ 调整因子让曲线在偏离平衡点时下降得更快。这对波动资产很重要——当价格剧烈变化导致池子失衡时，曲线需要更快地变陡来保护流动性。

![K 调整因子对比](/images/blog/curve-cryptoswap-formula/k_comparison.svg)

---

## CryptoSwap 不变量公式

### 最终形式

将动态 K 代入，得到 CryptoSwap 不变量：

$$K D^{N-1} \sum x_i + \prod x_i = K D^N + \left(\frac{D}{N}\right)^N$$

其中：

$$K = A \cdot K_0 \cdot \frac{\gamma^2}{(\gamma + 1 - K_0)^2}$$

$$K_0 = \frac{\prod x_i \cdot N^N}{D^N}$$

### 验证 n = 2 的情况

将 N = 2 代入：

$$K D (x+y) + xy = K D^2 + \frac{D^2}{4}$$

对比 v1 公式（两边乘以 xy/D）：

$$4A(x+y) + D = 4AD + \frac{D^3}{4xy}$$

形式一致，只是 v2 中的 K 是动态的，而 v1 中的 4A 是静态的。

### 函数形式

将不变量写成 F(x, D) = 0 的形式，便于牛顿法求解：

$$F(\mathbf{x}, D) = K D^{N-1} \sum x_i + \prod x_i - K D^N - \left(\frac{D}{N}\right)^N = 0$$

---

## 牛顿法求解

### 两种求解场景

CryptoSwap 需要在两种场景下求解方程：

1. **添加/移除流动性**：已知所有 xᵢ，求 D
2. **交易**：已知 D 和除 xⱼ 外的所有 xᵢ，求 xⱼ

由于方程是高次多项式，无法直接求解，必须使用数值方法。Curve 选择了牛顿法。

### 牛顿法迭代公式

牛顿法的核心思想是用切线逼近曲线：

$$x_{n+1} = x_n - \frac{F(x_n)}{F'(x_n)}$$

### 求解 D 的初值选择

初值的选择对收敛速度至关重要。Curve 使用几何平均数作为初值：

$$D_0 = N \cdot \left(\prod x_k\right)^{\frac{1}{N}}$$

这个选择有数学依据：几何平均数是「平衡点」的自然估计。

### 求解 xᵢ 的初值选择

$$x_{i,0} = \frac{D^N}{\prod_{k \neq i} x_k \cdot N^N}$$

> **白皮书勘误**：原白皮书中分子的 D 幂次写成 N-1，分母的 N 幂次也写成 N-1，都应该是 N。代码中已修正。

### Gas 消耗

牛顿法在 EVM 中消耗约 **35K gas**。通常 4 轮迭代即可收敛到精度 1（即误差 ≤ 1 wei）。如果 255 轮后仍未收敛，交易回滚——这通常意味着池子状态异常。

---

## Repegging 机制：自动追踪市场价格

### 核心问题

price_scale 是内部价格，但市场价格在不断变化。如果 WBTC 从 40,000 涨到 50,000，而 price_scale 还是 40,000，池子就会被套利掏空。

Repegging 机制解决这个问题：自动调整 price_scale，让它追踪市场真实价格。

### 三种价格的关系

CryptoSwap 维护三种价格：

1. **last_price**：每笔交易产生的即时价格
2. **price_oracle**：last_price 的指数移动平均（EMA）
3. **price_scale**：用于计算的内部缩放价格

它们的更新关系形成一个闭环：

![Repegging 机制流程](/images/blog/curve-cryptoswap-formula/repegging_flow.svg)

### 价格预言机（EMA）

price_oracle 使用指数移动平均来平滑 last_price：

$$\alpha = 2^{-\frac{t}{T_{1/2}}}$$

$$p^* = p_{last}(1-\alpha) + \alpha \cdot p^*_{prev}$$

其中 t 是距离上次更新的时间间隔，T₁/₂ 是半衰期（ma_half_time）。

EMA 的作用是过滤噪声：单笔大额交易不会立即改变 price_oracle，需要持续的价格偏离才会触发调整。

### 调整 price_scale 的公式

当 price_oracle 与 price_scale 偏离时，按以下公式调整：

$$\frac{p_i}{p_{i,prev}} = 1 + \frac{s}{\sqrt{\sum\left(\frac{p^*_j}{p_{j,prev}} - 1\right)^2}} \left(\frac{p^*_i}{p_{i,prev}} - 1\right)$$

这个公式的几何意义：

- 分母是 price_oracle 与 price_scale 偏差的欧几里得距离
- s 是调整步长（step size）
- 整体效果是让 price_scale 向 price_oracle 方向移动一小步

**为什么不直接设置 price_scale = price_oracle？** 因为突变会创造套利空间。渐进调整让套利者无法预测下一步的价格，保护了 LP。

### Repegging 的触发条件

不是每次交易都会触发 repegging。只有当利润足够时才执行：

$$p_{virtual} - 1 > \frac{X_{cp,profit} - 1}{2}$$

其中：

- p_virtual = X_cp / TotalSupply，衡量每单位 LP token 的价值
- X_cp,profit 是累计利润的量化

这个条件的含义是：**将池子累积总利润的一半用于 repegging**。只有当 LP 的实时收益超过累计收益的一半时，才调整价格。这保护了 LP 在亏损时不会被进一步伤害。

---

## 动态手续费

### v1 的固定费率

v1 StableSwap 使用固定手续费率（如 0.04%）。

### v2 的动态费率

v2 的手续费在 f_mid 和 f_out 之间动态调整：

$$g = \frac{\gamma_{fee}}{\gamma_{fee} + 1 - \frac{\prod x_i}{(\sum x_i / N)^N}}$$

$$f = g \cdot f_{mid} + (1-g) \cdot f_{out}$$

分析这个公式：

- 分母中的 ∏xᵢ / (Σxᵢ/N)^N 是几何平均与算术平均的比值
- 在平衡点时，这个比值最大（= 1），g ≈ 1，f ≈ f_mid（低手续费）
- 远离平衡点时，比值减小，g → 0，f → f_out（高手续费）

**经济意义**：鼓励使池子回到平衡状态的交易（低手续费），惩罚使池子远离平衡状态的交易（高手续费）。

典型参数：f_mid = 0.04%，f_out = 0.40%。手续费可以相差 10 倍。

![动态手续费机制](/images/blog/curve-cryptoswap-formula/dynamic_fee.svg)

---

## v1 vs v2 对比

| 特性 | v1 StableSwap | v2 CryptoSwap |
|------|---------------|---------------|
| 适用场景 | 锚定资产（稳定币） | 任意资产 |
| 价格假设 | 1:1 | 任意比例 |
| 基础单位 | 数量 xᵢ | 价值 xᵢ·pᵢ |
| 动态参数 | χ = A·4xy/D² | K = A·K₀·γ²/(γ+1-K₀)² |
| 价格调整 | 无 | Repegging 机制 |
| 手续费 | 固定 | 动态（0.04%-0.40%） |
| 复杂度 | 中等 | 高 |

---

## 局限性与权衡

CryptoSwap 是一个精妙的设计，但它不是万能的：

**1. 复杂性成本**

Repegging 机制涉及多个相互关联的变量（last_price、price_oracle、price_scale、virtual_price、xcp_profit），理解和审计都很困难。2022 年 Curve 的 Tricrypto 池曾因 repegging 逻辑的边界情况导致约 50 万美元的损失。

**2. Gas 消耗**

CryptoSwap 的计算比 StableSwap 复杂得多。一次交易的 Gas 消耗约 150K-200K，是 Uniswap V2 的 2-3 倍。

**3. 参数敏感性**

A、γ、ma_half_time、adjustment_step 等参数的选择需要专业判断。错误的参数可能导致：
- 曲线过于平坦，被套利掏空
- 曲线过于陡峭，滑点过高
- Repegging 过快，创造套利空间
- Repegging 过慢，无法跟踪市场

**4. 预言机延迟**

EMA 预言机有固有延迟。在剧烈波动时（如闪崩），price_scale 可能跟不上市场价格，导致 LP 损失。

**5. 流动性碎片化**

每个 CryptoSwap 池只能包含 2-3 种资产。对于需要多种资产组合的场景，流动性会被分散到多个池子。

---

## 关键公式汇总

**价值转换**
$$b'_i = b_i \cdot p_i$$

**D 的定义**
$$D = N \cdot x_{eq}$$

**K₀ 的定义**
$$K_0 = \frac{\prod x_i \cdot N^N}{D^N}$$

**K 的定义**
$$K = A \cdot K_0 \cdot \frac{\gamma^2}{(\gamma + 1 - K_0)^2}$$

**CryptoSwap 不变量**
$$K D^{N-1} \sum x_i + \prod x_i = K D^N + \left(\frac{D}{N}\right)^N$$

**牛顿法初值（求 D）**
$$D_0 = N \cdot \left(\prod x_k\right)^{\frac{1}{N}}$$

**牛顿法初值（求 xᵢ）**
$$x_{i,0} = \frac{D^N}{\prod_{k \neq i} x_k \cdot N^N}$$

**价格预言机（EMA）**
$$\alpha = 2^{-\frac{t}{T_{1/2}}}$$
$$p^* = p_{last}(1-\alpha) + \alpha \cdot p^*_{prev}$$

**Price Scale 调整**
$$\frac{p_i}{p_{i,prev}} = 1 + \frac{s}{\sqrt{\sum\left(\frac{p^*_j}{p_{j,prev}} - 1\right)^2}} \left(\frac{p^*_i}{p_{i,prev}} - 1\right)$$

**动态手续费**
$$g = \frac{\gamma_{fee}}{\gamma_{fee} + 1 - \frac{\prod x_i}{(\sum x_i / N)^N}}$$
$$f = g \cdot f_{mid} + (1-g) \cdot f_{out}$$

---

## 进一步阅读

- [Curve CryptoSwap 白皮书](https://curve.fi/files/crypto-pools-paper.pdf) — 原始论文，包含完整数学推导
- [Curve v2 CryptoSwap 详解系列](https://0xreviews.xyz/posts/2022-03-01-Curve-CryptoSwap-whitepaper/) — 0xreviews 的深度代码分析，本文参考了其中的勘误
- [Curve v2 参数深度分析](https://nagaking.substack.com/p/deep-dive-curve-v2-parameters) — A 和 γ 参数的选择指南
- [Curve 技术文档](https://docs.curve.finance/cryptoswap-exchange/overview/) — 官方文档，包含最新的合约接口
