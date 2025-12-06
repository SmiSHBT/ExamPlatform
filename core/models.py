from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Test(models.Model):
    title = models.CharField(max_length=200)
    file_path = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title

class Result(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    answers_json = models.TextField()
    start_time = models.DateTimeField()
    finish_time = models.DateTimeField()
    focus_loss_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class FocusLog(models.Model):
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='focus_logs')
    timestamp = models.DateTimeField()
    event_type = models.CharField(max_length=100)
    extra = models.TextField(blank=True, null=True)

class Screenshot(models.Model):
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='screenshots')
    image = models.ImageField(upload_to='screenshots/')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_to_telegram = models.BooleanField(default=False)
