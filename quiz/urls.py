from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('quiz/', views.quiz_view, name='quiz'),
    path('records/', views.answer_records, name='answer_records'),
    path('wrong-review/', views.wrong_review, name='wrong_review'),
]