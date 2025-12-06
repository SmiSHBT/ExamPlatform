from django.shortcuts import redirect
from functools import wraps
from django.contrib.auth.decorators import login_required

def auth_required(view_func):
    return login_required(view_func)
