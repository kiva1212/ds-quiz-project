from django.contrib import admin
from .models import Question, Choice


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'chapter', 'text')
    search_fields = ('text', 'chapter')
    inlines = [ChoiceInline]