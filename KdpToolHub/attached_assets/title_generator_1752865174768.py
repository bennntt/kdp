# app/routes/generator_tools/title_generator.py

from flask import render_template, request
from flask_login import login_required, current_user
from app.routes.generator_tools import bp
from app.models import Plan, UserPlan
from app.forms.title_generator_form import TitleGeneratorForm
# استيراد الوسيط
from app.routes.generator.generator import generate_title

@bp.route('/title-generator', methods=['GET', 'POST'])
@login_required
def title_generator():
    available_plans = Plan.query.filter_by(is_active=True).all()
    user_plan = UserPlan.get_active_plan(current_user.id)
    current_plan = Plan.query.get(user_plan.plan_id) if user_plan else None
    free_plan = Plan.get_free_plan()

    form = TitleGeneratorForm(request.form or None)
    generated_title = None

    if request.method == 'POST':
        book_name = form.book_name.data.strip()
        book_type = form.book_type.data.strip()
        book_lang = (form.book_lang.data or "").strip()
        keywords = form.keywords.data.strip() if form.keywords.data else ''

        # 👇 استخدام الوسيط لتوليد العنوان
        ai_title = generate_title(book_name, book_type,book_lang, keywords)



                # بعد استدعاء ai_title
        if ai_title:
            # تنظيف النتيجة وإبقاء أول جزأين فقط (اسم الكتاب + كلمة واحدة اختيارية)
            cleaned_title = ai_title.strip()

            if cleaned_title.lower().startswith("title:"):
                cleaned_title = cleaned_title[6:].strip()

            cleaned_title = cleaned_title.strip('"').strip("'")

            # تقسيم الكلمات وتحديد أول جزأين فقط
            words = cleaned_title.split()
            #generated_title = ' '.join(words[:2])  # مثل: "Cozy Friends Coloring"
            generated_title = cleaned_title  # عرض العنوان كامل كما هو من أول نتيجة

        else:
            generated_title = None


    return render_template(
        'generator_tools/title_generator.html',
        active_section='Title Generator',
        plans=available_plans,
        user_plan=user_plan,
        current_plan=current_plan,
        free_plan=free_plan,
        generated_title=generated_title,
        form=form
    )