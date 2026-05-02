from django.shortcuts import render
from .models import Question, Choice
import random


def home(request):
    return render(request, 'quiz/home.html')


def quiz_view(request):
    if request.method == 'POST':
        question_ids = request.POST.get('question_ids', '')
        question_ids = [int(qid) for qid in question_ids.split(',') if qid]

        questions = Question.objects.filter(id__in=question_ids)

        results = []
        score = 0

        for question in questions:
            selected_choice_id = request.POST.get(f'question_{question.id}')
            correct_choice = question.choices.filter(is_correct=True).first()
            selected_choice = None

            if selected_choice_id:
                selected_choice = Choice.objects.get(id=selected_choice_id)

            is_correct = selected_choice == correct_choice

            if is_correct:
                score += 1

            results.append({
                'question': question,
                'selected_choice': selected_choice,
                'correct_choice': correct_choice,
                'is_correct': is_correct,
            })

        return render(request, 'quiz/result.html', {
            'results': results,
            'score': score,
            'total': len(results),
        })

    questions = list(Question.objects.all().order_by('?')[:10])

    question_data = []
    for question in questions:
        choices = list(question.choices.all())
        random.shuffle(choices)
        question_data.append({
            'question': question,
            'choices': choices,
        })

    question_ids = ','.join(str(q.id) for q in questions)

    return render(request, 'quiz/quiz.html', {
        'question_data': question_data,
        'question_ids': question_ids,
    })
