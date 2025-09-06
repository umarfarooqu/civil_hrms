Civil HRMS (Django + MySQL)
Features:
1) Search by HRMS, Branch, College (/hr/search/).
2) Import for all tables in Admin via django-import-export.
3) Export CSV (/hr/export/csv), Excel (/hr/export/excel), PDF (/hr/export/pdf).
4) Employee login portal to edit ONLY related data (education/postings/...); link User to Employee.user.
5) Superuser can edit anything via Admin.
6) Report customization: edit templates/report.html (PDF), Excel/CSV follow search filters.

Setup:
- python -m venv .venv && source .venv/bin/activate  (Windows: .venv\Scripts\activate)
- pip install -r requirements.txt
- copy .env.sample .env  # set MySQL creds
- python manage.py migrate
- python manage.py createsuperuser
- python manage.py runserver
Admin: http://127.0.0.1:8000/admin
Portal: http://127.0.0.1:8000/hr/portal/
