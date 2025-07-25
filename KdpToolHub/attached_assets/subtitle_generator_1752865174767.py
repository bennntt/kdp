from flask import render_template, request
from flask_login import login_required, current_user
from app.routes.generator_tools import bp
from app.models import Plan, UserPlan
from app.routes.generator.generator import  generate_subtitle


@bp.route('/subtitle-generator', methods=['GET', 'POST'])
@login_required
def subtitle_generator():
    global book_name
    available_plans = Plan.query.filter_by(is_active=True).all()
    user_plan = UserPlan.get_active_plan(current_user.id)
    current_plan = Plan.query.get(user_plan.plan_id) if user_plan else None
    free_plan = Plan.get_free_plan()

    generated_subtitle = None

    if request.method == 'POST':
        book_name = request.form.get('book_name', '').strip()
        book_type = request.form.get('book_type', '').strip()
        language = request.form.get('language', '').strip()
        keywords = request.form.get('keywords', '').strip()

        if not book_name or len(book_name) < 2:
            generated_subtitle = "Invalid book name."
        elif language not in ['en', 'fr', 'es', 'de', 'ar']:
            generated_subtitle = "Invalid language selected."
        else:
            generated_subtitle = generate_subtitle(book_name, book_type, language, keywords)


    return render_template('generator_tools/subtitle_generator.html',
                           active_section='Subtitle Generator',
                           plans=available_plans,
                           user_plan=user_plan,
                           current_plan=current_plan,
                           free_plan=free_plan,
                           generated_subtitle=generated_subtitle)