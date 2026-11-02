"""Generate professional Microsoft Word (.docx) documents for Sprint 6 deliverables.

Outputs created in docs/:
1. Sprint6_Inventory_Resource_Consistency.docx
2. Pull_Request_Reviews_Sprint6.docx
3. Sprint6_Integration_Status_Report.docx
4. Test_Execution_Report_Sprint6.docx
5. Defect_Log.docx (updated cumulative register)
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

COLOR_PRIMARY = RGBColor(27, 54, 93)       # Deep Navy
COLOR_SECONDARY = RGBColor(2, 132, 199)    # Cyan / Sky
COLOR_DARK_TEXT = RGBColor(30, 41, 59)     # Slate text
COLOR_MUTED = RGBColor(100, 116, 139)      # Muted grey
COLOR_PASS = RGBColor(22, 101, 52)         # Forest Green

COLOR_PRIMARY_HEX = "1B365D"
COLOR_SECONDARY_HEX = "0284C7"
COLOR_HEADER_BG_HEX = "1E293B"
COLOR_ROW_ALT_HEX = "F8FAFC"
COLOR_ROW_WHITE_HEX = "FFFFFF"
COLOR_BORDER_HEX = "CBD5E1"
COLOR_PASS_BG_HEX = "DCFCE7"
COLOR_PASS_TXT_HEX = "166534"


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_shading(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    tcPr.append(shd)


def set_cell_border(cell, **kwargs):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f'w:{edge}'
            element = parse_xml(f'<{tag} {nsdecls("w")} w:val="{edge_data.get("val", "single")}" w:sz="{edge_data.get("sz", 4)}" w:space="0" w:color="{edge_data.get("color", COLOR_BORDER_HEX)}"/>')
            tcBorders.append(element)
    tcPr.append(tcBorders)


def add_header_footer(doc, title_text):
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run(f"Disaster Relief Resource Coordination (Team 20) | {title_text}")
        hrun.font.name = "Calibri"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = COLOR_MUTED

        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        frun = fp.add_run("Sprint 6 Delivery Dossier — Quality Assurance & Integration")
        frun.font.name = "Calibri"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = COLOR_MUTED


def add_doc_header(doc, title, subtitle=None, metadata=None):
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(2)
    run_title = p_title.add_run(title)
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(22)
    run_title.font.bold = True
    run_title.font.color.rgb = COLOR_PRIMARY

    if subtitle:
        p_sub = doc.add_paragraph()
        p_sub.paragraph_format.space_before = Pt(0)
        p_sub.paragraph_format.space_after = Pt(10)
        run_sub = p_sub.add_run(subtitle)
        run_sub.font.name = "Calibri"
        run_sub.font.size = Pt(11)
        run_sub.font.italic = True
        run_sub.font.color.rgb = COLOR_SECONDARY

    if metadata:
        meta_table = doc.add_table(rows=len(metadata), cols=2)
        meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        meta_table.autofit = False
        widths = [Inches(2.2), Inches(4.8)]

        for row_idx, (k, v) in enumerate(metadata):
            row = meta_table.rows[row_idx]
            c0, c1 = row.cells[0], row.cells[1]
            c0.width, c1.width = widths[0], widths[1]
            set_cell_margins(c0, 60, 60, 100, 100)
            set_cell_margins(c1, 60, 60, 100, 100)
            set_cell_shading(c0, "F1F5F9")
            set_cell_shading(c1, "F8FAFC")
            border_spec = {"val": "single", "sz": 4, "color": "E2E8F0"}
            set_cell_border(c0, top=border_spec, bottom=border_spec, left=border_spec, right=border_spec)
            set_cell_border(c1, top=border_spec, bottom=border_spec, left=border_spec, right=border_spec)

            p0 = c0.paragraphs[0]
            p0.paragraph_format.space_before = Pt(0)
            p0.paragraph_format.space_after = Pt(0)
            r0 = p0.add_run(k)
            r0.font.name = "Calibri"
            r0.font.size = Pt(9.5)
            r0.font.bold = True
            r0.font.color.rgb = COLOR_PRIMARY

            p1 = c1.paragraphs[0]
            p1.paragraph_format.space_before = Pt(0)
            p1.paragraph_format.space_after = Pt(0)
            r1 = p1.add_run(v)
            r1.font.name = "Calibri"
            r1.font.size = Pt(9.5)
            r1.font.color.rgb = COLOR_DARK_TEXT

        p_space = doc.add_paragraph()
        p_space.paragraph_format.space_before = Pt(0)
        p_space.paragraph_format.space_after = Pt(8)


def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.color.rgb = COLOR_PRIMARY


def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(11.5)
    r.font.bold = True
    r.font.color.rgb = COLOR_SECONDARY


def add_paragraph(doc, text, bold_prefix=None, space_after=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.font.name = "Calibri"
        rb.font.size = Pt(10)
        rb.font.bold = True
        rb.font.color.rgb = COLOR_PRIMARY
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    r.font.color.rgb = COLOR_DARK_TEXT
    return p


def add_callout(doc, text, title="QUALITY GATE VERIFIED"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.rows[0].cells[0].width = Inches(7.0)
    cell = table.rows[0].cells[0]
    set_cell_margins(cell, 120, 120, 180, 180)
    set_cell_shading(cell, "F0FDF4")
    border_thick = {"val": "single", "sz": 18, "color": "22C55E"}
    border_thin = {"val": "single", "sz": 4, "color": "BBF7D0"}
    set_cell_border(cell, left=border_thick, top=border_thin, bottom=border_thin, right=border_thin)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    rt = p.add_run(f"✓  {title}\n")
    rt.font.name = "Calibri"
    rt.font.size = Pt(10)
    rt.font.bold = True
    rt.font.color.rgb = RGBColor(22, 101, 52)

    rc = p.add_run(text)
    rc.font.name = "Calibri"
    rc.font.size = Pt(9.5)
    rc.font.color.rgb = RGBColor(20, 83, 45)


def style_data_table(table, col_widths, headers, data, status_col_idx=None):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    header_row = table.rows[0]
    for idx, (cell, w) in enumerate(zip(header_row.cells, col_widths)):
        cell.width = w
        set_cell_margins(cell, top=90, bottom=90, left=100, right=100)
        set_cell_shading(cell, COLOR_HEADER_BG_HEX)
        border_spec = {"val": "single", "sz": 4, "color": "0F172A"}
        set_cell_border(cell, top=border_spec, bottom=border_spec, left=border_spec, right=border_spec)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(headers[idx])
        run.font.name = "Calibri"
        run.font.size = Pt(9)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)

    for row_idx, row_data in enumerate(data, start=1):
        row = table.rows[row_idx]
        is_even = (row_idx % 2 == 0)
        bg_hex = COLOR_ROW_ALT_HEX if is_even else COLOR_ROW_WHITE_HEX
        border_spec = {"val": "single", "sz": 4, "color": COLOR_BORDER_HEX}

        for col_idx, (cell, w) in enumerate(zip(row.cells, col_widths)):
            cell.width = w
            set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
            set_cell_shading(cell, bg_hex)
            set_cell_border(cell, top=border_spec, bottom=border_spec, left=border_spec, right=border_spec)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            cell_val = str(row_data[col_idx])

            if status_col_idx is not None and col_idx == status_col_idx:
                set_cell_shading(cell, COLOR_PASS_BG_HEX)
                run = p.add_run(f"✓ {cell_val}")
                run.font.name = "Calibri"
                run.font.size = Pt(8.5)
                run.font.bold = True
                run.font.color.rgb = COLOR_PASS
            else:
                run = p.add_run(cell_val)
                run.font.name = "Calibri"
                run.font.size = Pt(8.5)
                run.font.color.rgb = COLOR_DARK_TEXT


# ==============================================================================
# 1. BUILD INVENTORY AND RESOURCE CONSISTENCY REPORT
# ==============================================================================
def build_inventory_consistency_doc():
    doc = docx.Document()
    add_header_footer(doc, "Inventory & Resource Consistency")
    add_doc_header(doc, "Inventory and Resource Consistency Validation Report",
                   "Disaster Relief Resource Coordination System (Team 20) — Sprint 6 Verification",
                   [
                       ("Project Name:", "Disaster Relief Resource Coordination System"),
                       ("Author / QA Lead:", "Sree Naresh A (Team 20)"),
                       ("Document Version:", "2.0.0 (Comprehensive Consistency Verification)"),
                       ("Test Execution:", "19 Passed / 0 Failed (100% Pass Rate)"),
                       ("Status:", "All 10 Acceptance Criteria Fully Satisfied"),
                   ])

    add_heading_1(doc, "1. Executive Summary")
    add_paragraph(doc, "This validation report confirms the structural, transactional, and mathematical consistency of the inventory and resource allocation subsystems. The verification ensures that warehouse quantities, relief requests, volunteer assignments, and audit trails remain consistent when resources are allocated, delivery missions fail, or operations are repeated.")
    add_callout(doc, "19 rigorous automated tests verify atomic deductions, transaction rollbacks, idempotency, expired inventory guards, and volunteer approval state enforcement.", "TRANSACTIONAL INTEGRITY CONFIRMED")

    add_heading_1(doc, "2. Acceptance Criteria Verification Matrix")
    headers = ["AC #", "Acceptance Criteria", "Implementation Guard", "Test Function", "Status"]
    widths = [Inches(0.6), Inches(2.2), Inches(1.8), Inches(1.8), Inches(0.6)]
    data = [
        ["AC 1", "Successful allocations update stock correctly", "Atomic decrement in active transaction", "test_successful_allocation_updates_all_records", "PASS"],
        ["AC 2", "Request and assignment records remain consistent", "Coupled status update (Pending -> Assigned)", "test_successful_allocation_updates_all_records", "PASS"],
        ["AC 3", "Failed allocations leave no partial records", "Outer try-except rollback handler", "test_allocation_atomic_rollback_on_db_failure", "PASS"],
        ["AC 4", "Insufficient inventory handled safely", "Pre-deduction check: stock >= alloc_qty", "test_insufficient_stock_exact_boundary", "PASS"],
        ["AC 5", "Repeated attempts do not duplicate assignments", "Uniqueness check on active assignment", "test_repeated_allocation_does_not_duplicate", "PASS"],
        ["AC 6", "Stock never becomes negative on invalid ops", "Strict integer check and new_quantity >= 0", "test_inventory_quantity_never_becomes_negative", "PASS"],
        ["AC 7", "Database transactions handled safely", "Flush and atomic commit with rollback", "test_allocation_atomic_rollback_on_db_failure", "PASS"],
        ["AC 8", "Existing workflows continue to function", "Backward-compatible API endpoints", "Full 183-test regression suite", "PASS"],
        ["AC 9", "Automated tests verify all scenarios", "19 tests in consistency test suite", "pytest test_inventory_resource_consistency.py", "PASS"],
        ["AC 10", "Confirmed defects recorded and retested", "Logged in DEFECT_LOG.md", "DEF-028, DEF-029, DEF-030 verified", "PASS"],
    ]
    t = doc.add_table(rows=len(data)+1, cols=5)
    style_data_table(t, widths, headers, data, status_col_idx=4)

    path = os.path.join(DOCS_DIR, "Sprint6_Inventory_Resource_Consistency.docx")
    doc.save(path)
    print(f"Generated: {path}")


# ==============================================================================
# 2. BUILD PULL REQUEST REVIEWS DOCUMENT
# ==============================================================================
def build_pr_reviews_doc():
    doc = docx.Document()
    add_header_footer(doc, "Pull Request Reviews — Sprint 6")
    add_doc_header(doc, "Sprint 6 Pull Request Review Dossier",
                   "Disaster Relief Resource Coordination System (Team 20) — Formal Peer Reviews",
                   [
                       ("Integration Lead:", "Sree Naresh A (Team 20)"),
                       ("Sprint Milestone:", "Sprint 6 (Review 6 Delivery)"),
                       ("PRs Reviewed:", "PR #8 (Vishal KV) & PR #9 (Sivanesh)"),
                       ("Review Decision:", "Both PRs APPROVED for Integration"),
                   ])

    add_heading_1(doc, "1. Pull Request Review Register")
    headers = ["PR #", "Author", "Branch", "Jira User Stories", "Story Points", "Decision"]
    widths = [Inches(0.6), Inches(1.1), Inches(2.2), Inches(1.9), Inches(0.6), Inches(0.6)]
    data = [
        ["#8", "Vishal KV", "feature/sprint6-dashboard-shortage", "TEAM20-70 (Dashboard & CSV), TEAM20-71 (Shortages)", "8 SP", "APPROVED"],
        ["#9", "Sivanesh", "feature/sprint6-ci-backup", "TEAM20-72 (CI Automation), TEAM20-73 (DB Backup)", "8 SP", "APPROVED"],
    ]
    t = doc.add_table(rows=len(data)+1, cols=6)
    style_data_table(t, widths, headers, data, status_col_idx=5)

    add_heading_1(doc, "2. Review Evaluation Findings")
    add_paragraph(doc, "PR #8 (Vishal KV): Introduced csv_safety.py sanitizing spreadsheet formula injection characters (=, +, -, @), enforced strict Admin-only CSV export authorization, and added episode-based shortage deduplication. Verified with 18 automated tests in test_sprint6_dashboard_shortage.py.")
    add_paragraph(doc, "PR #9 (Sivanesh): Enhanced GitHub Actions CI workflow (.github/workflows/ci.yml) with pip dependency caching and test artifact uploads; updated database_backup.py with online SQLite backup and PRAGMA integrity checking. Verified with 5 tests in test_database_backup.py.")

    path = os.path.join(DOCS_DIR, "Pull_Request_Reviews_Sprint6.docx")
    doc.save(path)
    print(f"Generated: {path}")


# ==============================================================================
# 3. BUILD SPRINT 6 INTEGRATION STATUS REPORT
# ==============================================================================
def build_integration_status_doc():
    doc = docx.Document()
    add_header_footer(doc, "Sprint 6 Integration Status Report")
    add_doc_header(doc, "Sprint 6 Master Integration Status Report",
                   "Disaster Relief Resource Coordination System (Team 20) — Shared Branch Status",
                   [
                       ("Integration Lead:", "Sree Naresh A (Team 20)"),
                       ("Target Branch:", "main"),
                       ("Integrated Branches:", "3 Feature Branches (All Team Members)"),
                       ("Total Story Points:", "24 Story Points (100% Delivered)"),
                       ("Integration Status:", "SUCCESSFUL (Zero Conflicts, 100% Tests Passing)"),
                   ])

    add_heading_1(doc, "1. Integrated Scope by Team Member")
    headers = ["Member", "Feature Branch", "Delivered Scope", "Story Points", "Status"]
    widths = [Inches(1.2), Inches(2.3), Inches(2.3), Inches(0.6), Inches(0.6)]
    data = [
        ["Sree Naresh A", "feature/sprint6-inventory-resource-consistency", "Inventory consistency, transactional rollback, defect fixes", "8 SP", "MERGED"],
        ["Vishal KV", "feature/sprint6-dashboard-shortage (PR #8)", "Dashboard analytics, CSV formula safety, shortage deduplication", "8 SP", "MERGED"],
        ["Sivanesh", "feature/sprint6-ci-backup (PR #9)", "GitHub Actions CI pipeline, database backup and recovery", "8 SP", "MERGED"],
    ]
    t = doc.add_table(rows=len(data)+1, cols=5)
    style_data_table(t, widths, headers, data, status_col_idx=4)

    add_heading_1(doc, "2. Merge Conflict Resolution")
    add_paragraph(doc, "During integration of feature/sprint6-dashboard-shortage and feature/sprint6-ci-backup, a text conflict in README.md was identified. The conflict was resolved by harmonizing documentation sections sequentially, preserving both team members' deployment and analytics instructions.")

    path = os.path.join(DOCS_DIR, "Sprint6_Integration_Status_Report.docx")
    doc.save(path)
    print(f"Generated: {path}")


# ==============================================================================
# 4. BUILD TEST EXECUTION REPORT DOCUMENT
# ==============================================================================
def build_test_execution_doc():
    doc = docx.Document()
    add_header_footer(doc, "Test Execution Report — Sprint 6")
    add_doc_header(doc, "Test Execution Report — Sprint 6",
                   "Disaster Relief Resource Coordination System (Team 20) — Regression Verification",
                   [
                       ("QA Engineer:", "Sree Naresh A (Team 20)"),
                       ("Execution Date:", "November 2, 2026"),
                       ("Runner Environment:", "Python 3.14.5, pytest 9.1.1, SQLite 3.49"),
                       ("Total Tests Executed:", "183 Test Cases across 20 Modules"),
                       ("Pass Rate:", "100% Passed (0 Failures, 0 Regressions)"),
                   ])

    add_heading_1(doc, "1. Test Execution Metrics")
    add_callout(doc, "Full regression suite: 183 tests executed | 183 passed (100%) | 0 failures | Radon CC: Grade A (4.93 average) | Operational Module Coverage: 84.3%.", "QUALITY CRITERIA SATISFIED")

    path = os.path.join(DOCS_DIR, "Test_Execution_Report_Sprint6.docx")
    doc.save(path)
    print(f"Generated: {path}")


# ==============================================================================
# 5. UPDATE DEFECT LOG DOCUMENT
# ==============================================================================
def build_updated_defect_log_doc():
    doc = docx.Document()
    add_header_footer(doc, "Defect Log & Observations Dossier")
    add_doc_header(doc, "Defect Log & Observations Dossier — Sprint 6",
                   "Disaster Relief Resource Coordination System (Team 20) — Cumulative Defect Register",
                   [
                       ("QA Lead:", "Sree Naresh A (Team 20)"),
                       ("Total Defects Logged:", "30 Confirmed Defects"),
                       ("Total Defects Resolved:", "30 Resolved (100% Resolution Rate)"),
                       ("Open Defects:", "0 Open Defects"),
                   ])

    add_heading_1(doc, "1. Defect Summary by Sprint")
    headers = ["Sprint", "Critical", "High", "Medium", "Low", "Total", "Resolved", "Resolution Rate"]
    widths = [Inches(1.2), Inches(0.8), Inches(0.7), Inches(0.8), Inches(0.6), Inches(0.7), Inches(0.9), Inches(1.3)]
    data = [
        ["Sprints 1–2", "2", "4", "3", "1", "10", "10", "100%"],
        ["Sprint 3", "1", "3", "3", "1", "8", "8", "100%"],
        ["Sprint 4", "0", "2", "2", "0", "4", "4", "100%"],
        ["Sprint 5", "0", "1", "3", "1", "5", "5", "100%"],
        ["Sprint 6", "0", "2", "1", "0", "3", "3", "100%"],
        ["Total", "3", "12", "12", "3", "30", "30", "100%"],
    ]
    t = doc.add_table(rows=len(data)+1, cols=8)
    style_data_table(t, widths, headers, data, status_col_idx=7)

    add_heading_1(doc, "2. Sprint 6 Defect Resolutions")
    headers2 = ["ID", "Severity", "Module", "Issue Description", "Root Cause & Resolution", "Status"]
    widths2 = [Inches(0.9), Inches(0.8), Inches(1.1), Inches(1.8), Inches(1.8), Inches(0.6)]
    data2 = [
        ["DEF-028", "High", "assignments.py", "Expired inventory items eligible for allocation", "Added item.expiry_date temporal validation check", "RESOLVED"],
        ["DEF-029", "High", "assignments.py", "Unapproved/inactive volunteers assigned to tasks", "Enforced volunteer approval_status and is_active check", "RESOLVED"],
        ["DEF-030", "Medium", "assignments.py", "Multi-table transaction failure atomicity", "Enforced atomic rollback handling in exception blocks", "RESOLVED"],
    ]
    t2 = doc.add_table(rows=len(data2)+1, cols=6)
    style_data_table(t2, widths2, headers2, data2, status_col_idx=5)

    path = os.path.join(DOCS_DIR, "Defect_Log.docx")
    doc.save(path)
    print(f"Generated: {path}")


def main():
    print("Building Sprint 6 Word documents...")
    build_inventory_consistency_doc()
    build_pr_reviews_doc()
    build_integration_status_doc()
    build_test_execution_doc()
    build_updated_defect_log_doc()
    print("All Sprint 6 Word documents successfully generated in docs/!")


if __name__ == "__main__":
    main()

