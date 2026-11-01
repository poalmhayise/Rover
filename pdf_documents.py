"""Generate polished customer documents after confirmed bank payment."""
from io import BytesIO
from html import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepTogether

PALETTES = {
    'violet': ('#5F51C7', '#EEEAFE', '#1D2034'),
    'navy': ('#254B70', '#E6F1FA', '#192B3C'),
    'forest': ('#41745F', '#E6F1E7', '#23392E'),
    'coral': ('#CE6B58', '#FFF0E9', '#322A29'),
}

def txt(v):
    return escape(str(v or '').strip()).replace('\n','<br/>')

def build_pdf(kind: str, data: dict, template: str = 'violet') -> bytes:
    accent_hex, pale_hex, ink_hex = PALETTES.get(template, PALETTES['violet'])
    accent, pale, ink = (colors.HexColor(s) for s in (accent_hex,pale_hex,ink_hex))
    out = BytesIO()
    def paint_page(c, doc):
        w,h = A4
        c.setFillColor(pale)
        c.rect(0,h-14*mm,w,14*mm,stroke=0,fill=1)
        c.setFillColor(accent)
        c.rect(0,h-14*mm,7*mm,14*mm,stroke=0,fill=1)
        c.setStrokeColor(colors.HexColor('#E0E2E6'))
        c.line(20*mm, 16*mm,w-20*mm,16*mm)
        c.setFont('Helvetica',8)
        c.setFillColor(colors.HexColor('#777B87'))
        c.drawString(20*mm, 11*mm, 'HIRED  /  PROFESSIONAL DOCUMENT')
        c.drawRightString(w-20*mm,11*mm,str(doc.page))
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=22*mm,rightMargin=22*mm,
                            topMargin=27*mm,bottomMargin=24*mm,
                            title=f"{data.get('fullName','')} — {'CV' if kind=='cv' else 'Application letter'}",
                            author='Hired')
    styles = {
        'name': ParagraphStyle('HiredName',fontName='Helvetica-Bold',fontSize=23,leading=27,textColor=ink,spaceAfter=5),
        'subtitle':ParagraphStyle('HiredSub',fontName='Helvetica',fontSize=11,leading=16,textColor=accent,spaceAfter=7),
        'contact':ParagraphStyle('HiredContact',fontName='Helvetica',fontSize=8.8,leading=14,textColor=colors.HexColor('#626776'),spaceAfter=19),
        'section':ParagraphStyle('HiredSection',fontName='Helvetica-Bold',fontSize=10.5,leading=15,textColor=accent,spaceBefore=14,spaceAfter=6),
        'body':ParagraphStyle('HiredBody',fontName='Helvetica',fontSize=9.8,leading=15,textColor=ink,spaceAfter=6),
        'letter':ParagraphStyle('HiredLetter',fontName='Helvetica',fontSize=10.6,leading=18,textColor=ink,spaceAfter=16),
        'small':ParagraphStyle('HiredSmall',fontName='Helvetica',fontSize=9.5,leading=15,textColor=ink,spaceAfter=7),
    }
    story=[]
    full_name = txt(data.get('fullName')) or 'Your name'
    story.append(Paragraph(full_name,styles['name']))
    if kind=='cv':
        story.append(Paragraph(txt(data.get('headline')) or 'Professional profile',styles['subtitle']))
    contact_items = [txt(data.get(k)) for k in ['email','phone','location','website'] if data.get(k)]
    if contact_items:
        story.append(Paragraph('  &nbsp;  |  &nbsp;  '.join(contact_items), styles['contact']))
    if kind=='cv':
        for field, heading in [
            ('summary','PROFILE'),('experience','EXPERIENCE'),('education','EDUCATION'),
            ('skills','CORE SKILLS'),('projects','PROJECTS & ACHIEVEMENTS'),('languages','LANGUAGES')
        ]:
            v=str(data.get(field,'')).strip()
            if not v: continue
            story.append(Paragraph(heading,styles['section']))
            story.append(HRFlowable(width='100%',thickness=0.8,color=colors.HexColor('#E6E7EA'),spaceAfter=8))
            for chunk in v.split('\n\n'):
                if chunk.strip():
                    story.append(Paragraph(txt(chunk),styles['body']))
    elif kind=='letter':
        company = str(data.get('company','')).strip()
        role = str(data.get('jobTitle','')).strip()
        manager = str(data.get('hiringManager','')).strip()
        story.append(Paragraph('APPLICATION LETTER',styles['subtitle']))
        if company or role:
            details = f"<b>Re: Application for {txt(role or 'a position')}</b>"
            if company: details += f" at {txt(company)}"
            story.append(Paragraph(details,styles['small']))
            story.append(Spacer(1, 9))
        story.append(Paragraph(f"Dear {txt(manager) if manager else 'Hiring Manager'},",styles['letter']))
        body=str(data.get('letterBody','')).strip()
        if body:
            for paragraph in body.split('\n\n'):
                if paragraph.strip(): story.append(Paragraph(txt(paragraph),styles['letter']))
        else:
            intro=f"I am writing to apply for the {txt(role or 'advertised')} position"
            if company: intro+=f" at {txt(company)}"
            intro+='. I would welcome the opportunity to contribute to your team.'
            story.append(Paragraph(intro,styles['letter']))
            strengths=str(data.get('strengths','')).strip()
            if strengths: story.append(Paragraph(txt(strengths),styles['letter']))
            motivation=str(data.get('motivation','')).strip()
            if motivation: story.append(Paragraph(txt(motivation),styles['letter']))
            story.append(Paragraph('Thank you for considering my application. I would appreciate the opportunity to discuss how I could contribute to your organisation.',styles['letter']))
        story.append(Paragraph('Yours sincerely,',styles['small']))
        story.append(Spacer(1,6))
        story.append(Paragraph(full_name,styles['body']))
    else:
        raise ValueError('Unknown document type')
    doc.build(story,onFirstPage=paint_page,onLaterPages=paint_page)
    return out.getvalue()
