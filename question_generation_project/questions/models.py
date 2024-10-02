from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class QuestionGenerationHistory(models.Model):
    context = models.TextField()
    questions = models.JSONField()
    generated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Generated at {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}"
