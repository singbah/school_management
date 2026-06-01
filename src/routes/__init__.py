from src.routes.students.users_auth import user_auths_bp
from src.routes.admin.admin_auths import admin_auths
from src.routes.services.students_services import student_records
from src.routes.admin.admin_dashboard import admin_dashboard
from src.routes.faculatities.teachers import teacher_bp
from src.routes.faculatities.fac_auths import facal_auths_bp

idle = [user_auths_bp, admin_auths, 
        admin_dashboard, teacher_bp, student_records, facal_auths_bp]

all_bps = [teacher_bp]