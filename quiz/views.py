from django.shortcuts import render
from .models import Question, Choice, QuizAttempt, AnswerRecord
import random


def get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def make_question_data(questions):
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

    return question_data


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

        # 建立「這一次」的測驗紀錄
        attempt = QuizAttempt.objects.create(
            session_key=session_key,
            score=0,
            total_questions=len(question_ids)
        )

        # 把這一次測驗的 id 存進 session
        # 之後作答記錄與錯題複習只看這一次
        request.session['current_attempt_id'] = attempt.id

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

    # 只要重新進入測驗頁，代表準備開始新的一次測驗
    # 在還沒送出前，不顯示上一輪的作答紀錄與錯題
    if 'current_attempt_id' in request.session:
        del request.session['current_attempt_id']

    questions = list(Question.objects.all().order_by('?')[:20])
    question_data = make_question_data(questions)
    question_ids = ','.join(str(q.id) for q in questions)

    return render(request, 'quiz/quiz.html', {
        'question_data': question_data,
        'question_ids': question_ids,
    })


def answer_records(request):
    current_attempt_id = request.session.get('current_attempt_id')

    # 如果目前還沒有完成測驗，就不顯示任何舊紀錄
    if not current_attempt_id:
        return render(request, 'quiz/answer_records.html', {
            'attempts': [],
        })

    attempts = QuizAttempt.objects.filter(
        id=current_attempt_id
    ).prefetch_related('answer_records__question')

    return render(request, 'quiz/answer_records.html', {
        'attempts': attempts,
    })


def wrong_review(request):
    current_attempt_id = request.session.get('current_attempt_id')

    # 如果目前還沒有完成測驗，就不顯示任何錯題
    if not current_attempt_id:
        return render(request, 'quiz/wrong_review.html', {
            'question_data': [],
            'question_ids': '',
        })

    if request.method == 'POST':
        question_ids = request.POST.get('question_ids', '')
        question_ids = [int(qid) for qid in question_ids.split(',') if qid]

        questions = Question.objects.filter(id__in=question_ids)

        results = []
        score = 0

        # 錯題複習也建立一次新的測驗紀錄
        attempt = QuizAttempt.objects.create(
            session_key=get_session_key(request),
            score=0,
            total_questions=len(question_ids)
        )

        # 錯題複習送出後，作答記錄改成顯示這一次錯題複習的結果
        request.session['current_attempt_id'] = attempt.id

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

    # 只抓「目前這一次測驗」答錯的題目
    wrong_records = AnswerRecord.objects.filter(
        attempt_id=current_attempt_id,
        is_correct=False
    )

    wrong_question_ids = wrong_records.values_list('question_id', flat=True)

    questions = list(Question.objects.filter(id__in=wrong_question_ids))
    question_data = make_question_data(questions)
    question_ids = ','.join(str(q.id) for q in questions)

    return render(request, 'quiz/wrong_review.html', {
        'question_data': question_data,
        'question_ids': question_ids,
    })