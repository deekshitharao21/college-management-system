from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('signup/', views.signup_view, name='signup'),
    path('signup/student/', views.student_signup_view, name='student_signup'),
    path('signup/faculty/', views.faculty_signup_view, name='faculty_signup'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/faculty/', views.faculty_dashboard, name='faculty_dashboard'),
    path('dashboard/principal/', views.principal_dashboard, name='principal_dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/student/attendance/', views.student_attendance, name='student_attendance'),
    path('dashboard/student/profile/', views.student_profile, name='student_profile'),
    path('dashboard/student/marks/', views.student_marks_detail, name='student_marks_detail'),
    path('dashboard/faculty/profile/', views.faculty_profile, name='faculty_profile'),
    path('dashboard/principal/profile/', views.principal_profile, name='principal_profile'),
    path('marks/import-xml/', views.import_marks_xml, name='import_marks_xml'),
    path('faculty/toggle-auth/<int:pk>/', views.toggle_faculty_authorization, name='toggle_faculty_authorization'),

    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/add/', views.notification_create, name='notification_add'),
    path('notifications/edit/<int:pk>/', views.notification_update, name='notification_edit'),
    path('notifications/delete/<int:pk>/', views.notification_delete, name='notification_delete'),

    # Student Management
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_create, name='student_add'),
    path('students/edit/<int:pk>/', views.student_update, name='student_edit'),
    path('students/delete/<int:pk>/', views.student_delete, name='student_delete'),

    # Attendance
    path('attendance/mark/', views.attendance_mark, name='attendance_mark'),
    path('attendance/report/', views.attendance_report, name='attendance_report'),

    # Marks
    path('marks/', views.marks_list, name='marks_list'),
    path('marks/add/', views.marks_add, name='marks_add'),
    path('marks/edit/<int:pk>/', views.marks_update, name='marks_edit'),
    path('marks/analytics/', views.marks_analytics, name='marks_analytics'),

    # Timetable
    path('timetable/', views.timetable_list, name='timetable_list'),
    path('timetable/add/', views.timetable_add, name='timetable_add'),
    path('timetable/edit/<int:pk>/', views.timetable_update, name='timetable_edit'),
    path('timetable/delete/<int:pk>/', views.timetable_delete, name='timetable_delete'),
    path('timetable/import-xml/', views.import_timetable_xml, name='import_timetable_xml'),

    # Export
    # Export
    path('export/attendance/', views.export_attendance_csv, name='export_attendance'),

    # Assignments
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/add/', views.assignment_create, name='assignment_add'),
    path('assignments/view/<int:pk>/', views.assignment_detail, name='assignment_detail'),
    path('assignments/submissions/<int:pk>/', views.submission_list, name='submission_list'),
]
