#!/usr/bin/env python3
"""
Generate SVG diagrams for Curve CryptoSwap (v2) article.
Cyber-Zen style: minimalist, professional, no hand-drawn feel.
"""

import math
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "public/images/blog/curve-cryptoswap-formula"

SVG_STYLE = """
    <style>
        text { font-family: 'Inter', -apple-system, sans-serif; fill: #474747; }
        .mono { font-family: 'JetBrains Mono', 'SF Mono', monospace; }
        .label { font-size: 14px; }
        .title { font-size: 16px; font-weight: 600; }
        .small { font-size: 12px; }
        .subtitle { font-size: 13px; fill: #8C928F; }
    </style>
"""

ARROW_MARKER = """
    <defs>
        <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
            <path d="M0,0 L0,6 L9,3 z" fill="#474747"/>
        </marker>
        <marker id="arrow-jade" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
            <path d="M0,0 L0,6 L9,3 z" fill="#4A8B71"/>
        </marker>
        <marker id="arrow-gray" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
            <path d="M0,0 L0,6 L9,3 z" fill="#8C928F"/>
        </marker>
    </defs>
"""


def generate_k_comparison():
    """
    Generate SVG showing K adjustment factor comparison between v1 and v2.
    Shows how gamma makes the curve steeper when away from equilibrium.
    """
    width, height = 550, 400
    margin = 60
    plot_width = width - 2 * margin
    plot_height = height - 2 * margin - 40
    
    def scale_x(k0):
        return margin + k0 * plot_width
    
    def scale_y(val, max_val=1.0):
        return margin + 40 + plot_height * (1 - val / max_val)
    
    paths = []
    
    A = 100
    gamma = 0.01
    
    v1_points = []
    v2_points = []
    
    for i in range(101):
        k0 = i / 100.0
        if k0 < 0.01:
            k0 = 0.01
        
        chi_v1 = A * k0
        
        adjustment = (gamma ** 2) / ((gamma + 1 - k0) ** 2)
        k_v2 = A * k0 * adjustment
        
        v1_points.append((scale_x(k0), scale_y(chi_v1 / A)))
        v2_points.append((scale_x(k0), scale_y(k_v2 / A)))
    
    v1_path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in v1_points)
    v2_path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in v2_points)
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">
{SVG_STYLE}
{ARROW_MARKER}
    
    <!-- Title -->
    <text x="{width/2}" y="25" class="title" text-anchor="middle">K 调整因子对比：v1 vs v2</text>
    <text x="{width/2}" y="45" class="subtitle" text-anchor="middle">γ 参数让曲线在偏离平衡点时下降更快</text>
    
    <!-- Axes -->
    <line x1="{margin}" y1="{margin + 40 + plot_height}" x2="{width - margin + 10}" y2="{margin + 40 + plot_height}" stroke="#474747" stroke-width="1.5" marker-end="url(#arrow)"/>
    <line x1="{margin}" y1="{margin + 40 + plot_height}" x2="{margin}" y2="{margin + 30}" stroke="#474747" stroke-width="1.5" marker-end="url(#arrow)"/>
    
    <!-- Axis labels -->
    <text x="{width - margin + 20}" y="{margin + 40 + plot_height + 5}" class="label mono">K₀</text>
    <text x="{margin - 10}" y="{margin + 25}" class="label mono">K/A</text>
    
    <!-- Grid lines -->
    <line x1="{scale_x(0.5)}" y1="{margin + 40}" x2="{scale_x(0.5)}" y2="{margin + 40 + plot_height}" stroke="#E5E7EB" stroke-width="1" stroke-dasharray="4,4"/>
    <line x1="{margin}" y1="{scale_y(0.5)}" x2="{width - margin}" y2="{scale_y(0.5)}" stroke="#E5E7EB" stroke-width="1" stroke-dasharray="4,4"/>
    
    <!-- Tick marks -->
    <text x="{scale_x(0)}" y="{margin + 40 + plot_height + 20}" class="small mono" text-anchor="middle">0</text>
    <text x="{scale_x(0.5)}" y="{margin + 40 + plot_height + 20}" class="small mono" text-anchor="middle">0.5</text>
    <text x="{scale_x(1)}" y="{margin + 40 + plot_height + 20}" class="small mono" text-anchor="middle">1</text>
    <text x="{margin - 15}" y="{scale_y(0) + 5}" class="small mono" text-anchor="end">0</text>
    <text x="{margin - 15}" y="{scale_y(0.5) + 5}" class="small mono" text-anchor="end">0.5</text>
    <text x="{margin - 15}" y="{scale_y(1) + 5}" class="small mono" text-anchor="end">1</text>
    
    <!-- v1 curve (blue) -->
    <path d="{v1_path}" stroke="#3B82F6" stroke-width="2.5" fill="none"/>
    
    <!-- v2 curve (jade) -->
    <path d="{v2_path}" stroke="#4A8B71" stroke-width="2.5" fill="none"/>
    
    <!-- Equilibrium point -->
    <circle cx="{scale_x(1)}" cy="{scale_y(1)}" r="5" fill="#D13429"/>
    <text x="{scale_x(1) + 10}" y="{scale_y(1) - 10}" class="small" fill="#D13429">平衡点</text>
    
    <!-- Annotation for difference -->
    <line x1="{scale_x(0.36)}" y1="{scale_y(0.36)}" x2="{scale_x(0.36)}" y2="{scale_y(0.36 * (gamma**2)/((gamma+1-0.36)**2))}" stroke="#8C928F" stroke-width="1" stroke-dasharray="2,2"/>
    <text x="{scale_x(0.36) + 5}" y="{(scale_y(0.36) + scale_y(0.36 * (gamma**2)/((gamma+1-0.36)**2))) / 2}" class="small" fill="#8C928F">差距</text>
    
    <!-- Legend -->
    <line x1="380" y1="80" x2="420" y2="80" stroke="#3B82F6" stroke-width="2.5"/>
    <text x="430" y="85" class="small mono">v1: χ = A·K₀</text>
    
    <line x1="380" y1="105" x2="420" y2="105" stroke="#4A8B71" stroke-width="2.5"/>
    <text x="430" y="110" class="small mono">v2: K = A·K₀·γ²/(γ+1-K₀)²</text>
    
</svg>'''
    
    return svg


def generate_value_conversion():
    """
    Generate SVG showing the concept of value conversion from quantity to value.
    """
    width, height = 600, 350
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">
{SVG_STYLE}
{ARROW_MARKER}
    
    <!-- Title -->
    <text x="{width/2}" y="30" class="title" text-anchor="middle">价值转换：从数量到价值</text>
    
    <!-- Left side: Quantity -->
    <rect x="40" y="70" width="200" height="200" rx="8" fill="none" stroke="#8C928F" stroke-width="1" stroke-dasharray="4,4"/>
    <text x="140" y="95" class="label" text-anchor="middle" fill="#8C928F">数量 (balance)</text>
    
    <rect x="60" y="115" width="160" height="40" rx="4" fill="none" stroke="#474747" stroke-width="1"/>
    <text x="140" y="140" class="mono small" text-anchor="middle">100,000 USDT</text>
    
    <rect x="60" y="165" width="160" height="40" rx="4" fill="none" stroke="#474747" stroke-width="1"/>
    <text x="140" y="190" class="mono small" text-anchor="middle">2 WBTC</text>
    
    <rect x="60" y="215" width="160" height="40" rx="4" fill="none" stroke="#474747" stroke-width="1"/>
    <text x="140" y="240" class="mono small" text-anchor="middle">30 WETH</text>
    
    <!-- Arrow -->
    <line x1="260" y1="170" x2="340" y2="170" stroke="#4A8B71" stroke-width="2" marker-end="url(#arrow-jade)"/>
    <text x="300" y="155" class="small mono" text-anchor="middle" fill="#4A8B71">× pᵢ</text>
    
    <!-- Right side: Value -->
    <rect x="360" y="70" width="200" height="200" rx="8" fill="none" stroke="#8C928F" stroke-width="1" stroke-dasharray="4,4"/>
    <text x="460" y="95" class="label" text-anchor="middle" fill="#8C928F">价值 (value)</text>
    
    <rect x="380" y="115" width="160" height="40" rx="4" fill="none" stroke="#474747" stroke-width="1"/>
    <text x="460" y="140" class="mono small" text-anchor="middle">100,000 USDT</text>
    
    <rect x="380" y="165" width="160" height="40" rx="4" fill="none" stroke="#474747" stroke-width="1"/>
    <text x="460" y="190" class="mono small" text-anchor="middle">80,000 USDT</text>
    
    <rect x="380" y="215" width="160" height="40" rx="4" fill="none" stroke="#474747" stroke-width="1"/>
    <text x="460" y="240" class="mono small" text-anchor="middle">90,000 USDT</text>
    
    <!-- Price annotations -->
    <text x="300" y="135" class="small" text-anchor="middle" fill="#8C928F">p₀ = 1</text>
    <text x="300" y="185" class="small" text-anchor="middle" fill="#8C928F">p₁ = 40,000</text>
    <text x="300" y="235" class="small" text-anchor="middle" fill="#8C928F">p₂ = 3,000</text>
    
    <!-- Total -->
    <line x1="380" y1="275" x2="540" y2="275" stroke="#474747" stroke-width="1"/>
    <text x="460" y="300" class="label mono" text-anchor="middle">总价值 = 270,000 USDT</text>
    
    <!-- Formula -->
    <text x="{width/2}" y="335" class="mono small" text-anchor="middle" fill="#8C928F">b'ᵢ = bᵢ × pᵢ</text>
    
</svg>'''
    
    return svg


def generate_repegging_flow():
    """
    Generate SVG showing the repegging mechanism flow.
    """
    width, height = 650, 400
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">
{SVG_STYLE}
{ARROW_MARKER}
    
    <!-- Title -->
    <text x="{width/2}" y="30" class="title" text-anchor="middle">Repegging 机制：价格自动追踪</text>
    <text x="{width/2}" y="50" class="subtitle" text-anchor="middle">三种价格的内部循环调整</text>
    
    <!-- Trade box -->
    <rect x="50" y="100" width="120" height="60" rx="6" fill="none" stroke="#474747" stroke-width="1.5"/>
    <text x="110" y="135" class="label" text-anchor="middle">交易</text>
    
    <!-- last_price box -->
    <rect x="230" y="100" width="120" height="60" rx="6" fill="none" stroke="#474747" stroke-width="1.5"/>
    <text x="290" y="125" class="label" text-anchor="middle">last_price</text>
    <text x="290" y="145" class="small mono" text-anchor="middle" fill="#8C928F">即时价格</text>
    
    <!-- price_oracle box -->
    <rect x="410" y="100" width="120" height="60" rx="6" fill="none" stroke="#474747" stroke-width="1.5"/>
    <text x="470" y="125" class="label" text-anchor="middle">price_oracle</text>
    <text x="470" y="145" class="small mono" text-anchor="middle" fill="#8C928F">EMA 平滑</text>
    
    <!-- price_scale box -->
    <rect x="410" y="240" width="120" height="60" rx="6" fill="none" stroke="#4A8B71" stroke-width="2"/>
    <text x="470" y="265" class="label" text-anchor="middle" fill="#4A8B71">price_scale</text>
    <text x="470" y="285" class="small mono" text-anchor="middle" fill="#8C928F">内部缩放价格</text>
    
    <!-- Curve box -->
    <rect x="230" y="240" width="120" height="60" rx="6" fill="none" stroke="#474747" stroke-width="1.5"/>
    <text x="290" y="265" class="label" text-anchor="middle">AMM 曲线</text>
    <text x="290" y="285" class="small mono" text-anchor="middle" fill="#8C928F">K, D, xp</text>
    
    <!-- Arrows -->
    <line x1="170" y1="130" x2="220" y2="130" stroke="#474747" stroke-width="1.5" marker-end="url(#arrow)"/>
    <text x="195" y="120" class="small mono" text-anchor="middle">dx/dy</text>
    
    <line x1="350" y1="130" x2="400" y2="130" stroke="#474747" stroke-width="1.5" marker-end="url(#arrow)"/>
    <text x="375" y="120" class="small mono" text-anchor="middle">EMA</text>
    
    <line x1="470" y1="160" x2="470" y2="230" stroke="#4A8B71" stroke-width="1.5" marker-end="url(#arrow-jade)"/>
    <text x="490" y="195" class="small" fill="#4A8B71">调整</text>
    
    <line x1="410" y1="270" x2="360" y2="270" stroke="#474747" stroke-width="1.5" marker-end="url(#arrow)"/>
    <text x="385" y="260" class="small mono" text-anchor="middle">更新</text>
    
    <line x1="230" y1="270" x2="110" y2="270" stroke="#474747" stroke-width="1.5"/>
    <line x1="110" y1="270" x2="110" y2="170" stroke="#474747" stroke-width="1.5" marker-end="url(#arrow)"/>
    <text x="170" y="260" class="small" text-anchor="middle">影响滑点</text>
    
    <!-- Condition annotation -->
    <rect x="520" y="180" width="110" height="50" rx="4" fill="none" stroke="#D13429" stroke-width="1" stroke-dasharray="4,4"/>
    <text x="575" y="200" class="small" text-anchor="middle" fill="#D13429">触发条件:</text>
    <text x="575" y="218" class="small mono" text-anchor="middle" fill="#D13429">利润 > 50%</text>
    
    <!-- Formula at bottom -->
    <text x="{width/2}" y="360" class="mono small" text-anchor="middle" fill="#8C928F">α = 2^(-t/T₁/₂), p* = p_last(1-α) + α·p*_prev</text>
    <text x="{width/2}" y="385" class="small" text-anchor="middle" fill="#8C928F">指数移动平均（EMA）平滑价格波动</text>
    
</svg>'''
    
    return svg


def generate_dynamic_fee():
    """
    Generate SVG showing dynamic fee mechanism.
    """
    width, height = 500, 350
    margin = 60
    plot_width = width - 2 * margin
    plot_height = height - 2 * margin - 60
    
    def scale_x(ratio):
        return margin + ratio * plot_width
    
    def scale_y(fee, f_mid=0.04, f_out=0.40):
        normalized = (fee - f_mid) / (f_out - f_mid)
        return margin + 60 + plot_height * (1 - normalized)
    
    gamma_fee = 0.5
    f_mid = 0.04
    f_out = 0.40
    
    points = []
    for i in range(101):
        ratio = i / 100.0
        if ratio < 0.01:
            ratio = 0.01
        
        g = gamma_fee / (gamma_fee + 1 - ratio)
        fee = g * f_mid + (1 - g) * f_out
        points.append((scale_x(ratio), scale_y(fee)))
    
    path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in points)
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">
{SVG_STYLE}
{ARROW_MARKER}
    
    <!-- Title -->
    <text x="{width/2}" y="25" class="title" text-anchor="middle">动态手续费机制</text>
    <text x="{width/2}" y="45" class="subtitle" text-anchor="middle">偏离平衡点越远，手续费越高</text>
    
    <!-- Axes -->
    <line x1="{margin}" y1="{margin + 60 + plot_height}" x2="{width - margin + 10}" y2="{margin + 60 + plot_height}" stroke="#474747" stroke-width="1.5" marker-end="url(#arrow)"/>
    <line x1="{margin}" y1="{margin + 60 + plot_height}" x2="{margin}" y2="{margin + 50}" stroke="#474747" stroke-width="1.5" marker-end="url(#arrow)"/>
    
    <!-- Axis labels -->
    <text x="{width - margin + 15}" y="{margin + 60 + plot_height + 5}" class="small mono">∏xᵢ/(Σxᵢ/N)ᴺ</text>
    <text x="{margin - 5}" y="{margin + 45}" class="label mono">fee</text>
    
    <!-- Horizontal reference lines -->
    <line x1="{margin}" y1="{scale_y(f_mid)}" x2="{width - margin}" y2="{scale_y(f_mid)}" stroke="#E5E7EB" stroke-width="1" stroke-dasharray="4,4"/>
    <line x1="{margin}" y1="{scale_y(f_out)}" x2="{width - margin}" y2="{scale_y(f_out)}" stroke="#E5E7EB" stroke-width="1" stroke-dasharray="4,4"/>
    
    <!-- Fee labels -->
    <text x="{margin - 10}" y="{scale_y(f_mid) + 5}" class="small mono" text-anchor="end" fill="#4A8B71">0.04%</text>
    <text x="{margin - 10}" y="{scale_y(f_out) + 5}" class="small mono" text-anchor="end" fill="#D13429">0.40%</text>
    
    <!-- X axis labels -->
    <text x="{scale_x(0)}" y="{margin + 60 + plot_height + 20}" class="small mono" text-anchor="middle">0</text>
    <text x="{scale_x(0.5)}" y="{margin + 60 + plot_height + 20}" class="small mono" text-anchor="middle">0.5</text>
    <text x="{scale_x(1)}" y="{margin + 60 + plot_height + 20}" class="small mono" text-anchor="middle">1</text>
    
    <!-- Fee curve -->
    <path d="{path}" stroke="#4A8B71" stroke-width="2.5" fill="none"/>
    
    <!-- Annotations -->
    <text x="{scale_x(0.15)}" y="{scale_y(0.35) - 10}" class="small" fill="#D13429">远离平衡</text>
    <text x="{scale_x(0.15)}" y="{scale_y(0.35) + 5}" class="small" fill="#D13429">高手续费</text>
    
    <text x="{scale_x(0.85)}" y="{scale_y(0.06) + 20}" class="small" fill="#4A8B71">接近平衡</text>
    <text x="{scale_x(0.85)}" y="{scale_y(0.06) + 35}" class="small" fill="#4A8B71">低手续费</text>
    
    <!-- Equilibrium point -->
    <circle cx="{scale_x(1)}" cy="{scale_y(f_mid)}" r="5" fill="#4A8B71"/>
    
    <!-- Formula -->
    <text x="{width/2}" y="{height - 20}" class="mono small" text-anchor="middle" fill="#8C928F">f = g·f_mid + (1-g)·f_out</text>
    
</svg>'''
    
    return svg


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    diagrams = [
        ("k_comparison.svg", generate_k_comparison()),
        ("value_conversion.svg", generate_value_conversion()),
        ("repegging_flow.svg", generate_repegging_flow()),
        ("dynamic_fee.svg", generate_dynamic_fee()),
    ]
    
    for filename, svg_content in diagrams:
        output_path = OUTPUT_DIR / filename
        output_path.write_text(svg_content, encoding="utf-8")
        print(f"Generated: {output_path}")


if __name__ == "__main__":
    main()
