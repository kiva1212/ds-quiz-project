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
        correct_count = 0
        total_questions = len(question_ids)

        # 建立這一次正式測驗紀錄
        attempt = QuizAttempt.objects.create(
            session_key=session_key,
            score=0,
            total_questions=total_questions
        )

        # 只記住這一次正式測驗
        request.session['current_attempt_id'] = attempt.id

        # 取得間隔學習錯題清單
        spaced_wrong_ids = request.session.get('spaced_wrong_ids', [])

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
                correct_count += 1

                # 如果這題之前答錯，這次正式測驗答對，就從間隔學習清單移除
                if question.id in spaced_wrong_ids:
                    spaced_wrong_ids.remove(question.id)
            else:
                # 如果這題答錯，加入間隔學習錯題清單
                if question.id not in spaced_wrong_ids:
                    spaced_wrong_ids.append(question.id)

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

        # 更新間隔學習錯題清單
        request.session['spaced_wrong_ids'] = spaced_wrong_ids
        request.session.modified = True

        # 正式測驗換算成 100 分
        score_percent = round((correct_count / total_questions) * 100) if total_questions > 0 else 0

        attempt.score = score_percent
        attempt.save()

        return render(request, 'quiz/result.html', {
            'results': results,
            'score': score_percent,
            'total': 100,
            'correct_count': correct_count,
            'total_questions': total_questions,
            'is_review': False,
        })

    # 重新進入正式測驗時，清除上一輪作答紀錄顯示狀態
    # 但不要清除 spaced_wrong_ids，因為它是間隔學習用的
    if 'current_attempt_id' in request.session:
        del request.session['current_attempt_id']

    # 允許學生選擇 5、10、15、20 題
    question_count = request.GET.get('count', '10')

    try:
        question_count = int(question_count)
    except ValueError:
        question_count = 10

    if question_count not in [5, 10, 15, 20]:
        question_count = 10

    # 取得之前正式測驗答錯的題目，優先安排出現
    spaced_wrong_ids = request.session.get('spaced_wrong_ids', [])

    spaced_wrong_questions = list(
        Question.objects.filter(id__in=spaced_wrong_ids)
    )

    random.shuffle(spaced_wrong_questions)

    # 先放錯題，但最多不超過本次題數
    selected_questions = spaced_wrong_questions[:question_count]
    selected_ids = [q.id for q in selected_questions]

    # 再用其他題目補滿
    remaining_count = question_count - len(selected_questions)

    if remaining_count > 0:
        other_questions = list(
            Question.objects.exclude(id__in=selected_ids).order_by('?')[:remaining_count]
        )
        selected_questions += other_questions

    random.shuffle(selected_questions)

    question_data = make_question_data(selected_questions)
    question_ids = ','.join(str(q.id) for q in selected_questions)

    return render(request, 'quiz/quiz.html', {
        'question_data': question_data,
        'question_ids': question_ids,
        'question_count': question_count,
    })


def answer_records(request):
    session_key = get_session_key(request)

    # 顯示這個瀏覽器目前所有正式測驗紀錄
    attempts = QuizAttempt.objects.filter(
        session_key=session_key
    ).order_by('-created_at').prefetch_related('answer_records__question')

    return render(request, 'quiz/answer_records.html', {
        'attempts': attempts,
    })

def wrong_review(request):
    current_attempt_id = request.session.get('current_attempt_id')

    # 如果還沒完成正式測驗，就不顯示錯題
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

        # 錯題複習只做練習，不新增作答紀錄
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
            'correct_count': score,
            'total_questions': len(results),
            'is_review': True,
        })

    # 只抓目前這一次正式測驗答錯的題目
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