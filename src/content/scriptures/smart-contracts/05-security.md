# 第 5 章：安全与常见漏洞

> 智能合约一旦部署就无法修改，漏洞可能导致数百万美元的损失。理解攻击模式是编写安全代码的前提。

---

## 重入攻击

重入攻击是智能合约历史上最著名的漏洞类型。2016 年的 DAO 攻击利用这个漏洞盗取了价值 6000 万美元的 ETH，直接导致了以太坊的硬分叉。

攻击的核心在于：当合约 A 调用合约 B 时，控制权转移到 B。如果 B 是恶意合约，它可以在 A 完成状态更新之前再次调用 A，利用 A 的旧状态执行操作。

![重入攻击流程](/images/scriptures/smart-contracts/05-reentrancy.png)

下面是一个存在重入漏洞的提款合约：

```solidity
contract VulnerableBank {
    mapping(address => uint256) public balances;
    
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
    
    function withdraw() external {
        uint256 balance = balances[msg.sender];
        require(balance > 0, "No balance");
        
        // 危险：先转账，后更新状态
        (bool success, ) = msg.sender.call{value: balance}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] = 0;  // 状态更新在转账之后
    }
}
```

攻击合约可以这样利用这个漏洞：

```solidity
contract Attacker {
    VulnerableBank public bank;
    
    constructor(address _bank) {
        bank = VulnerableBank(_bank);
    }
    
    function attack() external payable {
        bank.deposit{value: msg.value}();
        bank.withdraw();
    }
    
    receive() external payable {
        // 在收到 ETH 时再次调用 withdraw
        if (address(bank).balance >= 1 ether) {
            bank.withdraw();
        }
    }
}
```

攻击流程是：攻击者调用 `attack()`，存入 1 ETH 后调用 `withdraw()`。银行合约检查余额（1 ETH），然后向攻击者转账。攻击者的 `receive()` 函数被触发，立即再次调用 `withdraw()`。此时银行合约的 `balances[attacker]` 还没有被清零，所以检查通过，再次转账。这个循环持续到银行合约的余额耗尽。

### 防御方法

最有效的防御是 Checks-Effects-Interactions 模式：先检查条件，再更新状态，最后进行外部调用。

```solidity
contract SecureBank {
    mapping(address => uint256) public balances;
    
    function withdraw() external {
        uint256 balance = balances[msg.sender];
        require(balance > 0, "No balance");
        
        // 先更新状态
        balances[msg.sender] = 0;
        
        // 最后进行外部调用
        (bool success, ) = msg.sender.call{value: balance}("");
        require(success, "Transfer failed");
    }
}
```

另一种方法是使用重入锁：

```solidity
contract ReentrancyGuard {
    uint256 private _status;
    uint256 private constant NOT_ENTERED = 1;
    uint256 private constant ENTERED = 2;
    
    modifier nonReentrant() {
        require(_status != ENTERED, "ReentrancyGuard: reentrant call");
        _status = ENTERED;
        _;
        _status = NOT_ENTERED;
    }
}

contract SecureBankWithGuard is ReentrancyGuard {
    mapping(address => uint256) public balances;
    
    function withdraw() external nonReentrant {
        uint256 balance = balances[msg.sender];
        require(balance > 0, "No balance");
        
        balances[msg.sender] = 0;
        
        (bool success, ) = msg.sender.call{value: balance}("");
        require(success, "Transfer failed");
    }
}
```

OpenZeppelin 提供了经过审计的 `ReentrancyGuard` 合约，生产环境应该直接使用它。

---

## 整数溢出

在 Solidity 0.8.0 之前，整数运算不会自动检查溢出。`uint256` 的最大值是 `2^256 - 1`，加 1 会回绕到 0。

```solidity
// Solidity < 0.8.0
contract Overflow {
    uint8 public count = 255;
    
    function increment() external {
        count += 1;  // count 变成 0，而不是 256
    }
    
    function decrement() external {
        count -= 1;  // 如果 count 是 0，会变成 255
    }
}
```

这个漏洞曾被用于攻击多个代币合约。攻击者可以通过下溢让自己的余额从 0 变成一个巨大的数字。

Solidity 0.8.0 之后，算术运算默认会检查溢出，溢出时交易回滚。如果确定不会溢出且需要节省 Gas，可以使用 `unchecked` 块：

```solidity
// Solidity >= 0.8.0
contract SafeMath {
    function safeIncrement(uint256 x) external pure returns (uint256) {
        return x + 1;  // 溢出时自动回滚
    }
    
    function unsafeIncrement(uint256 x) external pure returns (uint256) {
        unchecked {
            return x + 1;  // 不检查溢出，节省约 100 Gas
        }
    }
}
```

> 即使在 0.8.0 之后，类型转换仍然不检查溢出。`uint8(256)` 会得到 0，而不是回滚。

---

## 访问控制漏洞

访问控制错误是最常见的漏洞类型之一。忘记添加权限检查，或者权限检查逻辑有误，都可能让攻击者执行未授权的操作。

```solidity
// 危险：任何人都可以调用
contract VulnerableToken {
    mapping(address => uint256) public balances;
    
    function mint(address to, uint256 amount) external {
        // 缺少权限检查！
        balances[to] += amount;
    }
}
```

正确的做法是实现严格的访问控制：

```solidity
contract SecureToken {
    mapping(address => uint256) public balances;
    address public owner;
    mapping(address => bool) public minters;
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    modifier onlyMinter() {
        require(minters[msg.sender], "Not minter");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    function setMinter(address minter, bool status) external onlyOwner {
        minters[minter] = status;
    }
    
    function mint(address to, uint256 amount) external onlyMinter {
        balances[to] += amount;
    }
}
```

对于复杂的权限系统，推荐使用 OpenZeppelin 的 `AccessControl` 合约，它支持基于角色的权限管理。

### tx.origin 陷阱

`tx.origin` 返回交易的原始发起者（EOA），而 `msg.sender` 返回直接调用者。使用 `tx.origin` 进行权限检查是危险的：

```solidity
// 危险：使用 tx.origin 进行权限检查
contract VulnerableWallet {
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    function transfer(address to, uint256 amount) external {
        require(tx.origin == owner, "Not owner");  // 危险！
        payable(to).transfer(amount);
    }
}
```

攻击者可以诱骗 owner 调用一个恶意合约，恶意合约再调用 `VulnerableWallet.transfer()`。此时 `tx.origin` 是 owner，检查通过，资金被转走。

```solidity
contract TxOriginAttacker {
    VulnerableWallet public wallet;
    address public attacker;
    
    constructor(address _wallet) {
        wallet = VulnerableWallet(_wallet);
        attacker = msg.sender;
    }
    
    // 诱骗 owner 调用这个函数
    function attack() external {
        wallet.transfer(attacker, address(wallet).balance);
    }
}
```

永远使用 `msg.sender` 而不是 `tx.origin` 进行权限检查。

---

## 预言机操纵

DeFi 协议通常依赖预言机获取资产价格。如果预言机可以被操纵，攻击者可以在操纵价格后执行有利于自己的操作。

最常见的攻击是闪电贷操纵。攻击者借入大量资金，在单个交易内操纵 AMM 的价格，利用被操纵的价格在目标协议中获利，然后归还闪电贷。

```solidity
// 危险：直接使用 AMM 现货价格
contract VulnerableLending {
    IUniswapV2Pair public pair;
    
    function getPrice() public view returns (uint256) {
        (uint112 reserve0, uint112 reserve1, ) = pair.getReserves();
        return uint256(reserve1) * 1e18 / uint256(reserve0);  // 可被操纵
    }
    
    function borrow(uint256 collateralAmount) external {
        uint256 price = getPrice();
        uint256 borrowLimit = collateralAmount * price / 1e18;
        // 基于可操纵的价格计算借款额度
    }
}
```

### 防御方法

使用时间加权平均价格（TWAP）而不是现货价格：

```solidity
contract SecureLending {
    IUniswapV3Pool public pool;
    uint32 public twapInterval = 1800;  // 30 分钟
    
    function getTWAP() public view returns (uint256) {
        uint32[] memory secondsAgos = new uint32[](2);
        secondsAgos[0] = twapInterval;
        secondsAgos[1] = 0;
        
        (int56[] memory tickCumulatives, ) = pool.observe(secondsAgos);
        
        int56 tickCumulativesDelta = tickCumulatives[1] - tickCumulatives[0];
        int24 averageTick = int24(tickCumulativesDelta / int56(uint56(twapInterval)));
        
        // 从 tick 计算价格
        return OracleLibrary.getQuoteAtTick(averageTick, 1e18, token0, token1);
    }
}
```

更好的选择是使用 Chainlink 等去中心化预言机网络：

```solidity
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract ChainlinkPriceFeed {
    AggregatorV3Interface public priceFeed;
    
    constructor(address _priceFeed) {
        priceFeed = AggregatorV3Interface(_priceFeed);
    }
    
    function getLatestPrice() public view returns (uint256) {
        (
            uint80 roundId,
            int256 price,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        ) = priceFeed.latestRoundData();
        
        // 检查数据新鲜度
        require(updatedAt > block.timestamp - 3600, "Stale price");
        require(price > 0, "Invalid price");
        require(answeredInRound >= roundId, "Stale round");
        
        return uint256(price);
    }
}
```

---

## 前端运行与 MEV

以太坊的交易在被打包进区块之前，会在公开的内存池中等待。任何人都可以看到待处理的交易，并尝试在它之前或之后插入自己的交易来获利。

常见的 MEV 攻击包括：

**三明治攻击**：攻击者看到一笔大额 DEX 交易，在它之前买入（推高价格），在它之后卖出（获利）。受害者以更差的价格成交。

**清算抢跑**：攻击者监控借贷协议，当发现可清算的头寸时，抢在其他清算人之前执行清算获取奖励。

**套利抢跑**：攻击者复制其他人发现的套利交易，用更高的 Gas 费抢先执行。

### 防御方法

对于普通用户，使用私有交易池（如 Flashbots Protect）可以避免交易被抢跑。交易直接发送给区块构建者，不经过公开内存池。

对于协议开发者，可以使用 commit-reveal 模式：

```solidity
contract CommitReveal {
    mapping(address => bytes32) public commits;
    mapping(address => uint256) public commitBlock;
    
    uint256 public constant REVEAL_DELAY = 2;  // 等待 2 个区块
    
    function commit(bytes32 hash) external {
        commits[msg.sender] = hash;
        commitBlock[msg.sender] = block.number;
    }
    
    function reveal(uint256 value, bytes32 salt) external {
        require(block.number >= commitBlock[msg.sender] + REVEAL_DELAY, "Too early");
        require(keccak256(abi.encodePacked(value, salt)) == commits[msg.sender], "Invalid reveal");
        
        // 执行操作
        delete commits[msg.sender];
    }
}
```

另一种方法是使用批量拍卖，所有订单以统一价格结算，消除抢跑的激励。

---

## 拒绝服务

拒绝服务（DoS）攻击让合约无法正常运行。常见的模式包括：

**Gas 耗尽**：如果合约需要遍历一个无限增长的数组，攻击者可以通过添加大量元素让遍历超出 Gas 限制。

```solidity
// 危险：无限循环
contract VulnerableAirdrop {
    address[] public recipients;
    
    function addRecipient(address recipient) external {
        recipients.push(recipient);
    }
    
    function distribute() external {
        // 如果 recipients 太多，会超出 Gas 限制
        for (uint256 i = 0; i < recipients.length; i++) {
            payable(recipients[i]).transfer(1 ether);
        }
    }
}
```

解决方案是使用拉取模式（pull over push）：

```solidity
contract SecureAirdrop {
    mapping(address => uint256) public claimable;
    
    function setClaimable(address[] calldata recipients, uint256 amount) external {
        for (uint256 i = 0; i < recipients.length; i++) {
            claimable[recipients[i]] = amount;
        }
    }
    
    function claim() external {
        uint256 amount = claimable[msg.sender];
        require(amount > 0, "Nothing to claim");
        
        claimable[msg.sender] = 0;
        payable(msg.sender).transfer(amount);
    }
}
```

**回滚攻击**：如果合约向多个地址转账，其中一个地址的 `receive()` 函数故意回滚，整个交易失败。

```solidity
// 危险：一个失败导致全部失败
contract VulnerablePayment {
    function payAll(address[] calldata recipients, uint256[] calldata amounts) external {
        for (uint256 i = 0; i < recipients.length; i++) {
            // 如果任何一个转账失败，整个交易回滚
            payable(recipients[i]).transfer(amounts[i]);
        }
    }
}
```

解决方案是使用 `call` 并忽略失败：

```solidity
contract SecurePayment {
    function payAll(address[] calldata recipients, uint256[] calldata amounts) external {
        for (uint256 i = 0; i < recipients.length; i++) {
            // 忽略单个失败，继续执行
            (bool success, ) = recipients[i].call{value: amounts[i]}("");
            // 可以记录失败的地址，让他们稍后手动领取
        }
    }
}
```

---

## 签名相关漏洞

链下签名在 DeFi 中广泛使用，但实现不当会导致严重漏洞。

**签名重放**：同一个签名被多次使用。

```solidity
// 危险：没有防重放机制
contract VulnerablePermit {
    function executeWithSignature(
        address to,
        uint256 amount,
        bytes calldata signature
    ) external {
        bytes32 hash = keccak256(abi.encodePacked(to, amount));
        address signer = recoverSigner(hash, signature);
        require(signer == owner, "Invalid signature");
        
        // 同一个签名可以被多次使用！
        payable(to).transfer(amount);
    }
}
```

解决方案是使用 nonce：

```solidity
contract SecurePermit {
    mapping(address => uint256) public nonces;
    
    function executeWithSignature(
        address to,
        uint256 amount,
        uint256 nonce,
        bytes calldata signature
    ) external {
        require(nonce == nonces[msg.sender], "Invalid nonce");
        
        bytes32 hash = keccak256(abi.encodePacked(to, amount, nonce));
        address signer = recoverSigner(hash, signature);
        require(signer == owner, "Invalid signature");
        
        nonces[msg.sender]++;
        payable(to).transfer(amount);
    }
}
```

**跨链重放**：签名在一条链上有效，被攻击者在另一条链上重放。解决方案是在签名中包含 `chainId`。

**签名延展性**：ECDSA 签名的 `s` 值可以被修改为 `n - s`（n 是曲线阶），产生另一个有效签名。如果合约使用签名作为唯一标识符，这会导致问题。解决方案是强制 `s` 在低半区间：

```solidity
function isValidSignature(bytes32 hash, uint8 v, bytes32 r, bytes32 s) internal pure returns (bool) {
    // 防止签名延展性
    if (uint256(s) > 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0) {
        return false;
    }
    
    address signer = ecrecover(hash, v, r, s);
    return signer != address(0);
}
```

---

## 安全开发实践

### 使用经过审计的库

不要重新发明轮子。OpenZeppelin Contracts 提供了经过多次审计的标准实现：

```solidity
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract MyToken is ERC20, Ownable, ReentrancyGuard, Pausable {
    constructor() ERC20("MyToken", "MTK") Ownable(msg.sender) {}
    
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
    
    function transfer(address to, uint256 amount) 
        public 
        override 
        whenNotPaused 
        nonReentrant 
        returns (bool) 
    {
        return super.transfer(to, amount);
    }
}
```

### 进行安全审计

在主网部署前，至少进行一次专业的安全审计。审计不能保证没有漏洞，但可以发现大部分常见问题。

### 设置漏洞赏金

部署后设置漏洞赏金计划，激励白帽黑客报告漏洞而不是利用它们。Immunefi 是最大的 Web3 漏洞赏金平台。

### 实现紧急暂停

为关键功能添加暂停机制，在发现漏洞时可以快速止损：

```solidity
contract EmergencyStop is Ownable, Pausable {
    function pause() external onlyOwner {
        _pause();
    }
    
    function unpause() external onlyOwner {
        _unpause();
    }
    
    function criticalFunction() external whenNotPaused {
        // 关键逻辑
    }
}
```

### 使用时间锁

对于高风险操作（如升级合约、修改关键参数），使用时间锁给用户反应时间：

```solidity
contract TimeLock {
    uint256 public constant DELAY = 2 days;
    
    mapping(bytes32 => uint256) public pendingActions;
    
    function scheduleAction(bytes32 actionId) external onlyOwner {
        pendingActions[actionId] = block.timestamp + DELAY;
    }
    
    function executeAction(bytes32 actionId) external onlyOwner {
        require(pendingActions[actionId] != 0, "Not scheduled");
        require(block.timestamp >= pendingActions[actionId], "Too early");
        
        delete pendingActions[actionId];
        // 执行操作
    }
}
```

---

## 总结

智能合约安全是一个持续演进的领域。新的攻击模式不断出现，防御方法也在不断改进。本章介绍的漏洞类型——重入、整数溢出、访问控制、预言机操纵、MEV、DoS、签名问题——覆盖了大部分历史上的重大攻击。

但安全不仅仅是避免已知漏洞。它需要防御性编程的思维方式：假设所有外部输入都是恶意的，假设所有外部调用都可能失败或重入，假设攻击者比你更了解你的代码。

下一章将讨论代币标准，这是 DeFi 生态系统的基础构建块。

---

## 参考文献

- [SWC Registry](https://swcregistry.io/) - 智能合约弱点分类
- [Consensys Smart Contract Best Practices](https://consensys.github.io/smart-contract-best-practices/)
- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts/)
- [Rekt News](https://rekt.news/) - DeFi 安全事件报道
- [Immunefi](https://immunefi.com/) - Web3 漏洞赏金平台
