#app/routes/generator_tools/author_name_generator.py
from flask import render_template, request
from flask_login import login_required, current_user

from app.routes.generator.generator import generate_author_name
from app.routes.generator_tools import bp
from app.models import Plan, UserPlan


@bp.route('/author-name-generator', methods=['GET', 'POST'])
@login_required
def author_name_generator():
    available_plans = Plan.query.filter_by(is_active=True).all()
    user_plan = UserPlan.get_active_plan(current_user.id)
    current_plan = Plan.query.get(user_plan.plan_id) if user_plan else None
    free_plan = Plan.get_free_plan()

    full_name = None  # ← هذا السطر ضروري

    if request.method == 'POST':
        gender = request.form.get('gender', 'male')
        country = request.form.get('country', 'US')
        selected_fields = [field.lower().replace(' ', '_') for field in request.form.getlist('fields')]

        valid_genders = ['male', 'female']
        valid_countries = ['US', 'FR', 'ES', 'DE']
        lang_map = {
            'US': 'en-US',
            'FR': 'fr-FR',
            'ES': 'es-ES',
            'DE': 'de-DE'
        }

        if gender not in valid_genders:
            full_name = {'Error': 'Invalid gender'}
        elif country not in lang_map:
            full_name = {'Error': 'Invalid country'}
        else:
            language = lang_map[country]
            full_name = generate_author_name(
                language=language,
                country=country,
                gender=gender,
                include_prefix='prefix' in selected_fields,
                include_middle_name='middle_name' in selected_fields,
                include_suffix='suffix' in selected_fields
            )



    return render_template(
            'generator_tools/author_name_generator.html',
            active_section='Author Name',
            plans=available_plans,
            user_plan=user_plan,
            current_plan=current_plan,
            free_plan=free_plan,
            full_name=full_name  # ← الآن لن يعطيك خطأ في GET
        )
