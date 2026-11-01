from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pdf_documents import build_pdf

DATA={
    'fullName':'Nandi Dlamini','email':'nandi@example.com','phone':'+268 7612 3456','location':'Mbabane, Eswatini',
    'headline':'Administrative Assistant & Office Coordinator',
    'summary':'A resourceful and organised graduate with strong communication skills, an eye for detail, and a passion for helping teams succeed.',
    'experience':'Office Assistant - Example Group, 2024 to Present\nManaged visitor enquiries, office records and meeting schedules.\n\nVolunteer Coordinator - Community Centre, 2023\nOrganised weekly activities and helped manage records.',
    'education':'Diploma in Business Management - Example College, 2023',
    'skills':'Microsoft Office, Customer Service, Scheduling, Administration, Communication',
    'projects':'Organised a community initiative with 40+ participants',
    'languages':'English and siSwati','jobTitle':'Administrative Assistant',
    'company':'Sample Organisation','hiringManager':'Recruitment Team',
    'strengths':'I am skilled in diary management, communication and data handling.',
    'motivation':'Your organisation is a great place to make a meaningful contribution.',
}

def test_each_theme_pdf():
    for kind in ('cv','letter'):
        for theme in ('violet','navy','forest','coral'):
            doc=build_pdf(kind,DATA,theme)
            assert doc.startswith(b'%PDF-')
            assert len(doc)>1500

def test_escapes_user_content():
    d={**DATA,'fullName':'<Nandi> & Co', 'summary':'Me & my team <3'}
    assert build_pdf('cv',d).startswith(b'%PDF-')
