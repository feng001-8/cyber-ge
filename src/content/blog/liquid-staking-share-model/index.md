---
title: "流动性质押的份额模型与汇率机制"
description: "深入解析 Lido 等流动性质押协议的核心设计：为什么 stETH 不是 1:1 锚定 ETH，汇率如何计算，Oracle 扮演什么角色。"
pubDate: "2026-03-02"
tags: ["Ethereum", "Staking", "DeFi", "Lido"]
hexagram: "䷀"
element: "metal"
---

**TL;DR:** 流动性质押代币本质是「份额凭证」而非 1:1 锚定资产。用户余额 = 份额 × 总质押ETH / 总份额，汇率随奖励累积自动上涨。Oracle 是整个系统的信任锚点，负责将信标链上的验证者余额同步到执行层。

> **前置知识**：本文假设读者了解以太坊 PoS 质押的基本概念，知道验证者需要 32 ETH。如果不熟悉，建议先阅读以太坊官方的 [质押介绍](https://ethereum.org/en/staking/)。

---

## 核心问题：质押收益如何分配给所有持有者

以太坊 PoS 质押面临一个根本性的用户体验问题：验证者的奖励直接累积在信标链上的验证者余额中，而不是自动分发到每个质押者的钱包。

假设一个流动性质押协议管理着 100 万 ETH，分布在 31,250 个验证者上。每天产生约 100 ETH 的质押奖励。如果协议要把这些奖励「分发」给 10 万个用户，每次 Oracle 报告都需要执行 10 万次转账——这在 Gas 成本上完全不可行。

Lido 的解决方案是**不分发奖励**。用户持有的不是 ETH，而是协议总资产的「份额」。当验证者余额增加时，每个份额对应的 ETH 数量自动增加，用户余额随之上涨。这就是 Rebase 机制的本质。

---

## 两种代币模型：Rebase vs Share

流动性质押代币有两种主流设计，理解它们的区别对于 DeFi 集成至关重要。

![stETH vs wstETH 对比](./steth-vs-wsteth.png)

### Rebase 模型（stETH）

stETH 是一个 Rebase 代币：用户钱包中的代币数量会随时间自动增加。如果你今天持有 100 stETH，明天可能变成 100.01 stETH。

这种设计的优点是直观——用户看到余额增长，心理上感觉「在赚钱」。但它有一个严重的技术问题：大多数 DeFi 协议无法正确处理 Rebase 代币。

考虑一个借贷协议。用户存入 100 stETH 作为抵押品，协议记录「用户存了 100 个代币」。一天后，用户的 stETH 变成了 100.01 个，但协议的记录还是 100。这 0.01 个代币的奖励去哪了？它被「困」在协议合约里，既不属于用户，也不属于协议。

跨链桥的问题更严重。用户在 L1 锁定 100 stETH，桥在 L2 铸造 100 个包装代币。一周后 L1 的 stETH 变成了 100.07 个，但 L2 的包装代币还是 100 个。这 0.07 个代币永久丢失在桥合约中。

### Share 模型（wstETH）

wstETH（wrapped stETH）是 Lido 为解决 DeFi 兼容性问题推出的包装代币。它的余额永远不变，但每个 wstETH 对应的 ETH 数量会增加。

用户用 100 stETH 包装成 wstETH，假设当时汇率是 1 wstETH = 1.1 stETH，用户得到约 90.9 wstETH。一年后，汇率变成 1 wstETH = 1.15 stETH，用户的 90.9 wstETH 可以解包成约 104.5 stETH。

余额没变，但价值增加了。这种模型与 ERC-4626 金库标准完全兼容，可以无缝集成到任何 DeFi 协议中。

### 选择哪种模型

| 场景 | 推荐代币 | 原因 |
|------|----------|------|
| 长期持有 | stETH | 直观看到余额增长 |
| 借贷抵押 | wstETH | 协议能正确计算抵押价值 |
| 跨链转移 | wstETH | 奖励不会丢失在桥中 |
| LP 提供流动性 | wstETH | 避免无常损失计算错误 |

实际上，大多数 DeFi 集成都使用 wstETH。stETH 更多是面向普通用户的「展示层」。

---

## 份额计算的数学基础

无论是 stETH 还是 wstETH，底层都使用相同的份额模型。理解这个模型是理解整个协议的关键。

![份额模型核心公式](./share-model-formula.png)

### 核心公式

Lido 不存储用户的 ETH 余额，而是存储用户拥有的「份额」。余额通过以下公式动态计算：

$$\text{balanceOf}(account) = \frac{\text{shares}[account] \times \text{totalPooledEther}}{\text{totalShares}}$$

公式中的三个变量分别是：`shares[account]` 表示用户拥有的份额数量，`totalPooledEther` 是协议控制的全部 ETH，`totalShares` 是所有用户份额的总和。

### 存款时的份额计算

当用户存入 ETH 时，协议需要计算应该给用户多少份额。这由 `getSharesByPooledEth` 函数完成：

```solidity
function getSharesByPooledEth(uint256 _ethAmount) public view returns (uint256) {
    return _ethAmount * _getTotalShares() / _getTotalPooledEther();
}
```

假设协议当前有 1,000,000 ETH 对应 900,000 份额。用户存入 100 ETH，获得的份额 = 100 × 900,000 / 1,000,000 = 90 份额。

注意这里的汇率：1 ETH 只能换到 0.9 份额。这是因为协议已经累积了奖励，每个份额对应的 ETH 已经超过 1。

### 为什么新用户不会稀释老用户

这是份额模型最精妙的地方。用一个具体例子来推演整个过程。

![新用户不稀释老用户](./no-dilution.png)

假设初始状态下，Alice 持有 100 份额，Bob 持有 400 份额，协议总共有 500 份额对应 500 ETH。此时汇率为 1:1，Alice 的余额是 100 ETH，Bob 的余额是 400 ETH。

当验证者获得 50 ETH 奖励后，totalPooledEther 变成 550 ETH，但 totalShares 保持 500 不变。根据余额公式重新计算：

$$\text{Alice 余额} = \frac{100 \times 550}{500} = 110 \text{ ETH}$$

$$\text{Bob 余额} = \frac{400 \times 550}{500} = 440 \text{ ETH}$$

Alice 增加了 10 ETH，Bob 增加了 40 ETH，奖励按份额比例自动分配，无需任何转账操作。

现在新用户 Carol 想存入 55 ETH。她能获得多少份额？按当前汇率计算：

$$\text{Carol 份额} = \frac{55 \times 500}{550} = 50 \text{ 份额}$$

存款后，totalShares 变成 550，totalPooledEther 变成 605 ETH。验证老用户的余额是否被稀释：

$$\text{Alice 余额} = \frac{100 \times 605}{550} = 110 \text{ ETH（不变）}$$

$$\text{Bob 余额} = \frac{400 \times 605}{550} = 440 \text{ ETH（不变）}$$

$$\text{Carol 余额} = \frac{50 \times 605}{550} = 55 \text{ ETH}$$

Carol 的加入没有稀释 Alice 和 Bob 的收益。这是因为 Carol 按当前汇率购买份额——她用 55 ETH 只换到了 50 份额，而不是 55 份额。这个「溢价」正好补偿了她获得的份额对应的已累积奖励。

---

## totalPooledEther：协议控制的三类资金

汇率计算的分母 `totalPooledEther` 是整个系统最关键的数值。它由三部分组成：

### 缓冲余额（Buffered Ether）

用户存入但尚未发送到信标链的 ETH。这部分资金存储在 Lido 主合约中，可以用于满足提款请求（快速路径），或者批量存入新验证者（每 32 ETH 一个）。

```solidity
function getBufferedEther() public view returns (uint256) {
    return BUFFERED_ETHER_POSITION.getStorageUint256();
}
```

### 过渡余额（Transient Balance）

已发送到以太坊官方 Deposit Contract，但验证者尚未在信标链激活的 ETH。

```solidity
function _getTransientBalance() internal view returns (uint256) {
    uint256 depositedValidators = DEPOSITED_VALIDATORS_POSITION.getStorageUint256();
    uint256 clValidators = CL_VALIDATORS_POSITION.getStorageUint256();
    // 已存款但未激活的验证者数量 × 32 ETH
    return (depositedValidators - clValidators) * DEPOSIT_SIZE;
}
```

验证者从存款到激活需要经过信标链的入队等待，这个时间取决于队列长度，可能从几小时到几天不等。

### 共识层余额（Consensus Layer Balance）

验证者在信标链上的实际余额总和。这是唯一会随时间增长（或因 slashing 减少）的部分。

```solidity
function _getTotalPooledEther() internal view returns (uint256) {
    return _getBufferedEther()
        + CL_BALANCE_POSITION.getStorageUint256()  // 共识层余额
        + _getTransientBalance();
}
```

关键问题在于：执行层合约无法直接读取共识层状态。`CL_BALANCE_POSITION` 的值必须由 Oracle 从链下同步上来。

---

## Oracle：连接两个世界的桥梁

以太坊的执行层（EVM）和共识层（信标链）是两个独立的状态机。执行层合约无法直接查询「我们的验证者现在有多少余额」。这个信息必须通过 Oracle 从链下带入。

![Oracle 报告流程](./oracle-flow.png)

### 为什么需要专用 Oracle

你可能会问：为什么不用 Chainlink 这样的通用 Oracle？

原因是数据的特殊性。Lido 需要的不是「ETH 价格」这样的公开市场数据，而是「Lido 管理的 31,250 个特定验证者的余额总和」。这个数据需要遍历大量验证者查询每个余额，需要通过提款凭证（withdrawal credentials）识别哪些是 Lido 的验证者，还需要处理 slashing、退出中、已退出等各种边缘情况。通用 Oracle 不具备这种专业能力，必须由协议自己运营专用 Oracle 网络。

### Lido 的 Oracle 架构

Lido 使用一个由多个节点组成的 Oracle 委员会，采用多签机制确保安全。整个流程分为四个阶段：首先是**数据收集**，每个 Oracle 节点独立查询信标链 API，获取所有 Lido 验证者的余额；然后是**哈希共识**，节点将报告数据哈希提交到 HashConsensus 合约；接着是**法定人数**确认，当超过 50% 的节点提交相同哈希时达成共识；最后是**报告提交**，其中一个节点提交完整报告数据，触发协议状态更新。

```solidity
struct ReportData {
    uint256 consensusVersion;      // 共识规则版本
    uint256 refSlot;               // 参考槽位
    uint256 numValidators;         // 验证者总数
    uint256 clBalanceGwei;         // 共识层余额（gwei）
    uint256 withdrawalVaultBalance;    // 提款金库余额
    uint256 elRewardsVaultBalance;     // 执行层奖励金库余额
    // ... 其他字段
}
```

### 报告周期

Oracle 报告按固定周期进行。每个报告帧长度为 225 个 epoch（约 1 天），参考槽位设置为每帧第一个 epoch 之前的最后一个槽位，处理窗口从参考槽位确定持续到帧结束。

为什么选择 225 epoch？这是在 Gas 成本和数据新鲜度之间的权衡。更频繁的报告意味着更高的 Gas 消耗，但用户看到的余额更接近实时。对于年化 3-5% 的质押收益，每天更新一次已经足够精确。

### 报告触发的状态变更

当 Oracle 报告被接受时，Lido 合约执行一系列操作：

```solidity
function handleOracleReport(
    uint256 _reportTimestamp,
    uint256 _timeElapsed,
    uint256 _clValidators,
    uint256 _clBalance,
    uint256 _withdrawalVaultBalance,
    uint256 _elRewardsVaultBalance,
    // ...
) external returns (uint256[4] postRebaseAmounts) {
    // 1. 更新共识层验证者数量和余额
    // 2. 从金库收集 ETH 到缓冲区
    // 3. 计算奖励并分配费用
    // 4. 处理提款请求
    // 5. 触发 Rebase 事件
}
```

这个函数是整个协议的「心跳」，每天执行一次，驱动所有状态更新。

---

## 信任假设与风险分析

Oracle 是流动性质押协议最大的信任假设。理解这些风险对于用户和开发者都很重要。

### Oracle 操纵攻击

如果 Oracle 被攻破，攻击者可以虚报高余额让协议认为验证者余额增加了，触发虚假的 Rebase 稀释所有持有者；或者虚报低余额让协议认为发生了大规模 slashing，触发恐慌性抛售；还可以延迟报告阻止提款请求被处理，造成流动性危机。

Lido 的防御措施包括多签机制（需要 9 个节点中的 5 个达成共识）、健全性检查（`OracleReportSanityChecker` 合约验证报告数据的合理性）、以及变化限制（单次报告的余额变化不能超过阈值）。

```solidity
// 简化的健全性检查逻辑
function checkAccountingOracleReport(
    uint256 _preCLBalance,
    uint256 _postCLBalance,
    uint256 _timeElapsed
) external view {
    // 检查余额变化是否在合理范围内
    uint256 maxIncrease = _preCLBalance * maxPositiveRebasePerDay * _timeElapsed / ONE_DAY;
    require(_postCLBalance <= _preCLBalance + maxIncrease, "Rebase too large");
}
```

### 去中心化的演进

Lido 的 Oracle 目前是许可制的——只有被批准的节点才能参与。这是一个中心化的信任点。

社区正在探索更去中心化的方案。**EIP-4788** 将信标链状态根暴露给执行层，允许合约直接验证信标链数据。**ZK 证明**方案使用零知识证明验证验证者余额，无需信任 Oracle。**乐观 Oracle** 允许任何人提交报告，但有挑战期和惩罚机制。这些方案都还在研发中，短期内 Oracle 委员会仍是主流设计。

### 与其他 Oracle 的对比

| 特性 | Lido Oracle | Chainlink | UMA |
|------|-------------|-----------|-----|
| 数据类型 | 协议专用 | 通用市场数据 | 任意 |
| 更新频率 | 每天 | 实时 | 按需 |
| 节点数量 | 9 | 数百 | 动态 |
| 许可模式 | 许可制 | 许可制 | 无许可 |
| 争议机制 | 无 | 无 | 有 |

Lido Oracle 的设计是针对特定用例优化的，不能简单地用通用 Oracle 替代。

---

## 汇率的经济学含义

理解汇率不仅是技术问题，也是经济问题。

### 汇率永远上涨吗

在正常情况下，是的。验证者持续获得质押奖励，totalPooledEther 增加，每个份额对应的 ETH 增加。

但有两种情况会导致汇率下跌。一是 **Slashing**，验证者因违规被罚没导致余额减少；二是**负奖励期**，如果大量验证者离线，整个网络的奖励可能为负。Lido 的历史上从未发生过汇率下跌，但这不意味着不可能。协议设计了「bunker 模式」来应对极端情况。

### 汇率与市场价格

stETH 的汇率（协议计算的理论价值）和市场价格（交易所的实际成交价）是两回事。

2022 年 6 月，stETH 在二级市场一度折价 5%。这不是因为协议出了问题，而是因为市场恐慌导致抛售压力，加上当时还没有提款功能 stETH 无法赎回，套利者无法消除价差。上海升级后，stETH 可以赎回为 ETH，市场价格与汇率的偏离大幅收窄。但在极端市场条件下，短期折价仍可能发生。

### 对 DeFi 的影响

汇率的持续上涨对 DeFi 协议有重要影响。在**借贷协议**中，使用 wstETH 作为抵押品时抵押价值会自动增加。在 **AMM** 中，stETH/ETH 池会产生「正向无常损失」——LP 的资产价值增加。在**期权协议**中，需要考虑汇率变化对行权价格的影响。

---

## 实现细节：代码层面的理解

最后，让我们看看核心函数的实际实现。

### 存款函数

```solidity
function _submit(address _referral) internal returns (uint256) {
    require(msg.value != 0, "ZERO_DEPOSIT");
    
    // 检查质押限制
    StakeLimitState.Data memory stakeLimitData = STAKING_STATE_POSITION.getStorageStakeLimitStruct();
    require(!stakeLimitData.isStakingPaused(), "STAKING_PAUSED");
    
    if (stakeLimitData.isStakingLimitSet()) {
        uint256 currentStakeLimit = stakeLimitData.calculateCurrentStakeLimit();
        require(msg.value <= currentStakeLimit, "STAKE_LIMIT");
        STAKING_STATE_POSITION.setStorageStakeLimitStruct(
            stakeLimitData.updatePrevStakeLimit(currentStakeLimit - msg.value)
        );
    }
    
    // 计算份额并铸造
    uint256 sharesAmount = getSharesByPooledEth(msg.value);
    _mintShares(msg.sender, sharesAmount);
    
    // 更新缓冲余额
    _setBufferedEther(_getBufferedEther() + msg.value);
    
    emit Submitted(msg.sender, msg.value, _referral);
    return sharesAmount;
}
```

注意质押限制机制：协议可以设置每个区块的最大存款量，防止协议增长过快导致验证者队列拥堵。

### 余额查询函数

```solidity
function balanceOf(address _account) public view returns (uint256) {
    return getPooledEthByShares(_sharesOf(_account));
}

function getPooledEthByShares(uint256 _sharesAmount) public view returns (uint256) {
    return _sharesAmount * _getTotalPooledEther() / _getTotalShares();
}
```

每次调用 `balanceOf` 都是实时计算的，不是读取存储的值。这就是 Rebase 的实现原理。

### 转账函数

```solidity
function _transfer(address _sender, address _recipient, uint256 _amount) internal {
    uint256 _sharesToTransfer = getSharesByPooledEth(_amount);
    _transferShares(_sender, _recipient, _sharesToTransfer);
    emit Transfer(_sender, _recipient, _amount);
}
```

转账时，协议先将 ETH 数量转换为份额，然后转移份额。这确保了转账金额的精确性。

---

## 局限性与权衡

份额模型虽然优雅，但也有其局限。**精度损失**是第一个问题，份额和 ETH 之间的转换涉及除法，可能产生舍入误差。**Gas 成本**是第二个问题，每次余额查询都需要计算，比直接读取存储值更贵。**ERC-20 不完全兼容**是第三个问题，Rebase 时不发出 Transfer 事件，某些工具可能无法正确追踪余额变化。最后是 **Oracle 依赖**，汇率的准确性完全依赖 Oracle 的诚实和可用性。

这些是设计上的权衡，不是缺陷。理解这些权衡有助于在集成时做出正确的决策。

---

## 进一步阅读

- [Lido 官方文档：stETH](https://docs.lido.fi/contracts/lido/) — 合约接口的完整参考
- [Lido 官方文档：AccountingOracle](https://docs.lido.fi/contracts/accounting-oracle/) — Oracle 机制的详细说明
- [EIP-4626: Tokenized Vault Standard](https://eips.ethereum.org/EIPS/eip-4626) — wstETH 兼容的金库标准
- [Lido 代码仓库](https://github.com/lidofinance/lido-dao) — 合约源码
