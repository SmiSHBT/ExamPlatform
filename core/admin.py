from django.contrib import admin
from .models import Test, Result, FocusLog, Screenshot
admin.site.register(Test)
admin.site.register(Result)
admin.site.register(FocusLog)
admin.site.register(Screenshot)
