# 第 8 章：测试与部署

> 代码写完只是开始。没有经过充分测试的合约就像没有经过检验的桥梁——看起来能用，但随时可能崩塌。本章介绍如何用 Foundry 构建可靠的测试体系，以及如何安全地将合约部署到生产环境。

---

## 为什么测试如此重要

智能合约与传统软件有一个根本区别：部署后无法修改。一个 bug 在传统应用中可能只是一次热修复，但在智能合约中可能意味着数百万美元的损失。2016 年的 DAO 攻击、2022 年的 Wormhole 漏洞、2023 年的 Euler Finance 事件，每一次都是血淋淋的教训。

测试不是可选的，而是必须的。好的测试不仅能发现 bug，还能作为合约行为的文档，帮助其他开发者理解代码的预期行为。当你修改代码时，测试会告诉你是否破坏了现有功能。

Foundry 是目前最流行的 Solidity 测试框架。它用 Solidity 编写测试（而不是 JavaScript），执行速度极快，并提供了强大的作弊码（cheatcodes）来模拟各种场景。

---

## Foundry 测试基础

一个 Foundry 测试文件的基本结构如下：

```solidity
// test/Counter.t.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test, console} from "forge-std/Test.sol";
import {Counter} from "../src/Counter.sol";

contract CounterTest is Test {
    Counter public counter;
    
    function setUp() public {
        counter = new Counter();
    }
    
    function test_Increment() public {
        counter.increment();
        assertEq(counter.count(), 1);
    }
    
    function test_RevertWhen_DecrementBelowZero() public {
        vm.expectRevert("Count is zero");
        counter.decrement();
    }
}
```

测试合约继承自 `Test`，这提供了断言函数和作弊码。`setUp` 函数在每个测试之前执行，用于初始化测试环境。测试函数必须以 `test` 开头，Foundry 会自动发现并执行它们。

运行测试很简单：

```bash
forge test                           # 运行所有测试
forge test --match-test test_Increment  # 运行特定测试
forge test -vvvv                     # 显示详细输出
forge test --gas-report              # 生成 Gas 报告
```

`-v` 参数控制输出详细程度。`-vvvv` 会显示每一步的执行细节，包括调用栈和存储变化，这在调试失败的测试时非常有用。

---

## 断言：验证预期行为

断言是测试的核心。Foundry 提供了丰富的断言函数：

```solidity
// 相等性检查
assertEq(a, b);                      // a == b
assertEq(a, b, "Error message");     // 带错误信息
assertNotEq(a, b);                   // a != b

// 比较
assertGt(a, b);                      // a > b
assertGe(a, b);                      // a >= b
assertLt(a, b);                      // a < b
assertLe(a, b);                      // a <= b

// 布尔
assertTrue(condition);
assertFalse(condition);

// 近似相等（处理精度问题）
assertApproxEqAbs(a, b, maxDelta);   // |a - b| <= maxDelta
assertApproxEqRel(a, b, maxPercent); // |a - b| / b <= maxPercent
```

近似相等断言在处理除法或百分比计算时特别有用。由于 Solidity 没有浮点数，除法会产生舍入误差，使用 `assertApproxEqAbs` 可以容忍小范围的误差。

---

## 作弊码：模拟任何场景

作弊码是 Foundry 最强大的功能。它们允许你操纵 EVM 状态，模拟各种难以在真实环境中重现的场景。

### 身份模拟

```solidity
function test_OnlyOwner() public {
    address alice = makeAddr("alice");
    address bob = makeAddr("bob");
    
    // 以 alice 身份执行下一次调用
    vm.prank(alice);
    contract.ownerFunction();
    
    // 以 bob 身份执行多次调用
    vm.startPrank(bob);
    contract.function1();
    contract.function2();
    vm.stopPrank();
}
```

`makeAddr` 创建一个带标签的地址，在调试输出中会显示 "alice" 而不是一串十六进制数字。`prank` 只影响下一次调用，`startPrank/stopPrank` 影响一个范围内的所有调用。

### 余额操作

```solidity
function test_Deposit() public {
    address user = makeAddr("user");
    
    // 设置 ETH 余额
    vm.deal(user, 100 ether);
    assertEq(user.balance, 100 ether);
    
    // 设置 ERC20 余额
    deal(address(token), user, 1000e18);
    assertEq(token.balanceOf(user), 1000e18);
}
```

`vm.deal` 设置 ETH 余额，`deal`（不带 vm 前缀）设置 ERC20 余额。后者会自动处理存储槽的计算，非常方便。

### 时间操作

```solidity
function test_TimeLock() public {
    // 设置区块时间
    vm.warp(1000);
    assertEq(block.timestamp, 1000);
    
    // 增加时间
    skip(1 days);
    assertEq(block.timestamp, 1000 + 1 days);
    
    // 设置区块号
    vm.roll(100);
    assertEq(block.number, 100);
}
```

时间操作对于测试时间锁、vesting 合约、利息计算等场景至关重要。

### 预期 Revert

```solidity
function test_Revert() public {
    // 预期错误消息
    vm.expectRevert("Insufficient balance");
    contract.withdraw(1000);
    
    // 预期自定义错误
    vm.expectRevert(InsufficientBalance.selector);
    contract.withdraw(1000);
    
    // 预期带参数的自定义错误
    vm.expectRevert(abi.encodeWithSelector(
        InsufficientBalance.selector,
        100,  // available
        1000  // requested
    ));
    contract.withdraw(1000);
}
```

`expectRevert` 必须在会 revert 的调用之前调用。如果下一次调用没有 revert，或者 revert 的原因不匹配，测试就会失败。

### 预期事件

```solidity
function test_EmitEvent() public {
    // 参数：checkTopic1, checkTopic2, checkTopic3, checkData
    vm.expectEmit(true, true, false, true);
    emit Transfer(alice, bob, 100);
    
    token.transfer(bob, 100);
}
```

`expectEmit` 的四个布尔参数控制检查哪些部分。前三个对应 indexed 参数（topic），最后一个对应非 indexed 数据。

---

## Fuzz 测试：让机器找 Bug

手动编写测试用例只能覆盖你想到的场景。Fuzz 测试让 Foundry 自动生成随机输入，可能发现你从未想到的边界情况。

```solidity
function testFuzz_Deposit(uint256 amount) public {
    // 限制输入范围
    vm.assume(amount > 0 && amount <= 1000 ether);
    
    vm.deal(address(this), amount);
    vault.deposit{value: amount}();
    
    assertEq(vault.balanceOf(address(this)), amount);
}
```

`vm.assume` 过滤掉不满足条件的输入。Foundry 会自动运行数百次测试，每次使用不同的随机值。

对于地址类型的 fuzz 测试，需要排除一些特殊地址：

```solidity
function testFuzz_Transfer(address to, uint256 amount) public {
    vm.assume(to != address(0));           // 排除零地址
    vm.assume(to != address(token));       // 排除合约自身
    vm.assume(to.code.length == 0);        // 排除合约地址
    
    // ... 测试逻辑
}
```

可以在 `foundry.toml` 中配置 fuzz 测试的运行次数：

```toml
[fuzz]
runs = 1000
max_test_rejects = 65536
```

---

## 不变量测试：验证系统属性

Fuzz 测试验证单个函数的行为，不变量测试验证整个系统在任意操作序列后都保持某些属性。

![测试金字塔](/images/scriptures/smart-contracts/08-testing-pyramid.png)

例如，一个金库合约应该始终满足：用户余额之和等于合约持有的 ETH。

```solidity
contract VaultInvariantTest is Test {
    Vault public vault;
    VaultHandler public handler;
    
    function setUp() public {
        vault = new Vault();
        handler = new VaultHandler(vault);
        targetContract(address(handler));
    }
    
    function invariant_SolvencyCheck() public {
        assertEq(vault.totalDeposits(), address(vault).balance);
    }
}
```

Handler 合约定义了可以执行的操作：

```solidity
contract VaultHandler is Test {
    Vault public vault;
    address[] public actors;
    
    constructor(Vault _vault) {
        vault = _vault;
    }
    
    function deposit(uint256 amount) public {
        amount = bound(amount, 0.01 ether, 10 ether);
        address actor = msg.sender;
        
        vm.deal(actor, amount);
        vm.prank(actor);
        vault.deposit{value: amount}();
        
        actors.push(actor);
    }
    
    function withdraw(uint256 amount) public {
        address actor = msg.sender;
        uint256 balance = vault.balanceOf(actor);
        amount = bound(amount, 0, balance);
        
        vm.prank(actor);
        vault.withdraw(amount);
    }
}
```

`bound` 函数将随机值限制在指定范围内，比 `vm.assume` 更高效，因为它不会丢弃输入。

Foundry 会随机调用 handler 的函数，构建各种操作序列，然后检查不变量是否被破坏。这种测试方法特别适合发现复杂的状态转换 bug。

---

## Fork 测试：在真实环境中验证

有些功能需要与已部署的合约交互，比如 DEX 集成、预言机调用等。Fork 测试允许你在主网状态的副本上运行测试。

```solidity
contract ForkTest is Test {
    uint256 mainnetFork;
    
    function setUp() public {
        mainnetFork = vm.createFork(vm.envString("MAINNET_RPC_URL"));
        vm.selectFork(mainnetFork);
    }
    
    function test_SwapOnUniswap() public {
        address WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
        address USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;
        
        deal(WETH, address(this), 1 ether);
        
        // 在真实的 Uniswap 合约上测试
        // ...
    }
}
```

你甚至可以在特定区块高度创建 fork，重现历史状态：

```solidity
vm.createSelectFork(vm.envString("MAINNET_RPC_URL"), 18000000);
```

这对于复现和分析历史漏洞非常有用。

---

## 部署脚本

Foundry 使用 Solidity 编写部署脚本，这比 JavaScript 脚本更类型安全，也更容易与合约代码保持一致。

```solidity
// script/Deploy.s.sol
contract DeployScript is Script {
    function run() public {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        vm.startBroadcast(deployerPrivateKey);
        
        // 部署实现合约
        MyContract implementation = new MyContract();
        console.log("Implementation:", address(implementation));
        
        // 部署代理
        bytes memory initData = abi.encodeCall(
            MyContract.initialize,
            (msg.sender)
        );
        ERC1967Proxy proxy = new ERC1967Proxy(
            address(implementation),
            initData
        );
        console.log("Proxy:", address(proxy));
        
        vm.stopBroadcast();
    }
}
```

`vm.startBroadcast` 和 `vm.stopBroadcast` 之间的所有交易会被记录并广播到网络。

运行部署脚本：

```bash
# 模拟部署（不实际发送交易）
forge script script/Deploy.s.sol --fork-url $RPC_URL

# 实际部署
forge script script/Deploy.s.sol \
    --rpc-url $SEPOLIA_RPC_URL \
    --broadcast \
    --verify \
    --etherscan-api-key $ETHERSCAN_API_KEY \
    -vvvv
```

`--broadcast` 实际发送交易，`--verify` 自动在 Etherscan 上验证合约源码。

---

## 合约验证

验证合约源码让用户可以在 Etherscan 上阅读和验证合约逻辑，这是建立信任的重要步骤。

如果部署时没有自动验证，可以手动验证：

```bash
forge verify-contract \
    --chain-id 1 \
    --num-of-optimizations 200 \
    --compiler-version v0.8.20+commit.a1b79de6 \
    --etherscan-api-key $ETHERSCAN_API_KEY \
    $CONTRACT_ADDRESS \
    src/MyContract.sol:MyContract
```

对于有构造函数参数的合约：

```bash
forge verify-contract \
    --constructor-args $(cast abi-encode "constructor(address,uint256)" 0x... 100) \
    ...
```

---

## Gas 优化分析

部署前应该分析 Gas 消耗，确保成本在可接受范围内。

```bash
forge test --gas-report
```

输出会显示每个函数的 Gas 消耗统计：

```
| Function Name | min   | avg   | median | max   | # calls |
|---------------|-------|-------|--------|-------|---------|
| deposit       | 22338 | 45672 | 45672  | 69006 | 100     |
| withdraw      | 8462  | 12462 | 12462  | 16462 | 50      |
```

Gas 快照可以追踪 Gas 消耗的变化：

```bash
forge snapshot           # 生成快照
forge snapshot --diff    # 对比变化
forge snapshot --check   # CI 中检查是否超出阈值
```

---

## 安全检查清单

部署到主网前，应该完成以下检查：

**代码质量**
- 所有关键路径都有测试覆盖
- Fuzz 测试运行了足够多的次数
- 不变量测试验证了核心属性
- 在 fork 环境中测试了外部集成

**安全审计**
- 运行了 Slither 静态分析
- 检查了常见漏洞模式（重入、溢出、访问控制）
- 如果金额较大，进行了专业审计

**部署配置**
- 构造函数/初始化参数正确
- 权限地址（owner、admin）设置正确
- 外部合约地址（预言机、DEX）正确
- 使用多签钱包部署

**应急准备**
- 有暂停机制
- 有升级路径（如果需要）
- 有监控和告警

---

## 总结

测试和部署是将合约推向生产环境的最后一步，也是最关键的一步。Foundry 提供了强大的工具链：单元测试验证基本功能，fuzz 测试发现边界情况，不变量测试验证系统属性，fork 测试在真实环境中验证集成。

但工具只是手段，真正重要的是测试思维：思考合约可能出错的方式，然后编写测试来验证它不会出错。每一个 `assertEq` 都是对合约行为的一个承诺，每一个 `expectRevert` 都是对错误处理的一个保证。

部署不是终点，而是新的开始。合约上线后需要持续监控，准备好应对可能出现的问题。在 Web3 的世界里，"move fast and break things" 的代价太高了——我们需要的是 "move carefully and build things that last"。

---

## 参考文献

- [Foundry Book](https://book.getfoundry.sh/)
- [Foundry Cheatcodes Reference](https://book.getfoundry.sh/cheatcodes/)
- [Slither Documentation](https://github.com/crytic/slither)
- [Smart Contract Security Best Practices](https://consensys.github.io/smart-contract-best-practices/)
- [Trail of Bits Testing Handbook](https://appsec.guide/)
