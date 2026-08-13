import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def draw_executive_certificate_background(canvas, doc):
    """Draws a premium corporate border with gold corner accents and watermark frames."""
    canvas.saveState()
    width, height = doc.pagesize

    # 1. Cream Premium Paper Tint Background
    canvas.setFillColor(colors.HexColor('#FAFAF9'))
    canvas.rect(0, 0, width, height, fill=1, stroke=0)

    # 2. Outer Navy Heavy Border Frame
    canvas.setStrokeColor(colors.HexColor('#0A192F'))  # Deep Navy
    canvas.setLineWidth(3)
    canvas.rect(16, 16, width - 32, height - 32)

    # 3. Inner Gold Accent Border
    canvas.setStrokeColor(colors.HexColor('#D97706'))  # Gold
    canvas.setLineWidth(1)
    canvas.rect(22, 22, width - 44, height - 44)

    # 4. Thin Guilloche-Style Inner Keyline
    canvas.setStrokeColor(colors.HexColor('#E2E8F0'))  # Soft Slate
    canvas.setLineWidth(0.5)
    canvas.rect(26, 26, width - 52, height - 52)

    # 5. Top Center Gold Crest Medallion Vector
    center_x = width / 2.0
    top_y = height - 48
    canvas.setFillColor(colors.HexColor('#D97706'))
    canvas.circle(center_x, top_y, 14, fill=1, stroke=0)

    canvas.setFillColor(colors.HexColor('#FFFFFF'))
    canvas.circle(center_x, top_y, 11, fill=1, stroke=0)

    canvas.setFillColor(colors.HexColor('#0A192F'))
    canvas.circle(center_x, top_y, 8, fill=1, stroke=0)

    canvas.restoreState()


def generate_certificate_pdf_bytes(cert_data):
    """Generates an executive-tier, highly polished professional PDF certificate."""
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=40
    )

    story = []
    styles = getSampleStyleSheet()

    # --- Typography Styles ---
    org_title_style = ParagraphStyle(
        'ExecOrgTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#0A192F'),
        alignment=1  # Centered
    )

    org_sub_style = ParagraphStyle(
        'ExecOrgSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#D97706'),
        alignment=1
    )

    cert_heading_style = ParagraphStyle(
        'ExecCertHeading',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=32,
        textColor=colors.HexColor('#0A192F'),
        alignment=1
    )

    cert_sub_style = ParagraphStyle(
        'ExecCertSub',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#64748B'),
        alignment=1
    )

    name_style = ParagraphStyle(
        'ExecStudentName',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=30,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1
    )

    body_style = ParagraphStyle(
        'ExecBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=17,
        textColor=colors.HexColor('#334155'),
        alignment=1
    )

    meta_label_style = ParagraphStyle(
        'ExecMetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#64748B'),
        alignment=1
    )

    meta_val_style = ParagraphStyle(
        'ExecMetaVal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0A192F'),
        alignment=1
    )

    sig_name_style = ParagraphStyle(
        'ExecSigName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#0A192F'),
        alignment=1
    )

    sig_role_style = ParagraphStyle(
        'ExecSigRole',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#64748B'),
        alignment=1
    )

    # --- 1. Top Header Organization Block ---
    story.append(Spacer(1, 10))
    story.append(Paragraph("AI EDUCATION ACADEMY", org_title_style))
    story.append(Paragraph("GLOBAL CREDENTIAL & LEARNING SERVICES", org_sub_style))
    story.append(Spacer(1, 16))

    # --- 2. Title Section ---
    story.append(Paragraph("CERTIFICATE OF COMPLETION", cert_heading_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("THIS CREDENTIAL IS PROUDLY PRESENTED TO", cert_sub_style))
    story.append(Spacer(1, 14))

    # --- 3. Student Name Box ---
    student_name = cert_data.get('student_name', 'Student Name')
    name_table_data = [[Paragraph(f"{student_name}", name_style)]]
    t_name = Table(name_table_data, colWidths=[550])
    t_name.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#D97706')),  # Gold Baseline
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
    ]))
    story.append(t_name)
    story.append(Spacer(1, 16))

    # --- 4. Description Body ---
    course_name = cert_data.get('course_name', 'Full-Stack Web Development')
    batch_code = cert_data.get('batch_code', 'AI-EDU-2026')
    comp_date = cert_data.get('completion_date', '13th August 2026')
    grade = cert_data.get('grade_achieved', 'Pass')

    body_text = (
        f"for successfully completing the official program requirements and practical assessments for<br/>"
        f"<b>{course_name}</b> (Batch: <b>{batch_code}</b>) with a final grade performance of <b>{grade}</b>."
    )
    story.append(Paragraph(body_text, body_style))
    story.append(Spacer(1, 22))

    # --- 5. Executive 4-Column Metadata Verification Grid ---
    cert_id = cert_data.get('certificate_id', 'CERT-2026-X1Y2Z3')
    issue_date = cert_data.get('issue_date', comp_date)

    meta_grid_data = [
        [
            Paragraph("CERTIFICATE ID", meta_label_style),
            Paragraph("COMPLETION DATE", meta_label_style),
            Paragraph("ISSUE DATE", meta_label_style),
            Paragraph("GRADE", meta_label_style),
        ],
        [
            Paragraph(f"<b>{cert_id}</b>", meta_val_style),
            Paragraph(f"<b>{comp_date}</b>", meta_val_style),
            Paragraph(f"<b>{issue_date}</b>", meta_val_style),
            Paragraph(f"<b>{grade}</b>", meta_val_style),
        ]
    ]

    t_meta = Table(meta_grid_data, colWidths=[170, 170, 170, 170])
    t_meta.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 26))

    # --- 6. Executive Signatures Row ---
    sig_table_data = [
        [
            Paragraph("___________________________", sig_name_style),
            Paragraph("<b>OFFICIAL SEAL</b>", meta_val_style),
            Paragraph("___________________________", sig_name_style),
        ],
        [
            Paragraph("<b>Program Director</b>", sig_name_style),
            Paragraph(f"<font size=7 color='#64748B'>Verification Code: {cert_id}</font>", sig_role_style),
            Paragraph("<b>Academic Dean</b>", sig_name_style),
        ],
        [
            Paragraph("AI Education Academy", sig_role_style),
            Paragraph("", sig_role_style),
            Paragraph("AI Education Foundation", sig_role_style),
        ]
    ]

    t_sig = Table(sig_table_data, colWidths=[230, 220, 230])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t_sig)

    # Render document with custom canvas
    doc.build(story, onFirstPage=draw_executive_certificate_background)

    buffer.seek(0)
    return buffer.getvalue()