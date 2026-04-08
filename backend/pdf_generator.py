"""
pdf_generator.py

Generates the CX Blueprint PDF from a blueprint dict.
Fully standalone — no Streamlit dependency.
Fixes vs Streamlit version:
  - Risk assessment section added
  - No blank page when diagram unavailable
  - All data sourced from blueprint dict, not session_state
  - conf_raw derived from blueprint dict
  - No unnecessary PageBreaks before empty sections
"""

import io
from datetime import datetime


THEMES = {
    "dark": {
        "page_bg": "#0a0a0a", "surface": "#141414", "surface_alt": "#1a1a1a",
        "border": "#2a2a2a", "text_primary": "#f1f5f9",
        "text_secondary": "#a1a1aa", "text_muted": "#71717a",
        "accent": "#6366f1", "accent_light": "#818cf8",
        "green": "#22c55e", "amber": "#f59e0b", "red": "#ef4444",
        "score_bar_bg": "#27272a",
    },
    "light": {
        "page_bg": "#ffffff", "surface": "#f8fafc", "surface_alt": "#f1f5f9",
        "border": "#e2e8f0", "text_primary": "#0f172a",
        "text_secondary": "#475569", "text_muted": "#94a3b8",
        "accent": "#4f46e5", "accent_light": "#6366f1",
        "green": "#16a34a", "amber": "#d97706", "red": "#dc2626",
        "score_bar_bg": "#e2e8f0",
    },
}


def _fmt(value, decimals=0):
    if value is None or (isinstance(value, float) and value != value):
        return "—"
    try:
        n = float(value)
        if abs(n) >= 1_000_000:
            return f"${n / 1_000_000:.1f}M"
        if abs(n) >= 1_000:
            return f"${n / 1_000:.0f}K"
        return f"${n:.{decimals}f}"
    except Exception:
        return str(value)


def _fmt_pct(value):
    try:
        return f"{float(value) * 100:.0f}%"
    except Exception:
        return "—"


def _ans(v):
    if isinstance(v, list):
        return ", ".join(str(x) for x in v if x)
    return str(v) if v else "—"


def generate_pdf(blueprint: dict, theme_name: str = "light") -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak,
    )
    from reportlab.graphics.shapes import Drawing, Rect
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os

    # Register Bitstream Vera — ships with ReportLab, full Unicode support
    rl_fonts = os.path.join(os.path.dirname(__import__("reportlab").__file__), "fonts")
    pdfmetrics.registerFont(TTFont("Vera",   os.path.join(rl_fonts, "Vera.ttf")))
    pdfmetrics.registerFont(TTFont("VeraBd", os.path.join(rl_fonts, "VeraBd.ttf")))
    pdfmetrics.registerFont(TTFont("VeraIt", os.path.join(rl_fonts, "VeraIt.ttf")))
    pdfmetrics.registerFont(TTFont("VeraBI", os.path.join(rl_fonts, "VeraBI.ttf")))
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    registerFontFamily("Vera", normal="Vera", bold="VeraBd",
                       italic="VeraIt", boldItalic="VeraBI")

    FONT      = "Vera"
    FONT_BOLD = "VeraBd"
    FONT_ITAL = "VeraIt"

    T = THEMES.get(theme_name, THEMES["light"])
    W = letter[0] - 1.7 * inch

    def _hex(h):
        return colors.HexColor(h)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=0.85 * inch, rightMargin=0.85 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    def _ps(name, **kw):
        kw.setdefault("fontName", FONT)
        return ParagraphStyle(name, parent=styles["Normal"], **kw)

    company_s = _ps("Co", fontSize=22, fontName=FONT_BOLD,
                    textColor=_hex(T["text_primary"]), leading=26, spaceAfter=2)
    tagline_s = _ps("Tag", fontSize=10, textColor=_hex(T["text_muted"]), spaceAfter=14)
    sec_s     = _ps("SH", fontSize=8, fontName=FONT_BOLD,
                    textColor=_hex(T["accent"]), leading=10, spaceBefore=16, spaceAfter=6)
    body_s    = _ps("Bo", fontSize=10, textColor=_hex(T["text_secondary"]),
                    leading=15, spaceAfter=8)
    italic_s  = _ps("It", fontSize=11, textColor=_hex(T["text_secondary"]),
                    leading=16, spaceAfter=10, fontName=FONT_ITAL)
    label_s   = _ps("La", fontSize=8, textColor=_hex(T["text_muted"]), fontName=FONT_BOLD)
    value_s   = _ps("Va", fontSize=9, textColor=_hex(T["text_primary"]))
    th_s      = _ps("TH", fontSize=8, fontName=FONT_BOLD, textColor=_hex(T["text_muted"]))
    tc_s      = _ps("TC", fontSize=9, textColor=_hex(T["text_primary"]), leading=12)
    td_s      = _ps("TD", fontSize=8, textColor=_hex(T["text_secondary"]), leading=11)
    bul_s     = _ps("Bu", fontSize=10, textColor=_hex(T["text_primary"]),
                    leading=15, leftIndent=14, spaceAfter=6)
    foot_s    = _ps("Fo", fontSize=7, textColor=_hex(T["text_muted"]), alignment=1)
    kpi_lbl_s = _ps("KL", fontSize=8, textColor=_hex(T["text_muted"]))

    def _hbar(value, max_value, bar_color, width=None, height=10):
        w   = width or W * 0.55
        bg  = T["score_bar_bg"]
        pct = min(max(value / max_value, 0), 1) if max_value else 0
        pad = 6
        d   = Drawing(w, height + pad * 2)
        d.add(Rect(0, pad, w, height, fillColor=_hex(bg), strokeColor=None))
        if pct > 0:
            d.add(Rect(0, pad, w * pct, height, fillColor=_hex(bar_color), strokeColor=None))
        return d

    def _div(sb=8, sa=8):
        return HRFlowable(width="100%", thickness=0.5,
                          color=_hex(T["border"]), spaceBefore=sb, spaceAfter=sa)

    def _kpi_row(items):
        n     = len(items)
        col_w = W / n
        hr, vr = [], []
        for lbl, val, col in items:
            hr.append(Paragraph(lbl, kpi_lbl_s))
            vr.append(Paragraph(
                f'<font color="{col}" size="14"><b>{val}</b></font>', value_s))
        tbl = Table([hr, vr], colWidths=[col_w] * n)
        tbl.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        return tbl

    def _info_table(rows):
        data = [[Paragraph(k, label_s), Paragraph(str(v), value_s)]
                for k, v in rows if v and v != "—"]
        if not data:
            return Spacer(1, 4)
        tbl = Table(data, colWidths=[1.6 * inch, W - 1.6 * inch])
        tbl.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS",(0, 0), (-1, -1), [_hex(T["surface"]), _hex(T["surface_alt"])]),
            ("LINEBELOW",     (0, 0), (-1, -2), 0.25, _hex(T["border"])),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        return tbl

    def _flow_table(flows, header_color):
        if not flows:
            return None
        rows = [[Paragraph("Flow", th_s), Paragraph("Score", th_s),
                 Paragraph("Phase", th_s), Paragraph("Opportunity", th_s)]]
        for f in flows:
            rows.append([
                Paragraph(f.get("flow_name", ""), tc_s),
                Paragraph(str(f.get("ai_score", 0)), tc_s),
                Paragraph(f.get("crawl_walk_run", ""), tc_s),
                Paragraph(f.get("rationale", ""), td_s),
            ])
        t = Table(rows, colWidths=[1.9 * inch, 0.55 * inch, 0.65 * inch, W - 3.1 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), _hex(T["surface_alt"])),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [_hex(T["surface"]), _hex(T["surface_alt"])]),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("GRID",          (0, 0), (-1, -1), 0.25, _hex(T["border"])),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        return t

    # ── Pull all data from blueprint dict ──────────────────────────

    company      = blueprint.get("company_name", "")
    domain       = blueprint.get("domain", "")
    generated    = blueprint.get("generated_at", "")[:10]
    for_name     = blueprint.get("generated_for", "")
    for_email    = blueprint.get("generated_email", "")
    industry     = blueprint.get("industry", "")
    regions      = _ans(blueprint.get("regions", ""))
    channels     = _ans(blueprint.get("channels", ""))
    crm          = blueprint.get("crm", "")
    cc_platform  = blueprint.get("cc_platform", "")
    primary_goal = blueprint.get("primary_goal", "")
    timeline     = blueprint.get("timeline", "")
    ai_score     = blueprint.get("business_ai_score", 0)
    score_label  = blueprint.get("score_label", "")
    flow_count   = blueprint.get("confirmed_flow_count", 0)
    qw_count     = blueprint.get("quick_win_count", 0)
    exec_summary = blueprint.get("executive_summary", "")
    next_steps   = blueprint.get("next_steps", [])
    flow_cards   = blueprint.get("flow_cards", [])
    quick_wins   = blueprint.get("quick_wins", [])
    walk_flows   = blueprint.get("walk_flows", [])
    crawl_flows  = blueprint.get("crawl_flows", [])
    bc           = blueprint.get("business_case", {})
    risk         = blueprint.get("risk_assessment", {})
    vendors      = blueprint.get("vendor_shortlist", [])

    # Profile completeness from blueprint dict
    conf_raw  = blueprint.get("profile_confidence", 0)
    if not conf_raw:
        filled   = sum(1 for k in ["crm", "cc_platform", "channels", "primary_goal", "timeline",
                                    "regions", "industry"] if blueprint.get(k))
        conf_raw = filled / 7
    conf_pct = int(conf_raw * 100)

    score_bar_color = (T["green"] if ai_score >= 70
                       else T["accent"] if ai_score >= 40
                       else T["text_muted"])

    story = []

    # ── PAGE 1: COVER ────────────────────────────────────────────

    # Try company favicon
    try:
        import urllib.request
        favicon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
        req = urllib.request.Request(favicon_url, headers={"User-Agent": "Mozilla/5.0"})
        favicon_bytes = urllib.request.urlopen(req, timeout=3).read()
        from reportlab.platypus import Image as RLImage
        img_buf = io.BytesIO(favicon_bytes)
        logo = RLImage(img_buf, width=0.45 * inch, height=0.45 * inch)
        ht = Table([[logo, Paragraph(company, company_s)]], colWidths=[0.6 * inch, None])
        ht.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(ht)
    except Exception:
        story.append(Paragraph(company, company_s))

    story.append(Paragraph("CX Blueprint", tagline_s))
    parts = []
    if for_name:  parts.append(f"Prepared for: {for_name}")
    if for_email: parts.append(for_email)
    parts.append(f"Generated: {generated}")
    story.append(Paragraph(" - ".join(parts), tagline_s))
    story.append(_div(4, 12))

    story.append(Paragraph("EXECUTIVE SUMMARY", sec_s))
    if exec_summary:
        story.append(Paragraph(exec_summary, italic_s))
    story.append(_div(4, 12))

    story.append(Paragraph("AI OPPORTUNITY SCORE", sec_s))
    story.append(Paragraph(
        f'<font color="{score_bar_color}" size="30"><b>{ai_score}</b></font>'
        f'<font color="{T["text_muted"]}" size="14"> / 100</font>',
        _ps("SN", fontSize=30, fontName=FONT_BOLD, leading=36, spaceAfter=2)))
    story.append(Paragraph(
        f'<font color="{score_bar_color}"><b>{score_label}</b></font>',
        _ps("SL", fontSize=12, textColor=_hex(score_bar_color),
            fontName="Helvetica-Bold", spaceAfter=8)))
    story.append(_hbar(ai_score, 100, score_bar_color, width=W * 0.7, height=10))
    story.append(Spacer(1, 16))
    story.append(_kpi_row([
        ("Confirmed Flows", str(flow_count), T["green"]),
        ("Quick Wins",      str(qw_count),   T["green"]),
        ("Industry",        industry or "—", T["text_primary"]),
        ("Timeline",        timeline or "—", T["text_primary"]),
    ]))
    story.append(PageBreak())

    # ── PAGE 2: DISCOVERY PROFILE ────────────────────────────────

    story.append(Paragraph("DISCOVERY PROFILE", sec_s))
    story.append(Paragraph("Business Context", _ps("BCH", fontSize=9,
        fontName="Helvetica-Bold", textColor=_hex(T["text_secondary"]), spaceAfter=4)))
    story.append(_info_table([
        ("Company",        company),
        ("Industry",       industry),
        ("Regions Served", regions),
        ("Channels",       channels),
        ("Primary Goal",   primary_goal),
        ("Timeline",       timeline),
    ]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Systems of Record", _ps("SRH", fontSize=9,
        fontName="Helvetica-Bold", textColor=_hex(T["text_secondary"]), spaceAfter=4)))
    story.append(_info_table([
        ("CRM",            crm or "—"),
        ("Contact Center", cc_platform or "—"),
    ]))
    story.append(Spacer(1, 10))

    conf_color = T["green"] if conf_pct >= 80 else T["accent"] if conf_pct >= 50 else T["amber"]
    story.append(Paragraph("Profile Completeness", _ps("PCH", fontSize=9,
        fontName="Helvetica-Bold", textColor=_hex(T["text_secondary"]), spaceAfter=4)))
    story.append(_hbar(conf_pct, 100, conf_color, width=W * 0.5, height=8))
    story.append(Paragraph(f"{conf_pct}% complete",
        _ps("CP", fontSize=8, textColor=_hex(T["text_muted"]), spaceAfter=0)))

    # ── BUSINESS CASE (same page, continued) ─────────────────────

    if bc.get("has_data"):
        story.append(_div(12, 12))
        story.append(Paragraph("CX BUSINESS CASE", sec_s))

        cur_agents  = bc.get("current_agents", 0)
        prop_agents = bc.get("proposed_agents", 0)
        auto_pct    = bc.get("automation_pct", 0)
        annual_sav  = bc.get("annual_savings", 0)
        impl_cost   = bc.get("impl_cost", 0)
        payback     = bc.get("payback_months")
        npv_3       = bc.get("npv_3yr", 0)
        npv_5       = bc.get("npv_5yr", 0)
        c_sav       = bc.get("conservative_savings", 0)
        o_sav       = bc.get("optimistic_savings", annual_sav * 1.3)
        payback_str = f"{payback:.1f} months" if payback else "N/A"

        # Environment comparison (two-column)
        def _env_col(title, sub_rows, total, cpc, col_color):
            cw     = W / 2 - 12
            trows  = [[
                Paragraph(f'<font color="{col_color}"><b>{title}</b></font>',
                    _ps("ET" + title[:3], fontSize=9, fontName="Helvetica-Bold",
                        textColor=_hex(col_color), spaceAfter=0, leading=12)),
                Paragraph("", label_s),
            ]]
            for lbl, val in sub_rows:
                trows.append([
                    Paragraph(lbl, _ps("EL", fontSize=8,
                        textColor=_hex(T["text_muted"]), spaceAfter=0, leading=11)),
                    Paragraph(val, _ps("EV", fontSize=9,
                        textColor=_hex(T["text_primary"]), spaceAfter=0, leading=12)),
                ])
            trows.append([Paragraph("", label_s), Paragraph("", label_s)])
            trows.append([
                Paragraph("Total CX Cost", _ps("ETL", fontSize=8, fontName="Helvetica-Bold",
                    textColor=_hex(T["text_muted"]), spaceAfter=0, leading=11)),
                Paragraph(f'<font color="{col_color}" size="11"><b>{total}</b></font>',
                    _ps("ETV", fontSize=11, spaceAfter=0, leading=14)),
            ])
            trows.append([
                Paragraph("Cost / Contact", _ps("ECL", fontSize=8,
                    textColor=_hex(T["text_muted"]), spaceAfter=0, leading=11)),
                Paragraph(cpc, _ps("ECV", fontSize=9,
                    textColor=_hex(T["text_secondary"]), spaceAfter=0, leading=12)),
            ])
            inner = Table(trows, colWidths=[cw * 0.48, cw * 0.52])
            inner.setStyle(TableStyle([
                ("TOPPADDING",    (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("LINEABOVE",     (0, -2), (1, -2), 0.5, _hex(T["border"])),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [_hex(T["surface"]), _hex(T["surface_alt"])]),
            ]))
            return inner

        cur_col  = _env_col("Current Environment",
            [("Agents", str(cur_agents))],
            _fmt(bc.get("current_total", 0)), _fmt(bc.get("current_cpc", 0), 2), T["text_muted"])
        prop_col = _env_col("Proposed Environment",
            [("Agents", str(prop_agents)), ("Self-service", _fmt_pct(auto_pct))],
            _fmt(bc.get("proposed_total", 0)), _fmt(bc.get("proposed_cpc", 0), 2), T["accent"])

        env_tbl = Table([[cur_col, prop_col]], colWidths=[W / 2 - 6, W / 2 - 6])
        env_tbl.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(env_tbl)
        story.append(Spacer(1, 10))
        story.append(_info_table([
            ("Annual Savings",  _fmt(annual_sav)),
            ("Implementation", f"({_fmt(impl_cost)})"),
            ("Payback Period",  payback_str),
            ("3-Year NPV",      _fmt(npv_3)),
            ("5-Year NPV",      _fmt(npv_5)),
            ("Agent Reduction", f"{cur_agents} to {prop_agents}"),
            ("Automation Rate", _fmt_pct(auto_pct)),
        ]))
        story.append(Spacer(1, 10))

        # Scenario bars
        story.append(Paragraph("Scenario Range — Annual Savings",
            _ps("SR", fontSize=8, fontName="Helvetica-Bold",
                textColor=_hex(T["text_secondary"]), spaceAfter=6)))
        max_s = max(o_sav, 1)
        bar_w = W * 0.55
        for lbl, val, bar_color in [
            ("Conservative", c_sav,     T["amber"]),
            ("Base Case",    annual_sav, T["accent"]),
            ("Optimistic",   o_sav,      T["green"]),
        ]:
            row = Table([[
                Paragraph(lbl, _ps("SL2", fontSize=8, textColor=_hex(T["text_secondary"]))),
                _hbar(val, max_s, bar_color, width=bar_w, height=8),
                Paragraph(_fmt(val), _ps("SV", fontSize=8, fontName="Helvetica-Bold",
                    textColor=_hex(bar_color))),
            ]], colWidths=[1.0 * inch, bar_w, 0.85 * inch])
            row.setStyle(TableStyle([
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
                ("TOPPADDING",    (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            story.append(row)

    story.append(PageBreak())

    # ── PAGE 3: RISK ASSESSMENT (new — was missing) ───────────────

    if risk.get("has_data"):
        story.append(Paragraph("IMPLEMENTATION RISK ASSESSMENT", sec_s))

        risk_score = risk.get("program_score", 0)
        risk_label = risk.get("program_label", "")
        risk_color = risk.get("program_color", T["amber"])
        risk_icon  = risk.get("program_icon", "")

        story.append(Paragraph(
            f'<font color="{risk_color}" size="28"><b>{risk_score}</b></font>'
            f'<font color="{T["text_muted"]}" size="12">  / 100  —  {risk_icon} {risk_label}</font>',
            _ps("RS", fontSize=28, leading=34, spaceAfter=6)))
        story.append(_hbar(risk_score, 100, risk_color, width=W * 0.6, height=8))
        story.append(Spacer(1, 12))

        # Dimension bars
        dims = risk.get("dimension_scores", {})
        DIM_LABELS = {
            "integration":      "Integration Complexity",
            "timeline":         "Timeline Pressure",
            "automation":       "Automation Baseline",
            "volume":           "Contact Volume",
            "flow_complexity":  "Flow Complexity",
        }
        RISK_COLORS = {
            "Low":      T["green"],
            "Moderate": T["amber"],
            "High":     "#f87171",
            "Critical": T["red"],
        }
        if dims:
            story.append(Paragraph("Risk Dimensions", _ps("RDH", fontSize=9,
                fontName="Helvetica-Bold", textColor=_hex(T["text_secondary"]), spaceAfter=6)))
            for key, dim in dims.items():
                dim_label = DIM_LABELS.get(key, key)
                dim_score = dim.get("score", 0) if isinstance(dim, dict) else 0
                dim_level = dim.get("label", "") if isinstance(dim, dict) else ""
                dim_color = RISK_COLORS.get(dim_level, T["amber"])
                dim_row = Table([[
                    Paragraph(dim_label, _ps("DL", fontSize=8, textColor=_hex(T["text_secondary"]))),
                    _hbar(dim_score, 100, dim_color, width=W * 0.45, height=7),
                    Paragraph(dim_level, _ps("DV", fontSize=8, fontName="Helvetica-Bold",
                        textColor=_hex(dim_color))),
                ]], colWidths=[1.6 * inch, W * 0.45, 0.9 * inch])
                dim_row.setStyle(TableStyle([
                    ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                    ("TOPPADDING",    (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]))
                story.append(dim_row)
            story.append(Spacer(1, 10))

        # Top risk flows
        top_risks = risk.get("top_risk_flows", [])
        if top_risks:
            story.append(Paragraph("Highest Risk Use Cases", _ps("TRH", fontSize=9,
                fontName="Helvetica-Bold", textColor=_hex(T["text_secondary"]), spaceAfter=4)))
            rows = [[Paragraph("Score", th_s), Paragraph("Use Case", th_s), Paragraph("Key Factor", th_s)]]
            for f in top_risks[:5]:
                factors = f.get("factors", [])
                rows.append([
                    Paragraph(str(f.get("risk_score", "")), tc_s),
                    Paragraph(f.get("flow_name", ""), tc_s),
                    Paragraph(factors[0] if factors else "", td_s),
                ])
            rt = Table(rows, colWidths=[0.6 * inch, 2.0 * inch, W - 2.6 * inch])
            rt.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), _hex(T["surface_alt"])),
                ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE",      (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [_hex(T["surface"]), _hex(T["surface_alt"])]),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING",   (0, 0), (-1, -1), 6),
                ("GRID",          (0, 0), (-1, -1), 0.25, _hex(T["border"])),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(rt)
            story.append(Spacer(1, 10))

        # Mitigations
        mitigations = risk.get("mitigations", [])
        if mitigations:
            story.append(Paragraph("Recommended Mitigations", _ps("MH", fontSize=9,
                fontName="Helvetica-Bold", textColor=_hex(T["text_secondary"]), spaceAfter=4)))
            for m in mitigations:
                text = m if isinstance(m, str) else m.get("description", str(m))
                story.append(Paragraph(f"->  {text}", bul_s))

        story.append(PageBreak())

    # ── PAGE 4: ROADMAP ──────────────────────────────────────────

    story.append(Paragraph("RECOMMENDED ROADMAP", sec_s))

    roadmap_sections = [
        ("[NOW] Quick Wins",            quick_wins,  T["green"]),
        ("[NEXT] AI-Assisted",          walk_flows,  T["amber"]),
        ("[LATER] Foundation First",    crawl_flows, T["text_muted"]),
    ]
    has_roadmap = any(flows for _, flows, _ in roadmap_sections)
    if not has_roadmap:
        story.append(Paragraph("Run the AI Assessment to generate the roadmap.",
            _ps("NR", fontSize=9, textColor=_hex(T["text_muted"]), spaceAfter=8)))
    else:
        for phase_label, flows, color in roadmap_sections:
            if not flows:
                continue
            story.append(Paragraph(phase_label, _ps(
                "PL" + phase_label[:4], fontSize=9, fontName="Helvetica-Bold",
                textColor=_hex(color), spaceBefore=10, spaceAfter=4)))
            t = _flow_table(flows, color)
            if t:
                story.append(t)

    story.append(PageBreak())

    # ── PAGE 5: CONFIRMED FLOWS + VENDORS ────────────────────────

    story.append(Paragraph("CONFIRMED INTERACTION FLOWS", sec_s))
    story.append(Paragraph(f"{flow_count} flows confirmed.",
        _ps("FC", fontSize=9, textColor=_hex(T["text_secondary"]), spaceAfter=8)))

    if flow_cards:
        src_map = {"inferred": "AI Pre-suggested", "discovered": "From Conversation",
                   "user_added": "Added Manually"}
        rows = [[Paragraph("Flow Name", th_s), Paragraph("Category", th_s),
                 Paragraph("AI Score", th_s), Paragraph("Phase", th_s),
                 Paragraph("Auto %", th_s), Paragraph("Source", th_s)]]
        for c in flow_cards:
            rows.append([
                Paragraph(c.get("flow_name", ""), tc_s),
                Paragraph(c.get("category", ""), td_s),
                Paragraph(str(c.get("ai_score", 0)), tc_s),
                Paragraph(c.get("crawl_walk_run", ""), tc_s),
                Paragraph(f"{c.get('automation_potential', 0)}%", td_s),
                Paragraph(src_map.get(c.get("source", ""), "Detected"), td_s),
            ])
        t = Table(rows, colWidths=[2.0 * inch, 1.1 * inch, 0.65 * inch,
                                    0.65 * inch, 0.55 * inch, 1.15 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), _hex(T["surface_alt"])),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [_hex(T["surface"]), _hex(T["surface_alt"])]),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("GRID",          (0, 0), (-1, -1), 0.25, _hex(T["border"])),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(t)

    if vendors:
        story.append(_div(12, 8))
        story.append(Paragraph("RECOMMENDED VENDORS", sec_s))
        story.append(Paragraph(
            "Top vendors matched to your confirmed flows, industry, and platform.",
            _ps("VD", fontSize=9, textColor=_hex(T["text_secondary"]), spaceAfter=8)))
        v_rows = [[
            Paragraph("Rank", th_s), Paragraph("Vendor", th_s),
            Paragraph("Tier", th_s), Paragraph("Fit Score", th_s),
            Paragraph("Why This Fits", th_s),
        ]]
        for v in vendors:
            reasons_text = " · ".join(v.get("fit_reasons", [])[:2])
            feat_label   = (" [" + v.get("feat_label", "Featured") + "]"
                            if v.get("featured") else "")
            v_rows.append([
                Paragraph(f"#{v['rank']}", tc_s),
                Paragraph(v["name"] + feat_label, tc_s),
                Paragraph(v.get("tier", "").replace("-", " ").title(), td_s),
                Paragraph(str(v["fit_score"]) + "/100", tc_s),
                Paragraph(reasons_text, td_s),
            ])
        vt = Table(v_rows, colWidths=[0.45 * inch, 1.3 * inch, 0.9 * inch,
                                       0.65 * inch, W - 3.3 * inch])
        vt.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), _hex(T["surface_alt"])),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [_hex(T["surface"]), _hex(T["surface_alt"])]),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("GRID",          (0, 0), (-1, -1), 0.25, _hex(T["border"])),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(vt)

    story.append(PageBreak())

    # ── PAGE 6: NEXT STEPS + FOOTER ─────────────────────────────

    story.append(Paragraph("RECOMMENDED NEXT STEPS", sec_s))
    if next_steps:
        for i, step in enumerate(next_steps, 1):
            if isinstance(step, str):
                text = step
            elif isinstance(step, dict):
                title = step.get("title", "")
                body  = step.get("body", step.get("description", ""))
                text  = f"{title} — {body}" if title and body else title or body
            else:
                text = str(step)
            story.append(Paragraph(f"{i}.   {text}", bul_s))
    else:
        story.append(Paragraph("No next steps generated.",
            _ps("NS", fontSize=9, textColor=_hex(T["text_muted"]), spaceAfter=8)))

    story.append(Spacer(1, 20))
    story.append(_div(4, 8))
    story.append(Paragraph(
        f"Generated by AchieveCX AI Consultant - {generated} - "
        f"Prepared for {for_name} - Confidential", foot_s))

    doc.build(story)
    return buffer.getvalue()