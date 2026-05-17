from django.contrib import admin
from .models import Question, Choice, QuizAttempt, AnswerRecord


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'chapter', 'text')
    search_fields = ('text', 'chapter')
    inlines = [ChoiceInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'session_key', 'score', 'total_questions', 'created_at')
    search_fields = ('session_key',)
    list_filter = ('created_at',)


@admin.register(AnswerRecord)
class AnswerRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'attempt', 'question', 'selected_answer_text', 'correct_answer_text', 'is_correct', 'created_at')
    search_fields = ('question__text', 'selected_answer_text', 'correct_answer_text')
    list_filter = ('is_correct', 'created_at')