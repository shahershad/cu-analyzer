import streamlit as st
import tempfile
import os
from pathlib import Path
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from collections import Counter
import re
import base64

# === Keyword lists ===
green_keywords = [kw.lower() for kw in [
    "emissions reduction", "low carbon", "pollution control", "waste minimization", "clean energy",
    "environmental footprint", "resource conservation", "ecosystem restoration", "biodiversity", "habitat preservation",
    "land rehabilitation", "sustainable agriculture", "reforestation", "conservation practices", "energy efficiency",
    "water efficiency", "sustainable materials", "circular economy", "recycling", "green manufacturing", "eco-design",
    "climate resilience", "greenhouse gas mitigation", "carbon neutrality", "climate adaptation", "renewable energy",
    "low-emission technologies", "disaster risk reduction", "environmental standards", "green certification", "esg",
    "sustainable policy", "green regulations", "environmental compliance", "strategic environmental planning"
]]

ir_keywords = [kw.lower() for kw in [
    "artificial intelligence", "internet of things", "3d printing", "big data analytics", "cloud computing", "smart technology",
    "digital twin", "horizontal integration", "vertical integration", "cyber-physical systems", "autonomous systems",
    "self-adapting systems", "interconnected networks", "digital ecosystems", "cybersecurity", "communication technology",
    "data management", "augmented reality", "virtual reality", "simulation systems", "advanced materials", "digital literacy",
    "talent retention", "reskilling and upskilling", "human-machine collaboration", "stem education", "knowledge workers",
    "future workforce", "policy framework", "innovation incentives", "sme inclusion", "strategic oversight",
    "regulatory compliance", "multi-stakeholder collaboration", "digital economy strategy", "robotics", "smart factories",
    "automation", "industry 4.0 machines", "predictive maintenance", "flexible manufacturing systems", "engineering design",
    "r&d intensity", "prototyping", "innovative materials", "product lifecycle innovation", "iot infrastructure",
    "smart logistics", "digital supply chains", "cloud integration", "intelligent monitoring", "waste reduction",
    "resource optimization", "technical skills", "industrial training", "competency-based learning", "technological adaptability",
    "job transformation"
]]

weights = {
    "CU TITLE": 5,
    "CU DESCRIPTOR": 20,
    "WORK ACTIVITY": 30,
    "PERFORMANCE CRITERIA": 45
}

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleH = styles['Heading2']
wrap_style = ParagraphStyle(name='WrapStyle', parent=styleN, alignment=TA_JUSTIFY, spaceAfter=6)

def highlight_keywords(text, gt_keywords, ir_keywords):
    all_keywords = sorted(set(gt_keywords + ir_keywords), key=len, reverse=True)
    def replacer(match):
        word = match.group(0)
        lw = word.lower()
        if lw in gt_keywords:
            return f'<font backcolor="yellow">{word}</font>'
        elif lw in ir_keywords:
            return f'<font backcolor="#ccffcc">{word}</font>'
        return word
    pattern = re.compile('|'.join(re.escape(k) for k in all_keywords), re.IGNORECASE)
    return pattern.sub(replacer, text)

def label(name):
    label_map = {
        "CU CODE": "CU CODE",
        "CU TITLE": "CU TITLE",
        "CU DESCRIPTOR": "CU<br/>DESCRIPTOR",
        "WORK ACTIVITY": "WORK<br/>ACTIVITIES",
        "PERFORMANCE CRITERIA": "PERFORMANCE<br/>CRITERIA",
        "TOTAL MATCH (%)": "TOTAL<br/>MATCH (%)"
    }
    return Paragraph(label_map.get(name, name), wrap_style)

def process_html_to_pdf(html_content, output_path):
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table", class_="table")
    profile_data, cu_blocks = {}, []
    current_cu, current_was, current_pcs = {}, [], []

    file_gt_keywords = Counter()
    file_ir_keywords = Counter()

    profile_table = soup.find("table", class_="table")
    if profile_table:
        for row in profile_table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) == 2:
                profile_data[cells[0].get_text(strip=True)] = cells[1].get_text(" ", strip=True)

    for table in tables:
        if "CU CODE" in table.text and "CU TITLE" in table.text:
            if current_cu:
                cu_blocks.append({
                    **current_cu,
                    "WORK ACTIVITY": " - ".join(current_was),
                    "PERFORMANCE CRITERIA": " - ".join(current_pcs),
                })
                current_was, current_pcs = [], []
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True)
                    val = cells[1].get_text(" ", strip=True)
                    if key in ["CU CODE", "CU TITLE", "CU DESCRIPTOR"]:
                        current_cu[key] = val
        elif "WORK ACTIVITIES" in table.text and "PERFORMANCE CRITERIA" in table.text:
            for row in table.find_all("tr")[1:]:
                cells = row.find_all("td")
                if len(cells) == 2:
                    current_was.append(cells[0].get_text(" ", strip=True))
                    current_pcs.append(cells[1].get_text(" ", strip=True))
    if current_cu:
        cu_blocks.append({
            **current_cu,
            "WORK ACTIVITY": " - ".join(current_was),
            "PERFORMANCE CRITERIA": " - ".join(current_pcs),
        })

    flowables = []
    flowables.append(Paragraph("<b>NOSS PROFILE</b>", styleH))
    flowables.append(Spacer(1, 0.3 * cm))
    for label_text in ["SECTION", "GROUP", "AREA", "NOSS CODE", "NOSS TITLE", "NOSS LEVEL"]:
        flowables.append(Paragraph(f"<b>{label_text}:</b> {profile_data.get(label_text, '')}", styleN))
    flowables.append(PageBreak())

    summary_data = [["CU", "Green Technology", "Industrial Revolution"]]

    for i, cu in enumerate(cu_blocks, 1):
        gt_scores, ir_scores = {}, {}
        for k in weights:
            cu_text = cu.get(k, "").lower()

            for kw in green_keywords:
                count = cu_text.count(kw)
                if count > 0:
                    file_gt_keywords[kw] += count
            for kw in ir_keywords:
                count = cu_text.count(kw)
                if count > 0:
                    file_ir_keywords[kw] += count

            gt_scores[k] = weights[k] if any(kw in cu_text for kw in green_keywords) else 0
            ir_scores[k] = weights[k] if any(kw in cu_text for kw in ir_keywords) else 0

        total_gt = sum(gt_scores.values())
        total_ir = sum(ir_scores.values())

        summary_data.append([
            f"CU #{i}",
            f"✅ {total_gt}%" if total_gt > 0 else "❌ 0%",
            f"✅ {total_ir}%" if total_ir > 0 else "❌ 0%"
        ])

        cu_title = highlight_keywords(cu.get("CU TITLE", ""), green_keywords, ir_keywords)
        cu_desc = highlight_keywords(cu.get("CU DESCRIPTOR", ""), green_keywords, ir_keywords)
        cu_wa = highlight_keywords(cu.get("WORK ACTIVITY", ""), green_keywords, ir_keywords)
        cu_pc = highlight_keywords(cu.get("PERFORMANCE CRITERIA", ""), green_keywords, ir_keywords)

        flowables.append(Paragraph(f"<b>CU #{i}</b>", styleH))
        flowables.append(Spacer(1, 0.2 * cm))

        table_top = Table([
            [label("CU CODE"), Paragraph(cu.get("CU CODE", ""), wrap_style), "", ""],
            [label("CU TITLE"), Paragraph(cu_title, wrap_style), f"{gt_scores['CU TITLE']}%", f"{ir_scores['CU TITLE']}%"],
            [label("CU DESCRIPTOR"), Paragraph(cu_desc, wrap_style), f"{gt_scores['CU DESCRIPTOR']}%", f"{ir_scores['CU DESCRIPTOR']}%"]
        ], colWidths=[3.5 * cm, 11 * cm, 1.25 * cm, 1.25 * cm])
        table_top.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('BOX', (0, 0), (-1, -1), 0.6, colors.black),
        ]))
        flowables.append(table_top)

        # Work Activities Table
        wa_data = []
        for j, item in enumerate(cu_wa.split(" - ")):
            wa_data.append([
                label("WORK ACTIVITY") if j == 0 else "",
                Paragraph(f"• {item.strip()}", wrap_style),
                f"{gt_scores['WORK ACTIVITY']}%" if j == 0 else "",
                f"{ir_scores['WORK ACTIVITY']}%" if j == 0 else ""
            ])
        table_wa = Table(wa_data, colWidths=[3.5 * cm, 11 * cm, 1.25 * cm, 1.25 * cm])
        table_wa.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('BOX', (0, 0), (-1, -1), 0.6, colors.black),
        ]))
        flowables.append(table_wa)

        # Performance Criteria Table
        pc_data = []
        for j, item in enumerate(cu_pc.split(" - ")):
            pc_data.append([
                label("PERFORMANCE CRITERIA") if j == 0 else "",
                Paragraph(f"• {item.strip()}", wrap_style),
                f"{gt_scores['PERFORMANCE CRITERIA']}%" if j == 0 else "",
                f"{ir_scores['PERFORMANCE CRITERIA']}%" if j == 0 else ""
            ])
        table_pc = Table(pc_data, colWidths=[3.5 * cm, 11 * cm, 1.25 * cm, 1.25 * cm])
        table_pc.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('BOX', (0, 0), (-1, -1), 0.6, colors.black),
        ]))
        flowables.append(table_pc)
        flowables.append(PageBreak())

    flowables.append(Paragraph("<b>Summary of CU Matching</b>", styleH))
    flowables.append(Spacer(1, 0.3 * cm))
    summary_table = Table(summary_data, colWidths=[4 * cm, 6 * cm, 6 * cm])
    summary_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.6, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    flowables.append(summary_table)

    flowables.append(PageBreak())
    flowables.append(Paragraph("<b>Matched Green Technology Keywords</b>", styleH))
    for kw, count in sorted(file_gt_keywords.items(), key=lambda x: (-x[1], x[0])):
        flowables.append(Paragraph(f"• {kw} ({count})", styleN))

    flowables.append(Spacer(1, 0.3 * cm))
    flowables.append(Paragraph("<b>Matched Industrial Revolution Keywords</b>", styleH))
    for kw, count in sorted(file_ir_keywords.items(), key=lambda x: (-x[1], x[0])):
        flowables.append(Paragraph(f"• {kw} ({count})", styleN))

    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    doc.build(flowables)
    return output_path

# === Streamlit UI ===
st.set_page_config(page_title="CU Analyzer", layout="wide")
st.title("📄 CU Keyword Analyzer & PDF Generator")
st.markdown("Upload your `.html` NOSS file to generate a full CU analysis report.")

uploaded_file = st.file_uploader("Upload NOSS HTML file", type=["html"])

if uploaded_file:
    filename = Path(uploaded_file.name).stem
    html_text = uploaded_file.read().decode("utf-8")
    output_path = os.path.join(tempfile.gettempdir(), f"{filename}.pdf")
    process_html_to_pdf(html_text, output_path)

    st.success(f"✅ PDF generated as: {filename}.pdf")

    with open(output_path, "rb") as f:
        st.download_button("📥 Download PDF", f, file_name=f"{filename}.pdf", mime="application/pdf")

    with open(output_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
        st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="1000"></iframe>', unsafe_allow_html=True)
