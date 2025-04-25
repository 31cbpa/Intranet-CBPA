from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from functools import wraps
from .models import UserProfile


def role_required(allowed_roles=None):

    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:

                if request.user.groups.filter(name__in=allowed_roles).exists():
                    return view_func(request, *args, **kwargs)
                else:
                    return redirect('home')
            else:
                return redirect('login')
        return _wrapped_view
    return decorator