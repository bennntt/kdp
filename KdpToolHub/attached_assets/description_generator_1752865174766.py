# app/routes/generator_tools/description_generator.py
from flask import render_template, request
from flask_login import login_required, current_user
from app.routes.generator_tools import bp
from app.models import Plan, UserPlan
from app.routes.generator.generator import generate_description

@bp.route('/description-generator', methods=['GET', 'POST'])
@login_required
def description_generator():
    available_plans = Plan.query.filter_by(is_active=True).all()
    user_plan = UserPlan.get_active_plan(current_user.id)
    current_plan = Plan.query.get(user_plan.plan_id) if user_plan else None
    free_plan = Plan.get_free_plan()

    generated_description = None

    if request.method == 'POST':
        product = request.form.get('product', '').strip()
        keywords = request.form.get('keywords', '').strip()
        language = request.form.get('language', '').strip()
        length_level = int(request.form.get('description_length', 3))

        binding_type = request.form.get('binding_type', '').strip()
        interior_type = request.form.get('interior_type', '').strip()
        page_count = request.form.get('page_count', '').strip()
        interior_trim_size = request.form.get('interior_trim_size', '').strip()

        # ✅ تحقق أساسي
        if not product or len(product) > 100:
            generated_description = "<p><b>Error:</b> Invalid product name.</p>"
        elif language not in ['en', 'fr', 'es', 'de', 'ar']:
            generated_description = "<p><b>Error:</b> Invalid language selected.</p>"
        elif not page_count.isdigit() or int(page_count) <= 0:
            generated_description = "<p><b>Error:</b> Page count must be a positive number.</p>"
        else:
            # ✅ استدعاء التوليد
            generated_description = generate_description(
                product=product,
                binding_type=binding_type,
                interior_type=interior_type,
                page_count=page_count,
                interior_trim_size=interior_trim_size,
                keywords=keywords,
                language=language,
                length_level=length_level
            )


    return render_template(
        'generator_tools/description_generator.html',
        active_section='Description Generator',
        plans=available_plans,
        user_plan=user_plan,
        current_plan=current_plan,
        free_plan=free_plan,
        generated_description=generated_description
    )
