import streamlit as st
from bs4 import BeautifulSoup
from collections import Counter
import re

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

def highlight_keywords(text, gt_keywords, ir_keywords):
    if not text:
        return ""
    all_keywords = sorted(set(gt_keywords + ir_keywords), key=len, reverse=True)
    def replacer(match):
        word = match.group(0)
        lw = word.lower()
        if lw in gt_keywords:
            return f'<mark style="background-color: yellow;">{word}</mark>'
        elif lw in ir_keywords:
            return f'<mark style="background-color: #ccffcc;">{word}</mark>'
        return word
    pattern = re.compile('|'.join(re.escape(k) for k in all_keywords), re.IGNORECASE)
    return pattern.sub(replacer, text)

def process_html_to_html_output(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    profile_data = {}
    tables = soup.find_all("table", class_="table")
    current_cu, current_was, current_pcs, cu_blocks = {}, [], [], []

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

    file_gt_keywords = Counter()
    file_ir_keywords = Counter()

    html_result = f"<h3>NOSS PROFILE</h3>"
    for key in ["SECTION", "GROUP", "AREA", "NOSS CODE", "NOSS TITLE", "NOSS LEVEL"]:
        html_result += f"<p><b>{key}:</b> {profile_data.get(key, '')}</p>"

    html_result += "<hr>"

    for i, cu in enumerate(cu_blocks, 1):
        html_result += f"<h4>CU #{i}</h4>"
        gt_scores = {}
        ir_scores = {}

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

        html_result += f"<p><b>CU CODE:</b> {cu.get('CU CODE', '')}</p>"
        html_result += f"<p><b>CU TITLE:</b> {highlight_keywords(cu.get('CU TITLE', ''), green_keywords, ir_keywords)}</p>"
        html_result += f"<p><b>CU DESCRIPTOR:</b> {highlight_keywords(cu.get('CU DESCRIPTOR', ''), green_keywords, ir_keywords)}</p>"
        html_result += f"<p><b>WORK ACTIVITY:</b> {highlight_keywords(cu.get('WORK ACTIVITY', ''), green_keywords, ir_keywords)}</p>"
        html_result += f"<p><b>PERFORMANCE CRITERIA:</b> {highlight_keywords(cu.get('PERFORMANCE CRITERIA', ''), green_keywords, ir_keywords)}</p>"
        html_result += f"<p><b>TOTAL MATCH:</b> Green Tech {total_gt}%, IR {total_ir}%</p><hr>"

    html_result += "<h3>Matched Green Technology Keywords</h3>"
    if file_gt_keywords:
        html_result += "<ul>" + "".join([f"<li>{kw} ({count})</li>" for kw, count in sorted(file_gt_keywords.items(), key=lambda x: (-x[1], x[0]))]) + "</ul>"
    else:
        html_result += "<p>No Green Technology keywords matched.</p>"

    html_result += "<h3>Matched Industrial Revolution Keywords</h3>"
    if file_ir_keywords:
        html_result += "<ul>" + "".join([f"<li>{kw} ({count})</li>" for kw, count in sorted(file_ir_keywords.items(), key=lambda x: (-x[1], x[0]))]) + "</ul>"
    else:
        html_result += "<p>No Industrial Revolution keywords matched.</p>"

    return html_result

# === Streamlit UI ===
st.title("NOSS Analyzer with HTML Preview")
uploaded_file = st.file_uploader("Upload NOSS HTML File", type="html")

if uploaded_file:
    html_content = uploaded_file.read().decode("utf-8")
    result_html = process_html_to_html_output(html_content)
    st.markdown(result_html, unsafe_allow_html=True)
