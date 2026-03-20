#!/usr/bin/env python3
"""
Generate SVG curves for Curve StableSwap formula article.
"""

import math

# Cyber-Zen color palette
LEAD_GRAY = "#474747"
JADE_GREEN = "#4A8B71"
CINNABAR_RED = "#D13429"
LIGHT_GRAY = "#9CA3AF"
BLUE = "#3B82F6"

def create_svg(width, height, content):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">
    <style>
        text {{ font-family: 'Inter', -apple-system, sans-serif; fill: {LEAD_GRAY}; }}
        .mono {{ font-family: 'JetBrains Mono', 'SF Mono', monospace; }}
        .label {{ font-size: 14px; }}
        .title {{ font-size: 16px; font-weight: 600; }}
        .small {{ font-size: 12px; }}
    </style>
    {content}
</svg>'''

def curve_path(points, color, width=2.5, dashed=False):
    d = f"M {points[0][0]:.1f} {points[0][1]:.1f}"
    for x, y in points[1:]:
        d += f" L {x:.1f} {y:.1f}"
    dash = ' stroke-dasharray="8,4"' if dashed else ''
    return f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="none"{dash}/>'

def draw_axes(ox, oy, width, height, x_label="x", y_label="y"):
    """Draw coordinate axes with labels."""
    return f'''
    <line x1="{ox}" y1="{oy}" x2="{ox + width}" y2="{oy}" stroke="{LEAD_GRAY}" stroke-width="1.5" marker-end="url(#arrow)"/>
    <line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy - height}" stroke="{LEAD_GRAY}" stroke-width="1.5" marker-end="url(#arrow)"/>
    <text x="{ox + width + 10}" y="{oy + 5}" class="label mono">{x_label}</text>
    <text x="{ox - 5}" y="{oy - height - 10}" class="label mono">{y_label}</text>
    <defs>
        <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
            <path d="M0,0 L0,6 L9,3 z" fill="{LEAD_GRAY}"/>
        </marker>
    </defs>
    '''

def generate_model_design():
    """
    Figure 1: Constant Product vs Constant Sum curves with intersection point P.
    """
    width, height = 500, 400
    ox, oy = 60, 340  # origin
    ax_w, ax_h = 380, 280  # axes dimensions
    
    # Scale: D = 200 (so D/2 = 100 in graph units)
    D = 200
    scale = 1.8  # pixels per unit
    
    # Constant Product: xy = D²/4
    k = (D/2) ** 2
    cp_points = []
    for x in range(20, 181, 2):
        y = k / x
        if y <= 180:
            px = ox + x * scale
            py = oy - y * scale
            cp_points.append((px, py))
    
    # Constant Sum: x + y = D
    cs_points = []
    for x in range(0, 201, 5):
        y = D - x
        if y >= 0:
            px = ox + x * scale
            py = oy - y * scale
            cs_points.append((px, py))
    
    # Intersection point P (D/2, D/2)
    px_p = ox + (D/2) * scale
    py_p = oy - (D/2) * scale
    
    content = f'''
    {draw_axes(ox, oy, ax_w, ax_h, "x", "y")}
    
    <!-- Constant Product curve (blue) -->
    {curve_path(cp_points, BLUE, 2.5)}
    
    <!-- Constant Sum line (green) -->
    {curve_path(cs_points, JADE_GREEN, 2.5)}
    
    <!-- Intersection point P -->
    <circle cx="{px_p}" cy="{py_p}" r="6" fill="{CINNABAR_RED}"/>
    <text x="{px_p + 12}" y="{py_p - 8}" class="label" fill="{CINNABAR_RED}">P (D/2, D/2)</text>
    
    <!-- Dashed lines to axes -->
    <line x1="{px_p}" y1="{py_p}" x2="{px_p}" y2="{oy}" stroke="{LIGHT_GRAY}" stroke-width="1" stroke-dasharray="4,4"/>
    <line x1="{px_p}" y1="{py_p}" x2="{ox}" y2="{py_p}" stroke="{LIGHT_GRAY}" stroke-width="1" stroke-dasharray="4,4"/>
    
    <!-- Axis labels -->
    <text x="{px_p}" y="{oy + 20}" class="small mono" text-anchor="middle">D/2</text>
    <text x="{ox - 25}" y="{py_p + 5}" class="small mono">D/2</text>
    
    <!-- Legend -->
    <line x1="320" y1="40" x2="360" y2="40" stroke="{BLUE}" stroke-width="2.5"/>
    <text x="370" y="45" class="small mono">xy = k</text>
    
    <line x1="320" y1="65" x2="360" y2="65" stroke="{JADE_GREEN}" stroke-width="2.5"/>
    <text x="370" y="70" class="small mono">x + y = D</text>
    
    <!-- Annotations -->
    <text x="150" y="100" class="small" fill="{BLUE}">曲率大，永不枯竭</text>
    <text x="280" y="250" class="small" fill="{JADE_GREEN}">完全平坦，会被掏空</text>
    '''
    
    return create_svg(width, height, content)

def generate_xy_position():
    """
    Figure 2: xy value as a function of x under Constant Sum constraint.
    Shows that xy is maximized at the balance point.
    """
    width, height = 500, 350
    ox, oy = 60, 290
    ax_w, ax_h = 380, 230
    
    D = 200
    scale_x = 1.8
    scale_y = 0.012  # xy values are large, need smaller scale
    
    # xy = x(D-x) = Dx - x² (parabola)
    points = []
    for x in range(5, 196, 2):
        y = x * (D - x)
        px = ox + x * scale_x
        py = oy - y * scale_y
        points.append((px, py))
    
    # Maximum point at x = D/2
    max_x = D / 2
    max_y = max_x * (D - max_x)  # = D²/4
    px_max = ox + max_x * scale_x
    py_max = oy - max_y * scale_y
    
    content = f'''
    {draw_axes(ox, oy, ax_w, ax_h, "x", "xy")}
    
    <!-- Parabola -->
    {curve_path(points, JADE_GREEN, 2.5)}
    
    <!-- Maximum point -->
    <circle cx="{px_max}" cy="{py_max}" r="6" fill="{CINNABAR_RED}"/>
    <text x="{px_max + 10}" y="{py_max - 10}" class="label" fill="{CINNABAR_RED}">最大值 D²/4</text>
    
    <!-- Dashed line to x-axis -->
    <line x1="{px_max}" y1="{py_max}" x2="{px_max}" y2="{oy}" stroke="{LIGHT_GRAY}" stroke-width="1" stroke-dasharray="4,4"/>
    
    <!-- X-axis labels -->
    <text x="{ox}" y="{oy + 20}" class="small mono">0</text>
    <text x="{px_max}" y="{oy + 20}" class="small mono" text-anchor="middle">D/2</text>
    <text x="{ox + D * scale_x}" y="{oy + 20}" class="small mono" text-anchor="middle">D</text>
    
    <!-- Annotations -->
    <text x="100" y="200" class="small" fill="{LEAD_GRAY}">偏离平衡</text>
    <text x="100" y="220" class="small" fill="{LEAD_GRAY}">xy 变小</text>
    
    <text x="320" y="200" class="small" fill="{LEAD_GRAY}">偏离平衡</text>
    <text x="320" y="220" class="small" fill="{LEAD_GRAY}">xy 变小</text>
    
    <!-- Title -->
    <text x="{width/2}" y="30" class="title" text-anchor="middle">在 x + y = D 约束下，xy 在平衡点达到最大</text>
    '''
    
    return create_svg(width, height, content)

def generate_amplification():
    """
    Figure 3: Effect of amplification coefficient A on curve shape.
    Shows curves for different A values.
    """
    width, height = 550, 400
    ox, oy = 70, 340
    ax_w, ax_h = 420, 280
    
    D = 200
    scale = 1.9
    
    def stableswap_y(x, A, D):
        """
        Solve for y given x using Newton's method.
        4A(x+y) + D = 4AD + D³/(4xy)
        """
        y = D / 2  # initial guess
        for _ in range(50):
            # f(y) = 4A(x+y) + D - 4AD - D³/(4xy)
            f = 4*A*(x + y) + D - 4*A*D - (D**3)/(4*x*y)
            # f'(y) = 4A + D³/(4xy²)
            df = 4*A + (D**3)/(4*x*y**2)
            y_new = y - f/df
            if abs(y_new - y) < 0.0001:
                break
            y = y_new
        return y if y > 0 else None
    
    # Generate curves for different A values
    curves = [
        (10, LIGHT_GRAY, "A = 10"),
        (100, BLUE, "A = 100"),
        (500, JADE_GREEN, "A = 500"),
    ]
    
    curve_paths = []
    for A, color, label in curves:
        points = []
        for x in range(15, 186, 2):
            y = stableswap_y(x, A, D)
            if y and 10 < y < 190:
                px = ox + x * scale
                py = oy - y * scale
                points.append((px, py))
        if points:
            curve_paths.append((curve_path(points, color, 2.5), color, label))
    
    # Also draw reference curves
    # Constant Product
    k = (D/2) ** 2
    cp_points = []
    for x in range(20, 181, 2):
        y = k / x
        if y <= 180:
            px = ox + x * scale
            py = oy - y * scale
            cp_points.append((px, py))
    
    # Constant Sum
    cs_points = [(ox, oy - D * scale), (ox + D * scale, oy)]
    
    content = f'''
    {draw_axes(ox, oy, ax_w, ax_h, "x", "y")}
    
    <!-- Reference: Constant Product (dashed) -->
    {curve_path(cp_points, LIGHT_GRAY, 1.5, dashed=True)}
    
    <!-- Reference: Constant Sum (dashed) -->
    {curve_path(cs_points, LIGHT_GRAY, 1.5, dashed=True)}
    
    <!-- StableSwap curves -->
    {curve_paths[0][0]}
    {curve_paths[1][0]}
    {curve_paths[2][0]}
    
    <!-- Balance point -->
    <circle cx="{ox + (D/2) * scale}" cy="{oy - (D/2) * scale}" r="5" fill="{CINNABAR_RED}"/>
    
    <!-- Legend -->
    <line x1="380" y1="40" x2="420" y2="40" stroke="{LIGHT_GRAY}" stroke-width="1.5" stroke-dasharray="8,4"/>
    <text x="430" y="45" class="small">xy = k</text>
    
    <line x1="380" y1="60" x2="420" y2="60" stroke="{LIGHT_GRAY}" stroke-width="2.5"/>
    <text x="430" y="65" class="small">{curves[0][2]}</text>
    
    <line x1="380" y1="80" x2="420" y2="80" stroke="{BLUE}" stroke-width="2.5"/>
    <text x="430" y="85" class="small">{curves[1][2]}</text>
    
    <line x1="380" y1="100" x2="420" y2="100" stroke="{JADE_GREEN}" stroke-width="2.5"/>
    <text x="430" y="105" class="small">{curves[2][2]}</text>
    
    <!-- Annotations -->
    <text x="150" y="80" class="small" fill="{JADE_GREEN}">A 越大</text>
    <text x="150" y="100" class="small" fill="{JADE_GREEN}">越接近直线</text>
    
    <text x="120" y="280" class="small" fill="{LIGHT_GRAY}">A 越小</text>
    <text x="120" y="300" class="small" fill="{LIGHT_GRAY}">越接近曲线</text>
    '''
    
    return create_svg(width, height, content)

def main():
    import os
    
    output_dir = "/Users/feng/Documents/person/cyber-zen/src/content/blog"
    
    # Generate all SVGs
    svgs = [
        ("curve_model_design.svg", generate_model_design()),
        ("curve_xy_position.svg", generate_xy_position()),
        ("curve_amplification.svg", generate_amplification()),
    ]
    
    for filename, content in svgs:
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Generated: {filepath}")

if __name__ == "__main__":
    main()
