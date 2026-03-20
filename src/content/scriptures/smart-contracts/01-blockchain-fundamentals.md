# 第 1 章：区块链与以太坊基础

> 智能合约运行在区块链上。在编写第一行 Solidity 代码之前，理解区块链的核心原理是必要的——它决定了你的代码如何被执行、存储和验证。

---

## 区块链概述

区块链是一种分布式账本技术，所有参与节点都持有完整的数据副本。与传统数据库不同，区块链没有中央服务器，数据分散存储在全球数千个节点上。这种架构通过密码学和共识机制实现了三个关键特性：数据一致性、不可篡改性和去中心化。

数据一致性意味着所有节点最终会看到相同的数据状态。当一笔交易被确认后，全网所有节点都会更新到相同的状态。不可篡改性是指历史记录一旦写入，就无法被修改或删除。去中心化则确保没有单一实体能够控制整个网络。

这些特性直接影响智能合约的设计。你无法"修复"已部署的合约代码——如果发现 bug，只能部署新版本并迁移数据。你无法删除链上数据——即使是错误的数据也会永久保存。每次状态变更都需要付费——这就是 Gas 机制存在的原因。理解这些约束是写出安全、高效合约的前提。

### 区块结构

以太坊的每个区块由区块头（Block Header）和区块体（Block Body）两部分组成。

![区块结构](/images/scriptures/smart-contracts/01-block-structure.png)

区块头包含了区块的元数据。`parentHash` 是前一区块的哈希值，它将区块链接成一条链。`stateRoot` 是世界状态树的根哈希，记录了所有账户的当前状态。`transactionsRoot` 和 `receiptsRoot` 分别是交易树和收据树的根哈希。`number` 是区块高度，从创世区块的 0 开始递增。`timestamp` 是出块时间戳。`gasLimit` 是区块能容纳的最大 Gas 总量，`gasUsed` 是实际使用的 Gas。`baseFeePerGas` 是 EIP-1559 引入的基础费用。

区块体包含了实际的交易数据。`transactions` 数组存储本区块包含的所有交易。在以太坊转向 PoS 后，还增加了 `withdrawals` 数组用于记录验证者的提款。

`parentHash` 是不可篡改性的核心机制。每个区块都包含前一区块的哈希值，如果攻击者试图修改历史交易，该区块的哈希会改变，导致后续所有区块的 `parentHash` 失效。要使篡改生效，攻击者必须重新计算从被修改区块到最新区块的所有哈希。在 PoS 机制下，这需要控制超过三分之二的质押 ETH，经济上完全不可行。

### 交易结构

交易是改变区块链状态的唯一方式。无论是转账 ETH、调用合约函数还是部署新合约，都必须通过交易完成。

每笔交易包含以下字段：`nonce` 是发送者的交易序号，从 0 开始严格递增。`to` 是接收地址，部署合约时为空。`value` 是转账金额，单位是 wei（1 ETH = 10^18 wei）。`data` 是调用数据，包含函数选择器和参数，部署合约时则是合约字节码。`gasLimit` 是用户愿意支付的最大 Gas 数量。`maxFeePerGas` 和 `maxPriorityFeePerGas` 是 EIP-1559 引入的费用参数。`signature` 是发送者的 ECDSA 签名。

nonce 的作用值得特别说明。nonce 必须严格递增，如果你发送 nonce=5 的交易，但 nonce=4 还未确认，交易会卡在内存池中等待。这个机制防止了交易重放攻击——攻击者无法复制一笔已确认的交易再次广播，因为 nonce 已经被使用过了。但这也意味着一笔卡住的交易会阻塞后续所有交易，解决方法是用相同的 nonce 发送一笔新交易来替换它。

---

## 以太坊账户模型

以太坊采用账户模型，而非比特币的 UTXO 模型。账户模型更直观，也更适合智能合约，因为它天然支持状态存储。每个账户都有一个余额和一个 nonce，合约账户还有代码和存储。

![以太坊账户模型](/images/scriptures/smart-contracts/02-account-model.png)

以太坊有两种账户类型：外部账户（EOA）和合约账户。

外部账户由私钥控制。用户通过私钥签名来授权交易，任何拥有私钥的人都可以控制该账户。EOA 只有两个字段：`nonce` 记录已发送的交易数，`balance` 记录 ETH 余额。EOA 可以主动发起交易，可以持有和转移 ETH。

合约账户由代码逻辑控制。合约没有私钥，它的行为完全由部署时的代码决定。合约账户有四个字段：`nonce` 记录该合约创建的子合约数，`balance` 记录 ETH 余额，`codeHash` 是合约代码的哈希，`storageRoot` 是存储树的根哈希。合约不能主动发起交易，只能被调用后执行代码。

这里有一个核心约束需要理解：合约不能"自己运行"。没有 cron job，没有定时任务，没有后台进程。如果你的业务逻辑需要定期执行，比如每天结算利息或每周分发奖励，必须依赖外部服务来触发。Chainlink Automation 和 Gelato 是常用的解决方案，它们会在满足条件时调用你的合约函数。

### 地址生成机制

![地址生成机制](/images/scriptures/smart-contracts/03-address-generation.png)

EOA 地址由公钥派生。首先用椭圆曲线算法从私钥生成公钥，然后对公钥进行 keccak256 哈希，取结果的后 20 字节作为地址。这个过程是单向的——从地址无法反推出公钥或私钥。

合约地址有两种生成方式。传统的 CREATE 方式下，地址取决于部署者地址和部署者的 nonce。这意味着同一个部署者在不同时间部署相同的代码，会得到不同的地址。

CREATE2 是确定性部署方式，地址取决于部署者地址、一个 salt 值和合约字节码的哈希。这允许在部署前就计算出合约地址。CREATE2 的实际应用非常广泛：工厂模式可以预测子合约地址，反事实部署允许先使用地址再部署合约，跨链部署可以确保相同的代码在不同链上有相同的地址。Uniswap V2 的交易对合约就使用 CREATE2，确保 ETH/USDC 交易对在任何链上都有相同的地址。

---

## EVM 执行模型

EVM（Ethereum Virtual Machine）是以太坊的运行时环境。所有智能合约最终都被编译为 EVM 字节码执行。理解 EVM 的架构对于编写高效合约和调试问题至关重要。

EVM 是一个基于栈的虚拟机。与基于寄存器的虚拟机不同，EVM 的所有操作都在栈上进行。栈的最大深度是 1024，每个栈项是 256 位。这个设计简化了虚拟机的实现，但也带来了一些限制，比如著名的"Stack too deep"错误。

![EVM 数据区域](/images/scriptures/smart-contracts/04-evm-data-regions.png)

EVM 有四个主要的数据区域。Stack 是操作栈，所有计算都在这里进行，访问是免费的。Memory 是临时内存，在函数调用期间有效，按字节寻址，线性扩展，成本较低。Storage 是永久存储，数据保存在区块链上，按 256 位的槽寻址，成本最高。Calldata 是只读的调用数据区域，存储函数参数，成本最低。

Gas 成本的排序是：Calldata < Stack < Memory < Storage。这个排序直接影响了 Gas 优化策略。如果一个存储变量在函数中被多次读取，应该先缓存到内存变量中，避免重复的 SLOAD 操作。

EVM 有三个关键特性。确定性执行意味着相同的输入必须产生相同的输出，这是共识机制的基础。因此合约不能使用随机数、系统时间（除了 `block.timestamp`）或外部 API。隔离性意味着每个合约在独立的执行环境中运行，只能通过消息调用与其他合约交互。原子性意味着交易要么完全成功，要么完全回滚，不存在中间状态。

栈深度限制是一个常见的坑。虽然栈最大深度是 1024，但实际可用约 1000 层，因为一些内部操作需要预留空间。深度递归或过多的局部变量会导致"Stack too deep"编译错误。解决方法包括减少局部变量数量、将变量打包到结构体中、或者将函数拆分成多个小函数。

---

## Gas 机制详解

Gas 是 EVM 的计算资源计量单位。每个操作都有固定的 Gas 成本，用户为交易支付 Gas 费用。这个机制有两个目的：防止滥用和激励验证者。

防止滥用是指无限循环会消耗完 Gas 后自动停止，而不是让网络陷入死循环。如果没有 Gas 机制，恶意用户可以部署一个无限循环的合约，让所有节点永远执行下去。激励验证者是指 Gas 费用作为验证者打包交易的收入，确保有人愿意运行节点。

![Gas 机制](/images/scriptures/smart-contracts/05-gas-mechanism.png)

不同操作的 Gas 成本差异很大。每笔交易有 21,000 的基础费用，这是固定成本。存储操作是最昂贵的：写入新存储槽（SSTORE 从 0 到非 0）需要 20,000 Gas，更新已有存储槽需要 5,000 Gas，清空存储槽会退还 4,800 Gas。读取存储槽（SLOAD）的成本取决于是否是首次访问：冷访问需要 2,100 Gas，热访问只需要 100 Gas。内存操作（MLOAD/MSTORE）只需要 3 Gas。算术运算（ADD/SUB/MUL）需要 3-5 Gas。调用外部合约（CALL）在冷地址时需要 2,600 Gas。

冷/热访问的概念来自 EIP-2929（柏林升级）。首次访问某个地址或存储槽称为"冷访问"，成本较高；同一交易内的后续访问称为"热访问"，成本大幅降低。这影响了 Gas 优化策略：如果一个存储变量在函数中被多次读取，应该在函数开始时缓存到内存变量中，后续使用内存变量而非重复读取存储。

### EIP-1559 费用模型

2021 年伦敦升级引入了新的 Gas 定价机制。在旧模型中，用户设置一个 Gas 价格，出价高的交易优先被打包，这导致了激烈的价格竞拍和剧烈的价格波动。

新模型将费用分为两部分：baseFee 和 priorityFee。baseFee 由协议根据网络拥堵程度动态调整，每个区块最多变化 12.5%。当区块使用量超过目标（50%）时，baseFee 上涨；低于目标时，baseFee 下降。baseFee 会被销毁，不会给验证者。priorityFee 是用户给验证者的小费，用于激励验证者优先打包自己的交易。

实际费用的计算公式是：(baseFee + priorityFee) × gasUsed。用户设置 maxFeePerGas 作为愿意支付的最高价格，如果 baseFee + priorityFee 超过这个值，交易会等待 baseFee 下降。

这个模型的优势是 Gas 价格更可预测，因为 baseFee 的变化是渐进的。同时 ETH 有了通缩机制，因为 baseFee 被销毁。在网络繁忙时，大量 ETH 被销毁，可能超过新发行的 ETH，导致总供应量下降。

---

## 开发环境搭建

现代 Solidity 开发推荐使用 Foundry 工具链。Foundry 由 Rust 编写，编译速度快，测试功能强大，已经成为专业开发者的首选工具。

Foundry 包含三个主要工具：forge 是编译器和测试框架，cast 是命令行交互工具，anvil 是本地测试网络。安装非常简单，只需要运行官方的安装脚本。

```bash
# 安装 Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

安装完成后可以验证版本。

```bash
# 验证安装
forge --version   # 编译器和测试框架
cast --version    # 命令行交互工具
anvil --version   # 本地测试网络
```

创建新项目使用 `forge init` 命令。

```bash
# 初始化新项目
forge init my-project
cd my-project
# 项目结构: src/(合约) test/(测试) script/(部署) foundry.toml(配置)
```

项目结构包含四个目录：src 存放合约源码，test 存放测试文件，script 存放部署脚本，foundry.toml 是配置文件。

下面是一个简单的计数器合约，演示了状态变量、函数和事件的基本用法。

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Counter {
    uint256 public count;  // 状态变量，存储在链上
    
    event CountChanged(uint256 newCount);  // 事件，用于通知前端
    
    function increment() external {
        count++;
        emit CountChanged(count);
    }
    
    function decrement() external {
        require(count > 0, "Counter: cannot decrement below zero");
        count--;
        emit CountChanged(count);
    }
}
```

编译、测试和部署的命令如下。

```bash
forge build    # 编译合约
forge test     # 运行测试
anvil          # 启动本地测试网络
# 部署到本地网络（使用 Anvil 默认测试账户）
forge create src/Counter.sol:Counter --rpc-url http://localhost:8545 --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

上面的私钥是 Anvil 默认测试账户，仅用于本地开发。永远不要在命令行中使用真实私钥，生产环境应使用硬件钱包或密钥管理服务。

---

## 总结

本章建立了智能合约开发的概念基础。区块链通过密码学保证数据一致性和不可篡改性，以太坊的账户模型支持智能合约的状态存储，EVM 提供了确定性的执行环境，Gas 机制防止资源滥用并激励验证者。

这些底层原理直接影响智能合约的设计决策。不可变性意味着需要升级模式来修复 bug。Gas 成本意味着需要优化存储访问。被动执行意味着需要外部触发机制。公开透明意味着不能存储敏感数据。

下一章将深入 Solidity 语言本身——数据类型、函数、修饰符等核心语法。

---

## 参考文献

- [Ethereum Developer Documentation](https://ethereum.org/en/developers/docs/)
- [EVM Codes](https://www.evm.codes/)
- [EIP-1559: Fee market change](https://eips.ethereum.org/EIPS/eip-1559)
- [EIP-2929: Gas cost increases for state access opcodes](https://eips.ethereum.org/EIPS/eip-2929)
- [Foundry Book](https://book.getfoundry.sh/)
- [Solidity Documentation](https://docs.soliditylang.org/)
