import streamlit as st
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from collections import Counter
import re
from io import BytesIO
import base64

# === Keyword Lists ===
green_keywords = [kw.lower() for kw in [
    "Emissions reduction", "Low carbon", "Pollution control", "Waste minimization", "Clean energy",
    "Environmental footprint", "Resource conservation", "Ecosystem restoration", "Biodiversity", "Habitat preservation",
    "Land rehabilitation", "Sustainable agriculture", "Reforestation", "Conservation practices", "Energy efficiency",
    "Water efficiency", "Sustainable materials", "Circular economy", "Recycling", "Green manufacturing", "Eco-design",
    "Climate resilience", "Greenhouse gas mitigation", "Carbon neutrality", "Climate adaptation", "Renewable energy",
    "Low-emission technologies", "Disaster risk reduction", "Environmental standards", "Green certification", "ESG",
    "Sustainable policy", "Green regulations", "Environmental compliance", "Strategic environmental planning"
]]

ir_keywords = [kw.lower() for kw in [
    "Artificial Intelligence (AI)", "Internet of Things (IoT)", "Additive Manufacturing (3D Printing)", "Big Data Analytics",
    "Cloud Computing", "Smart Technology", "Digital Twin", "Horizontal Integration", "Vertical Integration", "Cyber-Physical Systems",
    "Autonomous Systems", "Self-adapting Systems", "Interconnected Networks", "Digital Ecosystems", "Cybersecurity", "Communication Technology",
    "Data Management", "Augmented Reality (AR)", "Virtual Reality (VR)", "Simulation Systems", "Advanced Materials", "Digital Literacy",
    "Talent Retention", "Reskilling and Upskilling", "Human-Machine Collaboration", "STEM Education", "Knowledge Workers", "Future Workforce",
    "Policy Framework", "Innovation Incentives", "SME Inclusion", "Strategic Oversight", "Regulatory Compliance", "Multi-stakeholder Collaboration",
    "Digital Economy Strategy", "Robotics", "Smart Factories", "Automation", "Industry 4.0 Machines", "Predictive Maintenance",
    "Flexible Manufacturing Systems", "Engineering Design", "R&D Intensity", "Prototyping", "Innovative Materials", "Product Lifecycle Innovation",
    "IoT Infrastructure", "Smart Logistics", "Digital Supply Chains", "Cloud Integration", "Intelligent Monitoring", "Energy Efficiency",
    "Waste Reduction", "Circular Economy", "Resource Optimization", "Technical Skills", "Industrial Training", "Competency-Based Learning",
    "Technological Adaptability", "Job Transformation"
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
        "PERFORMANCE CRITERIA": "PERFORMANCE<br/>CRITERIA"
    }
    return Paragraph(label_map.get(name, name), wrap_style)

def process_html_to_pdf(html_content):
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

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    flowables = [Paragraph("<b>NOSS PROFILE</b>", styleH), Spacer(1, 0.3 * cm)]

    for k in ["SECTION", "GROUP", "AREA", "NOSS CODE", "NOSS TITLE", "NOSS LEVEL"]:
        flowables.append(Paragraph(f"<b>{k}:</b> {profile_data.get(k, '')}", styleN))

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

        flowables.append(Paragraph(f"<b>CU #{i}</b>", styleH))
        flowables.append(Spacer(1, 0.2 * cm))
        flowables.append(Table([
            [label("CU CODE"), Paragraph(cu.get("CU CODE", ""), wrap_style), "", ""],
            [label("CU TITLE"), Paragraph(cu_title, wrap_style), f"{gt_scores['CU TITLE']}%", f"{ir_scores['CU TITLE']}%"],
            [label("CU DESCRIPTOR"), Paragraph(cu_desc, wrap_style), f"{gt_scores['CU DESCRIPTOR']}%", f"{ir_scores['CU DESCRIPTOR']}%"]
        ], colWidths=[3.5 * cm, 11 * cm, 1.25 * cm, 1.25 * cm]))

        flowables.append(PageBreak())

    flowables.append(Paragraph("<b>Summary of CU Matching</b>", styleH))
    table = Table(summary_data, colWidths=[4*cm, 6*cm, 6*cm])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
    ]))
    flowables.append(table)

    flowables.append(PageBreak())
    flowables.append(Paragraph("<b>Matched Green Technology Keywords</b>", styleH))
    if file_gt_keywords:
        for kw, count in sorted(file_gt_keywords.items(), key=lambda x: -x[1]):
            flowables.append(Paragraph(f"• {kw} ({count})", styleN))
    else:
        flowables.append(Paragraph("No matches found.", styleN))

    flowables.append(Spacer(1, 0.3*cm))
    flowables.append(Paragraph("<b>Matched Industrial Revolution Keywords</b>", styleH))
    if file_ir_keywords:
        for kw, count in sorted(file_ir_keywords.items(), key=lambda x: -x[1]):
            flowables.append(Paragraph(f"• {kw} ({count})", styleN))
    else:
        flowables.append(Paragraph("No matches found.", styleN))

    doc.build(flowables)
    buffer.seek(0)
    return buffer

# === Streamlit UI ===
st.set_page_config(page_title="NOSS CU Analyzer", layout="centered")
st.title("🔍 NOSS CU Analyzer")
uploaded_file = st.file_uploader("Upload your HTML file", type="html")

if uploaded_file:
    with st.spinner("Analyzing... generating PDF..."):
        html_content = uploaded_file.read().decode("utf-8")
        pdf_buffer = process_html_to_pdf(html_content)
        base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')

        st.markdown("### 🔽 Download Result")
        st.download_button("📄 Download PDF", data=pdf_buffer, file_name=uploaded_file.name.replace(".html", ".pdf"))

        st.markdown("### 🔍 Preview")
        st.components.v1.html(f'''
            <iframe width="100%" height="600" src="data:application/pdf;base64,{base64_pdf}" type="application/pdf" frameborder="0"></iframe>
        ''', height=600)
