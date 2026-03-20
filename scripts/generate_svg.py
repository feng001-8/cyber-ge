#!/usr/bin/env python3
"""Generate SVG curves for DEX article - no external dependencies."""

import math

# Colors
JADE = '#4A8B71'
CINNABAR = '#D13429'
CHARCOAL = '#474747'
GRAY = '#8C928F'

def svg_header(width, height):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <style>
    text {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
    .title {{ font-size: 18px; font-weight: bold; fill: {CHARCOAL}; }}
    .label {{ font-size: 12px; fill: {CHARCOAL}; }}
    .small {{ font-size: 10px; fill: {GRAY}; }}
  </style>
  <rect width="100%" height="100%" fill="white"/>
'''

def svg_footer():
    return '</svg>'

def generate_constant_product():
    """x * y = k curve"""
    w, h = 500, 400
    svg = svg_header(w, h)
    
    # Title
    svg += f'  <text x="250" y="30" text-anchor="middle" class="title">恒定乘积曲线 x × y = k</text>\n'
    
    # Axes
    ox, oy = 60, 350  # origin
    ax_len = 380
    svg += f'  <line x1="{ox}" y1="{oy}" x2="{ox+ax_len}" y2="{oy}" stroke="{GRAY}" stroke-width="1.5"/>\n'
    svg += f'  <line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy-300}" stroke="{GRAY}" stroke-width="1.5"/>\n'
    svg += f'  <text x="{ox+ax_len+10}" y="{oy+5}" class="label">ETH</text>\n'
    svg += f'  <text x="{ox-10}" y="{oy-310}" class="label">USDC</text>\n'
    
    # Curve: x * y = 10000, scaled
    k = 10000
    scale_x, scale_y = 1.8, 1.4
    points = []
    for x in range(15, 200):
        y = k / x
        px = ox + x * scale_x
        py = oy - y * scale_y
        if 50 < py < 340:
            points.append(f"{px:.1f},{py:.1f}")
    
    path = "M " + " L ".join(points)
    svg += f'  <path d="{path}" fill="none" stroke="{JADE}" stroke-width="2.5"/>\n'
    
    # Current state point (100, 100)
    cx, cy = ox + 100*scale_x, oy - 100*scale_y
    svg += f'  <circle cx="{cx}" cy="{cy}" r="6" fill="{JADE}"/>\n'
    svg += f'  <text x="{cx+15}" y="{cy-10}" class="label">当前 (100, 100)</text>\n'
    
    # Trade point (83.3, 120)
    tx, ty = ox + 83.3*scale_x, oy - 120*scale_y
    svg += f'  <circle cx="{tx}" cy="{ty}" r="6" fill="{CINNABAR}"/>\n'
    svg += f'  <text x="{tx-80}" y="{ty}" class="label">交易后 (83, 120)</text>\n'
    
    # Arrow
    svg += f'  <line x1="{cx}" y1="{cy}" x2="{tx+8}" y2="{ty+8}" stroke="{CINNABAR}" stroke-width="2" marker-end="url(#arrow)"/>\n'
    svg += f'  <defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="{CINNABAR}"/></marker></defs>\n'
    
    # Formula
    svg += f'  <text x="350" y="100" class="label" fill="{JADE}">k = 10,000</text>\n'
    svg += f'  <text x="350" y="120" class="small">价格 = y/x</text>\n'
    
    svg += svg_footer()
    return svg

def generate_stableswap():
    """Compare constant product, constant sum, StableSwap"""
    w, h = 550, 450
    svg = svg_header(w, h)
    
    svg += f'  <text x="275" y="30" text-anchor="middle" class="title">AMM 曲线对比：稳定币场景</text>\n'
    
    ox, oy = 70, 380
    ax_len = 350
    svg += f'  <line x1="{ox}" y1="{oy}" x2="{ox+ax_len}" y2="{oy}" stroke="{GRAY}" stroke-width="1.5"/>\n'
    svg += f'  <line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy-320}" stroke="{GRAY}" stroke-width="1.5"/>\n'
    svg += f'  <text x="{ox+ax_len+10}" y="{oy+5}" class="label">USDC</text>\n'
    svg += f'  <text x="{ox-10}" y="{oy-330}" class="label">USDT</text>\n'
    
    D = 200
    scale = 1.5
    
    # Constant sum: x + y = D (dashed gray)
    svg += f'  <line x1="{ox}" y1="{oy-D*scale}" x2="{ox+D*scale}" y2="{oy}" stroke="{GRAY}" stroke-width="2" stroke-dasharray="8,4"/>\n'
    svg += f'  <text x="420" y="100" class="small">x + y = k (恒定和)</text>\n'
    
    # Constant product: x * y = (D/2)^2
    k = (D/2)**2
    points_cp = []
    for x in range(15, 185):
        y = k / x
        px = ox + x * scale
        py = oy - y * scale
        if 60 < py < 370:
            points_cp.append(f"{px:.1f},{py:.1f}")
    path_cp = "M " + " L ".join(points_cp)
    svg += f'  <path d="{path_cp}" fill="none" stroke="{CINNABAR}" stroke-width="2"/>\n'
    svg += f'  <text x="420" y="130" class="small" fill="{CINNABAR}">x × y = k (恒定乘积)</text>\n'
    
    # StableSwap (blend - flatter near equilibrium)
    points_ss = []
    for x in range(10, 190):
        y_sum = D - x
        y_prod = k / x if x > 0 else D
        dist = abs(x - D/2) / (D/2)
        weight = 0.1 + 0.9 * (dist ** 2)
        y = (1 - weight) * y_sum + weight * y_prod
        px = ox + x * scale
        py = oy - y * scale
        if 60 < py < 370:
            points_ss.append(f"{px:.1f},{py:.1f}")
    path_ss = "M " + " L ".join(points_ss)
    svg += f'  <path d="{path_ss}" fill="none" stroke="{JADE}" stroke-width="2.5"/>\n'
    svg += f'  <text x="420" y="160" class="label" fill="{JADE}">StableSwap (Curve)</text>\n'
    
    # Equilibrium point
    eq_x, eq_y = ox + 100*scale, oy - 100*scale
    svg += f'  <circle cx="{eq_x}" cy="{eq_y}" r="7" fill="{JADE}" stroke="white" stroke-width="2"/>\n'
    svg += f'  <text x="{eq_x+15}" y="{eq_y-5}" class="label">1:1 均衡</text>\n'
    
    # Low slippage zone
    svg += f'  <rect x="{ox+70*scale}" y="{oy-320}" width="{60*scale}" height="260" fill="{JADE}" opacity="0.1"/>\n'
    svg += f'  <text x="{ox+100*scale}" y="{oy-330}" text-anchor="middle" class="small" fill="{JADE}">低滑点区</text>\n'
    
    svg += svg_footer()
    return svg

def generate_concentrated_liquidity():
    """V2 vs V3 liquidity distribution"""
    w, h = 700, 350
    svg = svg_header(w, h)
    
    svg += f'  <text x="350" y="30" text-anchor="middle" class="title">集中流动性 vs 全范围流动性</text>\n'
    
    # V2 (left)
    svg += f'  <text x="175" y="60" text-anchor="middle" class="label">Uniswap V2</text>\n'
    svg += f'  <rect x="50" y="100" width="250" height="150" fill="{GRAY}" opacity="0.2"/>\n'
    svg += f'  <line x1="50" y1="250" x2="300" y2="250" stroke="{GRAY}" stroke-width="1.5"/>\n'
    svg += f'  <line x1="175" y1="100" x2="175" y2="260" stroke="{JADE}" stroke-width="2" stroke-dasharray="5,3"/>\n'
    svg += f'  <text x="175" y="275" text-anchor="middle" class="small">当前价格</text>\n'
    svg += f'  <text x="50" y="290" class="small">$0</text>\n'
    svg += f'  <text x="290" y="290" class="small">$∞</text>\n'
    svg += f'  <text x="175" y="320" text-anchor="middle" class="small" fill="{CINNABAR}">资本效率 ~1x</text>\n'
    
    # V3 (right)
    svg += f'  <text x="525" y="60" text-anchor="middle" class="label" fill="{JADE}">Uniswap V3</text>\n'
    svg += f'  <rect x="400" y="100" width="250" height="150" fill="none" stroke="{GRAY}" stroke-dasharray="5,3"/>\n'
    svg += f'  <rect x="475" y="100" width="100" height="150" fill="{JADE}" opacity="0.3"/>\n'
    svg += f'  <line x1="400" y1="250" x2="650" y2="250" stroke="{GRAY}" stroke-width="1.5"/>\n'
    svg += f'  <line x1="525" y1="100" x2="525" y2="260" stroke="{JADE}" stroke-width="2" stroke-dasharray="5,3"/>\n'
    svg += f'  <text x="525" y="275" text-anchor="middle" class="small">当前价格</text>\n'
    svg += f'  <text x="400" y="290" class="small">$0</text>\n'
    svg += f'  <text x="640" y="290" class="small">$∞</text>\n'
    svg += f'  <text x="475" y="290" class="small" fill="{JADE}">$1800</text>\n'
    svg += f'  <text x="565" y="290" class="small" fill="{JADE}">$2200</text>\n'
    svg += f'  <text x="525" y="320" text-anchor="middle" class="small" fill="{JADE}">资本效率 最高4000x</text>\n'
    
    svg += svg_footer()
    return svg

# Generate and save
if __name__ == '__main__':
    base = '/Users/feng/Documents/person/cyber-zen/src/content/blog/'
    
    with open(base + 'svg_constant_product.svg', 'w') as f:
        f.write(generate_constant_product())
    print("Generated: svg_constant_product.svg")
    
    with open(base + 'svg_stableswap.svg', 'w') as f:
        f.write(generate_stableswap())
    print("Generated: svg_stableswap.svg")
    
    with open(base + 'svg_concentrated.svg', 'w') as f:
        f.write(generate_concentrated_liquidity())
    print("Generated: svg_concentrated.svg")
    
    print("\nDone!")
