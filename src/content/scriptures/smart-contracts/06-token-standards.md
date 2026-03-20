# 第 6 章：代币标准

> 代币标准定义了智能合约之间的通用接口。理解 ERC-20、ERC-721 和 ERC-1155 的设计，是构建 DeFi 和 NFT 应用的基础。

---

## ERC-20：同质化代币

ERC-20 是以太坊上最广泛使用的代币标准。USDT、USDC、LINK、UNI 等主流代币都遵循这个标准。"同质化"意味着每个代币单位是完全相同的——1 个 USDC 和另 1 个 USDC 没有区别。

### 核心接口

ERC-20 定义了 6 个必须实现的函数和 2 个事件：

```solidity
interface IERC20 {
    // 查询函数
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function allowance(address owner, address spender) external view returns (uint256);
    
    // 转账函数
    function transfer(address to, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    
    // 事件
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
}
```

`transfer` 用于直接转账，`approve` + `transferFrom` 组合用于授权第三方（如 DEX）代为转账。这种两步授权模式是 DeFi 交互的基础。

![ERC-20 授权流程](/images/scriptures/smart-contracts/06-erc20-approve.png)

### 基础实现

一个最小的 ERC-20 实现：

```solidity
contract SimpleToken is IERC20 {
    string public name;
    string public symbol;
    uint8 public decimals = 18;
    
    uint256 private _totalSupply;
    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;
    
    constructor(string memory _name, string memory _symbol, uint256 initialSupply) {
        name = _name;
        symbol = _symbol;
        _mint(msg.sender, initialSupply);
    }
    
    function totalSupply() external view override returns (uint256) {
        return _totalSupply;
    }
    
    function balanceOf(address account) external view override returns (uint256) {
        return _balances[account];
    }
    
    function allowance(address owner, address spender) external view override returns (uint256) {
        return _allowances[owner][spender];
    }
    
    function transfer(address to, uint256 amount) external override returns (bool) {
        _transfer(msg.sender, to, amount);
        return true;
    }
    
    function approve(address spender, uint256 amount) external override returns (bool) {
        _allowances[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }
    
    function transferFrom(address from, address to, uint256 amount) external override returns (bool) {
        uint256 currentAllowance = _allowances[from][msg.sender];
        require(currentAllowance >= amount, "ERC20: insufficient allowance");
        
        unchecked {
            _allowances[from][msg.sender] = currentAllowance - amount;
        }
        
        _transfer(from, to, amount);
        return true;
    }
    
    function _transfer(address from, address to, uint256 amount) internal {
        require(from != address(0), "ERC20: transfer from zero address");
        require(to != address(0), "ERC20: transfer to zero address");
        require(_balances[from] >= amount, "ERC20: insufficient balance");
        
        unchecked {
            _balances[from] -= amount;
            _balances[to] += amount;
        }
        
        emit Transfer(from, to, amount);
    }
    
    function _mint(address to, uint256 amount) internal {
        require(to != address(0), "ERC20: mint to zero address");
        
        _totalSupply += amount;
        _balances[to] += amount;
        
        emit Transfer(address(0), to, amount);
    }
}
```

### decimals 的含义

`decimals` 表示代币的小数位数。以太坊不支持浮点数，所以 1 USDC 实际上存储为 `1000000`（6 位小数），1 ETH 存储为 `1000000000000000000`（18 位小数）。

```solidity
// 转账 1.5 USDC（6 decimals）
usdc.transfer(recipient, 1_500_000);

// 转账 1.5 DAI（18 decimals）
dai.transfer(recipient, 1_500_000_000_000_000_000);
```

不同代币的 decimals 不同，计算时必须注意单位转换。

### 常见扩展

**可销毁代币**：

```solidity
function burn(uint256 amount) external {
    _balances[msg.sender] -= amount;
    _totalSupply -= amount;
    emit Transfer(msg.sender, address(0), amount);
}
```

**带上限的代币**：

```solidity
uint256 public constant MAX_SUPPLY = 1_000_000_000 * 10**18;

function _mint(address to, uint256 amount) internal override {
    require(_totalSupply + amount <= MAX_SUPPLY, "Exceeds max supply");
    super._mint(to, amount);
}
```

**快照功能**（用于治理投票）：

```solidity
mapping(uint256 => mapping(address => uint256)) private _snapshotBalances;
uint256 private _currentSnapshotId;

function snapshot() external onlyOwner returns (uint256) {
    _currentSnapshotId++;
    return _currentSnapshotId;
}

function balanceOfAt(address account, uint256 snapshotId) external view returns (uint256) {
    return _snapshotBalances[snapshotId][account];
}
```

---

## ERC-721：非同质化代币

ERC-721 定义了 NFT（Non-Fungible Token）标准。每个代币都有唯一的 `tokenId`，代表独一无二的资产——可以是数字艺术品、游戏道具、域名或任何需要唯一性的东西。

### 核心接口

```solidity
interface IERC721 {
    // 查询函数
    function balanceOf(address owner) external view returns (uint256);
    function ownerOf(uint256 tokenId) external view returns (address);
    
    // 转账函数
    function transferFrom(address from, address to, uint256 tokenId) external;
    function safeTransferFrom(address from, address to, uint256 tokenId) external;
    function safeTransferFrom(address from, address to, uint256 tokenId, bytes calldata data) external;
    
    // 授权函数
    function approve(address to, uint256 tokenId) external;
    function setApprovalForAll(address operator, bool approved) external;
    function getApproved(uint256 tokenId) external view returns (address);
    function isApprovedForAll(address owner, address operator) external view returns (bool);
    
    // 事件
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);
}
```

与 ERC-20 不同，ERC-721 的转账是针对特定 `tokenId` 的。`safeTransferFrom` 会检查接收方是否能处理 NFT，防止代币被永久锁定在不支持的合约中。

### 元数据扩展

大多数 NFT 需要关联元数据（图片、属性等）。ERC-721 Metadata 扩展定义了获取元数据的接口：

```solidity
interface IERC721Metadata is IERC721 {
    function name() external view returns (string memory);
    function symbol() external view returns (string memory);
    function tokenURI(uint256 tokenId) external view returns (string memory);
}
```

`tokenURI` 返回一个 URL，指向 JSON 格式的元数据：

```json
{
    "name": "CryptoPunk #3100",
    "description": "One of 9 Alien punks",
    "image": "ipfs://QmXxx.../3100.png",
    "attributes": [
        {"trait_type": "Type", "value": "Alien"},
        {"trait_type": "Accessory", "value": "Headband"}
    ]
}
```

### 基础实现

```solidity
contract SimpleNFT is IERC721, IERC721Metadata {
    string public override name;
    string public override symbol;
    string private _baseURI;
    
    mapping(uint256 => address) private _owners;
    mapping(address => uint256) private _balances;
    mapping(uint256 => address) private _tokenApprovals;
    mapping(address => mapping(address => bool)) private _operatorApprovals;
    
    uint256 private _tokenIdCounter;
    
    constructor(string memory _name, string memory _symbol, string memory baseURI_) {
        name = _name;
        symbol = _symbol;
        _baseURI = baseURI_;
    }
    
    function balanceOf(address owner) external view override returns (uint256) {
        require(owner != address(0), "ERC721: zero address");
        return _balances[owner];
    }
    
    function ownerOf(uint256 tokenId) public view override returns (address) {
        address owner = _owners[tokenId];
        require(owner != address(0), "ERC721: nonexistent token");
        return owner;
    }
    
    function tokenURI(uint256 tokenId) external view override returns (string memory) {
        require(_owners[tokenId] != address(0), "ERC721: nonexistent token");
        return string(abi.encodePacked(_baseURI, toString(tokenId), ".json"));
    }
    
    function approve(address to, uint256 tokenId) external override {
        address owner = ownerOf(tokenId);
        require(msg.sender == owner || _operatorApprovals[owner][msg.sender], "ERC721: not authorized");
        _tokenApprovals[tokenId] = to;
        emit Approval(owner, to, tokenId);
    }
    
    function setApprovalForAll(address operator, bool approved) external override {
        _operatorApprovals[msg.sender][operator] = approved;
        emit ApprovalForAll(msg.sender, operator, approved);
    }
    
    function getApproved(uint256 tokenId) external view override returns (address) {
        require(_owners[tokenId] != address(0), "ERC721: nonexistent token");
        return _tokenApprovals[tokenId];
    }
    
    function isApprovedForAll(address owner, address operator) public view override returns (bool) {
        return _operatorApprovals[owner][operator];
    }
    
    function transferFrom(address from, address to, uint256 tokenId) public override {
        require(_isApprovedOrOwner(msg.sender, tokenId), "ERC721: not authorized");
        _transfer(from, to, tokenId);
    }
    
    function safeTransferFrom(address from, address to, uint256 tokenId) external override {
        safeTransferFrom(from, to, tokenId, "");
    }
    
    function safeTransferFrom(address from, address to, uint256 tokenId, bytes memory data) public override {
        transferFrom(from, to, tokenId);
        require(_checkOnERC721Received(from, to, tokenId, data), "ERC721: non-receiver");
    }
    
    function mint(address to) external returns (uint256) {
        uint256 tokenId = _tokenIdCounter++;
        _balances[to]++;
        _owners[tokenId] = to;
        emit Transfer(address(0), to, tokenId);
        return tokenId;
    }
    
    function _transfer(address from, address to, uint256 tokenId) internal {
        require(ownerOf(tokenId) == from, "ERC721: wrong owner");
        require(to != address(0), "ERC721: zero address");
        
        delete _tokenApprovals[tokenId];
        _balances[from]--;
        _balances[to]++;
        _owners[tokenId] = to;
        
        emit Transfer(from, to, tokenId);
    }
    
    function _isApprovedOrOwner(address spender, uint256 tokenId) internal view returns (bool) {
        address owner = ownerOf(tokenId);
        return (spender == owner || 
                _tokenApprovals[tokenId] == spender || 
                _operatorApprovals[owner][spender]);
    }
    
    function _checkOnERC721Received(address from, address to, uint256 tokenId, bytes memory data) private returns (bool) {
        if (to.code.length > 0) {
            try IERC721Receiver(to).onERC721Received(msg.sender, from, tokenId, data) returns (bytes4 retval) {
                return retval == IERC721Receiver.onERC721Received.selector;
            } catch {
                return false;
            }
        }
        return true;
    }
    
    function toString(uint256 value) internal pure returns (string memory) {
        if (value == 0) return "0";
        uint256 temp = value;
        uint256 digits;
        while (temp != 0) {
            digits++;
            temp /= 10;
        }
        bytes memory buffer = new bytes(digits);
        while (value != 0) {
            digits--;
            buffer[digits] = bytes1(uint8(48 + value % 10));
            value /= 10;
        }
        return string(buffer);
    }
}

interface IERC721Receiver {
    function onERC721Received(
        address operator,
        address from,
        uint256 tokenId,
        bytes calldata data
    ) external returns (bytes4);
}
```

### 枚举扩展

ERC-721 Enumerable 扩展允许遍历所有代币和某个地址拥有的代币：

```solidity
interface IERC721Enumerable is IERC721 {
    function totalSupply() external view returns (uint256);
    function tokenByIndex(uint256 index) external view returns (uint256);
    function tokenOfOwnerByIndex(address owner, uint256 index) external view returns (uint256);
}
```

这个扩展增加了存储成本，但对于需要在链上遍历 NFT 的应用很有用。

---

## ERC-1155：多代币标准

ERC-1155 是一个更灵活的标准，允许在单个合约中管理多种代币类型——既可以是同质化的（如游戏金币），也可以是非同质化的（如游戏装备）。

### 设计动机

在游戏场景中，可能需要管理数百种不同的物品。如果每种物品都部署一个 ERC-20 或 ERC-721 合约，Gas 成本会非常高。ERC-1155 允许在一个合约中管理所有物品，并支持批量操作，大幅降低 Gas 成本。

### 核心接口

```solidity
interface IERC1155 {
    // 查询函数
    function balanceOf(address account, uint256 id) external view returns (uint256);
    function balanceOfBatch(address[] calldata accounts, uint256[] calldata ids) external view returns (uint256[] memory);
    
    // 授权函数
    function setApprovalForAll(address operator, bool approved) external;
    function isApprovedForAll(address account, address operator) external view returns (bool);
    
    // 转账函数
    function safeTransferFrom(address from, address to, uint256 id, uint256 amount, bytes calldata data) external;
    function safeBatchTransferFrom(address from, address to, uint256[] calldata ids, uint256[] calldata amounts, bytes calldata data) external;
    
    // 事件
    event TransferSingle(address indexed operator, address indexed from, address indexed to, uint256 id, uint256 value);
    event TransferBatch(address indexed operator, address indexed from, address indexed to, uint256[] ids, uint256[] values);
    event ApprovalForAll(address indexed account, address indexed operator, bool approved);
    event URI(string value, uint256 indexed id);
}
```

注意 `balanceOf` 需要两个参数：地址和代币 ID。批量操作（`balanceOfBatch`、`safeBatchTransferFrom`）可以在一次交易中处理多种代币。

### 基础实现

```solidity
contract GameItems is IERC1155 {
    // id => account => balance
    mapping(uint256 => mapping(address => uint256)) private _balances;
    mapping(address => mapping(address => bool)) private _operatorApprovals;
    
    string private _uri;
    
    // 代币类型常量
    uint256 public constant GOLD = 0;      // 同质化：金币
    uint256 public constant SILVER = 1;    // 同质化：银币
    uint256 public constant SWORD = 2;     // 非同质化：剑（每把唯一）
    uint256 public constant SHIELD = 3;    // 非同质化：盾
    
    constructor(string memory uri_) {
        _uri = uri_;
    }
    
    function uri(uint256 id) external view returns (string memory) {
        return string(abi.encodePacked(_uri, toString(id), ".json"));
    }
    
    function balanceOf(address account, uint256 id) public view override returns (uint256) {
        require(account != address(0), "ERC1155: zero address");
        return _balances[id][account];
    }
    
    function balanceOfBatch(address[] calldata accounts, uint256[] calldata ids) 
        external view override returns (uint256[] memory) 
    {
        require(accounts.length == ids.length, "ERC1155: length mismatch");
        
        uint256[] memory batchBalances = new uint256[](accounts.length);
        for (uint256 i = 0; i < accounts.length; i++) {
            batchBalances[i] = balanceOf(accounts[i], ids[i]);
        }
        return batchBalances;
    }
    
    function setApprovalForAll(address operator, bool approved) external override {
        _operatorApprovals[msg.sender][operator] = approved;
        emit ApprovalForAll(msg.sender, operator, approved);
    }
    
    function isApprovedForAll(address account, address operator) public view override returns (bool) {
        return _operatorApprovals[account][operator];
    }
    
    function safeTransferFrom(
        address from, address to, uint256 id, uint256 amount, bytes calldata data
    ) external override {
        require(from == msg.sender || isApprovedForAll(from, msg.sender), "ERC1155: not authorized");
        require(to != address(0), "ERC1155: zero address");
        
        _balances[id][from] -= amount;
        _balances[id][to] += amount;
        
        emit TransferSingle(msg.sender, from, to, id, amount);
        
        _doSafeTransferAcceptanceCheck(msg.sender, from, to, id, amount, data);
    }
    
    function safeBatchTransferFrom(
        address from, address to, uint256[] calldata ids, uint256[] calldata amounts, bytes calldata data
    ) external override {
        require(from == msg.sender || isApprovedForAll(from, msg.sender), "ERC1155: not authorized");
        require(to != address(0), "ERC1155: zero address");
        require(ids.length == amounts.length, "ERC1155: length mismatch");
        
        for (uint256 i = 0; i < ids.length; i++) {
            _balances[ids[i]][from] -= amounts[i];
            _balances[ids[i]][to] += amounts[i];
        }
        
        emit TransferBatch(msg.sender, from, to, ids, amounts);
        
        _doSafeBatchTransferAcceptanceCheck(msg.sender, from, to, ids, amounts, data);
    }
    
    function mint(address to, uint256 id, uint256 amount) external {
        _balances[id][to] += amount;
        emit TransferSingle(msg.sender, address(0), to, id, amount);
    }
    
    function mintBatch(address to, uint256[] calldata ids, uint256[] calldata amounts) external {
        require(ids.length == amounts.length, "ERC1155: length mismatch");
        
        for (uint256 i = 0; i < ids.length; i++) {
            _balances[ids[i]][to] += amounts[i];
        }
        
        emit TransferBatch(msg.sender, address(0), to, ids, amounts);
    }
    
    function _doSafeTransferAcceptanceCheck(
        address operator, address from, address to, uint256 id, uint256 amount, bytes memory data
    ) private {
        if (to.code.length > 0) {
            try IERC1155Receiver(to).onERC1155Received(operator, from, id, amount, data) returns (bytes4 response) {
                require(response == IERC1155Receiver.onERC1155Received.selector, "ERC1155: rejected");
            } catch {
                revert("ERC1155: non-receiver");
            }
        }
    }
    
    function _doSafeBatchTransferAcceptanceCheck(
        address operator, address from, address to, uint256[] memory ids, uint256[] memory amounts, bytes memory data
    ) private {
        if (to.code.length > 0) {
            try IERC1155Receiver(to).onERC1155BatchReceived(operator, from, ids, amounts, data) returns (bytes4 response) {
                require(response == IERC1155Receiver.onERC1155BatchReceived.selector, "ERC1155: rejected");
            } catch {
                revert("ERC1155: non-receiver");
            }
        }
    }
    
    function toString(uint256 value) internal pure returns (string memory) {
        if (value == 0) return "0";
        uint256 temp = value;
        uint256 digits;
        while (temp != 0) { digits++; temp /= 10; }
        bytes memory buffer = new bytes(digits);
        while (value != 0) { digits--; buffer[digits] = bytes1(uint8(48 + value % 10)); value /= 10; }
        return string(buffer);
    }
}

interface IERC1155Receiver {
    function onERC1155Received(address operator, address from, uint256 id, uint256 value, bytes calldata data) external returns (bytes4);
    function onERC1155BatchReceived(address operator, address from, uint256[] calldata ids, uint256[] calldata values, bytes calldata data) external returns (bytes4);
}
```

---

## ERC-20 扩展：Permit

传统的 ERC-20 授权需要两笔交易：先 `approve`，再让 DEX 调用 `transferFrom`。ERC-2612（Permit）允许用户通过签名授权，将两笔交易合并为一笔。

```solidity
interface IERC20Permit {
    function permit(
        address owner,
        address spender,
        uint256 value,
        uint256 deadline,
        uint8 v, bytes32 r, bytes32 s
    ) external;
    
    function nonces(address owner) external view returns (uint256);
    function DOMAIN_SEPARATOR() external view returns (bytes32);
}
```

用户签署一个包含授权信息的消息，DEX 在调用 `transferFrom` 之前先调用 `permit` 验证签名并设置授权。整个过程只需要一笔交易。

```solidity
abstract contract ERC20Permit is ERC20, IERC20Permit {
    mapping(address => uint256) public override nonces;
    
    bytes32 public override DOMAIN_SEPARATOR;
    bytes32 private constant PERMIT_TYPEHASH = keccak256(
        "Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)"
    );
    
    constructor() {
        DOMAIN_SEPARATOR = keccak256(abi.encode(
            keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
            keccak256(bytes(name)),
            keccak256(bytes("1")),
            block.chainid,
            address(this)
        ));
    }
    
    function permit(
        address owner, address spender, uint256 value, uint256 deadline,
        uint8 v, bytes32 r, bytes32 s
    ) external override {
        require(block.timestamp <= deadline, "ERC20Permit: expired");
        
        bytes32 structHash = keccak256(abi.encode(
            PERMIT_TYPEHASH, owner, spender, value, nonces[owner]++, deadline
        ));
        
        bytes32 hash = keccak256(abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR, structHash));
        address signer = ecrecover(hash, v, r, s);
        
        require(signer != address(0) && signer == owner, "ERC20Permit: invalid signature");
        
        _approve(owner, spender, value);
    }
}
```

---

## ERC-4626：金库标准

ERC-4626 是 DeFi 中收益金库的标准化接口。Yearn、Aave、Compound 等协议的收益代币都可以用这个标准来描述。它让不同协议的金库可以互相组合，大大简化了 DeFi 的可组合性。

### 核心概念

金库的基本模式是：用户存入底层资产（如 USDC），获得份额代币（如 yUSDC）。金库用这些资产去赚取收益。当用户赎回时，用份额代币换回底层资产加上收益。

份额计算的核心公式：

```
shares = assets × totalShares / totalAssets
assets = shares × totalAssets / totalShares
```

收益来自 `totalAssets` 增加而 `totalShares` 不变。如果金库通过投资让资产从 1000 增长到 1100，而份额总量保持 1000 不变，那么每份额的价值就从 1 变成了 1.1。

### 核心接口

```solidity
interface IERC4626 is IERC20 {
    function asset() external view returns (address);
    function totalAssets() external view returns (uint256);
    
    function deposit(uint256 assets, address receiver) external returns (uint256 shares);
    function mint(uint256 shares, address receiver) external returns (uint256 assets);
    function withdraw(uint256 assets, address receiver, address owner) external returns (uint256 shares);
    function redeem(uint256 shares, address receiver, address owner) external returns (uint256 assets);
    
    function convertToShares(uint256 assets) external view returns (uint256);
    function convertToAssets(uint256 shares) external view returns (uint256);
    
    function previewDeposit(uint256 assets) external view returns (uint256);
    function previewMint(uint256 shares) external view returns (uint256);
    function previewWithdraw(uint256 assets) external view returns (uint256);
    function previewRedeem(uint256 shares) external view returns (uint256);
}
```

`deposit` 和 `mint` 都是存款，区别在于指定的是资产数量还是份额数量。`withdraw` 和 `redeem` 同理。`preview` 函数用于预估操作结果，`convert` 函数用于纯粹的数学转换。

### 通胀攻击

ERC-4626 最重要的安全问题是通胀攻击。攻击者作为第一个存款人，存入极少量资产（如 1 wei），然后直接向金库转入大量资产（不通过 deposit）。这会让后续存款人因为舍入误差而获得 0 份额。

```
攻击流程：
1. 攻击者存入 1 wei，获得 1 份额
2. 攻击者直接转入 1000 USDC（不通过 deposit）
3. 此时 totalAssets = 1000 USDC + 1 wei，totalShares = 1
4. 受害者存入 500 USDC
5. shares = 500 × 1 / 1000 = 0（舍入到 0）
```

防护方法是使用虚拟份额。OpenZeppelin 的 ERC4626 实现已经内置了这个防护：

```solidity
function _decimalsOffset() internal pure virtual returns (uint8) {
    return 0;  // 可以覆盖为更大的值
}

function convertToShares(uint256 assets) public view returns (uint256) {
    return assets.mulDiv(
        totalSupply() + 10 ** _decimalsOffset(),
        totalAssets() + 1,
        Math.Rounding.Down
    );
}
```

---

## 标准选择指南

![代币标准对比](/images/scriptures/smart-contracts/06-token-comparison.png)

选择代币标准的核心问题是：资产是否可互换？ERC-20 适合完全同质化的资产，每个单位没有区别；ERC-721 适合每个资产都独一无二的场景；ERC-1155 则是两者的结合，特别适合需要批量操作的游戏场景。

对于治理代币，通常选择 ERC-20 并添加快照功能，以便在投票时追溯历史余额。对于门票或会员卡，如果需要批量发行且每张票没有本质区别，ERC-1155 更高效；如果每张票需要独特属性，则选择 ERC-721。

---

## 总结

代币标准是以太坊生态系统的基础设施。ERC-20 的简洁设计让 DeFi 成为可能，ERC-721 开创了 NFT 市场，ERC-1155 为游戏和复杂应用提供了灵活性。

理解这些标准的接口和实现细节，不仅有助于开发自己的代币，也有助于理解与其他协议的交互方式。下一章将讨论合约升级模式，解决智能合约"部署后不可修改"的限制。

---

## 参考文献

- [EIP-20: Token Standard](https://eips.ethereum.org/EIPS/eip-20)
- [EIP-721: Non-Fungible Token Standard](https://eips.ethereum.org/EIPS/eip-721)
- [EIP-1155: Multi Token Standard](https://eips.ethereum.org/EIPS/eip-1155)
- [EIP-2612: Permit Extension](https://eips.ethereum.org/EIPS/eip-2612)
- [EIP-4626: Tokenized Vault Standard](https://eips.ethereum.org/EIPS/eip-4626)
- [OpenZeppelin ERC20](https://docs.openzeppelin.com/contracts/4.x/erc20)
- [OpenZeppelin ERC721](https://docs.openzeppelin.com/contracts/4.x/erc721)
- [OpenZeppelin ERC4626](https://docs.openzeppelin.com/contracts/4.x/erc4626)
