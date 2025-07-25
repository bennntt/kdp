#!/usr/bin/env python3
"""
Add Default Tools Script
"""

def add_default_tools():
    """Add default tools to database"""
    try:
        print("🛠️  Adding Default Tools...")
        
        from app import create_app, db
        from models import ToolConfiguration
        
        app = create_app()
        
        with app.app_context():
            # Add tools manually to avoid model conflicts
            default_tools = [
                ('title_generator', 'Title Generator', 'Generate compelling book titles', 'fas fa-magic', False, 1),
                ('subtitle_generator', 'Subtitle Generator', 'Create perfect subtitles', 'fas fa-heading', False, 2),
                ('description_generator', 'Description Generator', 'Write persuasive descriptions', 'fas fa-file-alt', False, 3),
                ('author_generator', 'Author Generator', 'Generate professional pen names', 'fas fa-user-edit', False, 4),
                ('keyword_research', 'Keyword Research', 'Discover high-traffic keywords', 'fas fa-search', True, 5),
                ('category_finder', 'Category Finder', 'Find the best Amazon categories', 'fas fa-tags', True, 6),
                ('royalty_calculator', 'Royalty Calculator', 'Calculate potential earnings', 'fas fa-calculator', False, 7),
                ('trademark_search', 'Trademark Search', 'Check for trademark conflicts', 'fas fa-shield-alt', True, 8)
            ]
            
            for tool_name, display_name, description, icon, requires_paid, sort_order in default_tools:
                existing = ToolConfiguration.query.filter_by(tool_name=tool_name).first()
                if not existing:
                    tool = ToolConfiguration(
                        tool_name=tool_name,
                        display_name=display_name,
                        description=description,
                        icon=icon,
                        is_enabled=True,
                        requires_paid_plan=requires_paid,
                        sort_order=sort_order,
                        daily_limit_free=3,
                        daily_limit_paid=50
                    )
                    db.session.add(tool)
                    print(f"✅ Added: {display_name}")
                else:
                    print(f"ℹ️  Exists: {display_name}")
            
            db.session.commit()
            print("\n🎉 Tools setup completed!")
            
            # Show summary
            total_tools = ToolConfiguration.query.count()
            free_tools = ToolConfiguration.query.filter_by(requires_paid_plan=False).count()
            paid_tools = ToolConfiguration.query.filter_by(requires_paid_plan=True).count()
            
            print(f"\n📊 Tools Summary:")
            print(f"   🛠️  Total Tools: {total_tools}")
            print(f"   🆓 Free Tools: {free_tools}")
            print(f"   👑 Premium Tools: {paid_tools}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_default_tools()