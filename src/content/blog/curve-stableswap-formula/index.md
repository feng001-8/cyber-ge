---
title: "Curve StableSwap 公式推导：从加权平均到动态参数"
description: "从第一性原理推导 Curve 的 StableSwap 不变量，理解为什么它能在稳定币交易中实现极低滑点。"
pubDate: "2026-03-01"
tags: ["DeFi", "AMM", "Curve", "数学"]
hexagram: "䷁"
element: "water"
---

**TL;DR:** Curve 的 StableSwap 公式本质是 Constant Product 和 Constant Sum 的加权平均，通过引入动态参数 χ = A × 4xy/D²，实现了「平衡点附近低滑点、远离时防掏空」的双重目标。理解这个推导过程，比记住最终公式更重要。

> **前置知识**：本文假设读者熟悉 Uniswap 的恒定乘积公式 xy = k，理解滑点的概念。如果不熟悉，建议先阅读 [DEX 交易机制](/blog/dex-trading-mechanisms)。

---

## 核心问题：稳定币交易的两难

2020 年之前，稳定币之间的兑换是一个尴尬的场景。

在 Uniswap V2 上用 100 万 USDC 换 USDT，滑点可能高达 0.3%——这意味着损失 3000 美元。对于理论上应该 1:1 锚定的资产，这个成本显然不合理。问题出在 Constant Product 公式本身：xy = k 的曲线曲率太大，即使价格只偏离 1% 也会产生明显滑点。

一个直觉的解决方案是使用 Constant Sum 公式：x + y = D。这条直线完全平坦，任意规模的交易都没有滑点。但它有一个致命缺陷：池子会被掏空。如果 USDC 价格稍微高于 USDT，套利者会把池中所有 USDT 换成 USDC，直到池子只剩单一资产。

Curve 的创新在于找到了一条中间路径：构造一条在平衡点附近接近直线、远离平衡点时接近双曲线的曲线。这就是 StableSwap 不变量的设计目标。

![Curve 模型设计](/images/blog/curve-stableswap-formula/curve_model_design.svg)

上图展示了两条基准曲线。蓝色的 xy = k 曲率大但永不枯竭，绿色的 x + y = D 完全平坦但会被掏空。两条曲线交于点 P（x = y = D/2），这个交点就是「平衡点」——Curve 曲线的设计锚点。

---

## 加权平均：统一两种模型

构造混合曲线的第一步是将两个方程组合起来。但直接相加行不通，因为因次不同：xy 的因次是 [数量²]，而 x + y 的因次是 [数量]。

解决方法是给 x + y 乘上 D，统一因次后再做加权平均。设 α 为 Constant Sum 的权重，β 为 Constant Product 的权重：

$$\alpha \cdot D(x + y) + \beta \cdot xy = \alpha \cdot D^2 + \beta \cdot \frac{D^2}{4}$$

等式右边是将平衡点 (D/2, D/2) 代入左边得到的常数。两边同时除以 β，令 χ = α/β，得到简化形式：

$$\chi D(x + y) + xy = \chi D^2 + \frac{D^2}{4}$$

参数 χ 控制两种模型的混合比例：

- χ = 0：退化为 xy = D²/4，纯 Constant Product
- χ → ∞：退化为 x + y = D，纯 Constant Sum
- χ 在中间：得到混合曲线

但静态的 χ 无法解决核心问题。平衡点附近需要大 χ（曲线平坦，低滑点），远离平衡点需要小 χ（曲线弯曲，防掏空）。这两个需求是矛盾的——除非让 χ 动态变化。

---

## 动态参数：让曲线自适应

关键洞察来自一个数学性质：在 Constant Sum 约束（x + y = D）下，xy 的值可以指示当前位置距离平衡点有多远。

![xy 与位置的关系](/images/blog/curve-stableswap-formula/curve_xy_position.svg)

这是一条开口向下的抛物线。当 x = y = D/2 时，xy 达到最大值 D²/4；当池子偏离平衡（x ≠ y）时，xy 变小。这个特性正好可以用来构造动态参数。

定义「位置因子」为 xy 相对于最大值的比例：

$$\text{位置因子} = \frac{xy}{(D/2)^2} = \frac{4xy}{D^2}$$

位置因子的取值范围是 (0, 1]。在平衡点等于 1，偏离越远越接近 0。

引入放大系数 A（Amplification Coefficient），构造动态参数：

$$\chi = A \times \frac{4xy}{D^2}$$

A 是一个固定常数，由 DAO 治理设定（Curve 3pool 的 A = 2000）。而 4xy/D² 随池子状态实时变化。这样就实现了自适应：

- 平衡点附近：4xy/D² ≈ 1，χ ≈ A，曲线接近直线
- 远离平衡点：4xy/D² → 0，χ → 0，曲线接近双曲线

---

## 最终公式的推导

将动态参数代入加权平均公式，展开计算。

**代入**：

$$A \times \frac{4xy}{D^2} \times D(x+y) + xy = A \times \frac{4xy}{D^2} \times D^2 + \frac{D^2}{4}$$

**化简左边第一项**：

$$\frac{4Axy \cdot D(x+y)}{D^2} = \frac{4Axy(x+y)}{D}$$

**化简右边第一项**：

$$A \times \frac{4xy}{D^2} \times D^2 = 4Axy$$

**得到形式 1**（推导直接结果）：

$$\frac{4Axy(x+y)}{D} + xy = 4Axy + \frac{D^2}{4}$$

为了得到白皮书中的标准形式，两边同时乘以 D，再除以 xy：

**两边乘 D**：

$$4Axy(x+y) + Dxy = 4AxyD + \frac{D^3}{4}$$

**两边除以 xy**：

$$4A(x+y) + D = 4AD + \frac{D^3}{4xy}$$

这就是 **Curve StableSwap 不变量**（n = 2 的情况）。

---

## 推广到多币种

Curve 的 3pool（USDC/USDT/DAI）包含三种资产，需要将公式推广到 n 个币种。推广规则是：

| 双币种 | n 币种 |
|--------|--------|
| x + y | Σxᵢ |
| xy | Πxᵢ |
| 4 (= 2²) | nⁿ |
| D³ | Dⁿ⁺¹ |

代入得到通用公式：

$$An^n \sum_{i=1}^{n} x_i + D = ADn^n + \frac{D^{n+1}}{n^n \prod_{i=1}^{n} x_i}$$

验证：当 n = 2 时，nⁿ = 4，Dⁿ⁺¹ = D³，与前面推导一致。

---

## 放大系数 A 的选择

A 决定了曲线在平衡点附近的「平坦程度」。A 越大，曲线越接近直线，滑点越低；A 越小，曲线越接近双曲线，抗掏空能力越强。

![放大系数 A 的影响](/images/blog/curve-stableswap-formula/curve_amplification.svg)

但 A 不是越大越好。选择 A 的核心目标是**最大化手续费收入**，而非单纯降低滑点。

Curve CEO Michael Egorov 给出的经验公式：

$$A_{\text{optimal}} \approx \frac{1}{\sigma}$$

其中 σ 是资产对价格的标准差。对于强锚定的稳定币（如 USDC/USDT），价格波动率约 0.05%，对应 A ≈ 2000；对于弱锚定资产（如 stETH/ETH），波动率约 1%，对应 A ≈ 100。

**A 值调整的风险**：

- 调整过快会创造套利空间
- 在池子不平衡时调整可能导致 LP 资金损失
- 没有时间锁保护会被抢跑攻击

因此 Curve 的 A 值调整通常需要 DAO 投票，并有 3 天的时间锁。2020 年 Curve 曾因 A 值调整不当导致约 14 万美元的套利损失。

---

## 实际效果：数字说话

以 Curve 3pool 为例（A = 2000，TVL 约 3 亿美元）：

| 交易规模 | Uniswap V2 滑点 | Curve 滑点 | 节省 |
|----------|-----------------|------------|------|
| 10 万美元 | 0.03% | 0.001% | 30 倍 |
| 100 万美元 | 0.3% | 0.01% | 30 倍 |
| 1000 万美元 | 3% | 0.1% | 30 倍 |

在平衡点附近，Curve 的滑点比 Uniswap V2 低约 30 倍。这就是 StableSwap 公式的威力。

---

## 公式速查

**Constant Product（Uniswap）**
$$xy = k$$

**Constant Sum（理想但不安全）**
$$x + y = D$$

**动态参数**
$$\chi = A \times \frac{4xy}{D^2}$$

**Curve StableSwap（n = 2）**
$$4A(x+y) + D = 4AD + \frac{D^3}{4xy}$$

**Curve StableSwap（通用）**
$$An^n \sum_{i=1}^{n} x_i + D = ADn^n + \frac{D^{n+1}}{n^n \prod_{i=1}^{n} x_i}$$

---

## 局限性与权衡

StableSwap 不是万能的。它的设计假设是资产价格应该接近 1:1，这带来几个限制：

1. **只适用于锚定资产**：对于 ETH/USDC 这样的非锚定对，StableSwap 的低滑点反而是缺陷——它无法正确反映价格变化。

2. **脱锚风险**：当稳定币脱锚时（如 2023 年 USDC 短暂脱锚至 0.87），StableSwap 池会遭受严重的无常损失，因为曲线假设价格会回归 1:1。

3. **A 值治理风险**：A 值的选择和调整需要专业判断，错误的治理决策可能导致资金损失。

4. **Gas 成本**：StableSwap 的计算比 Constant Product 复杂，链上 Gas 消耗更高（约 1.5-2 倍）。

理解这些权衡，才能在正确的场景使用正确的工具。

---

## 进一步阅读

- [Curve StableSwap 白皮书](https://curve.fi/files/stableswap-paper.pdf) — 原始论文，包含完整数学推导和稳定性分析
- [淺談穩定幣互換機制](https://medium.com/@cic.ethan/%E6%B7%BA%E8%AB%87%E7%A9%A9%E5%AE%9A%E5%B9%A3%E4%BA%92%E6%8F%9B%E6%A9%9F%E5%88%B6-%E5%BE%9E-balancer-%E5%88%B0-curve-f638f29b33f9) — 本文推导思路的来源，中文讲解清晰
- [Curve 技术文档](https://docs.curve.fi/) — 官方文档，包含 A 值选择指南和池子参数
- [Curve A Parameter Deep Dive](https://nagaking.substack.com/p/deep-dive-curve-finance-a-parameter) — A 值调整的风险分析
