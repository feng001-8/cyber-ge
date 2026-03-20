#!/usr/bin/env python3
"""Generate precise mathematical curve SVGs for DEX article."""

import math

# Cyber-Zen color palette
JADE = '#4A8B71'
CINNABAR = '#D13429'
CHARCOAL = '#474747'
GRAY = '#8C928F'
LIGHT_GRAY = '#E5E7EB'

def create_svg(width, height, content):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="{GRAY}"/>
    </marker>
  </defs>
  <style>
    text {{ font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif; }}
    .title {{ font-size: 20px; font-weight: 600; fill: {CHARCOAL}; }}
    .subtitle {{ font-size: 13px; fill: {GRAY}; }}
    .label {{ font-size: 13px; fill: {CHARCOAL}; }}
    .axis-label {{ font-size: 12px; fill: {GRAY}; }}
    .small {{ font-size: 11px; fill: {GRAY}; }}
    .formula {{ font-size: 14px; font-family: 'SF Mono', Monaco, monospace; }}
  </style>
  <rect width="100%" height="100%" fill="white"/>
{content}</svg>
'''

def draw_axes(ox, oy, width, height, x_label, y_label):
    """Draw coordinate axes with labels."""
    return f'''  <!-- Axes -->
  <line x1="{ox}" y1="{oy}" x2="{ox + width}" y2="{oy}" stroke="{GRAY}" stroke-width="1.5" marker-end="url(#arrowhead)"/>
  <line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy - height}" stroke="{GRAY}" stroke-width="1.5" marker-end="url(#arrowhead)"/>
  <text x="{ox + width + 5}" y="{oy + 5}" class="axis-label">{x_label}</text>
  <text x="{ox - 5}" y="{oy - height - 10}" class="axis-label" text-anchor="end">{y_label}</text>
'''

def curve_path(points, color, width=2.5, dashed=False):
    """Generate SVG path from points."""
    if not points:
        return ""
    path_data = f"M {points[0][0]:.1f},{points[0][1]:.1f}"
    for x, y in points[1:]:
        path_data += f" L {x:.1f},{y:.1f}"
    dash = ' stroke-dasharray="8,4"' if dashed else ''
    return f'  <path d="{path_data}" fill="none" stroke="{color}" stroke-width="{width}"{dash}/>\n'


def generate_constant_product():
    """恒定乘积曲线 x × y = k"""
    w, h = 600, 500
    ox, oy = 80, 420  # origin
    ax_w, ax_h = 450, 350
    
    content = f'''  <text x="{w/2}" y="35" text-anchor="middle" class="title">恒定乘积曲线</text>
  <text x="{w/2}" y="58" text-anchor="middle" class="subtitle">Uniswap V2: x × y = k</text>
'''
    content += draw_axes(ox, oy, ax_w, ax_h, "ETH 储备", "USDC 储备")
    
    # k = 10000, scale to fit
    k = 10000
    scale_x = ax_w / 220
    scale_y = ax_h / 220
    
    # Generate curve points
    points = []
    for x in range(12, 200):
        y = k / x
        px = ox + x * scale_x
        py = oy - y * scale_y
        if oy - ax_h < py < oy:
            points.append((px, py))
    
    content += curve_path(points, JADE, 3)
    
    # Current state point (100, 100)
    cx = ox + 100 * scale_x
    cy = oy - 100 * scale_y
    content += f'''  <circle cx="{cx}" cy="{cy}" r="8" fill="{JADE}" stroke="white" stroke-width="2"/>
  <text x="{cx + 15}" y="{cy - 15}" class="label">当前状态</text>
  <text x="{cx + 15}" y="{cy + 5}" class="small">(100 ETH, 100 USDC)</text>
'''
    
    # Trade: add 20 USDC, get ETH
    # New: y=120, x=10000/120=83.33
    tx = ox + 83.33 * scale_x
    ty = oy - 120 * scale_y
    content += f'''  <circle cx="{tx}" cy="{ty}" r="8" fill="{CINNABAR}" stroke="white" stroke-width="2"/>
  <text x="{tx - 100}" y="{ty - 5}" class="label" fill="{CINNABAR}">交易后</text>
  <text x="{tx - 100}" y="{ty + 15}" class="small">(83.3 ETH, 120 USDC)</text>
'''
    
    # Arrow showing trade direction
    content += f'''  <line x1="{cx - 5}" y1="{cy - 5}" x2="{tx + 10}" y2="{ty + 10}" stroke="{CINNABAR}" stroke-width="2" stroke-dasharray="4,3"/>
'''
    
    # Formula box
    content += f'''  <!-- Formula -->
  <rect x="400" y="80" width="170" height="120" rx="8" fill="{LIGHT_GRAY}" opacity="0.5"/>
  <text x="485" y="110" text-anchor="middle" class="label">核心公式</text>
  <text x="485" y="140" text-anchor="middle" class="formula" fill="{JADE}">x × y = k</text>
  <text x="485" y="170" text-anchor="middle" class="small">k = 10,000 (恒定)</text>
  <text x="485" y="190" text-anchor="middle" class="small">价格 = y / x</text>
'''
    
    return create_svg(w, h, content)


def generate_stableswap():
    """StableSwap 曲线对比"""
    w, h = 650, 520
    ox, oy = 80, 440
    ax_w, ax_h = 380, 360
    
    content = f'''  <text x="{w/2}" y="35" text-anchor="middle" class="title">StableSwap 曲线对比</text>
  <text x="{w/2}" y="58" text-anchor="middle" class="subtitle">Curve Finance: 稳定币专用 AMM</text>
'''
    content += draw_axes(ox, oy, ax_w, ax_h, "USDC", "USDT")
    
    D = 200  # total at equilibrium
    k = (D/2) ** 2
    scale = ax_w / 220
    
    # 1. Constant sum: x + y = D (dashed gray line)
    content += f'  <line x1="{ox}" y1="{oy - D*scale}" x2="{ox + D*scale}" y2="{oy}" stroke="{GRAY}" stroke-width="2" stroke-dasharray="8,4"/>\n'
    
    # 2. Constant product: x * y = k
    points_cp = []
    for x in range(12, 188):
        y = k / x
        px = ox + x * scale
        py = oy - y * scale
        if oy - ax_h < py < oy:
            points_cp.append((px, py))
    content += curve_path(points_cp, CINNABAR, 2)
    
    # 3. StableSwap curve (blend)
    points_ss = []
    for x in range(8, 192):
        y_sum = D - x
        y_prod = k / x if x > 5 else k / 5
        # Blend: flatter near equilibrium
        dist = abs(x - D/2) / (D/2)
        weight = 0.05 + 0.95 * (dist ** 1.5)  # More aggressive blend
        y = (1 - weight) * y_sum + weight * y_prod
        y = max(5, min(195, y))
        px = ox + x * scale
        py = oy - y * scale
        if oy - ax_h < py < oy:
            points_ss.append((px, py))
    content += curve_path(points_ss, JADE, 3)
    
    # Equilibrium point
    eq_x = ox + 100 * scale
    eq_y = oy - 100 * scale
    content += f'  <circle cx="{eq_x}" cy="{eq_y}" r="8" fill="{JADE}" stroke="white" stroke-width="2"/>\n'
    
    # Low slippage zone highlight
    zone_x = ox + 70 * scale
    zone_w = 60 * scale
    content += f'  <rect x="{zone_x}" y="{oy - ax_h}" width="{zone_w}" height="{ax_h - 20}" fill="{JADE}" opacity="0.08"/>\n'
    content += f'  <text x="{eq_x}" y="{oy - ax_h + 20}" text-anchor="middle" class="small" fill="{JADE}">低滑点区</text>\n'
    
    # Legend
    content += f'''  <!-- Legend -->
  <rect x="480" y="90" width="150" height="160" rx="8" fill="{LIGHT_GRAY}" opacity="0.4"/>
  <line x1="495" y1="120" x2="535" y2="120" stroke="{GRAY}" stroke-width="2" stroke-dasharray="8,4"/>
  <text x="545" y="125" class="small">x + y = k</text>
  <line x1="495" y1="150" x2="535" y2="150" stroke="{CINNABAR}" stroke-width="2"/>
  <text x="545" y="155" class="small" fill="{CINNABAR}">x × y = k</text>
  <line x1="495" y1="180" x2="535" y2="180" stroke="{JADE}" stroke-width="3"/>
  <text x="545" y="185" class="small" fill="{JADE}">StableSwap</text>
  
  <text x="485" y="220" class="small">1:1 附近: 接近恒定和</text>
  <text x="485" y="240" class="small">→ 滑点极低</text>
'''
    
    # Slippage comparison
    content += f'''  <!-- Slippage comparison -->
  <rect x="480" y="280" width="150" height="100" rx="8" fill="white" stroke="{JADE}" stroke-width="1"/>
  <text x="555" y="305" text-anchor="middle" class="label">$1M 交易滑点</text>
  <text x="495" y="335" class="small" fill="{CINNABAR}">Uniswap: ~0.3%</text>
  <text x="495" y="360" class="small" fill="{JADE}">Curve: ~0.01%</text>
'''
    
    return create_svg(w, h, content)


def generate_concentrated_liquidity():
    """集中流动性对比图"""
    w, h = 750, 420
    
    content = f'''  <text x="{w/2}" y="35" text-anchor="middle" class="title">集中流动性 vs 全范围流动性</text>
  <text x="{w/2}" y="58" text-anchor="middle" class="subtitle">Uniswap V2 → V3 资本效率革命</text>
'''
    
    # V2 section (left)
    v2_x, v2_y = 50, 120
    v2_w, v2_h = 280, 180
    
    content += f'''  <!-- V2 -->
  <text x="{v2_x + v2_w/2}" y="{v2_y - 20}" text-anchor="middle" class="label" fill="{GRAY}">Uniswap V2</text>
  <rect x="{v2_x}" y="{v2_y}" width="{v2_w}" height="{v2_h}" rx="4" fill="none" stroke="{GRAY}" stroke-dasharray="4,2"/>
  <rect x="{v2_x + 10}" y="{v2_y + 60}" width="{v2_w - 20}" height="60" rx="4" fill="{GRAY}" opacity="0.15"/>
  <line x1="{v2_x + v2_w/2}" y1="{v2_y + 10}" x2="{v2_x + v2_w/2}" y2="{v2_y + v2_h - 10}" stroke="{JADE}" stroke-width="2" stroke-dasharray="5,3"/>
  <text x="{v2_x + v2_w/2}" y="{v2_y + v2_h + 20}" text-anchor="middle" class="small" fill="{JADE}">当前价格</text>
  <text x="{v2_x + 5}" y="{v2_y + v2_h + 20}" class="small">$0</text>
  <text x="{v2_x + v2_w - 10}" y="{v2_y + v2_h + 20}" class="small">$∞</text>
  <text x="{v2_x + v2_w/2}" y="{v2_y + v2_h + 55}" text-anchor="middle" class="label" fill="{CINNABAR}">资本效率 ~1x</text>
  <text x="{v2_x + v2_w/2}" y="{v2_y + v2_h + 75}" text-anchor="middle" class="small">大部分流动性未使用</text>
'''
    
    # Arrow between
    content += f'''  <text x="375" y="210" text-anchor="middle" class="title" fill="{JADE}">→</text>
'''
    
    # V3 section (right)
    v3_x, v3_y = 420, 120
    v3_w, v3_h = 280, 180
    
    content += f'''  <!-- V3 -->
  <text x="{v3_x + v3_w/2}" y="{v3_y - 20}" text-anchor="middle" class="label" fill="{JADE}">Uniswap V3</text>
  <rect x="{v3_x}" y="{v3_y}" width="{v3_w}" height="{v3_h}" rx="4" fill="none" stroke="{GRAY}" stroke-dasharray="4,2"/>
  <rect x="{v3_x + 100}" y="{v3_y + 20}" width="80" height="{v3_h - 40}" rx="4" fill="{JADE}" opacity="0.25" stroke="{JADE}" stroke-width="2"/>
  <line x1="{v3_x + v3_w/2}" y1="{v3_y + 10}" x2="{v3_x + v3_w/2}" y2="{v3_y + v3_h - 10}" stroke="{JADE}" stroke-width="2" stroke-dasharray="5,3"/>
  <text x="{v3_x + v3_w/2}" y="{v3_y + v3_h + 20}" text-anchor="middle" class="small" fill="{JADE}">当前价格</text>
  <text x="{v3_x + 5}" y="{v3_y + v3_h + 20}" class="small">$0</text>
  <text x="{v3_x + v3_w - 10}" y="{v3_y + v3_h + 20}" class="small">$∞</text>
  <text x="{v3_x + 100}" y="{v3_y + v3_h + 20}" class="small" fill="{JADE}">$1800</text>
  <text x="{v3_x + 180}" y="{v3_y + v3_h + 20}" class="small" fill="{JADE}">$2200</text>
  <text x="{v3_x + v3_w/2}" y="{v3_y + v3_h + 55}" text-anchor="middle" class="label" fill="{JADE}">资本效率 最高4000x</text>
  <text x="{v3_x + v3_w/2}" y="{v3_y + v3_h + 75}" text-anchor="middle" class="small">同等资金，流动性深度提升40倍</text>
'''
    
    # Bottom comparison
    content += f'''  <!-- Comparison -->
  <rect x="220" y="360" width="310" height="45" rx="8" fill="{LIGHT_GRAY}" opacity="0.5"/>
  <text x="375" y="382" text-anchor="middle" class="label">$1800-$2200 区间提供流动性</text>
  <text x="375" y="400" text-anchor="middle" class="small">V2 需要 $100,000 → V3 只需 $2,500</text>
'''
    
    return create_svg(w, h, content)


def generate_pmm():
    """DODO PMM 曲线"""
    w, h = 600, 480
    ox, oy = 80, 400
    ax_w, ax_h = 350, 320
    
    content = f'''  <text x="{w/2}" y="35" text-anchor="middle" class="title">DODO PMM 主动做市</text>
  <text x="{w/2}" y="58" text-anchor="middle" class="subtitle">预言机辅助定价 vs 传统 AMM</text>
'''
    content += draw_axes(ox, oy, ax_w, ax_h, "ETH 储备", "USDC 储备")
    
    # Traditional AMM curve
    k = 10000
    scale_x = ax_w / 200
    scale_y = ax_h / 200
    
    points_amm = []
    for x in range(15, 180):
        y = k / x
        px = ox + x * scale_x
        py = oy - y * scale_y
        if oy - ax_h < py < oy:
            points_amm.append((px, py))
    content += curve_path(points_amm, GRAY, 2, dashed=True)
    
    # PMM curve (steeper, concentrated around market price)
    points_pmm = []
    base_x, base_y = 100, 100
    for x in range(20, 180):
        # PMM concentrates liquidity around oracle price
        deviation = (x - base_x) / base_x
        # More aggressive price change when deviating
        y = base_y * (1 - deviation * (1 + 0.8 * abs(deviation)))
        y = max(20, min(180, y))
        px = ox + x * scale_x
        py = oy - y * scale_y
        if oy - ax_h < py < oy:
            points_pmm.append((px, py))
    content += curve_path(points_pmm, JADE, 3)
    
    # Oracle price point
    oracle_x = ox + 100 * scale_x
    oracle_y = oy - 100 * scale_y
    content += f'''  <circle cx="{oracle_x}" cy="{oracle_y}" r="8" fill="{JADE}" stroke="white" stroke-width="2"/>
  <text x="{oracle_x + 15}" y="{oracle_y - 10}" class="label">预言机价格</text>
'''
    
    # Concentrated zone
    zone_x = ox + 70 * scale_x
    zone_w = 60 * scale_x
    content += f'  <rect x="{zone_x}" y="{oy - ax_h + 20}" width="{zone_w}" height="{ax_h - 40}" fill="{JADE}" opacity="0.08"/>\n'
    
    # Legend
    content += f'''  <!-- Legend -->
  <rect x="450" y="100" width="130" height="100" rx="8" fill="{LIGHT_GRAY}" opacity="0.4"/>
  <line x1="465" y1="130" x2="505" y2="130" stroke="{GRAY}" stroke-width="2" stroke-dasharray="8,4"/>
  <text x="515" y="135" class="small">传统 AMM</text>
  <line x1="465" y1="160" x2="505" y2="160" stroke="{JADE}" stroke-width="3"/>
  <text x="515" y="165" class="small" fill="{JADE}">DODO PMM</text>
  <text x="460" y="190" class="small">流动性集中在</text>
  <text x="460" y="205" class="small">预言机价格附近</text>
'''
    
    # Comparison box
    content += f'''  <!-- Comparison -->
  <rect x="450" y="240" width="130" height="120" rx="8" fill="white" stroke="{JADE}" stroke-width="1"/>
  <text x="515" y="265" text-anchor="middle" class="label">优势</text>
  <text x="460" y="295" class="small" fill="{JADE}">• 减少套利损失</text>
  <text x="460" y="320" class="small" fill="{JADE}">• 更低滑点</text>
  <text x="460" y="345" class="small" fill="{CINNABAR}">• 依赖预言机</text>
'''
    
    return create_svg(w, h, content)


if __name__ == '__main__':
    base = '/Users/feng/Documents/person/cyber-zen/src/content/blog/'
    
    with open(base + 'curve_constant_product.svg', 'w', encoding='utf-8') as f:
        f.write(generate_constant_product())
    print("✓ curve_constant_product.svg")
    
    with open(base + 'curve_stableswap.svg', 'w', encoding='utf-8') as f:
        f.write(generate_stableswap())
    print("✓ curve_stableswap.svg")
    
    with open(base + 'curve_concentrated.svg', 'w', encoding='utf-8') as f:
        f.write(generate_concentrated_liquidity())
    print("✓ curve_concentrated.svg")
    
    with open(base + 'curve_pmm.svg', 'w', encoding='utf-8') as f:
        f.write(generate_pmm())
    print("✓ curve_pmm.svg")
    
    print("\n所有数学曲线 SVG 生成完成!")
