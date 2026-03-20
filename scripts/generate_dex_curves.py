#!/usr/bin/env python3
"""Generate SVG curves for DEX mechanisms article."""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# Set style for clean, minimal look
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.linewidth'] = 1.5
plt.rcParams['grid.alpha'] = 0.3

# Color palette (Cyber-Zen style)
JADE = '#4A8B71'
CINNABAR = '#D13429'
CHARCOAL = '#474747'
GRAY = '#8C928F'

def generate_constant_product_curve():
    """Generate x * y = k curve (Uniswap V2)."""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # k = 10000 (100 ETH * 100 USDC for simplicity)
    k = 10000
    x = np.linspace(10, 200, 500)
    y = k / x
    
    ax.plot(x, y, color=JADE, linewidth=2.5, label='x × y = k')
    
    # Mark current state
    ax.scatter([100], [100], color=JADE, s=100, zorder=5)
    ax.annotate('当前状态\n(100, 100)', xy=(100, 100), xytext=(130, 130),
                fontsize=10, color=CHARCOAL,
                arrowprops=dict(arrowstyle='->', color=GRAY))
    
    # Mark trade: buy ETH with USDC
    # New state after adding 20 USDC: y = 120, x = 10000/120 = 83.33
    ax.scatter([83.33], [120], color=CINNABAR, s=100, zorder=5)
    ax.annotate('交易后\n(83.3, 120)', xy=(83.33, 120), xytext=(50, 150),
                fontsize=10, color=CHARCOAL,
                arrowprops=dict(arrowstyle='->', color=GRAY))
    
    # Draw trade path
    ax.annotate('', xy=(83.33, 120), xytext=(100, 100),
                arrowprops=dict(arrowstyle='->', color=CINNABAR, lw=2))
    
    ax.set_xlabel('ETH 储备', fontsize=12, color=CHARCOAL)
    ax.set_ylabel('USDC 储备', fontsize=12, color=CHARCOAL)
    ax.set_title('恒定乘积曲线 (x × y = k)', fontsize=14, color=CHARCOAL, fontweight='bold')
    ax.set_xlim(0, 220)
    ax.set_ylim(0, 220)
    ax.legend(loc='upper right', fontsize=10)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.savefig('/Users/feng/Documents/person/cyber-zen/src/content/blog/curve_constant_product.svg', 
                format='svg', transparent=True, dpi=150)
    plt.close()
    print("Generated: curve_constant_product.svg")

def generate_stableswap_comparison():
    """Generate comparison of constant product, constant sum, and StableSwap curves."""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Parameters
    D = 200  # Total liquidity (x + y at equilibrium)
    
    # 1. Constant sum: x + y = D (ideal for stablecoins but can be drained)
    x_sum = np.linspace(0, D, 500)
    y_sum = D - x_sum
    ax.plot(x_sum, y_sum, color=GRAY, linewidth=2, linestyle='--', label='x + y = k (恒定和)')
    
    # 2. Constant product: x * y = k, where k = (D/2)^2
    k = (D/2) ** 2
    x_prod = np.linspace(10, 190, 500)
    y_prod = k / x_prod
    ax.plot(x_prod, y_prod, color=CINNABAR, linewidth=2, label='x × y = k (恒定乘积)')
    
    # 3. StableSwap curve (simplified approximation)
    # The actual StableSwap invariant is complex, we'll use a blend
    # StableSwap: A * (x + y) + D = A * D + D^3 / (4 * x * y)
    # For visualization, we use a weighted average that's flatter near equilibrium
    A = 100  # Amplification coefficient
    
    def stableswap_y(x_val, A, D):
        """Approximate StableSwap curve."""
        # Blend between constant sum and constant product based on distance from equilibrium
        y_sum_val = D - x_val
        y_prod_val = k / x_val if x_val > 0 else D
        
        # Weight: closer to equilibrium = more like constant sum
        distance = abs(x_val - D/2) / (D/2)
        weight = np.exp(-A * (1 - distance**2) / 10)
        
        return (1 - weight) * y_sum_val + weight * y_prod_val
    
    x_stable = np.linspace(5, 195, 500)
    y_stable = [stableswap_y(x, A, D) for x in x_stable]
    ax.plot(x_stable, y_stable, color=JADE, linewidth=2.5, label='StableSwap (Curve)')
    
    # Mark equilibrium point
    ax.scatter([100], [100], color=JADE, s=120, zorder=5, edgecolors='white', linewidths=2)
    ax.annotate('1:1 均衡点', xy=(100, 100), xytext=(130, 130),
                fontsize=11, color=CHARCOAL,
                arrowprops=dict(arrowstyle='->', color=GRAY))
    
    # Highlight the "sweet spot" region
    ax.axvspan(80, 120, alpha=0.1, color=JADE)
    ax.text(100, 20, '低滑点区间', ha='center', fontsize=10, color=JADE)
    
    ax.set_xlabel('USDC 储备', fontsize=12, color=CHARCOAL)
    ax.set_ylabel('USDT 储备', fontsize=12, color=CHARCOAL)
    ax.set_title('AMM 曲线对比：稳定币场景', fontsize=14, color=CHARCOAL, fontweight='bold')
    ax.set_xlim(0, 210)
    ax.set_ylim(0, 210)
    ax.legend(loc='upper right', fontsize=11)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.savefig('/Users/feng/Documents/person/cyber-zen/src/content/blog/curve_stableswap_comparison.svg',
                format='svg', transparent=True, dpi=150)
    plt.close()
    print("Generated: curve_stableswap_comparison.svg")

def generate_concentrated_liquidity():
    """Generate concentrated liquidity visualization (V2 vs V3)."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Price range
    prices = np.linspace(500, 4000, 500)
    current_price = 2000
    
    # V2: Uniform liquidity distribution
    ax1 = axes[0]
    liquidity_v2 = np.ones_like(prices) * 0.5
    ax1.fill_between(prices, liquidity_v2, alpha=0.3, color=GRAY)
    ax1.plot(prices, liquidity_v2, color=GRAY, linewidth=2)
    ax1.axvline(x=current_price, color=JADE, linestyle='--', linewidth=2, label='当前价格')
    ax1.set_xlabel('价格 (USDC/ETH)', fontsize=12, color=CHARCOAL)
    ax1.set_ylabel('流动性深度', fontsize=12, color=CHARCOAL)
    ax1.set_title('Uniswap V2: 全范围流动性', fontsize=13, color=CHARCOAL, fontweight='bold')
    ax1.set_xlim(500, 4000)
    ax1.set_ylim(0, 3)
    ax1.legend(loc='upper right')
    ax1.text(2500, 0.7, '资本效率 ~1x', fontsize=11, color=CINNABAR)
    ax1.text(2500, 0.4, '大部分流动性未使用', fontsize=10, color=GRAY)
    
    # V3: Concentrated liquidity
    ax2 = axes[1]
    # Multiple LP positions at different ranges
    def gaussian(x, mu, sigma, height):
        return height * np.exp(-((x - mu) ** 2) / (2 * sigma ** 2))
    
    # Simulate multiple LPs concentrating around current price
    liq_v3 = (gaussian(prices, 1800, 100, 2.5) + 
              gaussian(prices, 2000, 150, 3) + 
              gaussian(prices, 2200, 120, 2))
    
    ax2.fill_between(prices, liq_v3, alpha=0.3, color=JADE)
    ax2.plot(prices, liq_v3, color=JADE, linewidth=2)
    ax2.axvline(x=current_price, color=JADE, linestyle='--', linewidth=2, label='当前价格')
    
    # Mark the concentrated range
    ax2.axvspan(1800, 2200, alpha=0.1, color=JADE)
    ax2.annotate('集中区间\n$1800-$2200', xy=(2000, 2.5), xytext=(2800, 2.5),
                fontsize=10, color=CHARCOAL,
                arrowprops=dict(arrowstyle='->', color=GRAY))
    
    ax2.set_xlabel('价格 (USDC/ETH)', fontsize=12, color=CHARCOAL)
    ax2.set_ylabel('流动性深度', fontsize=12, color=CHARCOAL)
    ax2.set_title('Uniswap V3: 集中流动性', fontsize=13, color=CHARCOAL, fontweight='bold')
    ax2.set_xlim(500, 4000)
    ax2.set_ylim(0, 3.5)
    ax2.legend(loc='upper right')
    ax2.text(2500, 3.2, '资本效率 最高4000x', fontsize=11, color=JADE)
    ax2.text(2500, 2.9, '同等资金，更深流动性', fontsize=10, color=GRAY)
    
    plt.tight_layout()
    plt.savefig('/Users/feng/Documents/person/cyber-zen/src/content/blog/curve_concentrated_liquidity.svg',
                format='svg', transparent=True, dpi=150)
    plt.close()
    print("Generated: curve_concentrated_liquidity.svg")

def generate_slippage_comparison():
    """Generate slippage comparison chart."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Trade sizes
    trade_sizes = np.array([1000, 10000, 100000, 500000, 1000000])
    trade_labels = ['$1K', '$10K', '$100K', '$500K', '$1M']
    
    # Slippage estimates (simplified model)
    # Uniswap V2: higher slippage
    slippage_v2 = np.array([0.05, 0.3, 2.5, 10, 18])
    
    # Curve (for stablecoins): much lower
    slippage_curve = np.array([0.001, 0.005, 0.02, 0.08, 0.15])
    
    # Uniswap V3 (concentrated): medium
    slippage_v3 = np.array([0.02, 0.1, 0.8, 3, 6])
    
    x = np.arange(len(trade_sizes))
    width = 0.25
    
    bars1 = ax.bar(x - width, slippage_v2, width, label='Uniswap V2', color=GRAY, alpha=0.8)
    bars2 = ax.bar(x, slippage_v3, width, label='Uniswap V3', color=JADE, alpha=0.8)
    bars3 = ax.bar(x + width, slippage_curve, width, label='Curve (稳定币)', color=CINNABAR, alpha=0.8)
    
    ax.set_xlabel('交易金额', fontsize=12, color=CHARCOAL)
    ax.set_ylabel('滑点 (%)', fontsize=12, color=CHARCOAL)
    ax.set_title('不同 AMM 的滑点对比', fontsize=14, color=CHARCOAL, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(trade_labels)
    ax.legend(loc='upper left', fontsize=10)
    ax.set_yscale('log')
    ax.set_ylim(0.001, 30)
    
    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height >= 1:
                ax.annotate(f'{height:.1f}%',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontsize=8, color=CHARCOAL)
    
    plt.tight_layout()
    plt.savefig('/Users/feng/Documents/person/cyber-zen/src/content/blog/curve_slippage_comparison.svg',
                format='svg', transparent=True, dpi=150)
    plt.close()
    print("Generated: curve_slippage_comparison.svg")

def generate_pmm_curve():
    """Generate DODO PMM curve comparison."""
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Market price from oracle
    market_price = 2000  # USDC per ETH
    
    # Traditional AMM: x * y = k
    k = 100 * 200000  # 100 ETH * 200000 USDC
    x_amm = np.linspace(20, 200, 500)
    y_amm = k / x_amm
    
    # PMM: liquidity concentrated around market price
    # Simplified model: steeper curve away from market price
    x_pmm = np.linspace(20, 200, 500)
    
    def pmm_price(x, base_x=100, base_y=200000, k_factor=0.5):
        """PMM concentrates liquidity around oracle price."""
        deviation = (x - base_x) / base_x
        # More aggressive price change when deviating from equilibrium
        return base_y * (1 - deviation * (1 + k_factor * abs(deviation)))
    
    y_pmm = [max(pmm_price(x), 50000) for x in x_pmm]
    
    ax.plot(x_amm, y_amm, color=GRAY, linewidth=2, linestyle='--', label='传统 AMM (x×y=k)')
    ax.plot(x_pmm, y_pmm, color=JADE, linewidth=2.5, label='DODO PMM')
    
    # Mark equilibrium
    ax.scatter([100], [200000], color=JADE, s=120, zorder=5, edgecolors='white', linewidths=2)
    ax.annotate('预言机价格\n$2000/ETH', xy=(100, 200000), xytext=(130, 220000),
                fontsize=10, color=CHARCOAL,
                arrowprops=dict(arrowstyle='->', color=GRAY))
    
    # Highlight concentrated region
    ax.axvspan(80, 120, alpha=0.1, color=JADE)
    ax.text(100, 100000, '流动性集中区', ha='center', fontsize=10, color=JADE)
    
    ax.set_xlabel('ETH 储备', fontsize=12, color=CHARCOAL)
    ax.set_ylabel('USDC 储备', fontsize=12, color=CHARCOAL)
    ax.set_title('DODO PMM vs 传统 AMM', fontsize=14, color=CHARCOAL, fontweight='bold')
    ax.set_xlim(0, 220)
    ax.set_ylim(0, 300000)
    ax.legend(loc='upper right', fontsize=11)
    
    # Add explanation
    ax.text(150, 50000, 'PMM 在市场价附近\n提供更深流动性', fontsize=10, color=JADE,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('/Users/feng/Documents/person/cyber-zen/src/content/blog/curve_pmm.svg',
                format='svg', transparent=True, dpi=150)
    plt.close()
    print("Generated: curve_pmm.svg")

if __name__ == '__main__':
    print("Generating DEX curve visualizations...")
    generate_constant_product_curve()
    generate_stableswap_comparison()
    generate_concentrated_liquidity()
    generate_slippage_comparison()
    generate_pmm_curve()
    print("\nAll curves generated successfully!")
