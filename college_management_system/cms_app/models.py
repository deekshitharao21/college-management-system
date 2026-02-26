from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ADMIN = 'ADMIN'
    FACULTY = 'FACULTY'
    PRINCIPAL = 'PRINCIPAL'
    STUDENT = 'STUDENT'
    
    ROLE_CHOICES = (
        (ADMIN, 'Admin'),
        (FACULTY, 'Faculty'),
        (PRINCIPAL, 'Principal'),
        (STUDENT, 'Student'),
    )

    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=FACULTY)
    is_authorized = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def unread_notifications_count(self):
        return self.notifications.filter(is_read=False).count()


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True)
    name = models.CharField(max_length=100)

    roll_no = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    semester = models.IntegerField()
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    history = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.roll_no})"

class Faculty(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty_profile')
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.designation}"

class Timetable(models.Model):
    DAYS = (
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
    )
    day = models.CharField(max_length=10, choices=DAYS)
    subject = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    room = models.CharField(max_length=20)
    department = models.CharField(max_length=100, default='General')
    semester = models.IntegerField(default=1)


    def __str__(self):
        return f"{self.day} - {self.subject} ({self.start_time}-{self.end_time})"

class Attendance(models.Model):
    STATUS = (
        ('Present', 'Present'),
        ('Absent', 'Absent'),
    )
    SESSION_CHOICES = (
        ('Morning', 'Morning'),
        ('Afternoon', 'Afternoon'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    session = models.CharField(max_length=10, choices=SESSION_CHOICES, default='Morning')
    status = models.CharField(max_length=10, choices=STATUS)
    marked_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ('student', 'date', 'session')

    def __str__(self):
        return f"{self.student.name} - {self.date} ({self.session}) - {self.status}"

class Marks(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    internal_marks = models.IntegerField(default=0)
    external_marks = models.IntegerField(default=0)
    total_marks = models.IntegerField(default=0)
    recorded_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)


    def save(self, *args, **kwargs):
        self.total_marks = self.internal_marks + self.external_marks
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.name} - {self.subject}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200, default="Campus Update")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"

class CollegeEvent(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class CollegePhoto(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='highlighter/')
    description = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='assignments')
    department = models.CharField(max_length=100)
    semester = models.IntegerField()
    deadline = models.DateTimeField()
    file = models.FileField(upload_to='assignments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.department} Sem {self.semester}"

class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    file = models.FileField(upload_to='submissions/')
    comment = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('assignment', 'student')

    def __str__(self):
        return f"{self.student.name} - {self.assignment.title}"
