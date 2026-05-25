from src.routes.students.users_auth import user_auths_bp
from src.routes.admin.admin_auths import admin_auths
from src.routes.services.students_services import student_records
from src.routes.admin.admin_dashboard import admin_dashboard

all_bps = [user_auths_bp, admin_auths, student_records, admin_dashboard]