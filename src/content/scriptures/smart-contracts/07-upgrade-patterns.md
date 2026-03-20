# 第 7 章：升级模式

> 智能合约一旦部署，代码就无法修改。但通过代理模式，可以在保留数据的同时更新逻辑。理解升级机制的原理和风险，是构建可维护 DeFi 系统的关键。

---

## 为什么需要升级

智能合约的不可变性是一把双刃剑。它保证了代码的可信度——用户可以验证合约的行为永远不会改变。但这也意味着，如果发现漏洞、需要添加功能或优化 Gas 消耗，就必须部署新合约并迁移所有数据。

2016 年的 DAO 攻击是一个典型案例。攻击者利用重入漏洞盗取了价值 6000 万美元的 ETH，而合约无法修复，最终导致以太坊硬分叉。如果当时有升级机制，损失可能会小得多。

代理模式解决了这个问题。它将合约分为两部分：存储数据的代理合约和包含业务逻辑的实现合约。升级时只需更换实现合约，数据保持不变。这种架构在 DeFi 协议中被广泛采用——Compound、Aave、Uniswap V3 都使用了某种形式的代理模式。

---

## 代理模式的核心：delegatecall

代理模式的基础是 EVM 的 `delegatecall` 指令。与普通的 `call` 不同，`delegatecall` 执行目标合约的代码，但使用调用者的存储空间和上下文。这意味着 `msg.sender`、`msg.value` 保持不变，状态变量的修改发生在调用者的存储中。

![代理模式架构](/images/scriptures/smart-contracts/07-proxy-architecture.png)

当用户调用代理合约的某个函数时，代理合约通过 `delegatecall` 将调用转发给实现合约。实现合约的代码被执行，但所有存储操作都发生在代理合约的存储空间中。从用户的角度看，他们只与代理合约交互，完全不知道实现合约的存在。

一个最简单的代理实现如下：

```solidity
contract SimpleProxy {
    address public implementation;
    
    constructor(address _implementation) {
        implementation = _implementation;
    }
    
    fallback() external payable {
        address impl = implementation;
        
        assembly {
            calldatacopy(0, 0, calldatasize())
            let result := delegatecall(gas(), impl, 0, calldatasize(), 0, 0)
            returndatacopy(0, 0, returndatasize())
            
            switch result
            case 0 { revert(0, returndatasize()) }
            default { return(0, returndatasize()) }
        }
    }
}
```

`fallback` 函数捕获所有对代理合约的调用。它将完整的 calldata 复制到内存，然后通过 `delegatecall` 转发给实现合约。返回数据被复制回来，根据调用结果决定返回还是回滚。

这段汇编代码看起来复杂，但逻辑很直接：复制输入 → 调用实现 → 复制输出 → 返回结果。使用汇编是因为 Solidity 不支持直接转发任意函数调用。

---

## 存储布局：代理模式的致命陷阱

代理模式最危险的问题是存储布局冲突。由于 `delegatecall` 使用调用者的存储空间，如果代理合约和实现合约的存储布局不一致，就会发生数据覆盖。

![存储布局与冲突](/images/scriptures/smart-contracts/07-storage-layout.png)

考虑这个错误示例：

```solidity
contract Proxy {
    address public implementation;  // slot 0
    address public admin;           // slot 1
}

contract LogicV1 {
    uint256 public value;           // slot 0
    address public owner;           // slot 1
}
```

当 `LogicV1` 的代码通过 `delegatecall` 执行时，它写入 `value` 实际上是写入 slot 0——这会覆盖代理合约的 `implementation` 地址。写入 `owner` 会覆盖 `admin`。这种冲突可能导致合约完全失控。

### EIP-1967：标准存储槽

EIP-1967 定义了一套标准的存储槽位置，专门用于代理合约的元数据。这些槽位置是通过对特定字符串取哈希再减 1 得到的，几乎不可能与正常的存储变量冲突。

```solidity
bytes32 constant IMPLEMENTATION_SLOT = 
    bytes32(uint256(keccak256("eip1967.proxy.implementation")) - 1);
// = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc

bytes32 constant ADMIN_SLOT = 
    bytes32(uint256(keccak256("eip1967.proxy.admin")) - 1);
// = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103
```

使用这些标准槽，代理合约的存储布局从 slot 0 开始就是空的，完全留给实现合约使用。实现合约可以自由定义自己的存储变量，不用担心与代理合约冲突。

```solidity
contract EIP1967Proxy {
    bytes32 private constant IMPLEMENTATION_SLOT = 
        0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    
    constructor(address _implementation) {
        assembly {
            sstore(IMPLEMENTATION_SLOT, _implementation)
        }
    }
    
    function _getImplementation() internal view returns (address impl) {
        assembly {
            impl := sload(IMPLEMENTATION_SLOT)
        }
    }
    
    fallback() external payable {
        address impl = _getImplementation();
        assembly {
            calldatacopy(0, 0, calldatasize())
            let result := delegatecall(gas(), impl, 0, calldatasize(), 0, 0)
            returndatacopy(0, 0, returndatasize())
            switch result
            case 0 { revert(0, returndatasize()) }
            default { return(0, returndatasize()) }
        }
    }
}
```

---

## Transparent Proxy：经典方案

OpenZeppelin 的 Transparent Proxy 是最早被广泛采用的代理模式。它的核心思想是通过调用者身份区分管理函数和业务函数：管理员调用代理合约的函数（如 `upgradeTo`），普通用户的调用被转发到实现合约。

```solidity
contract TransparentProxy {
    modifier ifAdmin() {
        if (msg.sender == _getAdmin()) {
            _;
        } else {
            _fallback();
        }
    }
    
    function upgradeTo(address newImplementation) external ifAdmin {
        _setImplementation(newImplementation);
    }
    
    function changeAdmin(address newAdmin) external ifAdmin {
        _setAdmin(newAdmin);
    }
    
    function _fallback() internal {
        address impl = _getImplementation();
        assembly {
            calldatacopy(0, 0, calldatasize())
            let result := delegatecall(gas(), impl, 0, calldatasize(), 0, 0)
            returndatacopy(0, 0, returndatasize())
            switch result
            case 0 { revert(0, returndatasize()) }
            default { return(0, returndatasize()) }
        }
    }
    
    fallback() external payable {
        _fallback();
    }
}
```

这种设计解决了函数选择器冲突的问题。如果代理合约和实现合约都有一个叫 `upgradeTo` 的函数，普通用户调用时会执行实现合约的版本，管理员调用时会执行代理合约的版本。

但 Transparent Proxy 有一个明显的缺点：每次调用都需要检查 `msg.sender == admin`，这增加了约 2100 Gas 的开销（读取 admin 地址的 SLOAD 操作）。对于高频调用的合约，这个开销会累积成可观的成本。

---

## UUPS：更高效的选择

Universal Upgradeable Proxy Standard（UUPS）将升级逻辑从代理合约移到实现合约中。代理合约变得极其简单，只负责转发调用。升级函数 `upgradeTo` 定义在实现合约中，通过 `delegatecall` 执行时会修改代理合约存储的实现地址。

```solidity
contract UUPSProxy {
    bytes32 private constant IMPLEMENTATION_SLOT = 
        0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    
    constructor(address _implementation, bytes memory _data) {
        assembly {
            sstore(IMPLEMENTATION_SLOT, _implementation)
        }
        if (_data.length > 0) {
            (bool success, ) = _implementation.delegatecall(_data);
            require(success, "Init failed");
        }
    }
    
    fallback() external payable {
        assembly {
            let impl := sload(IMPLEMENTATION_SLOT)
            calldatacopy(0, 0, calldatasize())
            let result := delegatecall(gas(), impl, 0, calldatasize(), 0, 0)
            returndatacopy(0, 0, returndatasize())
            switch result
            case 0 { revert(0, returndatasize()) }
            default { return(0, returndatasize()) }
        }
    }
}
```

实现合约需要继承一个包含升级逻辑的基类：

```solidity
abstract contract UUPSUpgradeable {
    bytes32 private constant IMPLEMENTATION_SLOT = 
        0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    
    function upgradeTo(address newImplementation) external virtual {
        _authorizeUpgrade(newImplementation);
        assembly {
            sstore(IMPLEMENTATION_SLOT, newImplementation)
        }
    }
    
    function _authorizeUpgrade(address newImplementation) internal virtual;
}

contract MyContractV1 is UUPSUpgradeable {
    address public owner;
    uint256 public value;
    
    function initialize(address _owner) external {
        require(owner == address(0), "Already initialized");
        owner = _owner;
    }
    
    function setValue(uint256 _value) external {
        value = _value;
    }
    
    function _authorizeUpgrade(address) internal override {
        require(msg.sender == owner, "Not owner");
    }
}
```

UUPS 的优势在于效率。普通调用不需要任何额外检查，直接转发到实现合约。只有在调用 `upgradeTo` 时才会执行权限检查。这使得 UUPS 成为大多数场景的首选。

但 UUPS 有一个严重的风险：如果升级到一个没有 `upgradeTo` 函数的实现合约，合约就永远无法再升级了。这种"锁死"是不可逆的。

```solidity
contract MyContractV2Bad {
    // 忘记继承 UUPSUpgradeable
    // 没有 upgradeTo 函数
    // 升级到这个版本后，合约将永远无法再升级
}
```

为了防止这种情况，OpenZeppelin 的 UUPS 实现会在升级时验证新实现合约确实包含升级函数。

---

## Beacon Proxy：批量升级

当需要部署大量相同逻辑的合约时（如每个用户一个钱包合约），Beacon Proxy 是更好的选择。所有代理合约共享一个 Beacon 合约，Beacon 存储实现合约的地址。升级 Beacon 就等于同时升级所有代理。

![三种代理模式对比](/images/scriptures/smart-contracts/07-proxy-comparison.png)

```solidity
contract Beacon {
    address public implementation;
    address public owner;
    
    constructor(address _implementation) {
        implementation = _implementation;
        owner = msg.sender;
    }
    
    function upgradeTo(address newImplementation) external {
        require(msg.sender == owner, "Not owner");
        implementation = newImplementation;
    }
}

contract BeaconProxy {
    address public beacon;
    
    constructor(address _beacon, bytes memory _data) {
        beacon = _beacon;
        if (_data.length > 0) {
            address impl = IBeacon(_beacon).implementation();
            (bool success, ) = impl.delegatecall(_data);
            require(success, "Init failed");
        }
    }
    
    fallback() external payable {
        address impl = IBeacon(beacon).implementation();
        assembly {
            calldatacopy(0, 0, calldatasize())
            let result := delegatecall(gas(), impl, 0, calldatasize(), 0, 0)
            returndatacopy(0, 0, returndatasize())
            switch result
            case 0 { revert(0, returndatasize()) }
            default { return(0, returndatasize()) }
        }
    }
}
```

Beacon Proxy 的每次调用都需要先查询 Beacon 获取实现地址，这增加了一次外部调用的开销。但对于需要批量升级的场景，这个开销是值得的——一次升级操作就能更新成百上千个代理合约。

---

## 升级兼容性

升级实现合约时，必须保持存储布局的兼容性。EVM 的存储是按槽位（slot）组织的，每个状态变量占据固定的槽位。如果新版本改变了变量的顺序或类型，就会导致数据错乱。

### 存储布局规则

升级时必须遵守以下规则：

1. **只能在末尾添加新变量**
2. **不能删除现有变量**
3. **不能改变变量顺序**
4. **不能改变变量类型**
5. **不能在现有变量之间插入新变量**

```solidity
contract MyContractV1 {
    uint256 public value;      // slot 0
    address public owner;      // slot 1
}

contract MyContractV2 {
    uint256 public value;      // slot 0 - 保持不变
    address public owner;      // slot 1 - 保持不变
    uint256 public newValue;   // slot 2 - 新增，在末尾
}

contract MyContractV2Bad {
    uint256 public newValue;   // slot 0 - 错误！覆盖了 value
    uint256 public value;      // slot 1 - 错误！覆盖了 owner
    address public owner;      // slot 2
}
```

### 使用 Gap 预留空间

为了给未来升级预留空间，可以在合约末尾定义一个 gap 数组：

```solidity
contract MyContractV1 {
    uint256 public value;
    address public owner;
    
    uint256[50] private __gap;  // 预留 50 个槽位
}

contract MyContractV2 {
    uint256 public value;
    address public owner;
    uint256 public newValue;    // 使用一个预留槽
    
    uint256[49] private __gap;  // 减少一个
}
```

这种模式在继承链中特别有用。每个基类都预留自己的 gap，子类可以安全地添加新变量。

---

## 初始化：不能使用 constructor

代理模式有一个重要的限制：实现合约不能使用 `constructor`。构造函数只在合约部署时执行一次，而代理模式下，实现合约的部署和代理合约的部署是分开的。构造函数设置的状态变量存储在实现合约的存储空间中，而不是代理合约的存储空间中。

```solidity
contract BadImplementation {
    address public owner;
    
    constructor() {
        owner = msg.sender;  // 这设置的是实现合约的存储，不是代理的
    }
}
```

正确的做法是使用初始化函数：

```solidity
import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";

contract GoodImplementation is Initializable {
    address public owner;
    
    function initialize(address _owner) external initializer {
        owner = _owner;
    }
}
```

`initializer` 修饰符确保初始化函数只能被调用一次。OpenZeppelin 的 `Initializable` 合约提供了这个功能。

还有一个安全问题：实现合约本身也可以被初始化。攻击者可能直接调用实现合约的 `initialize` 函数，获取实现合约的控制权。虽然这通常不会影响代理合约，但最好在实现合约的构造函数中禁用初始化：

```solidity
contract SecureImplementation is Initializable {
    address public owner;
    
    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }
    
    function initialize(address _owner) external initializer {
        owner = _owner;
    }
}
```

---

## 使用 OpenZeppelin 工具

手动实现代理模式容易出错。OpenZeppelin 提供了经过审计的实现和部署工具。

### Hardhat 部署

```bash
npm install @openzeppelin/hardhat-upgrades
```

```javascript
const { ethers, upgrades } = require("hardhat");

async function main() {
    const MyContract = await ethers.getContractFactory("MyContractV1");
    
    const proxy = await upgrades.deployProxy(MyContract, [initArg], {
        initializer: "initialize",
        kind: "uups"
    });
    
    console.log("Proxy deployed to:", proxy.address);
}

async function upgrade() {
    const MyContractV2 = await ethers.getContractFactory("MyContractV2");
    
    await upgrades.upgradeProxy(proxyAddress, MyContractV2);
    
    console.log("Upgraded!");
}
```

### Foundry 部署

```bash
forge install OpenZeppelin/openzeppelin-foundry-upgrades
```

OpenZeppelin 的工具会自动检查存储布局兼容性，在升级前验证新实现合约是否安全。

---

## 选择哪种模式

三种代理模式各有适用场景：

**Transparent Proxy** 适合简单场景，概念清晰，风险最低。缺点是每次调用都有额外的 Gas 开销。

**UUPS** 是大多数场景的首选。Gas 效率最高，但需要注意不要锁死升级能力。OpenZeppelin 的实现已经包含了防锁死检查。

**Beacon Proxy** 适合工厂模式，当需要部署大量相同逻辑的合约并批量升级时使用。

无论选择哪种模式，都要记住：升级能力是一把双刃剑。它提供了修复漏洞的能力，但也引入了中心化风险——控制升级权限的人可以任意修改合约逻辑。许多协议使用时间锁和多签来缓解这个风险，给用户足够的时间在升级生效前退出。

---

## 总结

代理模式通过 `delegatecall` 实现了智能合约的可升级性。理解存储布局、选择合适的代理模式、正确使用初始化函数，是安全实现升级的关键。

但升级能力也带来了信任问题。用户需要信任升级权限的持有者不会恶意修改合约。在设计升级机制时，应该考虑使用时间锁、多签、甚至最终放弃升级权限，以平衡灵活性和去中心化。

下一章将讨论测试和部署，这是将合约安全地推向生产环境的最后一步。

---

## 参考文献

- [EIP-1967: Proxy Storage Slots](https://eips.ethereum.org/EIPS/eip-1967)
- [EIP-1822: Universal Upgradeable Proxy Standard (UUPS)](https://eips.ethereum.org/EIPS/eip-1822)
- [OpenZeppelin Upgrades Plugins](https://docs.openzeppelin.com/upgrades-plugins/)
- [OpenZeppelin Proxy Contracts](https://docs.openzeppelin.com/contracts/4.x/api/proxy)
- [Proxy Upgrade Pattern](https://docs.openzeppelin.com/upgrades-plugins/1.x/proxies)
