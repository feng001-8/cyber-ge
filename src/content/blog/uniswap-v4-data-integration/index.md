---
title: "Uniswap V4 数据获取实战：定制合约与批量查询"
description: "可直接使用的 Uniswap V4 数据获取方案：已部署的查询合约、完整的 Go 代码、字节编码格式、各链 Hook 统计。"
pubDate: "2026-03-01"
tags: ["DeFi", "Uniswap", "Go", "智能合约"]
hexagram: "䷜"
element: "water"
---

**TL;DR:** 本文提供一套可直接使用的 Uniswap V4 数据获取方案：(1) 已部署在 Base/Arbitrum/Optimism/Unichain 的批量查询合约；(2) 完整的 Go 代码封装；(3) 事件驱动 + 批量查询的架构设计。所有代码和地址都经过生产验证。

> **前置知识**：本文假设读者熟悉 Uniswap V4 的基本架构。如果不熟悉，建议先阅读 [Uniswap V4 架构解析](/blog/uniswap-v4-architecture)。

---

## 数据获取架构

[![数据获取流程](/images/blog/uniswap-v4-data-integration/data-flow.png)](https://excalidraw.com/#json=-CkKthAygPkG4F6LAdZcZ,De_B9jlG32xB7EY-jTxLcw)

### 三层架构

**Layer 1: 事件驱动触发**

监听链上事件（Initialize、ModifyLiquidity、Swap），当检测到目标池子的状态变化时，将 PoolId 加入更新队列。

**Layer 2: 批量 RPC 查询**

使用定制智能合约，一次调用获取多个池子的 slot0、liquidity、tickBitmap 等数据。

**Layer 3: 缓存 + 内存分层**

查询结果写入 Redis，应用层从内存热数据读取。

---

## 关键事件

V4 定义了三个核心事件：

```solidity
event Initialize(
    PoolId indexed id,
    Currency indexed currency0,
    Currency indexed currency1,
    uint24 fee,
    int24 tickSpacing,
    IHooks hooks,
    uint160 sqrtPriceX96,
    int24 tick
);

event ModifyLiquidity(
    PoolId indexed id, 
    address indexed sender, 
    int24 tickLower, 
    int24 tickUpper, 
    int256 liquidityDelta,
    bytes32 salt
);

event Swap(
    PoolId indexed id,
    address indexed sender,
    int128 amount0,
    int128 amount1,
    uint160 sqrtPriceX96,
    uint128 liquidity,
    int24 tick,
    uint24 fee
);
```

Swap 事件已经包含了 sqrtPriceX96 和 tick，可以直接使用，减少后续查询。

---

## 定制查询合约

### 合约源码

```solidity
//SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

interface IPositionManager {
    struct PoolKey {
        address currency0;
        address currency1;
        uint24 fee;
        int24 tickSpacing;
        address hooks;
    }
    function nextTokenId() external view returns (uint256);
    function getPoolAndPositionInfo(uint256 tokenId) external view returns (PoolKey memory, uint);
}

contract Uniswap4QueryUtil {
    struct PoolData {
        int24 tick;
        uint24 protocolFee;
        uint24 lpFee;
        uint128 liquidity;
        uint160 sqrtPriceX96;
        uint256[] tickBitmaps;
    }

    function lastTokenId(IPositionManager pm) external view returns (uint256) {
        return pm.nextTokenId() - 1;
    }

    function batchpositionsStep(
        uint256 tokenIdStart,
        uint256 nums,
        IPositionManager pm
    ) external view returns (IPositionManager.PoolKey[] memory pools) {
        uint256[] memory tokenIds = new uint256[](nums);
        for (uint i; i < nums; ++i) {
            tokenIds[i] = tokenIdStart + i;
        }
        return batchPositions(tokenIds, pm);
    }

    function batchPositions(
        uint256[] memory tokenIds,
        IPositionManager pm
    ) internal view returns (IPositionManager.PoolKey[] memory pools) {
        uint l = tokenIds.length;
        pools = new IPositionManager.PoolKey[](l);
        for (uint i; i < l; ++i) {
            (pools[i], ) = pm.getPoolAndPositionInfo(tokenIds[i]);
        }
    }

    function getPoolDatas(bytes memory sdata) external view returns (PoolData[] memory poolDatas) {
        // 解析输入数据，批量查询多个池子
        // 详见完整源码
    }

    function getTickLiqs(bytes memory tickDatas) external view returns (int128[] memory liquidityNets) {
        // 批量获取 tick 的 liquidityNet
        // 详见完整源码
    }
}
```

### 已部署地址

| 链 | 查询合约 | StateView |
|----|----------|-----------|
| **Base** | `0x583A66CB2fB433F93c6B1d70cD976032774AE994` | `0xd13Dd3D6E93f276FAfc9Db9E6BB47C1180aeE0c4` |
| **Arbitrum** | `0xaaD84583a9A0e539F1561c0eE72617565E2FC71e` | - |
| **Optimism** | `0xf51E7e6dBab49C7098D48D99779103873AA47bC2` | - |
| **Unichain** | `0x1D092549f04305373bC7833F73b7584cA638D740` | - |

通用查询合约：`0x30348bEE05FB2a87EA964a7677420D6F15d2A0B6`

---

## 输入数据编码

### getPoolDatas 输入格式

```
[stateViewAddress: 20 bytes]
[poolId: 32 bytes][tickSpacing: 3 bytes][numWords: 1 byte]
[poolId: 32 bytes][tickSpacing: 3 bytes][numWords: 1 byte]
...
```

示例：

```
0xd13dd3d6e93f276fafc9db9e6bb47c1180aee0c4  // StateView 地址
F8C7B3C122F31AEC155C6BEB0C1C78A5E74208358A840CADFBC6129B59391850  // PoolId
000001  // tickSpacing = 1
02      // numWords = 2
```

### getTickLiqs 输入格式

```
[poolCount: 2 bytes][totalTickCount: 2 bytes]
[stateViewAddress: 20 bytes][poolId: 32 bytes][tickCount: 2 bytes][tick1: 3 bytes][tick2: 3 bytes]...
```

---

## Go 代码封装

### 获取 PoolKey 和 PoolId

```go
func TestGetPoolKeyAndId(t *testing.T) {
    conn, _ := ethereum.NewConnection("https://bsc.nodereal.io")
    
    uniswap4QueryUtil, _ := contracts.NewUniswap4QueryUtil(
        common.HexToAddress("0x30348bEE05FB2a87EA964a7677420D6F15d2A0B6"),
        conn.Client())
    
    positionManagerAddr := common.HexToAddress("0x7a4a5c919ae2541aed11041a1aeee68f1287f95b")
    
    // 获取最新 tokenId
    lastTokenId, _ := uniswap4QueryUtil.LastTokenId(nil, positionManagerAddr)
    
    // 批量获取 poolKey
    poolKeys, _ := uniswap4QueryUtil.BatchpositionsStep(
        nil, 
        big.NewInt(1),      // tokenIdStart
        big.NewInt(100),    // nums
        positionManagerAddr)
    
    // 计算 PoolId
    for _, poolKey := range poolKeys {
        bytes, _ := arguments.Pack(
            poolKey.Currency0,
            poolKey.Currency1,
            poolKey.Fee,
            poolKey.TickSpacing,
            poolKey.Hooks,
        )
        poolId := crypto.Keccak256(bytes)
        fmt.Printf("PoolId: %x\n", poolId)
    }
}
```

### 获取 PoolTickInfos

```go
func TestGetPoolTickInfo(t *testing.T) {
    // 构造查询数据
    stateViewAddress := "0xd13dd3d6e93f276fafc9db9e6bb47c1180aee0c4"
    poolIds := []string{
        "F8C7B3C122F31AEC155C6BEB0C1C78A5E74208358A840CADFBC6129B59391850",
        "1AFD24D7A5C2247B31858344E40BF69403B0CFBE4D8CAEEB4FB74AC6D1766FA1",
    }
    tickSpacings := []*big.Int{big.NewInt(1), big.NewInt(60)}
    
    // 编码输入
    sData := "0x" + stateViewAddress[2:]
    for i := range poolIds {
        sData += poolIds[i] + 
            fmt.Sprintf("%06x", tickSpacings[i]) + 
            fmt.Sprintf("%02x", numStart)
    }
    
    // 调用合约
    poolDatas, _ := uniswap4QueryUtil.GetPoolDatas(nil, hexutil.MustDecode(sData))
    
    // 解析 tickBitmap，找到已初始化的 tick
    for _, data := range poolDatas {
        for j, bitMap := range data.TickBitmaps {
            if bitMap.Cmp(big.NewInt(0)) != 0 {
                loadPopulatedTicksInWord(bitMap, wordPos, tickSpacing, tickInfo)
            }
        }
    }
    
    // 批量获取 liquidityNet
    tickLiqs, _ := uniswap4QueryUtil.GetTickLiqs(nil, tickData)
}
```

### 辅助函数

```go
func loadPopulatedTicksInWord(bitMap *big.Int, wordPos int64, tickSpacing int64, tickInfo *TickInfo) {
    for i := int64(0); i < 256; i++ {
        if new(big.Int).And(bitMap, new(big.Int).Lsh(big.NewInt(1), uint(i))).Cmp(big.NewInt(0)) > 0 {
            tick := ((wordPos << 8) + i) * tickSpacing
            tickInfo.Ticks = append(tickInfo.Ticks, big.NewInt(tick))
        }
    }
}

func GetInt24(tick *big.Int) *big.Int {
    tt24m1 := new(big.Int).Sub(math.BigPow(2, 24), big.NewInt(1))
    return new(big.Int).And(tick, tt24m1)
}
```

---

## V4 数据结构

### Slot0 位布局

```
| 24 bits | 24 bits | 12 bits | 12 bits | 24 bits | 160 bits |
| empty   | lpFee   | fee 1→0 | fee 0→1 | tick    | sqrtPriceX96 |
```

解析代码：

```go
sqrtPriceX96 := slot0 & ((1 << 160) - 1)
tick := int24((slot0 >> 160) & ((1 << 24) - 1))
protocolFee01 := (slot0 >> 184) & ((1 << 12) - 1)
protocolFee10 := (slot0 >> 196) & ((1 << 12) - 1)
lpFee := (slot0 >> 208) & ((1 << 24) - 1)
```

### TickInfo 结构

```solidity
struct TickInfo {
    uint128 liquidityGross;      // 总流动性
    int128 liquidityNet;         // 净流动性（穿越时更新）
    uint256 feeGrowthOutside0X128;
    uint256 feeGrowthOutside1X128;
}
```

### SwapParams 注意事项

```solidity
struct SwapParams {
    int256 amountSpecified;  // 负数 = exactInput，正数 = exactOutput
    int24 tickSpacing;
    bool zeroForOne;
    uint160 sqrtPriceLimitX96;
    uint24 lpFeeOverride;
}
```

**V4 的 amountSpecified 符号与 V3 相反**：
- V3：正数 = exactInput
- V4：**负数 = exactInput**

---

## Hook 使用统计

### Base 链 Top 10

| Hook 地址 | 池子数量 | 类型 |
|-----------|----------|------|
| `0xdd5eeaff...cdf0a68cc` | 29,059 | Clanker Static Fee |
| `0x34a45c6b...e29b35e0cc` | 2,241 | - |
| `0x2d0d55e8...f05248fc040` | 1,048 | - |
| `0x766d77aa...a36f80cc` | 26 | - |
| `0x9f37e240...c153a0eaec` | 26 | - |
| `0xf68e7120...892740cc` | 24 | - |
| `0x4440854b...d875c0c4` | 22 | - |
| `0xd61a675f...9409040` | 21 | - |
| `0xb9bf9560...c53067ca80cc` | 15 | - |
| `0xa6c8d751...151d43c0c0` | 14 | - |

### Arbitrum 链

| Hook 地址 | 池子数量 |
|-----------|----------|
| `0xf7ac6695...4f7aaa8cc` | 175 |
| `0xfd213be7...f22faa0ac0` | 40 |
| `0x4440854b...d875c0c4` | 22 |
| `0xa6c8d751...151d43c0c0` | 14 |

### Unichain

32 个不同的 Hook 合约，68 个池子。分布更加分散，反映了开发者在 Unichain 上的实验性部署。

---

## 性能指标

| 指标 | 数值 |
|------|------|
| 事件传播延迟 | 1-3 个区块 |
| 批量查询 RPC 调用 | O(1) per batch |
| 内存读取延迟 | <1ms |
| 单次 getPoolDatas 可查询池子数 | ~50（受 Gas 限制） |

---

## 进一步阅读

- [Uniswap V4 架构解析](/blog/uniswap-v4-architecture) — 本文的姊妹篇，解释 V4 的设计理念
- [v4-core GitHub](https://github.com/Uniswap/v4-core) — 核心合约源码
- [StateView 合约](https://basescan.org/address/0xd13Dd3D6E93f276FAfc9Db9E6BB47C1180aeE0c4) — Base 链上的 StateView
- [Clanker Hook](https://basescan.org/address/0xdd5eeaff7bd481ad55db083062b13a3cdf0a68cc) — 最广泛使用的 Hook 实现
