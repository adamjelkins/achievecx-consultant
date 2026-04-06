"""
platform_diagram.py

Generates a platform overview SVG diagram showing:
  Entry Channels → AI Platform → Use Cases → Outcomes
  Data Sources as a base layer strip

Two themes:
  dark  — matches app (default, used in Phase 2)
  light — print-friendly, used in PDF export

Entry point:
  render_platform_diagram(confirmed_flows, assessment, theme="dark")
  generate_platform_svg(confirmed_flows, assessment, theme="dark") → str
"""

import json
import math
from pathlib import Path
try:
    import streamlit as st
except ImportError:
    import types, sys
    st = types.ModuleType('streamlit')
    st.session_state = types.SimpleNamespace()
    st.spinner = lambda x: __import__('contextlib').nullcontext()
    st.error = lambda x: None
    st.warning = lambda x: None
    st.info = lambda x: None
    sys.modules['streamlit'] = st
import streamlit.components.v1 as components


# --------------------------------------------------
# Load flow templates
# --------------------------------------------------

_TEMPLATES_PATH = Path(__file__).parent / "data" / "flow_templates.json"
_templates_cache: dict | None = None



# Internal CWR keys → client-facing display labels
CWR_DISPLAY = {
    "Run":   "AI Automated",
    "Walk":  "AI Assisted",
    "Crawl": "Stay Manual",
}

def _load_templates() -> dict:
    global _templates_cache
    if _templates_cache is not None:
        return _templates_cache
    try:
        with open(_TEMPLATES_PATH) as f:
            _templates_cache = json.load(f)
    except Exception:
        _templates_cache = {}
    return _templates_cache


# --------------------------------------------------
# Theme palettes
# --------------------------------------------------

THEMES = {
    "dark": {
        "bg":              "#0d0d0d",
        "surface":         "#1e1e1e",
        "surface2":        "#252525",
        "border":          "#404040",
        "border2":         "#383838",
        "text_primary":    "#ffffff",
        "text_secondary":  "#d4d4d8",
        "text_muted":      "#a1a1aa",
        "accent":          "#818cf8",
        "green":           "#4ade80",
        "green_dim":       "#14532d",
        "amber":           "#fbbf24",
        "amber_dim":       "#451a03",
        "gray":            "#9ca3af",
        "gray_dim":        "#27272a",
        "red":             "#f87171",
        "line":            "#404040",
        "line_accent":     "#606060",
        "ds_bg":           "#181818",
        "ds_border":       "#404040",
        "platform_bg":     "#1a1a35",
        "platform_border": "#818cf8",
    },
    "light": {
        "bg":           "#ffffff",
        "surface":      "#f8fafc",
        "surface2":     "#f1f5f9",
        "border":       "#e2e8f0",
        "border2":      "#cbd5e1",
        "text_primary": "#0f172a",
        "text_secondary":"#475569",
        "text_muted":   "#94a3b8",
        "accent":       "#4f46e5",
        "green":        "#16a34a",
        "green_dim":    "#dcfce7",
        "amber":        "#d97706",
        "amber_dim":    "#fef3c7",
        "gray":         "#64748b",
        "gray_dim":     "#f1f5f9",
        "red":          "#dc2626",
        "line":         "#cbd5e1",
        "line_accent":  "#94a3b8",
        "ds_bg":        "#f8fafc",
        "ds_border":    "#e2e8f0",
        "platform_bg":  "#eef2ff",
        "platform_border": "#6366f1",
    },
}

# Channel icons (unicode — work in SVG text)
CHANNEL_ICONS = {
    "Phone":          "📞",
    "Web":            "🌐",
    "Chat":           "💬",
    "SMS":            "📱",
    "Email":          "✉",
    "Mobile App":     "📲",
    "App":            "📲",
    "IVR":            "📟",
    "App Push":       "🔔",
    "Automated Phone Call": "📣",
    "Social Media":   "🔗",
    "Kiosk":          "🖥",
}

# Human role icons
HUMAN_ICONS = {
    "None":          "✓",
    "Escalation":    "↗",
    "In-Loop":       "👤",
    "Post-Review":   "◎",
    "Collaborative": "🤝",
}

HUMAN_COLORS = {
    "None":          "green",
    "Escalation":    "accent",
    "In-Loop":       "amber",
    "Post-Review":   "accent",
    "Collaborative": "amber",
}


# --------------------------------------------------
# Data preparation
# --------------------------------------------------

def _prepare_diagram_data(confirmed_flows: list, assessment: dict) -> dict:
    """
    Extract channels, use cases, data sources from confirmed flows.
    Returns structured data for SVG layout.
    """
    templates  = _load_templates()
    score_map  = {f["flow_id"]: f for f in assessment.get("scored_flows", [])}

    channels_seen   = {}   # channel_name → count
    data_sources_seen = {} # ds_name → count
    use_cases       = []

    for flow in confirmed_flows:
        fid      = flow["flow_id"]
        tmpl     = templates.get(fid, {})
        scored   = score_map.get(fid, {})

        flow_name    = tmpl.get("flow_name") or flow.get("flow_name", fid)
        cwr          = scored.get("crawl_walk_run", "Crawl")
        ai_score     = scored.get("ai_score", 0)
        containment  = tmpl.get("containment_target")
        contain_type = tmpl.get("containment_type", "standard")
        eng_target   = tmpl.get("engagement_target", "")
        human_role   = tmpl.get("human_role", "Escalation")
        channels     = tmpl.get("entry_channels", ["Phone", "Web"])
        data_srcs    = tmpl.get("data_sources", ["CRM"])

        # Track channels
        for ch in channels:
            channels_seen[ch] = channels_seen.get(ch, 0) + 1

        # Track data sources
        for ds in data_srcs:
            data_sources_seen[ds] = data_sources_seen.get(ds, 0) + 1

        # Containment display
        if contain_type == "engagement":
            contain_display = eng_target
            contain_label   = "Engagement"
        elif contain_type == "ai_assisted":
            contain_display = "AI-Assisted"
            contain_label   = "Triage & Route"
        else:
            contain_display = f"{containment}%" if containment else "—"
            contain_label   = "Containment"

        use_cases.append({
            "flow_id":       fid,
            "name":          flow_name,
            "cwr":           cwr,
            "ai_score":      ai_score,
            "containment":   containment,
            "contain_type":  contain_type,
            "contain_display": contain_display,
            "contain_label": contain_label,
            "human_role":    human_role,
            "channels":      channels,
        })

    # Sort channels by frequency, cap at 6
    top_channels = sorted(channels_seen.items(), key=lambda x: x[1], reverse=True)
    top_channels = [c[0] for c in top_channels[:6]]

    # Sort data sources by frequency, cap at 8
    top_ds = sorted(data_sources_seen.items(), key=lambda x: x[1], reverse=True)
    top_ds = [d[0] for d in top_ds[:8]]

    # Sort use cases by CWR then ai_score
    cwr_order = {"Run": 0, "Walk": 1, "Crawl": 2}
    use_cases.sort(key=lambda x: (cwr_order.get(x["cwr"], 3), -x["ai_score"]))

    # Business info
    bp       = st.session_state.get("business_profile", {})
    asmnt    = assessment or {}
    ai_score = asmnt.get("business_ai_score", 0)
    company  = bp.get("company_name", "AI Platform")

    return {
        "company":      company,
        "ai_score":     ai_score,
        "score_label":  asmnt.get("score_label", ""),
        "channels":     top_channels,
        "use_cases":    use_cases,
        "data_sources": top_ds,
    }


# --------------------------------------------------
# SVG layout constants
# --------------------------------------------------

# Column X positions (proportional, scaled by total width)
COL_CHANNELS    = 0.06   # left edge of channel nodes
COL_PLATFORM    = 0.34   # center of AI platform node
COL_USECASES    = 0.60   # left edge of use case nodes
COL_OUTCOMES    = 0.92   # center of outcome nodes

NODE_W_CHANNEL  = 110
NODE_H_CHANNEL  = 36
NODE_W_USECASE  = 160
NODE_H_USECASE  = 44
NODE_W_PLATFORM = 130
NODE_H_PLATFORM = 70
NODE_W_OUTCOME  = 80
NODE_H_OUTCOME  = 32

DS_HEIGHT       = 40   # data source strip height
TOP_PAD         = 28
BOT_PAD         = 20
SECTION_PAD     = 16


def _svg_rect(x, y, w, h, rx=8, fill="#141414", stroke="#2a2a2a",
              stroke_w=1, opacity=1.0) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w}" '
        f'opacity="{opacity}"/>'
    )


def _svg_text(x, y, text, size=11, fill="#f1f5f9", weight="normal",
              anchor="middle", dy=0) -> str:
    dy_attr = f' dy="{dy}"' if dy else ""
    return (
        f'<text x="{x}" y="{y}"{dy_attr} font-size="{size}" fill="{fill}" '
        f'font-weight="{weight}" text-anchor="{anchor}" '
        f'font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif">'
        + _escape(text) + '</text>'
    )


def _escape(text: str) -> str:
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _svg_line(x1, y1, x2, y2, stroke="#2a2a2a", sw=1.5,
              dash="", opacity=0.6) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{stroke}" stroke-width="{sw}"{dash_attr} '
        f'opacity="{opacity}"/>'
    )


def _svg_arrow(x1, y1, x2, y2, stroke="#3f3f46", sw=1.5, opacity=0.7) -> str:
    """Arrow with a simple triangular arrowhead at x2,y2."""
    # Arrowhead size
    ah = 7
    angle = math.atan2(y2 - y1, x2 - x1)
    ax1 = x2 - ah * math.cos(angle - 0.4)
    ay1 = y2 - ah * math.sin(angle - 0.4)
    ax2 = x2 - ah * math.cos(angle + 0.4)
    ay2 = y2 - ah * math.sin(angle + 0.4)
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"/>'
        f'<polygon points="{x2:.1f},{y2:.1f} {ax1:.1f},{ay1:.1f} {ax2:.1f},{ay2:.1f}" '
        f'fill="{stroke}" opacity="{opacity}"/>'
    )


# --------------------------------------------------
# SVG generator
# --------------------------------------------------

def generate_platform_svg(
    confirmed_flows: list,
    assessment: dict,
    theme: str = "dark",
    width: int = 820,
    selected_flow_id: str = "",
) -> str:
    """
    Generate the platform overview SVG string.

    Args:
        confirmed_flows: list of confirmed flow dicts from discovery
        assessment:      maturity assessment dict
        theme:           "dark" or "light"
        width:           SVG width in px (height is calculated)

    Returns:
        Complete SVG string ready for embedding.
    """
    T    = THEMES.get(theme, THEMES["dark"])
    data = _prepare_diagram_data(confirmed_flows, assessment)

    channels   = data["channels"]
    use_cases  = data["use_cases"]
    data_srcs  = data["data_sources"]
    company    = data["company"]
    ai_score   = data["ai_score"]
    score_label= data["score_label"]

    n_ch  = max(len(channels), 1)
    n_uc  = max(len(use_cases), 1)
    n_rows = max(n_ch, n_uc)

    # Height calculation
    row_h       = 52
    content_h   = n_rows * row_h
    ds_strip_h  = DS_HEIGHT + 16
    total_h     = TOP_PAD + content_h + SECTION_PAD + ds_strip_h + BOT_PAD + 40

    # X positions (absolute)
    x_ch   = int(width * COL_CHANNELS)
    x_plt  = int(width * COL_PLATFORM)
    x_uc   = int(width * COL_USECASES)
    x_out  = int(width * COL_OUTCOMES)

    # Platform node
    plt_y  = TOP_PAD + (content_h - NODE_H_PLATFORM) // 2
    plt_cx = x_plt  # center x
    plt_cy = plt_y + NODE_H_PLATFORM // 2

    # AI score color
    if ai_score >= 70:
        score_color = T["green"]
    elif ai_score >= 40:
        score_color = T["accent"]
    else:
        score_color = T["amber"]

    # Outcome positions
    cwr_counts = {
        "Run":   sum(1 for u in use_cases if u["cwr"] == "Run"),
        "Walk":  sum(1 for u in use_cases if u["cwr"] == "Walk"),
        "Crawl": sum(1 for u in use_cases if u["cwr"] == "Crawl"),
    }
    outcome_y_run   = TOP_PAD + row_h * 0.5
    outcome_y_walk  = TOP_PAD + content_h * 0.5
    outcome_y_crawl = TOP_PAD + content_h - row_h * 0.5

    svg_parts = []

    # ── SVG header ──
    svg_parts.append(
        f'<svg viewBox="0 0 {width} {total_h}" '
        f'width="{width}" height="{total_h}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="background:{T["bg"]};border-radius:12px;">'
    )

    # ── Background ──
    svg_parts.append(_svg_rect(0, 0, width, total_h, rx=12,
                               fill=T["bg"], stroke="none"))

    # ── Section labels ──
    label_y = TOP_PAD - 10
    for lx, label in [
        (x_ch + NODE_W_CHANNEL // 2,   "Entry Channels"),
        (x_plt,                         "AI Platform"),
        (x_uc + NODE_W_USECASE // 2,    "Use Cases"),
        (x_out,                         "Outcomes"),
    ]:
        svg_parts.append(_svg_text(
            lx, label_y, label,
            size=10, fill=T["text_muted"], weight="700",
            anchor="middle",
        ))

    # ── Channel nodes ──
    ch_positions = {}  # channel_name → (cx, cy)
    ch_spacing   = content_h / n_ch
    for i, ch in enumerate(channels):
        cy = TOP_PAD + ch_spacing * i + ch_spacing / 2
        cx = x_ch + NODE_W_CHANNEL // 2
        ch_positions[ch] = (cx, cy)

        icon = CHANNEL_ICONS.get(ch, "◆")
        svg_parts.append(_svg_rect(
            x_ch, cy - NODE_H_CHANNEL // 2,
            NODE_W_CHANNEL, NODE_H_CHANNEL,
            rx=6, fill=T["surface"], stroke=T["border"],
        ))
        svg_parts.append(_svg_text(
            x_ch + 14, cy + 1,
            icon, size=13, fill=T["text_secondary"], anchor="start",
        ))
        svg_parts.append(_svg_text(
            x_ch + 30, cy + 4,
            ch, size=10, fill=T["text_primary"],
            weight="500", anchor="start",
        ))

    # ── AI Platform node ──
    # Taller node to give breathing room
    NODE_H_PLT_ACTUAL = max(NODE_H_PLATFORM, 90)
    plt_y_adj = TOP_PAD + (content_h - NODE_H_PLT_ACTUAL) // 2
    plt_x     = x_plt - NODE_W_PLATFORM // 2
    plt_cy    = plt_y_adj + NODE_H_PLT_ACTUAL // 2

    svg_parts.append(_svg_rect(
        plt_x, plt_y_adj,
        NODE_W_PLATFORM, NODE_H_PLT_ACTUAL,
        rx=10, fill=T["platform_bg"],
        stroke=T["platform_border"], stroke_w=2,
    ))

    # Company name at top of node
    company_short = company if len(company) <= 14 else company[:13] + "…"
    svg_parts.append(_svg_text(
        plt_cx, plt_y_adj + 18,
        company_short, size=10,
        fill=T["text_muted"], weight="500",
    ))

    # Divider line inside node
    svg_parts.append(_svg_line(
        plt_x + 10, plt_y_adj + 24,
        plt_x + NODE_W_PLATFORM - 10, plt_y_adj + 24,
        stroke=T["platform_border"], sw=0.5, opacity=0.4,
    ))

    # Score — only show when assessment has been run (score > 0)
    if ai_score > 0:
        svg_parts.append(_svg_text(
            plt_cx, plt_y_adj + 52,
            str(ai_score), size=28,
            fill=score_color, weight="700",
        ))
        svg_parts.append(_svg_text(
            plt_cx, plt_y_adj + 67,
            score_label or "AI Score", size=9,
            fill=score_color, weight="500",
        ))
        svg_parts.append(_svg_text(
            plt_cx, plt_y_adj + NODE_H_PLT_ACTUAL - 10,
            "Agentic AI Platform", size=9,
            fill=T["text_muted"],
        ))
    else:
        # No score yet — just show platform label prominently
        svg_parts.append(_svg_text(
            plt_cx, plt_y_adj + 50,
            "Agentic AI", size=13,
            fill=T["text_secondary"], weight="700",
        ))
        svg_parts.append(_svg_text(
            plt_cx, plt_y_adj + 66,
            "Platform", size=13,
            fill=T["text_secondary"], weight="700",
        ))

    # Update plt_cy for arrow calculations to use adjusted center
    plt_cy = plt_y_adj + NODE_H_PLT_ACTUAL // 2

    # ── Channels → Platform arrows ──
    for ch, (cx, cy) in ch_positions.items():
        x1 = x_ch + NODE_W_CHANNEL
        x2 = plt_x
        svg_parts.append(_svg_arrow(
            x1, cy, x2, plt_cy,
            stroke=T["line_accent"], sw=1.5, opacity=0.8,
        ))

    # ── Use case nodes ──
    uc_positions = {}  # flow_id → (lx, cy)  lx = left edge
    uc_spacing   = content_h / n_uc

    for i, uc in enumerate(use_cases):
        cy  = TOP_PAD + uc_spacing * i + uc_spacing / 2
        lx  = x_uc
        cx  = lx + NODE_W_USECASE // 2
        uc_positions[uc["flow_id"]] = (lx, cy)

        fid        = uc["flow_id"]
        cwr        = uc["cwr"]
        is_selected = (fid == selected_flow_id)

        cwr_colors = {
            "Run":   T["green"],
            "Walk":  T["amber"],
            "Crawl": T["gray"],
        }
        node_color = cwr_colors.get(cwr, T["gray"])

        # Selected node gets brighter border + glow
        node_stroke     = node_color if is_selected else T["border2"]
        node_stroke_w   = 2 if is_selected else 1
        node_fill       = T["surface2"] if is_selected else T["surface"]

        # Wrap node in a <g> for grouping only (no click — handled by Streamlit buttons)
        svg_parts.append(
            f'<g data-flow-id="{fid}">'
        )

        # Optional glow for selected node
        if is_selected:
            svg_parts.append(
                f'<rect x="{lx-3}" y="{cy - NODE_H_USECASE//2 - 3}" '
                f'width="{NODE_W_USECASE+6}" height="{NODE_H_USECASE+6}" '
                f'rx="9" fill="{node_color}" opacity="0.12" stroke="none"/>'
            )

        # Node background
        svg_parts.append(_svg_rect(
            lx, cy - NODE_H_USECASE // 2,
            NODE_W_USECASE, NODE_H_USECASE,
            rx=6, fill=node_fill,
            stroke=node_stroke, stroke_w=node_stroke_w,
        ))
        # Left color bar — thicker for visibility
        svg_parts.append(_svg_rect(
            lx, cy - NODE_H_USECASE // 2,
            4, NODE_H_USECASE,
            rx=1, fill=node_color, stroke="none",
        ))

        # Flow name (truncate if needed)
        name = uc["name"]
        if len(name) > 20:
            name = name[:18] + "…"
        svg_parts.append(_svg_text(
            lx + 12, cy - 5,
            name, size=11,
            fill=T["text_primary"], weight="600", anchor="start",
        ))

        # Containment display — brighter, larger
        contain = uc["contain_display"]
        contain_color = node_color if uc["contain_type"] == "standard" else T["amber"]
        svg_parts.append(_svg_text(
            lx + 12, cy + 10,
            contain, size=10,
            fill=contain_color, weight="700", anchor="start",
        ))

        # Human role badge (right side)
        hr        = uc["human_role"]
        hr_icon   = HUMAN_ICONS.get(hr, "↗")
        hr_col_key= HUMAN_COLORS.get(hr, "accent")
        hr_color  = T.get(hr_col_key, T["accent"])
        badge_x   = lx + NODE_W_USECASE - 22
        badge_y   = cy - 8
        svg_parts.append(_svg_rect(
            badge_x, badge_y, 18, 18, rx=4,
            fill=hr_color, stroke="none", opacity=0.15,
        ))
        svg_parts.append(_svg_text(
            badge_x + 9, badge_y + 12,
            hr_icon, size=9,
            fill=hr_color, anchor="middle",
        ))

        # Close the <g> click wrapper
        svg_parts.append('</g>')

    # ── Platform → Use case arrows ──
    for i, uc in enumerate(use_cases):
        lx, cy = uc_positions[uc["flow_id"]]
        x1 = x_plt + NODE_W_PLATFORM // 2
        x2 = lx
        svg_parts.append(_svg_arrow(
            x1, plt_cy, x2, cy,
            stroke=T["line_accent"], sw=1.5, opacity=0.7,
        ))

    # ── Outcome nodes ──
    outcomes = [
        ("AI Automated", T["green"],  "✓", "Run"),
        ("AI Assisted",  T["accent"], "↗", "Walk"),
        ("Stay Manual",  T["amber"],  "⚡", "Crawl"),
    ]
    out_positions = {}
    out_spacing   = content_h / 3
    for i, (label, color, icon, cwr_key) in enumerate(outcomes):
        oy  = TOP_PAD + out_spacing * i + out_spacing / 2
        ocx = x_out
        out_positions[cwr_key] = (ocx, oy)

        # Only show if there are flows of this type
        count = cwr_counts.get(cwr_key, 0)
        if count == 0:
            continue

        svg_parts.append(_svg_rect(
            ocx - NODE_W_OUTCOME // 2, oy - NODE_H_OUTCOME // 2,
            NODE_W_OUTCOME, NODE_H_OUTCOME,
            rx=6, fill=T["surface2"], stroke=color, stroke_w=1.5,
        ))
        svg_parts.append(_svg_text(
            ocx, oy - 4,
            icon + " " + label, size=11,
            fill=color, weight="700",
        ))
        svg_parts.append(_svg_text(
            ocx, oy + 10,
            str(count) + " flow" + ("s" if count != 1 else ""),
            size=9, fill=T["text_secondary"],
        ))

    # ── Use case → Outcome arrows ──
    for uc in use_cases:
        lx, cy = uc_positions[uc["flow_id"]]
        cwr    = uc["cwr"]
        if cwr not in out_positions:
            continue
        ocx, ocy = out_positions[cwr]
        x1 = lx + NODE_W_USECASE
        x2 = ocx - NODE_W_OUTCOME // 2
        cwr_colors = {"Run": T["green"], "Walk": T["accent"], "Crawl": T["gray"]}
        svg_parts.append(_svg_arrow(
            x1, cy, x2, ocy,
            stroke=cwr_colors.get(cwr, T["line_accent"]),
            sw=1.2, opacity=0.6,
        ))

    # ── Data Sources strip ──
    ds_y = TOP_PAD + content_h + SECTION_PAD
    svg_parts.append(_svg_rect(
        8, ds_y,
        width - 16, DS_HEIGHT + 8,
        rx=8, fill=T["ds_bg"], stroke=T["ds_border"],
    ))
    svg_parts.append(_svg_text(
        20, ds_y + 13,
        "Data Sources:", size=10,
        fill=T["text_secondary"], weight="700", anchor="start",
    ))

    ds_x = 110
    ds_cx = ds_y + DS_HEIGHT // 2 + 2
    for ds in data_srcs:
        chip_w = len(ds) * 6.5 + 16
        if ds_x + chip_w > width - 20:
            break
        svg_parts.append(_svg_rect(
            ds_x, ds_y + 4,
            chip_w, 24, rx=4,
            fill=T["surface"], stroke=T["border"],
        ))
        svg_parts.append(_svg_text(
            ds_x + chip_w // 2, ds_y + 20,
            ds, size=10,
            fill=T["text_primary"], anchor="middle",
        ))
        ds_x += chip_w + 6

    # ── Connector lines from platform down to data sources ──
    svg_parts.append(_svg_line(
        plt_cx, plt_y + NODE_H_PLATFORM,
        plt_cx, ds_y,
        stroke=T["platform_border"], sw=1, dash="4 3", opacity=0.4,
    ))

    # ── Legend ──
    legend_y = ds_y + DS_HEIGHT + 18
    legend_x = 16
    for label, color in [
        ("AI Automated", T["green"]),
        ("AI Assisted",  T["amber"]),
        ("Stay Manual",  T["gray"]),
    ]:
        svg_parts.append(_svg_rect(
            legend_x, legend_y - 7, 10, 10, rx=2,
            fill=color, stroke="none",
        ))
        svg_parts.append(_svg_text(
            legend_x + 14, legend_y + 2,
            label, size=10,
            fill=T["text_secondary"], anchor="start",
        ))
        legend_x += len(label) * 6 + 30

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


# --------------------------------------------------
# Streamlit renderer
# --------------------------------------------------

def render_platform_diagram(
    confirmed_flows: list,
    assessment: dict,
    theme: str = "dark",
    width: int = 780,
    selected_flow_id: str = "",
) -> None:
    """
    Render the platform overview diagram — purely visual, no click handlers.
    Node selection is handled by Streamlit buttons outside the iframe.

    Args:
        confirmed_flows:  list of confirmed flow dicts from discovery
        assessment:       maturity assessment dict
        theme:            "dark" | "light"
        width:            display width in pixels
        selected_flow_id: flow_id to highlight (brighter border + glow)
    """
    if not confirmed_flows:
        return

    svg = generate_platform_svg(
        confirmed_flows, assessment,
        theme=theme, width=width,
        selected_flow_id=selected_flow_id,
    )

    T = THEMES.get(theme, THEMES["dark"])
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: {T["bg"]};
    display: flex;
    justify-content: center;
    padding: 0;
  }}
  .diagram-wrap {{ width: 100%; max-width: {width}px; }}
  svg {{ width: 100%; height: auto; display: block; }}
</style>
</head>
<body>
<div class="diagram-wrap">{svg}</div>
</body>
</html>"""

    import re
    m     = re.search(r'height="(\d+)"', svg)
    svg_h = int(m.group(1)) + 16 if m else 500
    components.html(html, height=svg_h, scrolling=False)