from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import User

def role_required(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "You are not authorized to view this page.")
                return redirect('dashboard')
        return _wrapped_view
    return decorator

def admin_only(view_func):
    return role_required(allowed_roles=[User.ADMIN])(view_func)

def faculty_only(view_func):
    return role_required(allowed_roles=[User.FACULTY])(view_func)

def principal_only(view_func):
    return role_required(allowed_roles=[User.PRINCIPAL])(view_func)

def faculty_or_admin(view_func):
    return role_required(allowed_roles=[User.FACULTY, User.ADMIN])(view_func)
