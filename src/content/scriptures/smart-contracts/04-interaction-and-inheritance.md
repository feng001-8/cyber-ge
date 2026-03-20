# 第 4 章：合约交互与继承

> 智能合约不是孤岛。理解合约之间的调用方式和代码复用机制，是构建复杂 DeFi 系统的基础。

---

## 外部调用

合约之间的交互通过消息调用实现。当合约 A 调用合约 B 的函数时，EVM 会创建一个新的执行上下文，切换到合约 B 的代码和存储空间执行，完成后返回结果给合约 A。

![合约调用流程](/images/scriptures/smart-contracts/04-contract-call.png)

### 调用方式

Solidity 提供了几种不同的调用方式，它们在安全性和灵活性上各有取舍。

最常见的方式是通过接口或合约类型直接调用。这种方式类型安全，编译器会检查函数签名是否匹配。

```solidity
interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract TokenUser {
    IERC20 public token;
    
    constructor(address tokenAddress) {
        token = IERC20(tokenAddress);
    }
    
    function sendTokens(address to, uint256 amount) external {
        bool success = token.transfer(to, amount);  // 类型安全的调用
        require(success, "Transfer failed");
    }
}
```

如果目标合约的接口未知，或者需要更底层的控制，可以使用 `call` 进行低级调用。`call` 返回一个布尔值表示调用是否成功，以及返回数据的字节数组。

```solidity
contract LowLevelCaller {
    function callTransfer(address token, address to, uint256 amount) external returns (bool) {
        // 编码函数调用
        bytes memory data = abi.encodeWithSignature(
            "transfer(address,uint256)",
            to,
            amount
        );
        
        // 低级调用
        (bool success, bytes memory returnData) = token.call(data);
        
        if (success && returnData.length > 0) {
            return abi.decode(returnData, (bool));
        }
        return false;
    }
}
```

低级调用的一个重要特性是：即使目标合约不存在或调用失败，它也不会自动回滚。调用者必须显式检查返回值并决定如何处理失败情况。这与直接调用不同——直接调用在失败时会自动回滚整个交易。

### delegatecall

`delegatecall` 是一种特殊的调用方式。它执行目标合约的代码，但使用调用者的存储空间和上下文。这意味着 `msg.sender` 和 `msg.value` 保持不变，状态变量的修改发生在调用者的存储中。

![delegatecall 执行上下文](/images/scriptures/smart-contracts/04-delegatecall.png)

```solidity
contract Implementation {
    uint256 public value;  // 槽 0
    
    function setValue(uint256 _value) external {
        value = _value;  // 修改槽 0
    }
}

contract Proxy {
    uint256 public value;  // 槽 0，与 Implementation 布局相同
    address public implementation;
    
    constructor(address _impl) {
        implementation = _impl;
    }
    
    fallback() external payable {
        address impl = implementation;
        assembly {
            // 复制 calldata
            calldatacopy(0, 0, calldatasize())
            // delegatecall 到实现合约
            let result := delegatecall(gas(), impl, 0, calldatasize(), 0, 0)
            // 复制返回数据
            returndatacopy(0, 0, returndatasize())
            // 根据结果返回或回滚
            switch result
            case 0 { revert(0, returndatasize()) }
            default { return(0, returndatasize()) }
        }
    }
}
```

`delegatecall` 是代理模式的基础，但也是最危险的调用方式之一。如果实现合约的存储布局与代理合约不匹配，会导致存储冲突，可能造成严重的安全问题。

### staticcall

`staticcall` 用于只读调用。它保证被调用的函数不会修改任何状态。如果被调用的代码尝试写入存储、发送 ETH 或创建合约，调用会失败。

```solidity
contract ReadOnlyCaller {
    function safeGetBalance(address token, address account) external view returns (uint256) {
        bytes memory data = abi.encodeWithSignature("balanceOf(address)", account);
        
        // staticcall 保证不会修改状态
        (bool success, bytes memory returnData) = token.staticcall(data);
        
        require(success, "Static call failed");
        return abi.decode(returnData, (uint256));
    }
}
```

当函数声明为 `view` 或 `pure` 时，Solidity 编译器会自动使用 `staticcall` 进行外部调用。

---

## 接收 ETH

合约接收 ETH 需要特殊处理。有两个特殊函数用于此目的：`receive` 和 `fallback`。

`receive` 函数在合约收到纯 ETH 转账（没有 calldata）时被调用。它必须是 `external payable`，不能有参数和返回值。

```solidity
contract ETHReceiver {
    event Received(address sender, uint256 amount);
    
    receive() external payable {
        emit Received(msg.sender, msg.value);
    }
}
```

`fallback` 函数在两种情况下被调用：收到 ETH 但没有 `receive` 函数，或者调用了不存在的函数。如果 `fallback` 声明为 `payable`，它也可以接收 ETH。

```solidity
contract FallbackExample {
    event FallbackCalled(address sender, uint256 value, bytes data);
    
    fallback() external payable {
        emit FallbackCalled(msg.sender, msg.value, msg.data);
    }
}
```

调用顺序是：如果有 calldata，调用 `fallback`；如果没有 calldata 且存在 `receive`，调用 `receive`；否则调用 `fallback`（如果存在且 payable）。

### 发送 ETH

发送 ETH 有三种方式，它们的 Gas 限制和错误处理方式不同。

`transfer` 发送固定 2300 Gas，失败时自动回滚。这个 Gas 限制只够执行一个事件日志，不足以执行复杂逻辑。

```solidity
function sendViaTransfer(address payable recipient) external payable {
    recipient.transfer(msg.value);  // 失败自动回滚
}
```

`send` 也发送 2300 Gas，但失败时返回 `false` 而不是回滚。

```solidity
function sendViaSend(address payable recipient) external payable {
    bool success = recipient.send(msg.value);
    require(success, "Send failed");
}
```

`call` 是推荐的方式。它转发所有可用 Gas（或指定数量），返回成功状态和返回数据。

```solidity
function sendViaCall(address payable recipient) external payable {
    (bool success, ) = recipient.call{value: msg.value}("");
    require(success, "Call failed");
}
```

> 由于 EIP-1884 提高了某些操作码的 Gas 成本，2300 Gas 限制可能不足以让接收合约执行 `receive` 函数。推荐使用 `call` 发送 ETH。

---

## 继承

Solidity 支持多重继承，允许合约从多个父合约继承状态变量和函数。继承使用 `is` 关键字。

```solidity
contract Ownable {
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
}

contract Pausable is Ownable {
    bool public paused;
    
    modifier whenNotPaused() {
        require(!paused, "Paused");
        _;
    }
    
    function pause() external onlyOwner {
        paused = true;
    }
    
    function unpause() external onlyOwner {
        paused = false;
    }
}

contract Token is Pausable {
    mapping(address => uint256) public balances;
    
    function transfer(address to, uint256 amount) external whenNotPaused {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
}
```

`Token` 合约继承了 `Pausable` 的所有功能，而 `Pausable` 又继承了 `Ownable`。这形成了一个继承链：`Token -> Pausable -> Ownable`。

### 函数重写

子合约可以重写父合约的函数。父合约的函数必须标记为 `virtual`，子合约的重写函数必须标记为 `override`。

```solidity
contract Base {
    function greet() public virtual returns (string memory) {
        return "Hello from Base";
    }
}

contract Child is Base {
    function greet() public virtual override returns (string memory) {
        return "Hello from Child";
    }
}

contract GrandChild is Child {
    function greet() public override returns (string memory) {
        return string.concat(super.greet(), " and GrandChild");
    }
}
```

`super` 关键字用于调用父合约的函数。在多重继承中，`super` 会按照 C3 线性化顺序调用所有父合约的同名函数。

### 多重继承

当合约从多个父合约继承时，需要注意继承顺序。Solidity 使用 C3 线性化算法确定函数调用顺序。基本规则是：从最基础的合约到最派生的合约，从右到左。

```solidity
contract A {
    function foo() public virtual returns (string memory) {
        return "A";
    }
}

contract B is A {
    function foo() public virtual override returns (string memory) {
        return string.concat(super.foo(), "B");
    }
}

contract C is A {
    function foo() public virtual override returns (string memory) {
        return string.concat(super.foo(), "C");
    }
}

// 继承顺序：A -> B -> C -> D
contract D is B, C {
    function foo() public override(B, C) returns (string memory) {
        return string.concat(super.foo(), "D");  // 返回 "ABCD"
    }
}
```

在 `D` 中调用 `super.foo()` 会触发整个继承链：`D.foo()` -> `C.foo()` -> `B.foo()` -> `A.foo()`。

### 构造函数继承

如果父合约的构造函数有参数，子合约必须提供这些参数。有两种方式：

```solidity
contract Parent {
    uint256 public value;
    
    constructor(uint256 _value) {
        value = _value;
    }
}

// 方式 1：在继承列表中指定
contract Child1 is Parent(100) {
    // value 被初始化为 100
}

// 方式 2：在构造函数中指定
contract Child2 is Parent {
    constructor(uint256 _value) Parent(_value) {
        // 可以使用动态值
    }
}
```

---

## 抽象合约与接口

抽象合约包含至少一个未实现的函数。它不能被直接部署，只能被继承。

```solidity
abstract contract Animal {
    string public name;
    
    constructor(string memory _name) {
        name = _name;
    }
    
    // 抽象函数，子合约必须实现
    function speak() public virtual returns (string memory);
    
    // 具体函数，子合约可以直接使用
    function getName() public view returns (string memory) {
        return name;
    }
}

contract Dog is Animal {
    constructor() Animal("Dog") {}
    
    function speak() public pure override returns (string memory) {
        return "Woof!";
    }
}
```

接口是更严格的抽象。接口不能有状态变量、构造函数或函数实现。所有函数必须是 `external`。

```solidity
interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
}
```

接口定义了合约的外部 API，是合约之间交互的契约。ERC-20、ERC-721 等标准都是以接口形式定义的。

---

## 库

库是一种特殊的合约，用于代码复用。库不能有状态变量（除了常量），不能继承或被继承，不能接收 ETH。

```solidity
library SafeMath {
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 c = a + b;
        require(c >= a, "SafeMath: addition overflow");
        return c;
    }
    
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b <= a, "SafeMath: subtraction overflow");
        return a - b;
    }
}

contract Calculator {
    using SafeMath for uint256;  // 附加库函数到类型
    
    function calculate(uint256 a, uint256 b) external pure returns (uint256) {
        return a.add(b);  // 等价于 SafeMath.add(a, b)
    }
}
```

`using A for B` 语法将库 `A` 的函数附加到类型 `B`。调用时，类型 `B` 的值会作为第一个参数传入。

库函数可以是 `internal` 或 `external`。`internal` 函数会被内联到调用合约中，不产生外部调用开销。`external` 函数需要部署库合约，通过 `delegatecall` 调用。

```solidity
library ArrayUtils {
    // internal 函数，会被内联
    function sum(uint256[] memory arr) internal pure returns (uint256) {
        uint256 total = 0;
        for (uint256 i = 0; i < arr.length; i++) {
            total += arr[i];
        }
        return total;
    }
    
    // external 函数，需要部署库
    function sort(uint256[] storage arr) external {
        // 原地排序
        for (uint256 i = 0; i < arr.length; i++) {
            for (uint256 j = i + 1; j < arr.length; j++) {
                if (arr[i] > arr[j]) {
                    (arr[i], arr[j]) = (arr[j], arr[i]);
                }
            }
        }
    }
}
```

---

## 工厂模式

工厂合约用于动态创建其他合约。这在需要部署多个相似合约时非常有用，比如 Uniswap 的交易对工厂。

```solidity
contract Token {
    string public name;
    string public symbol;
    address public owner;
    
    constructor(string memory _name, string memory _symbol, address _owner) {
        name = _name;
        symbol = _symbol;
        owner = _owner;
    }
}

contract TokenFactory {
    address[] public tokens;
    
    event TokenCreated(address indexed token, string name, string symbol);
    
    function createToken(string memory name, string memory symbol) external returns (address) {
        Token token = new Token(name, symbol, msg.sender);
        tokens.push(address(token));
        emit TokenCreated(address(token), name, symbol);
        return address(token);
    }
    
    function getTokenCount() external view returns (uint256) {
        return tokens.length;
    }
}
```

### CREATE2

普通的 `new` 使用 CREATE 操作码，合约地址由部署者地址和 nonce 决定。CREATE2 允许预先计算合约地址，地址由部署者地址、salt 和合约字节码的哈希决定。

```solidity
contract Create2Factory {
    event Deployed(address addr, bytes32 salt);
    
    function deploy(bytes32 salt, bytes memory bytecode) external returns (address) {
        address addr;
        assembly {
            addr := create2(0, add(bytecode, 0x20), mload(bytecode), salt)
            if iszero(extcodesize(addr)) {
                revert(0, 0)
            }
        }
        emit Deployed(addr, salt);
        return addr;
    }
    
    function computeAddress(bytes32 salt, bytes memory bytecode) external view returns (address) {
        return address(uint160(uint256(keccak256(abi.encodePacked(
            bytes1(0xff),
            address(this),
            salt,
            keccak256(bytecode)
        )))));
    }
}
```

CREATE2 的主要用途包括：
- 反事实部署：在合约部署前就知道地址，可以先向该地址转账
- 确定性地址：相同的 salt 和字节码总是产生相同的地址
- 合约升级：销毁旧合约后，可以在同一地址部署新合约

---

## 总结

合约交互是 DeFi 生态系统的基础。理解不同调用方式的特性——`call` 的灵活性、`delegatecall` 的上下文保持、`staticcall` 的只读保证——对于编写安全的合约至关重要。继承和库提供了代码复用的机制，而工厂模式则支持动态合约部署。

但是，合约交互也带来了安全风险。外部调用可能触发重入攻击，`delegatecall` 可能导致存储冲突，不当的继承顺序可能产生意外行为。下一章将深入讨论这些安全问题以及如何防范。

---

## 参考文献

- [Solidity Documentation - Contracts](https://docs.soliditylang.org/en/latest/contracts.html)
- [Solidity Documentation - Inheritance](https://docs.soliditylang.org/en/latest/contracts.html#inheritance)
- [EIP-1014: Skinny CREATE2](https://eips.ethereum.org/EIPS/eip-1014)
- [OpenZeppelin Contracts](https://github.com/OpenZeppelin/openzeppelin-contracts)
