from django.db import models


class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', '易'),
        ('medium', '中'),
        ('hard', '難'),
    ]

    chapter = models.CharField(max_length=100, verbose_name='章節')
    text = models.TextField(verbose_name='題目內容')
    explanation = models.TextField(blank=True, verbose_name='詳解')
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        verbose_name='難易度'
    )

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
class QuizAttempt(models.Model):
    session_key = models.CharField(max_length=100)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"作答紀錄：{self.score}/{self.total_questions}"


class AnswerRecord(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answer_records"
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )
    selected_choice = models.ForeignKey(
        Choice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    selected_answer_text = models.CharField(max_length=255, blank=True)
    correct_answer_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.question.text[:20]} - {'答對' if self.is_correct else '答錯'}"