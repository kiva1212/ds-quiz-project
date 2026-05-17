from django.shortcuts import render
from .models import Question, Choice, QuizAttempt, AnswerRecord
import random


def get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def home(request):
    return render(request, 'quiz/home.html')


def quiz_view(request):
    if request.method == 'POST':
        session_key = get_session_key(request)

        question_ids = request.POST.get('question_ids', '')
        question_ids = [int(qid) for qid in question_ids.split(',') if qid]

        questions = Question.objects.filter(id__in=question_ids)

        results = []
        score = 0

        attempt = QuizAttempt.objects.create(
            session_key=session_key,
            score=0,
            total_questions=len(question_ids)
        )

        for question in questions:
            selected_choice_id = request.POST.get(f'question_{question.id}')
            correct_choice = question.choices.filter(is_correct=True).first()
            selected_choice = None

            if selected_choice_id:
                selected_choice = question.choices.filter(id=selected_choice_id).first()

            is_correct = (
                selected_choice is not None and
                correct_choice is not None and
                selected_choice.id == correct_choice.id
            )

            if is_correct:
                score += 1

            AnswerRecord.objects.create(
                attempt=attempt,
                question=question,
                selected_choice=selected_choice,
                selected_answer_text=selected_choice.text if selected_choice else '未作答',
                correct_answer_text=correct_choice.text if correct_choice else '未設定正確答案',
                is_correct=is_correct
            )

            results.append({
                'question': question,
                'selected_choice': selected_choice,
                'correct_choice': correct_choice,
                'is_correct': is_correct,
            })

        attempt.score = score
        attempt.save()

        return render(request, 'quiz/result.html', {
            'results': results,
            'score': score,
            'total': len(results),
        })

    questions = list(Question.objects.all().order_by('?')[:10])

    question_data = []

    for question in questions:
        choices = list(question.choices.all())

        # 隨機排列選項，但讓「以上皆非」固定在最後
        none_choices = [c for c in choices if c.text.strip() == '以上皆非']
        normal_choices = [c for c in choices if c.text.strip() != '以上皆非']

        random.shuffle(normal_choices)
        choices = normal_choices + none_choices

        question_data.append({
            'question': question,
            'choices': choices,
        })

    question_ids = ','.join(str(q.id) for q in questions)

    return render(request, 'quiz/quiz.html', {
        'question_data': question_data,
        'question_ids': question_ids,
    })


def answer_records(request):
    session_key = get_session_key(request)

    attempts = QuizAttempt.objects.filter(
        session_key=session_key
    ).order_by('-created_at').prefetch_related('answer_records__question')

    return render(request, 'quiz/answer_records.html', {
        'attempts': attempts,
    })


def wrong_review(request):
    session_key = get_session_key(request)

    if request.method == 'POST':
        question_ids = request.POST.get('question_ids', '')
        question_ids = [int(qid) for qid in question_ids.split(',') if qid]

        questions = Question.objects.filter(id__in=question_ids)

        results = []
        score = 0

        attempt = QuizAttempt.objects.create(
            session_key=session_key,
            score=0,
            total_questions=len(question_ids)
        )

        for question in questions:
            selected_choice_id = request.POST.get(f'question_{question.id}')
            correct_choice = question.choices.filter(is_correct=True).first()
            selected_choice = None

            if selected_choice_id:
                selected_choice = question.choices.filter(id=selected_choice_id).first()

            is_correct = (
                selected_choice is not None and
                correct_choice is not None and
                selected_choice.id == correct_choice.id
            )

            if is_correct:
                score += 1

            AnswerRecord.objects.create(
                attempt=attempt,
                question=question,
                selected_choice=selected_choice,
                selected_answer_text=selected_choice.text if selected_choice else '未作答',
                correct_answer_text=correct_choice.text if correct_choice else '未設定正確答案',
                is_correct=is_correct
            )

            results.append({
                'question': question,
                'selected_choice': selected_choice,
                'correct_choice': correct_choice,
                'is_correct': is_correct,
            })

        attempt.score = score
        attempt.save()

        return render(request, 'quiz/result.html', {
            'results': results,
            'score': score,
            'total': len(results),
        })

    # 只抓「每一題最新一次作答仍然答錯」的題目
    # 如果某題後來在錯題複習答對，就不會再出現在錯題複習模式
    records = AnswerRecord.objects.filter(
        attempt__session_key=session_key
    ).order_by('question_id', '-created_at', '-id')

    latest_records = {}

    for record in records:
        if record.question_id not in latest_records:
            latest_records[record.question_id] = record

    wrong_question_ids = [
        question_id
        for question_id, record in latest_records.items()
        if not record.is_correct
    ]

    questions = list(Question.objects.filter(id__in=wrong_question_ids))

    question_data = []

    for question in questions:
        choices = list(question.choices.all())

        # 隨機排列選項，但讓「以上皆非」固定在最後
        none_choices = [c for c in choices if c.text.strip() == '以上皆非']
        normal_choices = [c for c in choices if c.text.strip() != '以上皆非']

        random.shuffle(normal_choices)
        choices = normal_choices + none_choices

        question_data.append({
            'question': question,
            'choices': choices,
        })

    question_ids = ','.join(str(q.id) for q in questions)

    return render(request, 'quiz/wrong_review.html', {
        'question_data': question_data,
        'question_ids': question_ids,
    })