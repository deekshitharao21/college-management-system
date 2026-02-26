from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import (
    CustomUserCreationForm, FacultySignUpForm, LoginForm, StudentForm,
    MarksForm, TimetableForm, StudentSignUpForm, NotificationForm,
    UserProfileForm, FacultyForm, AssignmentForm, AssignmentSubmissionForm
)

from .models import (
    User, Student, Faculty, Attendance, Marks, Timetable,
    Notification, CollegeEvent, CollegePhoto, Assignment, AssignmentSubmission
)



from django.contrib import messages

from .decorators import admin_only, faculty_only, principal_only, faculty_or_admin
from django.db.models import Q
from django.utils import timezone


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/signup.html', {'form': form})

def faculty_signup_view(request):
    if request.method == 'POST':
        form = FacultySignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Faculty account created successfully! Please log in.')
            return redirect('login')
    else:
        form = FacultySignUpForm()
    return render(request, 'auth/faculty_signup.html', {'form': form})

def student_signup_view(request):
    if request.method == 'POST':
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student account created successfully! Please log in.')
            return redirect('login')
    else:
        form = StudentSignUpForm()
    return render(request, 'auth/student_signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required
def dashboard_view(request):
    if request.user.role == User.ADMIN:
        return redirect('admin_dashboard')
    elif request.user.role == User.FACULTY:
        return redirect('faculty_dashboard')
    elif request.user.role == User.PRINCIPAL:
        return redirect('principal_dashboard')
    elif request.user.role == User.STUDENT:
        return redirect('student_dashboard')
    else:
        return redirect('login')


@login_required
def admin_dashboard(request):
    return render(request, 'dashboard/admin.html', {
        'student_count': Student.objects.count(),
        'faculty_count': Faculty.objects.count(),
    })

@login_required
def faculty_dashboard(request):
    fac = getattr(request.user, 'faculty_profile', None)
    if not fac:
        messages.error(request, "Faculty profile not found.")
        return redirect('login')
    
    if not request.user.is_authorized:
        return render(request, 'dashboard/pending_approval.html')
        
    return render(request, 'dashboard/faculty.html', {'faculty': fac})

@login_required
def principal_dashboard(request):
    faculty_list = Faculty.objects.all()
    all_marks = Marks.objects.all().select_related('student')
    # We need to link marks to faculty. Let's assume marks are recorded by the faculty marked in Attendance or just add a field later.
    # For now, I'll just show the marks and the faculty list.
    return render(request, 'dashboard/principal.html', {
        'faculty_list': faculty_list,
        'all_marks': all_marks
    })


@login_required
def student_dashboard(request):
    try:
        student = request.user.student_profile
    except Student.RelatedObjectDoesNotExist:
        messages.error(request, "You do not have a student profile.")
        return redirect('dashboard')
        
    timetable = Timetable.objects.filter(department=student.department, semester=student.semester).order_by('day', 'start_time')
    attendance = Attendance.objects.filter(student=student).order_by('-date')
    marks = Marks.objects.filter(student=student)
    
    # Calculate attendance percentage
    total = attendance.count()
    present = attendance.filter(status='Present').count()
    attendance_percent = (present / total * 100) if total > 0 else 0
    
    # Assignments due
    assignments_due = Assignment.objects.filter(
        department=student.department, 
        semester=student.semester,
        deadline__gte=timezone.now()
    ).count()
    
    events = CollegeEvent.objects.all().order_by('-date')[:5]
    photos = CollegePhoto.objects.all().order_by('order')
    
    return render(request, 'dashboard/student.html', {
        'student': student,
        'timetable': timetable,
        'attendance': attendance,
        'marks': marks,
        'attendance_percent': round(attendance_percent, 2),
        'assignments_due': assignments_due,
        'events': events,
        'photos': photos
    })



@login_required
def student_attendance(request):
    try:
        student = request.user.student_profile
    except Student.RelatedObjectDoesNotExist:
        messages.error(request, "You do not have a student profile.")
        return redirect('dashboard')
        
    attendance = Attendance.objects.filter(student=student).order_by('-date')
    
    total = attendance.count()
    present = attendance.filter(status='Present').count()
    attendance_percent = (present / total * 100) if total > 0 else 0
    
    return render(request, 'dashboard/student_attendance.html', {
        'student': student,
        'attendance': attendance,
        'attendance_percent': round(attendance_percent, 2)
    })




@login_required
def student_profile(request):
    try:
        student = request.user.student_profile
    except Student.RelatedObjectDoesNotExist:
        messages.error(request, "You do not have a student profile.")
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        u_form = UserProfileForm(request.POST, instance=request.user)
        s_form = StudentForm(request.POST, instance=student)
        if u_form.is_valid() and s_form.is_valid():
            u_form.save()
            s_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('student_profile')
    else:
        u_form = UserProfileForm(instance=request.user)
        s_form = StudentForm(instance=student)
    
    return render(request, 'dashboard/profile.html', {
        'student': student,
        'u_form': u_form,
        's_form': s_form
    })

@login_required
def student_marks_detail(request):
    try:
        student = request.user.student_profile
    except Student.RelatedObjectDoesNotExist:
        messages.error(request, "You do not have a student profile.")
        return redirect('dashboard')
    
    marks = Marks.objects.filter(student=student)
    return render(request, 'dashboard/marks_detail.html', {
        'student': student,
        'marks': marks
    })

@login_required
def faculty_profile(request):
    try:
        faculty = request.user.faculty_profile
    except Faculty.RelatedObjectDoesNotExist:
        messages.error(request, "Faculty profile not found.")
        return redirect('faculty_dashboard')
        
    if request.method == 'POST':
        u_form = UserProfileForm(request.POST, instance=request.user)
        f_form = FacultyForm(request.POST, instance=faculty)
        if u_form.is_valid() and f_form.is_valid():
            u_form.save()
            f_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('faculty_profile')
    else:
        u_form = UserProfileForm(instance=request.user)
        f_form = FacultyForm(instance=faculty)
        
    return render(request, 'dashboard/faculty_profile.html', {
        'faculty': faculty,
        'u_form': u_form,
        'f_form': f_form
    })

@login_required
def principal_profile(request):
    if request.method == 'POST':
        u_form = UserProfileForm(request.POST, instance=request.user)
        if u_form.is_valid():
            u_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('principal_profile')
    else:
        u_form = UserProfileForm(instance=request.user)
        
    return render(request, 'dashboard/principal_profile.html', {
        'user': request.user,
        'u_form': u_form
    })

@login_required
@faculty_only
def import_marks_xml(request):
    fac_profile = request.user.faculty_profile
    if request.method == 'POST' and request.FILES.get('xml_file'):
        import xml.etree.ElementTree as ET
        xml_file = request.FILES['xml_file']
        try:
            content = xml_file.read()
            if content.startswith(b'\xef\xbb\xbf'):
                content = content[3:]
            
            root = ET.fromstring(content)
            count = 0
            errors = []
            
            for item in root.findall('mark'):
                roll_el = item.find('roll_no')
                subj_el = item.find('subject')
                int_el = item.find('internal')
                ext_el = item.find('external')
                
                if any(el is None or el.text is None for el in (roll_el, subj_el, int_el, ext_el)):
                    errors.append("Invalid or empty fields in XML record.")
                    continue
                    
                roll_no = roll_el.text.strip()
                subject = subj_el.text.strip()
                try:
                    internal = int(int_el.text.strip())
                    external = int(ext_el.text.strip())
                except ValueError:
                    errors.append(f"Invalid marks for student {roll_no}")
                    continue
                
                try:
                    # Core Requirement: Linking to students correctly and ensuring department matches
                    student = Student.objects.get(roll_no=roll_no)
                    if student.department != fac_profile.department:
                        errors.append(f"Student {roll_no} does not belong to your department.")
                        continue

                    Marks.objects.update_or_create(
                        student=student, 
                        subject=subject,
                        defaults={
                            'internal_marks': internal,
                            'external_marks': external,
                            'recorded_by': fac_profile
                        }
                    )
                    count += 1
                except Student.DoesNotExist:
                    errors.append(f"Student with roll no {roll_no} not found.")
            
            if count > 0:
                messages.success(request, f'Successfully imported {count} marks.')
            if errors:
                for err in errors[:5]: # Show first 5 errors to avoid flooding
                    messages.warning(request, err)
                if len(errors) > 5:
                    messages.warning(request, f"...and {len(errors)-5} more errors.")
                    
        except Exception as e:
            messages.error(request, f'Error parsing XML: {str(e)}')
    return redirect('marks_list')



@login_required
@faculty_or_admin
def import_timetable_xml(request):
    if request.method == 'POST' and request.FILES.get('xml_file'):
        import xml.etree.ElementTree as ET
        xml_file = request.FILES['xml_file']
        try:
            content = xml_file.read()
            if content.startswith(b'\xef\xbb\xbf'):
                content = content[3:]
            
            root = ET.fromstring(content)
            count = 0
            errors = []
            
            for item in root.findall('entry'):
                day_el = item.find('day')
                subj_el = item.find('subject')
                start_el = item.find('start_time')
                end_el = item.find('end_time')
                fac_id_el = item.find('faculty_id') # User ID or Username? Let's use username for clarity
                room_el = item.find('room')
                dept_el = item.find('department')
                sem_el = item.find('semester')
                
                if any(el is None or el.text is None for el in (day_el, subj_el, start_el, end_el, fac_id_el, room_el, dept_el, sem_el)):
                    errors.append("Empty/Invalid data in XML entry.")
                    continue
                
                try:
                    faculty_user = User.objects.get(username=fac_id_el.text.strip())
                    faculty_profile = faculty_user.faculty_profile
                except (User.DoesNotExist, Faculty.RelatedObjectDoesNotExist):
                    errors.append(f"Faculty {fac_id_el.text} not found.")
                    continue
                
                try:
                    sem_val = int(sem_el.text.strip())
                except (ValueError, TypeError):
                    errors.append(f"Invalid semester '{sem_el.text}' for {subj_el.text}.")
                    continue

                Timetable.objects.create(
                    day=day_el.text.strip().capitalize(),
                    subject=subj_el.text.strip(),
                    start_time=start_el.text.strip(),
                    end_time=end_el.text.strip(),
                    faculty=faculty_profile,
                    room=room_el.text.strip(),
                    department=dept_el.text.strip(),
                    semester=sem_val
                )
                count += 1
            
            if count > 0:
                messages.success(request, f'Successfully imported {count} timetable entries.')
            if errors:
                for err in errors[:5]:
                    messages.warning(request, err)
                    
        except Exception as e:
            messages.error(request, f'Error parsing XML: {str(e)}')
            
    return redirect('timetable_list')

@login_required
@principal_only
def toggle_faculty_authorization(request, pk):
    faculty = Faculty.objects.get(pk=pk)
    user = faculty.user
    user.is_authorized = not user.is_authorized
    user.save()
    status = "authorized" if user.is_authorized else "de-authorized"
    messages.success(request, f'Faculty {user.username} has been {status}.')
    return redirect('principal_dashboard')

# Student Management (Admin Only)


@admin_only
def student_list(request):
    query = request.GET.get('q')
    students = Student.objects.all()
    if query:
        students = students.filter(
            Q(name__icontains=query) | 
            Q(roll_no__icontains=query) |
            Q(department__icontains=query)
        )
    return render(request, 'students/student_list.html', {'students': students})

@admin_only
def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student added successfully.")
            return redirect('student_list')
    else:
        form = StudentForm()
    return render(request, 'students/student_form.html', {'form': form, 'title': 'Add Student'})

@admin_only
def student_update(request, pk):
    student = Student.objects.get(pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Student details updated.")
            return redirect('student_list')
    else:
        form = StudentForm(instance=student)
    return render(request, 'students/student_form.html', {'form': form, 'title': 'Edit Student'})

@admin_only
def student_delete(request, pk):
    student = Student.objects.get(pk=pk)
    if request.method == 'POST':
        student.delete()
        messages.success(request, "Student deleted successfully.")
        return redirect('student_list')
    return render(request, 'students/student_confirm_delete.html', {'student': student})

# Attendance Management
@faculty_only
def attendance_mark(request):
    fac_profile = request.user.faculty_profile
    students = Student.objects.filter(department=fac_profile.department)
    
    if request.method == 'POST':
        date = request.POST.get('date')
        session = request.POST.get('session')
        if not date or not session:
            messages.error(request, "Please select both date and session.")
        else:
            for student in students:
                status = request.POST.get(f'status_{student.id}')
                if status:
                    Attendance.objects.update_or_create(
                        student=student, 
                        date=date,
                        session=session,
                        defaults={'status': status, 'marked_by': fac_profile}
                    )
            messages.success(request, f"Attendance marked for {date} ({session} session).")
            return redirect('faculty_dashboard')
    
    from datetime import date as dt
    return render(request, 'attendance/mark_attendance.html', {
        'students': students,
        'today': dt.today().strftime('%Y-%m-%d'),
        'sessions': ['Morning', 'Afternoon']
    })

@login_required
def attendance_report(request):
    if request.user.role not in [User.ADMIN, User.PRINCIPAL, User.FACULTY]:
        return redirect('login')

    students = Student.objects.all()
    if request.user.role == User.FACULTY:
        students = students.filter(department=request.user.faculty_profile.department)
    
    student_stats = []
    for student in students:
        total_sessions = Attendance.objects.filter(student=student).count()
        present_sessions = Attendance.objects.filter(student=student, status='Present').count()
        percent = (present_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        # Breakdown
        morning_present = Attendance.objects.filter(student=student, session='Morning', status='Present').count()
        morning_total = Attendance.objects.filter(student=student, session='Morning').count()
        afternoon_present = Attendance.objects.filter(student=student, session='Afternoon', status='Present').count()
        afternoon_total = Attendance.objects.filter(student=student, session='Afternoon').count()

        student_stats.append({
            'student': student,
            'total': total_sessions,
            'present': present_sessions,
            'percent': round(percent, 2),
            'morning_present': morning_present,
            'morning_total': morning_total,
            'afternoon_present': afternoon_present,
            'afternoon_total': afternoon_total,
        })

    return render(request, 'attendance/attendance_report.html', {'stats': student_stats})

# Marks Management
@faculty_only
def marks_list(request):
    fac_profile = request.user.faculty_profile
    # Filter marks for students in faculty's department
    marks = Marks.objects.filter(student__department=fac_profile.department)
    return render(request, 'marks/marks_list.html', {'marks': marks})

@faculty_only
def marks_add(request):
    if request.method == 'POST':
        form = MarksForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Marks uploaded successfully.")
            return redirect('marks_list')
    else:
        # Only show students in faculty's department
        form = MarksForm()
        form.fields['student'].queryset = Student.objects.filter(department=request.user.faculty_profile.department)
    return render(request, 'marks/marks_form.html', {'form': form, 'title': 'Upload Marks'})

@faculty_only
def marks_update(request, pk):
    marks = Marks.objects.get(pk=pk)
    if request.method == 'POST':
        form = MarksForm(request.POST, instance=marks)
        if form.is_valid():
            form.save()
            messages.success(request, "Marks updated.")
            return redirect('marks_list')
    else:
        form = MarksForm(instance=marks)
    return render(request, 'marks/marks_form.html', {'form': form, 'title': 'Edit Marks'})

@login_required
def marks_analytics(request):
    if request.user.role not in [User.ADMIN, User.PRINCIPAL]:
        return redirect('login')
    
    marks = Marks.objects.all()
    # Simple analytics: average marks per subject
    from django.db.models import Avg
    analytics = Marks.objects.values('subject').annotate(avg_total=Avg('total_marks'))
    
    return render(request, 'marks/analytics.html', {'analytics': analytics})

# Timetable Management
@login_required
def timetable_list(request):
    timetable = Timetable.objects.all().order_by('day', 'start_time')
    return render(request, 'timetable/timetable_list.html', {'timetable': timetable})

@login_required
def timetable_manage(request):
    if request.user.role not in [User.PRINCIPAL, User.FACULTY]:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    # Faculty only manage their department/semester if strictly required, but usually they manage global for visibility
    timetable = Timetable.objects.all().order_by('day', 'start_time')
    return render(request, 'timetable/timetable_list.html', {'timetable': timetable})

@login_required
def timetable_add(request):
    if request.user.role not in [User.PRINCIPAL, User.FACULTY]:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = TimetableForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Timetable entry added.")
            return redirect('timetable_list')
    else:
        form = TimetableForm()
    return render(request, 'timetable/timetable_form.html', {'form': form, 'title': 'Add Timetable Entry'})

@login_required
def timetable_update(request, pk):
    if request.user.role not in [User.PRINCIPAL, User.FACULTY]:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
        
    entry = get_object_or_404(Timetable, pk=pk)
    if request.method == 'POST':
        form = TimetableForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, "Timetable entry updated.")
            return redirect('timetable_list')
    else:
        form = TimetableForm(instance=entry)
    return render(request, 'timetable/timetable_form.html', {'form': form, 'title': 'Edit Timetable Entry'})

@login_required
def timetable_delete(request, pk):
    if request.user.role not in [User.PRINCIPAL, User.FACULTY]:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
        
    entry = get_object_or_404(Timetable, pk=pk)
    if request.method == 'POST':
        entry.delete()
        messages.success(request, "Entry deleted.")
        return redirect('timetable_list')
    return render(request, 'timetable/timetable_confirm_delete.html', {'entry': entry})

@login_required
def notification_list(request):
    # Principal and Faculty can see all, Students only see all public notifications
    notifications = Notification.objects.all().order_by('-created_at')
    return render(request, 'notifications/notification_list.html', {'notifications': notifications})

@login_required
def export_attendance_csv(request):
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student', 'Roll No', 'Date', 'Status'])

    attendances = Attendance.objects.all()
    if request.user.role == User.FACULTY:
        attendances = attendances.filter(student__department=request.user.faculty_profile.department)

    for att in attendances:
        writer.writerow([att.student.name, att.student.roll_no, att.date, att.status])

    return response





@login_required
def notification_create(request):
    if request.user.role not in [User.PRINCIPAL, User.FACULTY]:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.user = request.user
            notification.save()
            messages.success(request, "Notification posted successfully.")
            return redirect('notification_list')
    else:
        form = NotificationForm()
    return render(request, 'notifications/notification_form.html', {'form': form, 'title': 'Post Notification'})

@login_required
def notification_update(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    if notification.user != request.user and request.user.role != User.PRINCIPAL:
        messages.error(request, "Access denied.")
        return redirect('notification_list')
    
    if request.method == 'POST':
        form = NotificationForm(request.POST, instance=notification)
        if form.is_valid():
            form.save()
            messages.success(request, "Notification updated successfully.")
            return redirect('notification_list')
    else:
        form = NotificationForm(instance=notification)
    return render(request, 'notifications/notification_form.html', {'form': form, 'title': 'Edit Notification'})

@login_required
def notification_delete(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    if notification.user != request.user and request.user.role != User.PRINCIPAL:
        messages.error(request, "Access denied.")
        return redirect('notification_list')
    
    if request.method == 'POST':
        notification.delete()
        messages.success(request, "Notification deleted.")
        return redirect('notification_list')
    return render(request, 'notifications/notification_confirm_delete.html', {'notification': notification})


# Assignment Management
@login_required
def assignment_list(request):
    if request.user.role == User.FACULTY:
        assignments = Assignment.objects.filter(faculty=request.user.faculty_profile).order_by('-created_at')
    elif request.user.role == User.STUDENT:
        student = request.user.student_profile
        assignments = Assignment.objects.filter(department=student.department, semester=student.semester).order_by('-created_at')
    else:
        assignments = Assignment.objects.all().order_by('-created_at')
    
    return render(request, 'assignments/assignment_list.html', {'assignments': assignments})

@faculty_only
def assignment_create(request):
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.faculty = request.user.faculty_profile
            assignment.save()
            messages.success(request, "Assignment posted successfully.")
            return redirect('assignment_list')
    else:
        form = AssignmentForm()
    return render(request, 'assignments/assignment_form.html', {'form': form, 'title': 'Post Assignment'})

@login_required
def assignment_detail(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    submission = None
    if request.user.role == User.STUDENT:
        submission = AssignmentSubmission.objects.filter(assignment=assignment, student=request.user.student_profile).first()
        
    if request.method == 'POST' and request.user.role == User.STUDENT:
        form = AssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.assignment = assignment
            sub.student = request.user.student_profile
            sub.save()
            messages.success(request, "Assignment submitted successfully.")
            return redirect('assignment_detail', pk=pk)
    else:
        form = AssignmentSubmissionForm(instance=submission)
        
    return render(request, 'assignments/assignment_detail.html', {
        'assignment': assignment,
        'form': form,
        'submission': submission
    })

@faculty_only
def submission_list(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    if assignment.faculty != request.user.faculty_profile:
        messages.error(request, "Access denied.")
        return redirect('assignment_list')
        
    submissions = assignment.submissions.all()
    return render(request, 'assignments/submission_list.html', {
        'assignment': assignment,
        'submissions': submissions
    })
