from pathlib import Path
import textwrap

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from PIL import Image, ImageDraw, ImageFont


SOURCE = Path(r"C:\Users\gerla\Downloads\MIS-FINAL-1-3.docx")
OUTPUT = Path(r"C:\Users\gerla\Downloads\MIS-FINAL-1-3-Waterfall-and-Objective-Results.docx")
ASSET_DIR = Path(r"C:\Users\gerla\revision\rexis\doc_assets")
DIAGRAM_DIR = ASSET_DIR / "diagrams"
SCREENSHOT_DIR = ASSET_DIR / "screenshots"
DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)


def font(size=30, bold=False):
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibrib.ttf" if bold else r"C:\Windows\Fonts\calibri.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def draw_wrapped(draw, text, box, fnt, fill=(20, 30, 45), align="center", line_gap=6):
    x1, y1, x2, y2 = box
    width = x2 - x1 - 18
    words = text.split()
    lines, line = [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if draw.textbbox((0, 0), trial, font=fnt)[2] <= width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    total_h = sum(draw.textbbox((0, 0), ln, font=fnt)[3] for ln in lines) + line_gap * (len(lines) - 1)
    y = y1 + max(4, (y2 - y1 - total_h) / 2)
    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=fnt)
        if align == "left":
            x = x1 + 10
        else:
            x = x1 + (x2 - x1 - (bbox[2] - bbox[0])) / 2
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += (bbox[3] - bbox[1]) + line_gap


def arrow(draw, start, end, fill=(55, 65, 80), width=4):
    draw.line([start, end], fill=fill, width=width)
    import math
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 14
    pts = [
        end,
        (end[0] - size * math.cos(ang - 0.45), end[1] - size * math.sin(ang - 0.45)),
        (end[0] - size * math.cos(ang + 0.45), end[1] - size * math.sin(ang + 0.45)),
    ]
    draw.polygon(pts, fill=fill)


def actor(draw, x, y, label):
    draw.ellipse((x - 18, y, x + 18, y + 36), outline=(20, 30, 45), width=4)
    draw.line((x, y + 36, x, y + 100), fill=(20, 30, 45), width=4)
    draw.line((x - 42, y + 62, x + 42, y + 62), fill=(20, 30, 45), width=4)
    draw.line((x, y + 100, x - 35, y + 155), fill=(20, 30, 45), width=4)
    draw.line((x, y + 100, x + 35, y + 155), fill=(20, 30, 45), width=4)
    draw_wrapped(draw, label, (x - 90, y + 164, x + 90, y + 224), font(24, True))


def box(draw, xy, text, fill=(242, 247, 255), outline=(70, 100, 160), fnt=None, bold=False):
    draw.rounded_rectangle(xy, radius=18, fill=fill, outline=outline, width=4)
    draw_wrapped(draw, text, xy, fnt or font(24, bold), align="center")


def create_use_case():
    img = Image.new("RGB", (1800, 1100), "white")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((370, 95, 1430, 1005), radius=35, outline=(30, 58, 138), width=5, fill=(248, 251, 255))
    d.text((645, 35), "Web-Based MIS for Research and Extension", font=font(42, True), fill=(15, 23, 42))
    actor(d, 145, 185, "Faculty")
    actor(d, 145, 690, "Administrator")
    actor(d, 1645, 185, "Research Staff")
    actor(d, 1645, 690, "Extension Staff")

    cases = {
        "Login / Logout": (760, 145, 1040, 215),
        "Submit Proposal and Upload Requirements": (455, 265, 810, 350),
        "Track Proposal Status": (455, 410, 810, 495),
        "Review Proposal": (970, 265, 1285, 350),
        "Approve / Reject with Requirements": (970, 410, 1285, 495),
        "Create Research Record": (455, 565, 810, 650),
        "Manage Extension Activity": (970, 565, 1285, 650),
        "Submit Quarterly Narrative Report": (970, 710, 1285, 795),
        "Generate Reports and Dashboard Summaries": (690, 845, 1110, 930),
        "Manage User Accounts": (455, 710, 810, 795),
    }
    for text, xy in cases.items():
        box(d, xy, text, fill=(239, 246, 255), outline=(37, 99, 235), fnt=font(23, True))

    # Connections
    lines = [
        ((235, 260), (455, 305)), ((235, 295), (455, 445)), ((235, 330), (760, 180)),
        ((235, 765), (455, 750)), ((235, 805), (970, 310)), ((235, 835), (970, 455)), ((235, 865), (690, 885)),
        ((1560, 260), (1040, 180)), ((1560, 300), (970, 310)), ((1560, 345), (455, 605)), ((1560, 385), (690, 885)),
        ((1560, 765), (970, 605)), ((1560, 805), (970, 750)), ((1560, 845), (690, 885)), ((1560, 885), (1040, 180)),
    ]
    for start, end in lines:
        d.line([start, end], fill=(96, 116, 140), width=3)
    out = DIAGRAM_DIR / "figure-3-1-use-case.png"
    img.save(out)
    return out


def create_waterfall():
    img = Image.new("RGB", (1700, 1050), "white")
    d = ImageDraw.Draw(img)
    d.text((575, 45), "Waterfall Model for MIS Development", font=font(44, True), fill=(15, 23, 42))
    steps = [
        ("Requirements\nGathering", "Identify app users, current manual problems, needed modules, reports, and uploaded documents."),
        ("System\nDesign", "Prepare workflow diagrams, database classes, role access, screens, and module structure."),
        ("Development", "Build Django modules for dashboards, proposals, research, extension, reports, and users."),
        ("Testing", "Validate forms, role access, lists, uploads, status tracking, reports, and dashboard counts."),
        ("Deployment", "Run the MIS on the target server and prepare users for actual institutional use."),
        ("Maintenance", "Fix errors, back up data, update features, and improve the system from user feedback."),
    ]
    x0, y0 = 105, 170
    w, h = 330, 115
    dx, dy = 210, 125
    prev = None
    for idx, (title, desc) in enumerate(steps):
        x = x0 + idx * dx
        y = y0 + idx * dy
        d.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=(239, 246, 255), outline=(37, 99, 235), width=4)
        d.text((x + 18, y + 15), title, font=font(28, True), fill=(15, 23, 42))
        draw_wrapped(d, desc, (x + 10, y + 55, x + w - 10, y + h - 5), font(17), align="left", line_gap=3)
        if prev:
            arrow(d, (prev[0] + w - 10, prev[1] + h - 10), (x + 10, y + 10), fill=(51, 65, 85), width=4)
        prev = (x, y)
    d.rounded_rectangle((105, 905, 1595, 990), radius=22, fill=(240, 253, 244), outline=(22, 163, 74), width=4)
    draw_wrapped(
        d,
        "The model was used because the MIS follows a clear sequence: understand the office needs first, design the system, develop the modules, test the workflow, deploy the application, and maintain it after use.",
        (130, 918, 1570, 980),
        font(25, True),
        fill=(20, 83, 45),
    )
    out = DIAGRAM_DIR / "figure-3-1-waterfall.png"
    img.save(out)
    return out


def create_sequence():
    img = Image.new("RGB", (1800, 1100), "white")
    d = ImageDraw.Draw(img)
    d.text((565, 35), "Proposal Review and Record Management Sequence", font=font(42, True), fill=(15, 23, 42))
    participants = [("Faculty", 180), ("MIS Web App", 520), ("Database", 860), ("Administrator", 1200), ("Research / Extension Staff", 1560)]
    for label, x in participants:
        box(d, (x - 130, 120, x + 130, 185), label, fill=(239, 246, 255), outline=(37, 99, 235), fnt=font(23, True))
        d.line((x, 185, x, 1030), fill=(148, 163, 184), width=3)
    messages = [
        (245, 520, 250, "1. Login and open proposal form"),
        (520, 860, 330, "2. Validate and save proposal, files, and status"),
        (520, 1200, 410, "3. Notify admin of pending proposal"),
        (1200, 520, 490, "4. Review proposal and mark approval / rejection"),
        (520, 860, 570, "5. Update status, notes, and missing requirements"),
        (520, 180, 650, "6. Show status or resubmission instructions"),
        (1200, 1560, 730, "7. Approved proposal becomes research / extension work"),
        (1560, 520, 810, "8. Encode record, activity, or quarterly report"),
        (520, 860, 890, "9. Store records and generate dashboard/report data"),
        (520, 1200, 970, "10. Display monitoring reports and summaries"),
    ]
    for x1, x2, y, text in messages:
        arrow(d, (x1, y), (x2, y), fill=(51, 65, 85), width=4)
        d.rectangle((min(x1, x2) + 18, y - 38, max(x1, x2) - 18, y - 5), fill="white")
        d.text((min(x1, x2) + 25, y - 38), text, font=font(21), fill=(15, 23, 42))
    out = DIAGRAM_DIR / "figure-3-2-sequence.png"
    img.save(out)
    return out


def create_activity():
    img = Image.new("RGB", (1600, 1500), "white")
    d = ImageDraw.Draw(img)
    d.text((430, 35), "System Activity Flow", font=font(44, True), fill=(15, 23, 42))
    nodes = [
        ("Start", (700, 120, 900, 180)),
        ("User logs in", (620, 240, 980, 320)),
        ("System checks role", (620, 390, 980, 470)),
        ("Faculty submits proposal and uploads documents", (140, 560, 560, 660)),
        ("Admin reviews proposal", (620, 560, 980, 660)),
        ("Research / Extension staff manages approved work", (1040, 560, 1480, 660)),
        ("If rejected, faculty uploads missing requirements", (140, 780, 560, 880)),
        ("If approved, create research or extension record", (620, 780, 980, 880)),
        ("Submit quarterly narrative report for extension", (1040, 780, 1480, 880)),
        ("Generate dashboards, lists, and reports", (620, 1010, 980, 1110)),
        ("Administrator monitors users and records", (620, 1210, 980, 1310)),
        ("End", (700, 1400, 900, 1460)),
    ]
    for text, xy in nodes:
        fill = (220, 252, 231) if text in ("Start", "End") else (239, 246, 255)
        outline = (22, 163, 74) if text in ("Start", "End") else (37, 99, 235)
        box(d, xy, text, fill=fill, outline=outline, fnt=font(25, True))
    arrows = [
        ((800, 180), (800, 240)), ((800, 320), (800, 390)),
        ((620, 430), (350, 560)), ((800, 470), (800, 560)), ((980, 430), (1260, 560)),
        ((350, 660), (350, 780)), ((800, 660), (800, 780)), ((1260, 660), (1260, 780)),
        ((560, 830), (620, 830)), ((800, 880), (800, 1010)), ((1260, 880), (980, 1065)),
        ((800, 1110), (800, 1210)), ((800, 1310), (800, 1400)),
    ]
    for start, end in arrows:
        arrow(d, start, end)
    out = DIAGRAM_DIR / "figure-3-3-activity.png"
    img.save(out)
    return out


def create_class():
    img = Image.new("RGB", (1800, 1300), "white")
    d = ImageDraw.Draw(img)
    d.text((590, 35), "System Class Diagram", font=font(44, True), fill=(15, 23, 42))
    classes = {
        "CustomUser": (80, 150, 455, 390, ["id", "username", "role", "employee_id", "department", "phone"], ["is_admin()", "is_faculty()", "is_research_staff()", "is_extension_staff()"]),
        "Proposal": (605, 150, 995, 430, ["title", "abstract", "full_description", "proposal_type", "faculty_author", "status", "review_notes"], ["submit()", "edit()", "review()", "resubmit()"]),
        "ProposalRequirement": (1215, 150, 1700, 390, ["proposal", "requirement_key", "label", "uploaded_file", "is_resubmitted"], ["upload_missing_requirement()"]),
        "ProposalDocumentVersion": (1215, 470, 1700, 690, ["proposal", "document", "version_number", "uploaded_by"], ["store_version_history()"]),
        "ResearchRecord": (160, 760, 600, 1055, ["proposal", "lead_researcher", "co_researchers", "status", "start_date", "end_date", "funding_source", "citation_count"], ["create_record()", "update_status()"]),
        "ExtensionRecord": (720, 760, 1165, 1055, ["proposal", "title", "extension_type", "coordinator", "team_members", "status", "beneficiary_count"], ["create_activity()", "upload_outputs()"]),
        "NarrativeReport": (1285, 760, 1700, 1015, ["extension_record", "quarter", "report_year", "narrative", "submitted_by"], ["submit_quarterly_report()"]),
    }
    for title, (x1, y1, x2, y2, attrs, methods) in classes.items():
        d.rounded_rectangle((x1, y1, x2, y2), radius=16, outline=(30, 64, 175), width=4, fill=(248, 251, 255))
        d.rectangle((x1, y1, x2, y1 + 55), fill=(219, 234, 254), outline=(30, 64, 175), width=3)
        d.text((x1 + 16, y1 + 12), title, font=font(27, True), fill=(15, 23, 42))
        d.line((x1, y1 + 55, x2, y1 + 55), fill=(30, 64, 175), width=3)
        y = y1 + 70
        for attr in attrs:
            d.text((x1 + 18, y), f"- {attr}", font=font(22), fill=(30, 41, 59))
            y += 30
        d.line((x1, y + 5, x2, y + 5), fill=(30, 64, 175), width=2)
        y += 18
        for method in methods:
            d.text((x1 + 18, y), f"+ {method}", font=font(22), fill=(30, 41, 59))
            y += 30
    rels = [
        ((455, 250), (605, 250), "1 submits many"),
        ((995, 250), (1215, 250), "1 has many"),
        ((995, 350), (1215, 575), "1 has versions"),
        ((800, 430), (380, 760), "approved research"),
        ((835, 430), (940, 760), "approved extension"),
        ((1165, 900), (1285, 890), "1 has many"),
        ((360, 390), (380, 760), "lead/co-researcher"),
        ((360, 390), (940, 760), "coordinator/team"),
    ]
    for start, end, label in rels:
        arrow(d, start, end, fill=(71, 85, 105), width=3)
        mx, my = (start[0] + end[0]) // 2, (start[1] + end[1]) // 2
        d.rectangle((mx - 90, my - 20, mx + 90, my + 12), fill="white")
        d.text((mx - 82, my - 18), label, font=font(18), fill=(30, 41, 59))
    out = DIAGRAM_DIR / "figure-3-4-class.png"
    img.save(out)
    return out


def set_run_font(run, bold=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)
    run.bold = bold
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), "Times New Roman")
    rfonts.set(qn("w:hAnsi"), "Times New Roman")


def format_paragraph(paragraph, center=False, first_line=True):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.first_line_indent = Inches(0.5) if first_line and not center else None
    for run in paragraph.runs:
        set_run_font(run, bool(run.bold))


def add_para(doc, text="", bold=False, center=False, first_line=True):
    p = doc.add_paragraph()
    r = p.add_run(text)
    set_run_font(r, bold)
    format_paragraph(p, center=center, first_line=first_line)
    return p


def add_heading(doc, text):
    add_para(doc, text, bold=True, first_line=False)


def add_chapter(doc, chapter, title):
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)
    format_paragraph(p, center=True, first_line=False)
    add_para(doc, chapter, bold=True, center=True, first_line=False)
    add_para(doc, title, bold=True, center=True, first_line=False)
    add_para(doc, "", first_line=False)


def add_figure(doc, image_path, caption, width=6.4):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(image_path), width=Inches(width))
    format_paragraph(p, center=True, first_line=False)
    add_para(doc, caption, center=True, first_line=False)


def remove_from_chapter3(doc):
    body = doc._body._element
    remove = False
    for child in list(body):
        texts = child.xpath(".//w:t/text()")
        joined = " ".join(t.strip() for t in texts if t.strip()).upper()
        if joined in {"CHAPTER 3", "CHAPTER III"}:
            remove = True
        if remove:
            body.remove(child)


def main():
    diagrams = {
        "waterfall": create_waterfall(),
        "use_case": create_use_case(),
        "sequence": create_sequence(),
        "activity": create_activity(),
        "class": create_class(),
    }

    doc = Document(SOURCE)
    remove_from_chapter3(doc)

    add_chapter(doc, "CHAPTER III", "SYSTEM DESIGN AND METHODOLOGY")
    add_para(doc, "This chapter presents the system design and methodology of the Web-Based Management Information System for Research and Extension of J.H. Cerilles State College - Dumingag Campus. The design is based on the actual Django web application, which includes role-based dashboards, proposal submission and review, research record management, extension activity management, quarterly narrative reports, document uploads, search, and user administration.")
    add_para(doc, "The system follows a structured web-based architecture where faculty members submit proposals and supporting files, administrators review and monitor institutional records, research staff manage approved research outputs, and extension staff manage community service activities and narrative reports. The following diagrams describe the system users, process flow, object interaction, and database-oriented class structure.")

    add_heading(doc, "SDLC Waterfall Model")
    add_figure(doc, diagrams["waterfall"], "Figure 3.1 Waterfall Model Used in the Development of the Web-Based MIS", width=6.45)
    add_para(doc, "Figure 3.1 shows the Waterfall Model used in developing the Web-Based Management Information System for Research and Extension. The model was selected because the system requirements can be arranged in a clear sequence. The Research and Extension Office first needed a system that could organize proposals, research records, extension activities, document uploads, quarterly reports, dashboards, and user accounts. Since these needs can be identified before coding, the Waterfall Model provides an orderly guide for completing one phase before moving to the next.")
    add_para(doc, "In the requirements gathering phase, the proponents identified the users of the application, including faculty members, administrators, research staff, and extension staff. The proponents also identified the current manual problems, such as scattered proposal files, difficult retrieval of research outputs, fragmented extension records, and the need for reports for accreditation and administrative decision-making.")
    add_para(doc, "In the system design phase, the gathered requirements were transformed into diagrams, database structures, and user interface plans. The design included the proposal workflow, role-based dashboards, research record module, extension activity module, quarterly narrative report module, document upload process, and user management module. This phase served as the blueprint for the actual application.")
    add_para(doc, "In the development phase, the system modules were built using Django. The users module handled role-based accounts, the proposals module handled proposal submission, review, rejection, and resubmission, the research module handled approved research records, the extension module handled extension activities and quarterly reports, and the portal module displayed dashboard summaries.")
    add_para(doc, "In the testing phase, the proponents checked whether the system functions worked properly. Proposal submission, status display, document upload areas, research records, extension activities, quarterly reports, user management, dashboard counts, and role-based access were tested to ensure that the MIS matched the needs of the intended users.")
    add_para(doc, "In the deployment phase, the system was prepared for actual use through a web server where authorized users can log in and access the system through a browser. In the maintenance phase, the system can be improved through backups, error correction, feature updates, security improvements, and user feedback.")

    add_heading(doc, "Use Case Diagram")
    add_figure(doc, diagrams["use_case"], "Figure 3.2 Comprehensive Use Case Diagram of the Web-Based MIS for Research and Extension")
    add_para(doc, "Figure 3.2 shows the main functions available to each user role. Faculty members can log in, submit proposals, upload required documents, track proposal status, and resubmit missing requirements when a proposal is rejected. Administrators can review proposals, approve or reject submissions, request missing requirements, manage user accounts, and generate monitoring summaries. Research staff handle approved research proposals by creating and updating research records, while extension staff manage extension activities, submit quarterly narrative reports, and monitor community-based accomplishments.")
    add_para(doc, "The diagram emphasizes role-based access control. Each actor only accesses the functions needed for their responsibility, which supports data privacy and reduces confusion during system use. The dashboard and report generation features connect all major modules because they summarize proposal, research, extension, and user data for institutional monitoring.")

    add_heading(doc, "Sequence Diagram")
    add_figure(doc, diagrams["sequence"], "Figure 3.3 Sequence Diagram for Proposal Review, Record Creation, and Reporting")
    add_para(doc, "Figure 3.3 presents the sequence of interaction among the faculty user, MIS web application, database, administrator, and research or extension staff. The process begins when a faculty member logs in and submits a proposal with the required details and uploaded documents. The system validates the submitted data and stores the proposal in the database with a pending status.")
    add_para(doc, "After submission, the administrator reviews the proposal. If the proposal is approved, it becomes available for research or extension processing. If rejected, the system records the missing requirements and allows the faculty member to upload the requested documents for resubmission. Approved research proposals can be converted into research records, while approved extension proposals can become extension activities with quarterly narrative reports. The database supports all these actions by storing statuses, document versions, requirements, and report records.")

    add_heading(doc, "Activity Diagram")
    add_figure(doc, diagrams["activity"], "Figure 3.4 Activity Diagram of the Web-Based MIS Workflow")
    add_para(doc, "Figure 3.4 illustrates the overall activity flow of the system. The workflow begins with user login and role checking. Faculty users proceed to proposal submission and document uploading, administrators proceed to proposal review and user monitoring, while research and extension staff proceed to managing approved work. The system provides separate paths for approved and rejected proposals to ensure that incomplete submissions can be corrected without losing the original record.")
    add_para(doc, "For approved work, the system continues into research record management or extension activity management. Extension staff can submit quarterly narrative reports, allowing the institution to monitor progress over time. The workflow ends with dashboard summaries and generated reports, which help administrators view the current status of proposals, research projects, extension activities, and users.")

    add_heading(doc, "Class Diagram")
    add_figure(doc, diagrams["class"], "Figure 3.5 Class Diagram of the Web-Based MIS")
    add_para(doc, "Figure 3.5 shows the main classes used by the application. The CustomUser class represents all users and stores their role, employee information, department, and contact details. The Proposal class stores proposal information, type, status, author, review notes, and reviewer data. The ProposalRequirement and ProposalDocumentVersion classes support the rejection and resubmission workflow by storing missing requirements and document version history.")
    add_para(doc, "The ResearchRecord class is connected to approved research proposals and stores lead researcher, co-researchers, funding, status, publication year, citations, and output details. The ExtensionRecord class is connected to approved extension proposals and stores activity type, coordinator, team members, partner community, location, status, beneficiaries, documents, and photos. The NarrativeReport class stores quarterly reports for each extension activity, making it possible to monitor accomplishments by quarter and year.")

    add_heading(doc, "Development Methodology")
    add_para(doc, "The proponents used the Waterfall Model as the development methodology because the institutional workflow can be divided into clear stages: requirements gathering, system design, development, testing, deployment, and maintenance. Requirements were identified from the existing needs of the Research and Extension Office, especially the need to centralize proposals, research outputs, extension activities, supporting documents, and reports.")
    add_para(doc, "After requirements gathering, system design was prepared using the diagrams presented in this chapter. Development then focused on creating the Django modules for authentication, dashboards, proposals, research, extension, narrative reports, search, and user management. Testing was conducted by checking whether each module supported the expected user role and whether data could be saved, viewed, updated, filtered, and monitored correctly.")

    add_chapter(doc, "CHAPTER IV", "DEVELOPMENT, TESTING AND IMPLEMENTATION")
    add_heading(doc, "Description of the Prototype")
    add_para(doc, "The prototype is a Django-based web application titled Research & Extension (MIS). It is designed to help J.H. Cerilles State College - Dumingag Campus manage proposal submissions, research outputs, extension activities, quarterly reports, uploaded documents, and user accounts. The system uses a role-based interface so that each user sees the tools appropriate to their responsibilities.")
    add_para(doc, "The actual application includes an administrator workspace, proposal management page, research record page, extension activity page, quarterly narrative reports page, and user management page. These screens demonstrate that the prototype is not only a document repository but also a monitoring platform for institutional research and extension operations.")

    screenshots = [
        ("01-admin-dashboard.png", "Figure 4.1 Admin Dashboard / Operational Summary", "Figure 4.1 shows the administrator dashboard. This screen gives the administrator a quick operational summary of total proposals, research projects, extension activities, and system users. It also displays recent proposals and quick action buttons for reviewing pending proposals, managing users, adding research records, and creating new proposals. This page is useful because it gives decision-makers an immediate overview of institutional activity."),
        ("02-proposals-list.png", "Figure 4.2 Proposal Management Page", "Figure 4.2 shows the proposal list page. This page allows authorized users to view submitted proposals, check whether each proposal is pending, approved, or rejected, and filter records according to type or status. The page supports the proposal workflow by keeping faculty submissions organized and making it easier for administrators to locate proposals that need review."),
        ("03-research-records.png", "Figure 4.3 Research Records Page", "Figure 4.3 shows the research records module. This page records approved research activities and displays important information such as research title, lead researcher, status, year, and related actions. The module supports monitoring of completed, ongoing, and published research outputs, making it useful for institutional assessment and accreditation documentation."),
        ("04-extension-records.png", "Figure 4.4 Extension Activities Page", "Figure 4.4 shows the extension activity module. This page lists community-oriented activities with their status, coordinator, date, partner community, and action buttons. It helps the Research and Extension Office monitor planned, ongoing, and completed extension activities in one centralized location."),
        ("05-quarterly-reports.png", "Figure 4.5 Quarterly Narrative Reports Page", "Figure 4.5 shows the quarterly narrative reports page. This page compiles submitted narrative reports by extension activity, quarter, year, and submitting user. It is important because extension projects often continue across several months, and quarterly reports provide a chronological record of accomplishments, issues, and progress."),
        ("06-user-management.png", "Figure 4.6 User Management Page", "Figure 4.6 shows the user management module. This page allows the administrator to view system users, their roles, employee IDs, departments, and account status. It supports role-based access by ensuring that faculty, research staff, extension staff, and administrators are properly registered and managed.")
    ]
    for file_name, caption, explanation in screenshots:
        add_figure(doc, SCREENSHOT_DIR / file_name, caption, width=6.45)
        add_para(doc, explanation)

    add_heading(doc, "Testing")
    add_para(doc, "Testing focused on verifying whether the system modules worked according to their intended purpose. The proposal module was tested by checking proposal listing, status display, document-related workflows, review actions, and resubmission support. The research module was tested by checking whether approved research records could be displayed with their correct status and details. The extension module was tested by checking activity listing, status tracking, and quarterly narrative report display.")
    add_para(doc, "The administrator dashboard and user management screens were also tested to confirm that summary counts, recent proposal records, quick action links, and role information were shown correctly. The screenshots presented in this chapter serve as evidence that the major modules are available and functioning in the prototype.")

    add_heading(doc, "Implementation")
    add_para(doc, "The system was implemented as a modular Django application. The users module handles role-based accounts, the proposals module handles proposal submission and review, the research module manages research records, the extension module manages extension activities and quarterly narrative reports, and the portal module displays role-based dashboards. The interface is built using responsive HTML templates and static assets so users can access the system through a standard web browser.")
    add_para(doc, "During implementation, sample data were used to demonstrate how the system behaves when proposals, research projects, extension activities, narrative reports, and users are already present in the database. This allowed the proponents to verify dashboard counts, list views, filters, and monitoring features before full deployment.")

    add_chapter(doc, "CHAPTER V", "RESULTS, DISCUSSION, CONCLUSION AND RECOMMENDATION")
    add_heading(doc, "Results and Discussion")
    add_para(doc, "The results and discussion are presented according to the five objectives of the study. Each objective is supported by a screenshot taken from the developed Web-Based Management Information System for Research and Extension. The figures show how the actual application addresses the required functions for research recording, extension activity documentation, centralized uploads, system validation, and automated reporting.")

    add_heading(doc, "Objective 1: To develop a web-based management information system to digitally record and monitor research outputs such as completed, ongoing, presented, published, and utilized researches.")
    add_figure(doc, SCREENSHOT_DIR / "03-research-records.png", "Figure 5.1 Research Records Module for Digital Recording and Monitoring of Research Outputs", width=6.45)
    add_para(doc, "Figure 5.1 shows the Research Records module of the system. This module directly supports the first objective because it provides a centralized screen where research outputs can be viewed and monitored. Each research entry is connected to an approved proposal and can contain important information such as the research title, lead researcher, status, dates, publication details, and citation-related data.")
    add_para(doc, "Through this module, the Research and Extension Office no longer needs to rely only on physical folders or separate spreadsheet files when checking research accomplishments. Ongoing, completed, and published research records can be organized in one web-based platform, making retrieval faster and improving the accuracy of institutional reports.")

    add_heading(doc, "Objective 2: To design a module for extension activities that documents planned target activities, actual accomplishments, attendance, budget utilization, materials needed, and remarks for unaccomplished targets.")
    add_figure(doc, SCREENSHOT_DIR / "04-extension-records.png", "Figure 5.2 Extension Activities Module for Monitoring Planned and Accomplished Extension Work", width=6.45)
    add_para(doc, "Figure 5.2 shows the Extension Activities module. This result supports the second objective because the system provides a dedicated area for managing extension activities, including activity title, coordinator, status, date, partner community, and related action buttons. The module helps the Extension Office monitor whether activities are still in planning, ongoing, completed, or cancelled status.")
    add_para(doc, "The extension module gives the institution a clearer way to document community-based work. It can be used to record planned activities and later update the accomplishments and supporting details. This improves transparency because extension projects can be tracked from preparation up to completion, including follow-up reports and evidence of implementation.")

    add_heading(doc, "Objective 3: To create a centralized system where faculty members and research coordinators can upload abstracts, certificates of presentation, conference proceedings, publication details, and narrative reports.")
    add_figure(doc, SCREENSHOT_DIR / "07-proposal-upload-form.png", "Figure 5.3 Proposal Submission and Document Upload Interface", width=6.45)
    add_para(doc, "Figure 5.3 shows the document upload stage of the proposal submission workflow. The interface includes upload areas for the proposal document, budget PDF, and supporting image. This supports the third objective because it demonstrates that the system can receive and organize digital files needed for proposal documentation and institutional evidence.")
    add_para(doc, "The upload feature helps centralize supporting documents instead of storing them in separate personal folders or email threads. Faculty members can submit proposal-related files directly through the system, while authorized personnel can later access the records for review, monitoring, and reporting. This strengthens document management and reduces the possibility of misplaced or duplicated files.")

    add_heading(doc, "Objective 4: To conduct system testing and validation to ensure the MIS functions correctly, is user-friendly, and meets the requirements of faculty, researchers, administrators, and other stakeholders.")
    add_figure(doc, SCREENSHOT_DIR / "06-user-management.png", "Figure 5.4 User Management Module for Role Validation and Access Control", width=6.45)
    add_para(doc, "Figure 5.4 shows the User Management module, where the administrator can view registered users, their assigned roles, departments, employee IDs, and account status. This result supports the fourth objective because role validation is an important part of testing whether the system functions correctly for different users. The system must recognize faculty, research staff, extension staff, and administrators so that each user can access the correct modules.")
    add_para(doc, "The presence of role-based user management indicates that the system was tested not only as a single-user application but as a multi-role institutional platform. This helps confirm that the MIS is user-friendly and appropriate for its intended stakeholders because each role is guided toward the functions needed for their responsibilities.")

    add_heading(doc, "Objective 5: To enable automated report generation to support accreditation, institutional assessment, and administrative decision-making while improving data accuracy, accessibility, and transparency.")
    add_figure(doc, SCREENSHOT_DIR / "05-quarterly-reports.png", "Figure 5.5 Quarterly Narrative Reports Module for Institutional Reporting", width=6.45)
    add_para(doc, "Figure 5.5 shows the Quarterly Narrative Reports module. This module supports the fifth objective because it organizes extension reports by activity, quarter, year, and submitting user. The system makes it easier for administrators and extension personnel to retrieve reports needed for accreditation, annual reporting, and institutional assessment.")
    add_para(doc, "The report module improves accessibility and transparency because submitted narratives are stored in one location and can be reviewed when needed. Instead of manually collecting reports from different files, the office can use the system to monitor submitted accomplishments by quarter. This supports better administrative decision-making and helps ensure that extension records remain accurate and available.")

    add_heading(doc, "Conclusions")
    add_para(doc, "The Web-Based Management Information System for Research and Extension achieved its purpose of providing a centralized and role-based platform for research and extension documentation. The system reduces dependence on paper files and scattered spreadsheets by allowing users to manage proposals, research records, extension activities, reports, and user accounts in one application.")
    add_para(doc, "The comprehensive diagrams in Chapter III show that the system has a clear structure and workflow. The screenshots in Chapter IV confirm that the planned modules are represented in the actual prototype. Overall, the MIS can improve accessibility, monitoring, reporting, and transparency for the Research and Extension Office of JHCSC Dumingag Campus.")

    add_heading(doc, "Recommendations")
    add_para(doc, "First, the system may be enhanced with automated email or SMS notifications so users can receive updates about proposal status, missing requirements, approval decisions, and report deadlines.")
    add_para(doc, "Second, the dashboard may be improved with more visual analytics such as graphs for research productivity, extension accomplishment rates, proposal approval trends, and quarterly report submission rates.")
    add_para(doc, "Third, future development may include more detailed document management features such as preview, version comparison, required-file checklists, and download logs for accreditation evidence.")
    add_para(doc, "Fourth, the system should include regular backup procedures and stricter security policies to protect uploaded documents and user information.")
    add_para(doc, "Lastly, the system may be expanded into a mobile-friendly or progressive web application so faculty members and staff can submit updates and view records more conveniently during fieldwork or off-campus activities.")

    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
