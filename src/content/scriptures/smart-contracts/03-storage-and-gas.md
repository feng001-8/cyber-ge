# 第 3 章：数据存储与 Gas 优化

> Gas 是智能合约的运行成本。理解 EVM 的存储机制和 Gas 定价规则，是编写高效合约的基础。

---

## 存储槽机制

EVM 的永久存储是一个巨大的键值映射，键和值都是 256 位。每个合约有自己独立的存储空间，从槽 0 开始编号。状态变量按照声明顺序依次占用存储槽，但 EVM 会尽可能将多个小变量打包到同一个槽中。

![存储槽布局](/images/scriptures/smart-contracts/03-storage-layout.png)

一个存储槽是 32 字节（256 位）。如果一个变量小于 32 字节，EVM 会尝试将它与后续的变量打包到同一个槽中。打包的规则是：从右向左填充，如果当前槽剩余空间不足以容纳下一个变量，则开启新槽。

下面的合约演示了存储槽的分配方式。

```solidity
contract StorageLayout {
    uint256 a;      // 槽 0（完整占用）
    uint128 b;      // 槽 1 低 128 位
    uint128 c;      // 槽 1 高 128 位（与 b 打包）
    uint64 d;       // 槽 2 低 64 位
    uint64 e;       // 槽 2 中 64 位
    uint64 f;       // 槽 2 高 64 位
    uint64 g;       // 槽 2 最高 64 位（4 个 uint64 正好填满）
    uint256 h;      // 槽 3（完整占用）
}
```

`uint256` 独占一个槽，因为它正好是 32 字节。两个 `uint128` 可以打包到一个槽中，四个 `uint64` 也可以打包到一个槽中。这种打包机制可以显著减少存储槽的使用数量，从而降低 Gas 成本。

但是，变量的声明顺序会影响打包效果。如果把上面的合约改成这样，存储效率会大幅下降。

```solidity
contract BadLayout {
    uint256 a;      // 槽 0
    uint64 d;       // 槽 1（只用了 8 字节，浪费 24 字节）
    uint256 h;      // 槽 2（uint256 必须独占一槽）
    uint128 b;      // 槽 3 低 128 位
    uint64 e;       // 槽 3 高 64 位（与 b 打包）
    uint128 c;      // 槽 4（剩余空间不够，开新槽）
    uint64 f;       // 槽 4 高 64 位
    uint64 g;       // 槽 5
}
```

原本只需要 4 个槽的数据，现在需要 6 个槽。每个额外的槽在首次写入时需要 20,000 Gas，这是一笔可观的成本。

### 动态类型的存储

动态数组和映射的存储方式比较特殊。它们不能直接存储在声明位置的槽中，因为大小不确定。

动态数组在声明位置的槽中存储数组长度，实际元素存储在 `keccak256(slot)` 开始的连续槽中。

```solidity
contract DynamicArray {
    uint256[] public arr;  // 槽 0 存储 arr.length
    
    // arr[0] 存储在 keccak256(0) 位置
    // arr[1] 存储在 keccak256(0) + 1 位置
    // arr[n] 存储在 keccak256(0) + n 位置
}
```

映射在声明位置的槽不存储任何数据（始终为 0）。每个键值对存储在 `keccak256(key . slot)` 位置，其中 `.` 表示拼接。

```solidity
contract MappingStorage {
    mapping(address => uint256) public balances;  // 槽 0（空）
    
    // balances[addr] 存储在 keccak256(addr . 0) 位置
}
```

嵌套映射的计算方式是递归的。`mapping(address => mapping(address => uint256))` 中，`map[a][b]` 存储在 `keccak256(b . keccak256(a . slot))` 位置。

---

## Gas 成本详解

Gas 是 EVM 的计算资源计量单位。不同操作的 Gas 成本差异巨大，理解这些差异是优化的基础。

![Gas 成本对比](/images/scriptures/smart-contracts/03-gas-costs.png)

### 存储操作

存储操作是最昂贵的。SSTORE（写入存储）的成本取决于当前值和新值的状态。

从零写入非零值需要 20,000 Gas，这是最昂贵的操作。从非零值改为另一个非零值需要 5,000 Gas。从非零值改为零会退还 4,800 Gas（但退还有上限，不能超过交易总 Gas 的 20%）。

SLOAD（读取存储）的成本取决于是否是首次访问。冷访问（同一交易中首次读取该槽）需要 2,100 Gas，热访问（已经读取过）只需要 100 Gas。

```solidity
contract StorageCost {
    uint256 public value;  // 槽 0
    
    function expensive() external {
        value = 1;  // 冷 SLOAD (2100) + SSTORE 0→1 (20000) = 22100 Gas
    }
    
    function cheaper() external {
        value = 2;  // 冷 SLOAD (2100) + SSTORE 1→2 (5000) = 7100 Gas
    }
    
    function cheapest() external {
        value = 0;  // 冷 SLOAD (2100) + SSTORE 2→0 (5000 - 4800) = 2300 Gas
    }
}
```

### 内存操作

内存操作比存储便宜得多。MLOAD 和 MSTORE 只需要 3 Gas。但内存有一个特殊的成本模型：随着使用量增加，扩展成本会二次增长。

内存按 32 字节的字（word）计费。前几个字很便宜，但当内存使用量超过一定阈值后，每增加一个字的成本会显著上升。这个设计防止了合约无限制地使用内存。

```solidity
function memoryExpansion() external pure {
    uint256[] memory arr = new uint256[](100);   // 扩展到 3200 字节
    uint256[] memory arr2 = new uint256[](1000); // 扩展到 32000 字节，成本急剧上升
}
```

### Calldata 操作

Calldata 是最便宜的数据区域。读取 calldata 只需要 3 Gas，而且没有扩展成本。这就是为什么外部函数的数组参数应该使用 `calldata` 而不是 `memory`。

```solidity
// 推荐：使用 calldata
function processData(uint256[] calldata data) external pure returns (uint256) {
    uint256 sum = 0;
    for (uint256 i = 0; i < data.length; i++) {
        sum += data[i];  // 直接从 calldata 读取
    }
    return sum;
}

// 不推荐：使用 memory（会复制整个数组）
function processDataBad(uint256[] memory data) external pure returns (uint256) {
    uint256 sum = 0;
    for (uint256 i = 0; i < data.length; i++) {
        sum += data[i];
    }
    return sum;
}
```

---

## Transient Storage (EIP-1153)

2024 年 3 月的 Cancun 升级引入了瞬态存储（Transient Storage），这是 EVM 的第四种数据位置。瞬态存储的数据只在当前交易内有效，交易结束后自动清零。

瞬态存储通过两个新操作码实现：`TSTORE` 写入数据，`TLOAD` 读取数据。它们的 Gas 成本约为 100，远低于永久存储的 5,000-20,000 Gas。这使得某些模式的实现成本大幅降低。

### 原生语法支持（Solidity 0.8.28+）

从 Solidity 0.8.28 开始，`transient` 关键字可以直接用于状态变量声明，无需内联汇编。

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract TransientExample {
    uint256 transient lock;           // 瞬态存储变量
    address transient tempApproval;   // 瞬态存储变量
    uint256 public counter;           // 永久存储变量
    
    modifier nonReentrant() {
        require(lock == 0, "Reentrant call");
        lock = 1;
        _;
        lock = 0;
    }
    
    function withdraw() external nonReentrant {
        // 安全的提款逻辑
    }
}
```

瞬态变量的声明规则：

- 目前只支持值类型（`uint256`、`address`、`bool` 等），不支持数组、映射、结构体等引用类型
- 不能在声明时初始化（因为值会在交易结束后清零，初始化无意义）
- 不能与 `constant` 或 `immutable` 一起使用
- 可以声明为 `public`，编译器会自动生成 getter 函数

瞬态存储和永久存储的地址空间完全独立，它们的变量可以交错声明而不会相互影响。

```solidity
contract MixedStorage {
    uint256 a;              // storage 槽 0
    uint128 transient b;    // transient 槽 0 低 128 位
    uint256 c;              // storage 槽 1
    uint128 transient d;    // transient 槽 0 高 128 位（与 b 打包）
}
```

### 内联汇编方式（Solidity 0.8.24+）

对于 0.8.24 到 0.8.27 版本，或者需要更精细控制的场景，可以使用内联汇编。

```solidity
contract TransientReentrancyGuard {
    modifier nonReentrant() {
        assembly {
            // 检查锁状态（槽 0）
            if tload(0) { revert(0, 0) }
            // 设置锁
            tstore(0, 1)
        }
        _;
        assembly {
            // 释放锁
            tstore(0, 0)
        }
    }
    
    function withdraw() external nonReentrant {
        // 安全的提款逻辑
    }
}
```

### 瞬态存储的关键特性

**交易级生命周期**：数据在交易开始时为零，交易结束后自动清零，无需手动清理。

**跨调用可见**：同一交易内的所有调用（包括内部调用、外部调用、delegatecall）都可以访问相同的瞬态存储数据。这一点需要特别注意——如果合约 A 调用合约 B，B 中的瞬态存储对 A 是可见的。

**无退款机制**：与永久存储不同，瞬态存储没有清零退款，Gas 计算更简单。

**打包规则相同**：瞬态存储变量的打包规则与永久存储完全相同，多个小变量可以共享一个槽。

### 典型应用场景

**重入锁**：传统的重入锁使用永久存储，每次调用需要支付高昂的 SSTORE 成本。使用瞬态存储后，成本降低了 99%。

**闪电贷标记**：标记当前交易是否在闪电贷回调中，防止非法调用。

```solidity
contract FlashLender {
    uint256 transient flashLoanActive;
    
    function flashLoan(uint256 amount, address callback) external {
        flashLoanActive = 1;
        // 转账给借款人
        IFlashBorrower(callback).onFlashLoan(amount);
        // 验证还款
        flashLoanActive = 0;
    }
    
    function repay() external {
        require(flashLoanActive == 1, "Not in flash loan");
        // 处理还款
    }
}
```

**临时授权**：单交易内的临时权限，无需永久存储。

**跨合约通信**：在同一交易的多个合约调用间传递数据，避免使用函数参数或返回值。

### 注意事项

瞬态存储的跨调用可见性是一把双刃剑。在使用 `delegatecall` 时，被调用合约会访问调用者的瞬态存储空间，这可能导致意外的数据覆盖。设计合约时需要仔细考虑这一点。

---

## Custom Storage Layout (Solidity 0.8.29+)

Solidity 0.8.29 引入了自定义存储布局功能，允许开发者指定状态变量的起始存储槽。这对于代理合约和需要精确控制存储布局的场景非常有用。

### 基本语法

使用 `layout at N` 语法指定存储起始槽。

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.29;

contract CustomLayout layout at 100 {
    uint256 a;  // 槽 100
    uint256 b;  // 槽 101
    uint256 c;  // 槽 102
}
```

在这个例子中，所有状态变量从槽 100 开始分配，而不是默认的槽 0。

### 继承中的存储布局

当使用继承时，`layout at` 只能在最派生的合约中指定，它会影响整个继承链的存储布局。

```solidity
contract A {
    uint256 a;  // 相对位置 0
}

contract B {
    uint256[] e;           // 相对位置 0
    mapping(uint => uint) f;  // 相对位置 1
    uint16 g;              // 相对位置 2
    uint16 h;              // 相对位置 2（与 g 打包）
}

contract C is A, B layout at 42 {
    bytes21 l;  // 相对位置 3
    uint8[10] m;  // 相对位置 4
}
```

在合约 C 中：
- `a`（来自 A）存储在槽 42
- `e`（来自 B）存储在槽 43
- `f`（来自 B）存储在槽 44
- `g` 和 `h`（来自 B）存储在槽 45
- `l`（C 自己的）存储在槽 46
- `m`（C 自己的）存储在槽 47

### 与瞬态存储的关系

`layout at` 只影响永久存储，不影响瞬态存储。瞬态存储始终从槽 0 开始。

```solidity
contract MixedLayout layout at 100 {
    uint256 a;              // storage 槽 100
    uint256 transient b;    // transient 槽 0（不受 layout at 影响）
    uint256 c;              // storage 槽 101
}
```

### 应用场景

**代理合约**：确保实现合约的存储布局与代理合约兼容，避免存储冲突。

```solidity
// 代理合约使用 EIP-1967 标准槽
// 实现合约可以从特定槽开始，避开代理的管理槽
contract Implementation layout at 100 {
    // 业务逻辑的存储从槽 100 开始
    // 槽 0-99 保留给代理合约使用
    uint256 public value;
    mapping(address => uint256) public balances;
}
```

**钻石代理（EIP-2535）**：多个 facet 合约可以使用不同的存储区域，避免冲突。

### 注意事项

- `layout at` 的值必须是编译时常量
- 动态数组和映射的实际数据位置会根据基础槽的偏移而改变
- 独立部署的合约（不作为继承链的一部分）仍然从槽 0 开始

---

## 常见优化技巧

### 变量打包

将小于 32 字节的变量放在一起声明，让 EVM 可以打包它们。

```solidity
// 优化前：3 个槽
contract Unoptimized {
    uint128 a;  // 槽 0
    uint256 b;  // 槽 1
    uint128 c;  // 槽 2
}

// 优化后：2 个槽
contract Optimized {
    uint128 a;  // 槽 0 低 128 位
    uint128 c;  // 槽 0 高 128 位
    uint256 b;  // 槽 1
}
```

结构体内部的变量也遵循同样的打包规则。

```solidity
// 优化前：3 个槽
struct UserBad {
    uint64 id;        // 槽 0（浪费 24 字节）
    address wallet;   // 槽 1（浪费 12 字节）
    uint64 timestamp; // 槽 2（浪费 24 字节）
}

// 优化后：2 个槽
struct UserGood {
    address wallet;   // 槽 0 低 160 位
    uint64 id;        // 槽 0 高 64 位（与 wallet 打包）
    uint64 timestamp; // 槽 1 低 64 位
    // 槽 1 还剩 192 位可用
}
```

### 缓存存储变量

如果一个存储变量在函数中被多次读取，应该先缓存到内存变量中。

```solidity
contract CacheExample {
    uint256 public value;
    
    // 不推荐：多次 SLOAD
    function badLoop() external view returns (uint256) {
        uint256 sum = 0;
        for (uint256 i = 0; i < 10; i++) {
            sum += value;  // 每次循环都 SLOAD（首次 2100，后续 100）
        }
        return sum;
    }
    
    // 推荐：缓存后使用
    function goodLoop() external view returns (uint256) {
        uint256 _value = value;  // 一次 SLOAD (2100)
        uint256 sum = 0;
        for (uint256 i = 0; i < 10; i++) {
            sum += _value;  // 读取栈变量（3 Gas）
        }
        return sum;
    }
}
```

`badLoop` 需要 2100 + 9 × 100 = 3000 Gas 用于读取。`goodLoop` 只需要 2100 Gas。循环次数越多，差距越大。

### 使用 unchecked

Solidity 0.8.0 默认开启溢出检查，每次算术运算都会检查是否溢出。如果确定不会溢出，可以使用 `unchecked` 块跳过检查，节省 Gas。

```solidity
contract UncheckedExample {
    // 标准写法：有溢出检查
    function normalIncrement(uint256 x) external pure returns (uint256) {
        return x + 1;  // 包含溢出检查
    }
    
    // 优化写法：跳过溢出检查
    function uncheckedIncrement(uint256 x) external pure returns (uint256) {
        unchecked {
            return x + 1;  // 无溢出检查，节省约 100 Gas
        }
    }
}
```

最常见的应用场景是循环计数器。循环变量通常不会溢出（除非循环 2^256 次），可以安全地使用 `unchecked`。

```solidity
function sumArray(uint256[] calldata arr) external pure returns (uint256) {
    uint256 sum = 0;
    uint256 len = arr.length;
    for (uint256 i = 0; i < len;) {
        sum += arr[i];
        unchecked { ++i; }  // i 不会溢出
    }
    return sum;
}
```

### 使用 immutable 和 constant

`constant` 和 `immutable` 变量不占用存储槽，值被直接内联到字节码中。读取它们几乎不消耗 Gas。

```solidity
contract Constants {
    // 存储变量：每次读取 2100/100 Gas
    uint256 public storedValue = 100;
    
    // constant：编译时确定，内联到字节码
    uint256 public constant CONSTANT_VALUE = 100;
    
    // immutable：部署时确定，内联到字节码
    uint256 public immutable IMMUTABLE_VALUE;
    
    constructor(uint256 _value) {
        IMMUTABLE_VALUE = _value;
    }
}
```

### 短路求值

利用 `&&` 和 `||` 的短路特性，把便宜的检查放在前面。

```solidity
contract ShortCircuit {
    mapping(address => bool) public whitelist;
    
    // 优化前：先检查存储（贵），再检查参数（便宜）
    function checkBad(address user, uint256 amount) external view returns (bool) {
        return whitelist[user] && amount > 0;  // SLOAD 在前
    }
    
    // 优化后：先检查参数（便宜），再检查存储（贵）
    function checkGood(address user, uint256 amount) external view returns (bool) {
        return amount > 0 && whitelist[user];  // 如果 amount == 0，不会 SLOAD
    }
}
```

### 批量操作

多次调用合约比一次调用处理多个数据更贵，因为每次调用都有固定的开销（21,000 Gas 基础费 + calldata 成本）。

```solidity
contract BatchOperations {
    mapping(address => uint256) public balances;
    
    // 不推荐：多次调用
    function transfer(address to, uint256 amount) external {
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
    
    // 推荐：批量处理
    function batchTransfer(address[] calldata recipients, uint256[] calldata amounts) external {
        require(recipients.length == amounts.length, "Length mismatch");
        uint256 totalAmount = 0;
        for (uint256 i = 0; i < recipients.length;) {
            balances[recipients[i]] += amounts[i];
            totalAmount += amounts[i];
            unchecked { ++i; }
        }
        balances[msg.sender] -= totalAmount;
    }
}
```

---

## 存储模式

### 位图存储

当需要存储大量布尔值时，使用位图比 `mapping(uint256 => bool)` 更高效。一个 `uint256` 可以存储 256 个布尔值。

```solidity
contract Bitmap {
    // 不推荐：每个布尔值占一个槽
    mapping(uint256 => bool) public claimed;
    
    // 推荐：256 个布尔值共享一个槽
    mapping(uint256 => uint256) public claimedBitmap;
    
    function isClaimed(uint256 index) public view returns (bool) {
        uint256 wordIndex = index / 256;
        uint256 bitIndex = index % 256;
        uint256 word = claimedBitmap[wordIndex];
        uint256 mask = 1 << bitIndex;
        return word & mask != 0;
    }
    
    function setClaimed(uint256 index) external {
        uint256 wordIndex = index / 256;
        uint256 bitIndex = index % 256;
        claimedBitmap[wordIndex] |= (1 << bitIndex);
    }
}
```

这种模式在空投领取、投票记录等场景非常有用。Uniswap 的 Merkle Distributor 就使用了这种技术。

### 紧凑编码

当多个小数值需要一起存储和读取时，可以手动打包到一个 `uint256` 中。

```solidity
contract PackedData {
    // 将多个值打包到一个 uint256
    // [0-63]: timestamp (64 bits)
    // [64-127]: amount (64 bits)  
    // [128-159]: price (32 bits)
    // [160-167]: status (8 bits)
    // [168-255]: reserved
    
    mapping(uint256 => uint256) public packedData;
    
    function setData(uint256 id, uint64 timestamp, uint64 amount, uint32 price, uint8 status) external {
        uint256 packed = uint256(timestamp) |
                        (uint256(amount) << 64) |
                        (uint256(price) << 128) |
                        (uint256(status) << 160);
        packedData[id] = packed;  // 一次 SSTORE
    }
    
    function getData(uint256 id) external view returns (
        uint64 timestamp, uint64 amount, uint32 price, uint8 status
    ) {
        uint256 packed = packedData[id];  // 一次 SLOAD
        timestamp = uint64(packed);
        amount = uint64(packed >> 64);
        price = uint32(packed >> 128);
        status = uint8(packed >> 160);
    }
}
```

### 冷热数据分离

将频繁访问的数据和不常访问的数据分开存储，可以减少冷访问的次数。

```solidity
contract DataSeparation {
    // 热数据：频繁读写
    struct HotData {
        uint128 balance;
        uint64 lastUpdate;
        uint64 nonce;
    }
    
    // 冷数据：很少访问
    struct ColdData {
        string name;
        string metadata;
        uint256 createdAt;
    }
    
    mapping(address => HotData) public hotData;
    mapping(address => ColdData) public coldData;
    
    // 大多数操作只访问热数据
    function updateBalance(address user, uint128 newBalance) external {
        HotData storage data = hotData[user];
        data.balance = newBalance;
        data.lastUpdate = uint64(block.timestamp);
        data.nonce++;
        // 不需要访问 coldData
    }
}
```

---

## Gas 估算与测试

### 使用 Foundry 测试 Gas

Foundry 提供了内置的 Gas 报告功能。

```solidity
// test/GasTest.t.sol
contract GasTest is Test {
    MyContract public target;
    
    function setUp() public {
        target = new MyContract();
    }
    
    function testGasUsage() public {
        uint256 gasBefore = gasleft();
        target.someFunction();
        uint256 gasUsed = gasBefore - gasleft();
        console.log("Gas used:", gasUsed);
    }
}
```

运行 `forge test --gas-report` 可以看到每个函数的 Gas 消耗统计。

```bash
forge test --gas-report
```

### 使用 Hardhat Gas Reporter

如果使用 Hardhat，可以安装 `hardhat-gas-reporter` 插件。

```javascript
// hardhat.config.js
require("hardhat-gas-reporter");

module.exports = {
    gasReporter: {
        enabled: true,
        currency: "USD",
        gasPrice: 30,  // Gwei
    }
};
```

### 内联汇编优化

对于极端性能要求的场景，可以使用内联汇编。但这会牺牲可读性和安全性，应该谨慎使用。

```solidity
contract AssemblyOptimization {
    // Solidity 版本
    function addSolidity(uint256 a, uint256 b) external pure returns (uint256) {
        return a + b;
    }
    
    // 汇编版本（节省少量 Gas）
    function addAssembly(uint256 a, uint256 b) external pure returns (uint256 result) {
        assembly {
            result := add(a, b)
        }
    }
}
```

内联汇编的主要应用场景包括：批量内存操作、自定义哈希计算、低级调用优化等。

---

## 总结

Gas 优化的核心原则是减少存储操作。存储是最昂贵的资源，一次 SSTORE 的成本可能是一次算术运算的数千倍。通过合理的变量布局、缓存策略、批量操作，可以显著降低合约的运行成本。

但优化不应该以牺牲安全性和可读性为代价。过度优化的代码难以维护和审计，可能引入新的漏洞。在大多数情况下，遵循基本的优化原则（变量打包、缓存存储、使用 calldata）就足够了。

下一章将讨论合约之间的交互方式——继承、接口、库，以及外部调用的安全考量。

---

## 参考文献

- [Solidity Documentation - Layout of State Variables in Storage](https://docs.soliditylang.org/en/v0.8.34/internals/layout_in_storage.html)
- [Solidity Documentation - Transient Storage](https://docs.soliditylang.org/en/v0.8.34/contracts.html#transient-storage)
- [Solidity Documentation - Custom Storage Layout](https://docs.soliditylang.org/en/v0.8.34/contracts.html#custom-storage-layout)
- [EIP-1153: Transient storage opcodes](https://eips.ethereum.org/EIPS/eip-1153)
- [EVM Codes - Gas Costs](https://www.evm.codes/)
- [EIP-2929: Gas cost increases for state access opcodes](https://eips.ethereum.org/EIPS/eip-2929)
- [EIP-2930: Optional access lists](https://eips.ethereum.org/EIPS/eip-2930)
- [Foundry Book - Gas Reports](https://book.getfoundry.sh/forge/gas-reports)
