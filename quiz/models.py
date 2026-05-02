from django.db import models


class Question(models.Model):
    chapter = models.CharField(max_length=100, verbose_name='章節')
    text = models.TextField(verbose_name='題目內容')
    explanation = models.TextField(blank=True, verbose_name='詳解')

    def __str__(self):
        return self.text[:30]


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices'
    )
    text = models.CharField(max_length=255, verbose_name='選項內容')
    is_correct = models.BooleanField(default=False, verbose_name='是否為正確答案')

    def __str__(self):
        return self.text