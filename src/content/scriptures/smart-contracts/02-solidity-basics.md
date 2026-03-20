# 第 2 章：Solidity 语言基础

> Solidity 是以太坊智能合约的主要编程语言。本章覆盖核心语法——数据类型、函数、修饰符、事件——为后续章节打下基础。

---

## 数据类型

Solidity 是静态类型语言，所有变量必须在编译时确定类型。这与 JavaScript 或 Python 不同，后者允许变量在运行时改变类型。静态类型的好处是编译器能在部署前捕获类型错误，这对于不可变的智能合约尤为重要——一旦部署，代码无法修改。

Solidity 的类型系统分为两大类：值类型和引用类型。值类型在赋值或传参时会被完整复制，而引用类型则传递指向数据的引用。理解这个区别对于编写高效、安全的合约至关重要。

![Solidity 数据类型概览](/images/scriptures/smart-contracts/02-data-types.png)

### 值类型

值类型是 Solidity 中最基础的数据类型。当你将一个值类型变量赋给另一个变量时，数据会被完整复制，两个变量之间没有任何关联。

**布尔型**是最简单的值类型，只有 `true` 和 `false` 两个值。布尔型支持逻辑运算符：`!`（非）、`&&`（与）、`||`（或）、`==`（等于）、`!=`（不等于）。值得注意的是，`&&` 和 `||` 采用短路求值——如果第一个操作数已经能确定结果，第二个操作数不会被计算。

```solidity
bool public isActive = true;    // 布尔状态变量
bool public isPaused = false;
bool result = !isActive && isPaused;  // 短路求值
```

**整数**是智能合约中使用最频繁的类型。Solidity 提供有符号整数（`int`）和无符号整数（`uint`），位宽从 8 到 256，步长为 8。`uint256` 是最常用的类型，因为 EVM 原生支持 256 位运算，使用其他位宽反而可能增加 Gas 消耗。

Solidity 0.8.0 引入了一个重要的安全特性：默认的溢出检查。在此之前，整数溢出不会报错，而是静默回绕——`uint8` 类型的 255 加 1 会变成 0，而不是报错。这个行为导致了大量安全漏洞，包括著名的 BEC 代币漏洞。现在，溢出会触发 `revert`，交易回滚。如果确实需要回绕行为（比如某些哈希计算），可以使用 `unchecked` 块。

```solidity
uint256 public totalSupply = 1_000_000 * 10**18;  // 下划线分隔符提高可读性
int256 public temperature = -40;  // 有符号整数

uint8 x = 255;
unchecked {
    x = x + 1;  // 回绕到 0，不会 revert
}
```

**地址**类型是以太坊特有的，表示一个 20 字节的账户地址。`address` 和 `address payable` 的区别在于后者可以接收 ETH。地址类型提供了几个有用的成员：`balance` 返回该地址的 ETH 余额（单位是 wei），`code` 返回该地址的合约代码（如果是 EOA 则为空），`codehash` 返回代码的 keccak256 哈希。

向地址转账有三种方式：`transfer`、`send` 和 `call`。`transfer` 和 `send` 只转发 2300 gas，这对于简单的 EOA 转账足够，但如果接收方是合约且 `receive()` 函数有逻辑，可能会因 gas 不足而失败。推荐使用 `call` 并配合重入保护。

```solidity
address public owner = 0x1234567890123456789012345678901234567890;
address payable public treasury;  // 可接收 ETH 的地址

// 推荐的转账方式
(bool success, ) = treasury.call{value: 1 ether}("");
require(success, "Transfer failed");
```

**固定大小字节数组**从 `bytes1` 到 `bytes32`，常用于存储哈希值或函数选择器。`bytes32` 是最常用的，因为 keccak256 哈希的输出正好是 32 字节。

```solidity
bytes32 public merkleRoot;  // 存储 Merkle 树根哈希
bytes4 public selector = bytes4(keccak256("transfer(address,uint256)"));  // 函数选择器
```

**枚举**用于定义一组命名常量，使代码更具可读性。枚举值在底层存储为 `uint8`（如果枚举成员不超过 256 个）。

```solidity
// 枚举底层存储为 uint8
enum Status { Pending, Active, Completed, Cancelled }
Status public currentStatus = Status.Pending;
```

### 引用类型

引用类型在赋值时传递引用而非复制数据。这意味着修改一个变量可能会影响另一个变量。引用类型必须指定数据位置：`storage`、`memory` 或 `calldata`。

![数据位置](/images/scriptures/smart-contracts/02-data-location.png)

**storage** 是永久存储在区块链上的数据，状态变量默认存储在这里。读写 storage 是最昂贵的操作，因为数据需要被所有节点永久保存。

**memory** 是函数执行期间的临时内存，函数返回后数据被丢弃。memory 比 storage 便宜得多，适合存储函数内部的临时数据。

**calldata** 是只读的函数参数区域，只能用于外部函数的参数。calldata 比 memory 更便宜，因为数据不需要被复制。

```solidity
uint256[] public numbers;  // storage 数组

function example(uint256[] calldata input) external {
    uint256 first = input[0];  // 从 calldata 读取
    uint256[] memory temp = new uint256[](10);  // memory 临时数组
    temp[0] = first;
    uint256[] storage nums = numbers;  // storage 引用
    nums.push(first);
}
```

**数组**分为固定大小和动态大小两种。固定大小数组在声明时指定长度，如 `uint256[10]`。动态数组的长度可以改变，支持 `push`、`pop` 等操作。需要注意的是，`delete` 操作只会将元素重置为默认值，不会改变数组长度。

**映射**是 Solidity 最重要的数据结构，用于键值存储。映射的键可以是任何值类型，值可以是任何类型。映射有一个重要限制：无法遍历，因为 Solidity 不存储键的列表。如果需要遍历，必须额外维护一个数组来存储所有的键。

```solidity
// 基本映射
mapping(address => uint256) public balances;
// 嵌套映射（用于 ERC20 授权）
mapping(address => mapping(address => uint256)) public allowances;

// 可遍历映射的实现方式
address[] public holders;
mapping(address => bool) public isHolder;

function addHolder(address account) internal {
    if (!isHolder[account]) {
        holders.push(account);
        isHolder[account] = true;
    }
}
```

**结构体**允许定义自定义的复合类型。结构体可以包含任意类型的成员，包括其他结构体、数组和映射。

```solidity
struct User {
    address wallet;      // 用户钱包地址
    uint256 balance;     // 余额
    uint64 createdAt;    // 创建时间戳
    bool isActive;       // 是否激活
}

mapping(uint256 => User) public users;
```

---

## 变量与可见性

Solidity 中的变量分为三类：状态变量、局部变量和全局变量。状态变量存储在 storage 中，是合约的持久化数据。局部变量存在于函数执行期间。全局变量是 EVM 提供的特殊变量，如 `msg.sender`、`block.timestamp` 等。

### 常量与不可变量

除了普通的状态变量，Solidity 还提供了两种特殊的变量类型：`constant` 和 `immutable`。

`constant` 变量必须在编译时确定值，值会被直接内联到字节码中，不占用存储槽。这意味着读取 constant 变量几乎不消耗 gas。constant 变量只能用于值类型和 `string`。

`immutable` 变量可以在构造函数中赋值，之后不能修改。与 constant 类似，immutable 变量也被内联到字节码中，不占用存储槽。immutable 的优势是可以在部署时动态确定值，比如记录部署者地址或部署时间。

```solidity
contract Constants {
    // constant: 编译时确定，内联到字节码
    uint256 public constant MAX_SUPPLY = 1_000_000 * 10**18;
    
    // immutable: 部署时确定，内联到字节码
    address public immutable DEPLOYER;
    uint256 public immutable DEPLOY_TIME;
    
    constructor() {
        DEPLOYER = msg.sender;
        DEPLOY_TIME = block.timestamp;
    }
}
```

### 可见性

Solidity 提供四种可见性修饰符：`public`、`external`、`internal` 和 `private`。

![函数可见性](/images/scriptures/smart-contracts/02-visibility.png)

**public** 函数和变量可以从任何地方访问——合约内部、继承合约、外部调用。对于状态变量，编译器会自动生成一个同名的 getter 函数。

**external** 函数只能从合约外部调用，不能在合约内部直接调用（除非使用 `this.functionName()`）。external 函数的参数直接从 calldata 读取，比 public 函数更省 gas。

**internal** 函数和变量只能在当前合约和继承合约中访问，外部无法调用。

**private** 函数和变量只能在当前合约中访问，继承合约也无法访问。

需要特别强调的是，`private` 不等于保密。区块链上所有数据都是公开的，任何人都可以通过读取存储槽来获取 `private` 变量的值。`private` 只是限制了 Solidity 层面的访问，不要在合约中存储敏感信息。

```solidity
contract Visibility {
    uint256 public publicVar;      // 任何地方可访问
    uint256 internal internalVar;  // 当前合约和子合约
    uint256 private privateVar;    // 仅当前合约
    
    function publicFunc() public { }     // 内外部都可调用
    function externalFunc() external { } // 仅外部调用
    function internalFunc() internal { } // 仅内部调用
    function privateFunc() private { }   // 仅当前合约
}
```

---

## 函数

函数是智能合约的核心组成部分。Solidity 函数的声明包含多个部分：函数名、参数列表、可见性、状态可变性、修饰符和返回类型。

### 状态可变性

状态可变性描述函数如何与区块链状态交互。

不带任何修饰符的函数可以读取和修改状态，但不能接收 ETH。这是最常见的函数类型。

**view** 函数只能读取状态，不能修改。从外部调用 view 函数不消耗 gas（因为不需要发送交易），但如果从另一个非 view 函数内部调用，仍然会消耗 gas。

**pure** 函数既不能读取也不能修改状态，只能使用传入的参数进行计算。pure 函数适合实现纯粹的数学运算或数据转换。

**payable** 函数可以接收 ETH。如果一个函数需要接收 ETH，必须标记为 payable，否则发送 ETH 的交易会失败。

```solidity
contract Functions {
    uint256 public value;
    
    // 可读写状态
    function setValue(uint256 _value) external {
        value = _value;
    }
    
    // view: 只读状态
    function getValue() external view returns (uint256) {
        return value;
    }
    
    // pure: 不访问状态
    function add(uint256 a, uint256 b) external pure returns (uint256) {
        return a + b;
    }
    
    // payable: 可接收 ETH
    function deposit() external payable {
        // msg.value 是发送的 ETH 数量
    }
}
```

### 特殊函数

Solidity 定义了几种特殊函数。

**constructor** 是构造函数，在合约部署时执行一次，用于初始化状态变量。构造函数不能被外部调用，也不能有返回值。

**receive** 函数在合约收到纯 ETH 转账（没有 calldata）时触发。一个合约最多只能有一个 receive 函数，必须是 `external payable`，不能有参数和返回值。

**fallback** 函数在调用不存在的函数时触发，也可以在收到 ETH 但没有 receive 函数时触发。fallback 函数常用于实现代理模式。

```solidity
contract SpecialFunctions {
    address public owner;
    
    // 构造函数：部署时执行一次
    constructor(address _owner) {
        owner = _owner;
    }
    
    // receive: 接收纯 ETH 转账
    receive() external payable {
        emit Received(msg.sender, msg.value);
    }
    
    // fallback: 调用不存在的函数时触发
    fallback() external payable {
        // 可用于代理模式
    }
    
    event Received(address sender, uint256 amount);
}
```

---

## 修饰符

修饰符（modifier）是 Solidity 的一个强大特性，用于在函数执行前后插入检查逻辑。修饰符可以复用代码，使合约更加简洁和安全。

修饰符的定义类似函数，但使用 `modifier` 关键字。修饰符体中的 `_` 表示被修饰函数的执行位置。`_` 之前的代码在函数执行前运行，`_` 之后的代码在函数执行后运行。

```solidity
contract Modifiers {
    address public owner;
    bool public paused;
    
    constructor() {
        owner = msg.sender;
    }
    
    // 权限检查修饰符
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;  // 函数体在这里执行
    }
    
    // 状态检查修饰符
    modifier whenNotPaused() {
        require(!paused, "Contract paused");
        _;
    }
    
    // 带参数的修饰符
    modifier validAddress(address addr) {
        require(addr != address(0), "Invalid address");
        _;
    }
    
    function pause() external onlyOwner {
        paused = true;
    }
    
    // 多个修饰符按顺序执行
    function transfer(address to, uint256 amount) 
        external 
        whenNotPaused 
        validAddress(to) 
    {
        // 转账逻辑
    }
}
```

当一个函数有多个修饰符时，它们按照声明顺序嵌套执行。如果函数声明为 `function foo() external A B`，执行顺序是：A 的前置逻辑 → B 的前置逻辑 → 函数体 → B 的后置逻辑 → A 的后置逻辑。

![修饰符执行流程](/images/scriptures/smart-contracts/02-modifier-flow.png)

最常用的修饰符之一是重入锁。重入攻击是智能合约最常见的安全漏洞之一，攻击者通过在回调中重复调用函数来窃取资金。重入锁通过一个状态变量来防止函数被重复进入。

```solidity
contract ReentrancyGuard {
    uint256 private _status;
    uint256 private constant NOT_ENTERED = 1;
    uint256 private constant ENTERED = 2;
    
    constructor() {
        _status = NOT_ENTERED;
    }
    
    // 重入锁：防止函数被重复进入
    modifier nonReentrant() {
        require(_status != ENTERED, "ReentrancyGuard: reentrant call");
        _status = ENTERED;
        _;
        _status = NOT_ENTERED;  // 函数执行后重置
    }
    
    function withdraw() external nonReentrant {
        // 安全的提款逻辑
    }
}
```

---

## 事件与日志

事件（Event）是合约与外部世界通信的主要方式。当合约触发事件时，数据被写入交易日志。日志存储在区块链上，但不能被合约读取——它们是为外部应用（如前端、索引服务）设计的。

事件的 gas 成本远低于 storage 写入。写入一个 256 位的 storage 槽需要 20,000 gas（首次写入）或 5,000 gas（更新），而记录一个事件只需要 375 gas 加上每字节 8 gas。因此，如果数据只需要被外部读取而不需要被合约使用，应该使用事件而非 storage。

事件参数可以标记为 `indexed`。indexed 参数存储在日志的 topics 中，可以被高效过滤。每个事件最多有 3 个 indexed 参数。非 indexed 参数存储在 data 中，需要解码才能读取。

```solidity
contract Events {
    // indexed 参数可被高效过滤
    event Transfer(
        address indexed from,
        address indexed to,
        uint256 value
    );
    
    event Approval(
        address indexed owner,
        address indexed spender,
        uint256 value
    );
    
    function transfer(address to, uint256 amount) external {
        // 转账逻辑...
        emit Transfer(msg.sender, to, amount);
    }
}
```

前端可以通过 Web3 库监听和过滤事件。indexed 参数使得过滤非常高效——可以只获取特定地址发出或接收的转账，而不需要遍历所有事件。

```javascript
// 前端监听事件示例
const filter = contract.filters.Transfer(fromAddress, null);
contract.on(filter, (from, to, value, event) => {
    console.log(`Transfer: ${from} -> ${to}: ${value}`);
});
```

---

## 错误处理

Solidity 提供三种错误处理机制：`require`、`revert` 和 `assert`。

**require** 用于验证输入和前置条件。如果条件为 false，交易回滚并退还剩余 gas。require 是最常用的错误处理方式，适合检查用户输入、权限、状态等。

**revert** 与 require 类似，但更适合复杂的条件判断。当需要在多个条件分支中回滚时，revert 比嵌套的 require 更清晰。

**assert** 用于检查不应该发生的内部错误。与 require 不同，assert 失败会消耗所有剩余 gas。assert 应该只用于检查代码逻辑错误，比如数组越界、除以零等。如果 assert 失败，说明合约有 bug。

```solidity
function withdraw(uint256 amount) external {
    // require: 验证输入和前置条件
    require(amount > 0, "Amount must be positive");
    require(balances[msg.sender] >= amount, "Insufficient balance");
    
    // revert: 复杂条件判断
    if (paused && msg.sender != owner) {
        revert("Contract paused for non-owners");
    }
    
    balances[msg.sender] -= amount;
    
    // assert: 检查不应发生的内部错误
    assert(balances[msg.sender] <= totalSupply);
    
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success, "Transfer failed");
}
```

Solidity 0.8.4 引入了自定义错误，比字符串错误消息更省 gas。自定义错误可以携带参数，提供更丰富的错误信息。

```solidity
// 自定义错误：比字符串更省 gas
error Unauthorized(address caller);
error InsufficientBalance(uint256 available, uint256 required);
error InvalidAddress();

contract CustomErrors {
    mapping(address => uint256) public balances;
    address public owner;
    
    function withdraw(uint256 amount) external {
        if (msg.sender != owner) {
            revert Unauthorized(msg.sender);
        }
        
        uint256 balance = balances[msg.sender];
        if (balance < amount) {
            revert InsufficientBalance(balance, amount);
        }
    }
}
```

**try/catch** 用于处理外部调用的错误。当调用外部合约时，如果被调用的函数 revert，默认会导致整个交易回滚。try/catch 允许捕获错误并优雅地处理，而不是让整个交易失败。

```solidity
interface IExternalContract {
    function riskyOperation() external returns (uint256);
}

contract TryCatch {
    event CallFailed(string reason);
    event PanicOccurred(uint256 errorCode);
    event LowLevelError(bytes data);
    
    // try/catch: 捕获外部调用错误
    function safeCall(address target) external returns (uint256) {
        try IExternalContract(target).riskyOperation() returns (uint256 result) {
            return result;
        } catch Error(string memory reason) {
            // 捕获 require/revert 的字符串错误
            emit CallFailed(reason);
            return 0;
        } catch Panic(uint256 errorCode) {
            // 捕获 assert 失败或算术错误
            emit PanicOccurred(errorCode);
            return 0;
        } catch (bytes memory lowLevelData) {
            // 捕获其他低级错误
            emit LowLevelError(lowLevelData);
            return 0;
        }
    }
}
```

---

## 总结

本章覆盖了 Solidity 的核心语法。值类型在赋值时复制，引用类型传递引用。数据位置决定了数据存储在哪里以及 gas 成本。可见性控制了谁可以访问函数和变量。状态可变性描述了函数如何与区块链状态交互。修饰符提供了代码复用和访问控制的机制。事件是与外部世界通信的高效方式。错误处理确保合约在异常情况下安全回滚。

下一章将深入数据存储机制和 Gas 优化策略——如何利用存储槽布局、打包变量、缓存读取来降低合约的运行成本。

---

## 参考文献

- [Solidity Documentation - Types](https://docs.soliditylang.org/en/latest/types.html)
- [Solidity Documentation - Units and Globally Available Variables](https://docs.soliditylang.org/en/latest/units-and-global-variables.html)
- [Solidity Documentation - Expressions and Control Structures](https://docs.soliditylang.org/en/latest/control-structures.html)
- [Solidity by Example](https://solidity-by-example.org/)
- [OpenZeppelin Contracts](https://github.com/OpenZeppelin/openzeppelin-contracts)
