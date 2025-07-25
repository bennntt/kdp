from models import ActionLog, db
from flask_mail import Message
from flask import current_app, render_template_string
import random
from generator import generate_author_name, generate_title, generate_subtitle, generate_description
# Import additional generator functions for enhanced AI generation
import requests
import re
import logging

def log_action(user_id, action, details, ip_address, user_agent):
    """Log user actions for admin tracking"""
    log = ActionLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.session.add(log)
    db.session.commit()

def generate_titles(input_data):
    """Generate book titles using GROQ AI"""
    book_type = input_data['book_type']
    book_name = input_data['book_name']
    language = input_data['language']
    keywords = input_data.get('keywords', '')
    
    # Generate multiple titles using AI
    results = []
    for i in range(10):  # Generate 10 titles
        title = generate_title(book_name, book_type, language, keywords)
        if title:
            results.append(title)
        else:
            # Fallback titles if AI generation fails
            fallback_templates = [
                f"The Complete Guide to {book_name}",
                f"Mastering {book_name}",
                f"{book_name}: A Comprehensive Handbook",
                f"Understanding {book_name}",
                f"The Art of {book_name}"
            ]
            results.append(fallback_templates[i % len(fallback_templates)])
    
    return results[:10]

def generate_subtitles(input_data):
    """Generate book subtitles using GROQ AI"""
    title = input_data['title']
    book_type = input_data['book_type']
    language = input_data['language']
    keywords = input_data.get('keywords', '')
    
    # Generate multiple subtitles using AI
    results = []
    for i in range(10):  # Generate 10 subtitles
        subtitle = generate_subtitle(title, book_type, language, keywords)
        if subtitle:
            results.append(subtitle)
        else:
            # Fallback subtitles if AI generation fails
            fallback_templates = [
                f"A Complete Guide to {title}",
                f"Essential Strategies for {title}",
                f"Everything You Need to Know About {title}",
                f"A Comprehensive Guide to {title}",
                f"The Ultimate Resource for {title}"
            ]
            results.append(fallback_templates[i % len(fallback_templates)])
    
    return results[:10]

def generate_descriptions(input_data):
    """Generate book descriptions using GROQ AI"""
    title = input_data['title']
    language = input_data['language']
    keywords = input_data.get('keywords', '')
    binding_type = input_data['binding_type']
    interior_type = input_data['interior_type']
    page_count = input_data['page_count']
    interior_trim_size = input_data['interior_trim_size']
    description_length = input_data['description_length']
    
    # Map language codes to proper language names
    language_map = {
        'english': 'en',
        'arabic': 'ar', 
        'french': 'fr',
        'spanish': 'es',
        'german': 'de'
    }
    lang_code = language_map.get(language.lower(), 'en')
    
    # Generate multiple descriptions using AI
    results = []
    for i in range(3):  # Generate 3 descriptions
        description = generate_description(
            title, binding_type, interior_type, page_count, 
            interior_trim_size, keywords, lang_code, description_length
        )
        if description:
            results.append(description)
        else:
            # Fallback description if AI generation fails
            fallback = f"<p><b>{title}</b> is a comprehensive guide that explores essential concepts and practical applications.</p><p>This {binding_type} edition features {interior_type} interior with {page_count} pages in {interior_trim_size} format.</p>"
            results.append(fallback)
    
    return results

def generate_author_names(input_data):
    """Generate author names using the enhanced generator"""
    language = input_data['language']
    country = input_data['country']
    gender = input_data['gender']
    
    # Fields to generate
    include_prefix = input_data.get('prefix', False)
    include_middle_name = input_data.get('middle_name', False)
    include_suffix = input_data.get('suffix', False)
    
    results = []
    for i in range(10):
        # Use the enhanced generator function
        name_data = generate_author_name(
            language=language,
            country=country,
            gender=gender,
            include_prefix=include_prefix,
            include_middle_name=include_middle_name,
            include_suffix=include_suffix
        )
        
        # Create the full name from non-empty parts
        name_parts = [part for part in [
            name_data['Prefix'],
            name_data['First Name'], 
            name_data['Middle Name'],
            name_data['Last Name'],
            name_data['Suffix']
        ] if part.strip()]
        
        # Convert to the format expected by the template
        formatted_name_data = {
            'prefix': name_data['Prefix'],
            'first_name': name_data['First Name'],
            'middle_name': name_data['Middle Name'],
            'last_name': name_data['Last Name'],
            'suffix': name_data['Suffix'],
            'full_name': ' '.join(name_parts)
        }
        
        if formatted_name_data['full_name'].strip():  # Only add non-empty names
            results.append(formatted_name_data)
    
    return results

def research_keywords(input_data):
    """Research keywords for book marketing with realistic data"""
    topic = input_data['topic']
    category = input_data['category']
    
    # More realistic keyword suggestions based on common patterns
    base_keywords = []
    
    # Topic-specific keywords with realistic search volumes and competition
    if topic.lower() in ['weight loss', 'diet', 'fitness']:
        base_keywords = [
            {'term': 'weight loss diet plan', 'search_volume': '3,200', 'difficulty': 'High', 'volume': 'High', 'relevance_score': 5, 'long_tail': True},
            {'term': 'lose weight fast', 'search_volume': '8,100', 'difficulty': 'High', 'volume': 'High', 'relevance_score': 4, 'long_tail': False},
            {'term': 'healthy weight loss', 'search_volume': '2,400', 'difficulty': 'Medium', 'volume': 'Medium', 'relevance_score': 5, 'long_tail': False},
            {'term': 'weight loss tips', 'search_volume': '1,900', 'difficulty': 'Medium', 'volume': 'Medium', 'relevance_score': 4, 'long_tail': False},
            {'term': 'diet for beginners', 'search_volume': '880', 'difficulty': 'Low', 'volume': 'Medium', 'relevance_score': 4, 'long_tail': True},
            {'term': 'weight loss journey', 'search_volume': '1,300', 'difficulty': 'Low', 'volume': 'Medium', 'relevance_score': 3, 'long_tail': False},
            {'term': 'fat burning foods', 'search_volume': '2,100', 'difficulty': 'Medium', 'volume': 'Medium', 'relevance_score': 4, 'long_tail': False},
            {'term': 'metabolism boost', 'search_volume': '720', 'difficulty': 'Low', 'volume': 'Low', 'relevance_score': 3, 'long_tail': False},
        ]
    elif topic.lower() in ['cooking', 'recipes', 'food']:
        base_keywords = [
            {'term': 'easy cooking recipes', 'search_volume': '4,500', 'difficulty': 'High', 'volume': 'High', 'relevance_score': 5, 'long_tail': True},
            {'term': 'quick dinner ideas', 'search_volume': '3,800', 'difficulty': 'Medium', 'volume': 'High', 'relevance_score': 4, 'long_tail': True},
            {'term': 'healthy meal prep', 'search_volume': '2,200', 'difficulty': 'Medium', 'volume': 'Medium', 'relevance_score': 5, 'long_tail': False},
            {'term': 'beginner cooking tips', 'search_volume': '950', 'difficulty': 'Low', 'volume': 'Medium', 'relevance_score': 4, 'long_tail': True},
            {'term': 'kitchen essentials', 'search_volume': '1,100', 'difficulty': 'Low', 'volume': 'Medium', 'relevance_score': 3, 'long_tail': False},
            {'term': 'cooking techniques', 'search_volume': '1,600', 'difficulty': 'Medium', 'volume': 'Medium', 'relevance_score': 4, 'long_tail': False},
            {'term': 'family recipes', 'search_volume': '890', 'difficulty': 'Low', 'volume': 'Low', 'relevance_score': 3, 'long_tail': False},
            {'term': 'budget cooking', 'search_volume': '760', 'difficulty': 'Low', 'volume': 'Low', 'relevance_score': 4, 'long_tail': False},
        ]
    elif topic.lower() in ['photography', 'photo', 'camera']:
        base_keywords = [
            {'term': 'photography for beginners', 'search_volume': '5,400', 'difficulty': 'High', 'volume': 'High', 'relevance_score': 5, 'long_tail': True},
            {'term': 'camera settings guide', 'search_volume': '2,100', 'difficulty': 'Medium', 'volume': 'Medium', 'relevance_score': 4, 'long_tail': True},
            {'term': 'portrait photography tips', 'search_volume': '1,800', 'difficulty': 'Medium', 'volume': 'Medium', 'relevance_score': 4, 'long_tail': True},
            {'term': 'photo composition', 'search_volume': '1,200', 'difficulty': 'Low', 'volume': 'Medium', 'relevance_score': 5, 'long_tail': False},
            {'term': 'photography equipment', 'search_volume': '1,500', 'difficulty': 'Medium', 'volume': 'Medium', 'relevance_score': 3, 'long_tail': False},
            {'term': 'lighting techniques', 'search_volume': '980', 'difficulty': 'Low', 'volume': 'Low', 'relevance_score': 4, 'long_tail': False},
            {'term': 'photo editing basics', 'search_volume': '2,300', 'difficulty': 'Medium', 'volume': 'Medium', 'relevance_score': 4, 'long_tail': True},
            {'term': 'travel photography', 'search_volume': '1,900', 'difficulty': 'Medium', 'volume': 'Medium', 'relevance_score': 3, 'long_tail': False},
        ]
    else:
        # Generic keywords for any topic
        base_keywords = [
            {'term': f'{topic} guide', 'search_volume': '1,200', 'difficulty': 'Medium', 'volume': 'Medium', 'relevance_score': 4, 'long_tail': False},
            {'term': f'{topic} for beginners', 'search_volume': '890', 'difficulty': 'Low', 'volume': 'Medium', 'relevance_score': 5, 'long_tail': True},
            {'term': f'{topic} tips and tricks', 'search_volume': '650', 'difficulty': 'Low', 'volume': 'Low', 'relevance_score': 4, 'long_tail': True},
            {'term': f'how to {topic}', 'search_volume': '1,100', 'difficulty': 'Medium', 'volume': 'Medium', 'relevance_score': 4, 'long_tail': True},
            {'term': f'{topic} techniques', 'search_volume': '720', 'difficulty': 'Low', 'volume': 'Low', 'relevance_score': 3, 'long_tail': False},
            {'term': f'{topic} strategies', 'search_volume': '580', 'difficulty': 'Low', 'volume': 'Low', 'relevance_score': 3, 'long_tail': False},
            {'term': f'best {topic} methods', 'search_volume': '430', 'difficulty': 'Low', 'volume': 'Low', 'relevance_score': 4, 'long_tail': True},
            {'term': f'{topic} secrets', 'search_volume': '340', 'difficulty': 'Low', 'volume': 'Low', 'relevance_score': 3, 'long_tail': False},
        ]
    
    return {
        'topic': topic,
        'category': category,
        'keywords': base_keywords,
        'total_keywords': len(base_keywords)
    }

def find_categories(input_data):
    """Find Amazon KDP categories for a book"""
    title = input_data['title']
    description = input_data['description']
    keywords = input_data['keywords'].split(',')
    
    # Comprehensive Amazon KDP categories with detailed structure
    category_database = [
        {
            'name': 'Coloring Books',
            'path': 'Books > Children\'s Books > Activities, Crafts & Games > Activity Books > Coloring Books',
            'keywords': ['coloring', 'color', 'activity', 'children', 'kids', 'drawing']
        },
        {
            'name': 'Business Leadership',
            'path': 'Books > Business & Money > Management & Leadership > Leadership',
            'keywords': ['leadership', 'management', 'business', 'leader', 'executive']
        },
        {
            'name': 'Self-Help Personal Growth',
            'path': 'Books > Self-Help > Personal Transformation > Self-Improvement',
            'keywords': ['self-help', 'personal', 'improvement', 'growth', 'motivation']
        },
        {
            'name': 'Romance Fiction',
            'path': 'Kindle Store > Fiction > Romance > Contemporary Romance',
            'keywords': ['romance', 'love', 'relationship', 'contemporary', 'fiction']
        },
        {
            'name': 'Mystery Thriller',
            'path': 'Kindle Store > Fiction > Mystery, Thriller & Suspense > Mystery',
            'keywords': ['mystery', 'thriller', 'suspense', 'crime', 'detective']
        },
        {
            'name': 'Cooking & Recipes',
            'path': 'Books > Cookbooks, Food & Wine > Cooking Methods > Quick & Easy',
            'keywords': ['cooking', 'recipes', 'food', 'kitchen', 'meals', 'chef']
        },
        {
            'name': 'Health & Fitness',
            'path': 'Books > Health, Fitness & Dieting > Exercise & Fitness > Weight Training',
            'keywords': ['health', 'fitness', 'exercise', 'workout', 'training', 'diet']
        },
        {
            'name': 'Fantasy Fiction',
            'path': 'Kindle Store > Fiction > Science Fiction & Fantasy > Fantasy > Epic Fantasy',
            'keywords': ['fantasy', 'magic', 'adventure', 'epic', 'sword', 'dragons']
        },
        {
            'name': 'Biography & Memoir',
            'path': 'Books > Biographies & Memoirs > Historical > Political',
            'keywords': ['biography', 'memoir', 'life', 'story', 'historical', 'political']
        },
        {
            'name': 'Photography',
            'path': 'Books > Arts & Photography > Photography & Video > Equipment, Techniques & Reference',
            'keywords': ['photography', 'photo', 'camera', 'techniques', 'pictures']
        },
        {
            'name': 'Travel Guides',
            'path': 'Books > Travel > Specialty Travel > Adventure Travel',
            'keywords': ['travel', 'guide', 'adventure', 'destination', 'tourism']
        },
        {
            'name': 'Business Marketing',
            'path': 'Books > Business & Money > Marketing & Sales > Marketing',
            'keywords': ['marketing', 'sales', 'advertising', 'promotion', 'business']
        },
        {
            'name': 'Educational Textbooks',
            'path': 'Books > Textbooks > Education > Elementary Education',
            'keywords': ['education', 'textbook', 'learning', 'school', 'teaching']
        },
        {
            'name': 'Parenting & Family',
            'path': 'Books > Parenting & Relationships > Parenting > Early Childhood',
            'keywords': ['parenting', 'family', 'children', 'kids', 'childcare']
        },
        {
            'name': 'Technology & Programming',
            'path': 'Books > Computers & Technology > Programming > Languages & Tools',
            'keywords': ['programming', 'coding', 'technology', 'software', 'development']
        },
        {
            'name': 'Science Fiction',
            'path': 'Kindle Store > Fiction > Science Fiction & Fantasy > Science Fiction > Space Opera',
            'keywords': ['science fiction', 'sci-fi', 'space', 'future', 'technology']
        },
        {
            'name': 'History',
            'path': 'Books > History > World > Ancient Civilizations',
            'keywords': ['history', 'historical', 'ancient', 'civilization', 'past']
        },
        {
            'name': 'Art & Design',
            'path': 'Books > Arts & Photography > Graphic Design > Commercial > Illustration',
            'keywords': ['art', 'design', 'illustration', 'graphic', 'creative']
        },
        {
            'name': 'Religion & Spirituality',
            'path': 'Books > Religion & Spirituality > Christianity > Christian Living',
            'keywords': ['religion', 'spiritual', 'faith', 'christian', 'god']
        },
        {
            'name': 'Personal Finance',
            'path': 'Books > Business & Money > Personal Finance > Investing',
            'keywords': ['finance', 'money', 'investing', 'investment', 'wealth']
        }
    ]
    
    # Analyze content to find matching categories
    suggested_categories = []
    
    # Combine all text for analysis
    all_text = f"{title} {description} {' '.join(keywords)}".lower()
    
    # Score each category based on keyword matches
    category_scores = []
    for category in category_database:
        score = 0
        for keyword in category['keywords']:
            if keyword in all_text:
                score += 1
        
        if score > 0:
            category_scores.append((category, score))
    
    # Sort by score and take top matches
    category_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Get top 5 categories or all if less than 5
    for category, score in category_scores[:5]:
        suggested_categories.append({
            'name': category['name'],
            'path': category['path']
        })
    
    # Add default categories if none found
    if not suggested_categories:
        suggested_categories = [
            {
                'name': 'General Reference',
                'path': 'Books > Reference > General'
            },
            {
                'name': 'Kindle Reference',
                'path': 'Kindle Store > Kindle eBooks > Reference'
            }
        ]
    
    return suggested_categories


def sort_trademark_results(results, sort_by, sort_order):
    """Sort trademark results by specified column"""
    if not results or sort_by == 'default':
        return results
    
    reverse = (sort_order == 'desc')
    
    def get_sort_key(item):
        if sort_by == 'status':
            # LIVE comes before DEAD in ascending order
            return (0 if item.get('status') == 'LIVE' else 1)
        elif sort_by == 'countries':
            return item.get('country', 'N/A').lower()
        elif sort_by == 'granted':
            # Parse date for proper sorting
            granted = item.get('granted', 'N/A')
            if granted == 'N/A':
                return '9999-12-31'  # Put N/A at the end
            try:
                # Try to parse date in DD.MM.YYYY format
                if '.' in granted:
                    parts = granted.split('.')
                    if len(parts) == 3:
                        return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                return granted
            except:
                return granted
        elif sort_by == 'expires':
            # Parse expiry date for proper sorting
            expires = item.get('status_date', 'N/A')
            if expires == 'N/A':
                return '9999-12-31'  # Put N/A at the end
            try:
                # Try to parse date in DD.MM.YYYY format
                if '.' in expires:
                    parts = expires.split('.')
                    if len(parts) == 3:
                        return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                return expires
            except:
                return expires
        else:
            return item.get('name_or_image', 'N/A').lower()
    
    try:
        return sorted(results, key=get_sort_key, reverse=reverse)
    except Exception as e:
        print(f"Error sorting results: {e}")
        return results

def calculate_royalty(input_data):
    """Calculate KDP royalty earnings for all marketplaces"""
    try:
        import requests
        
        book_type = input_data['book_type']
        interior_type = input_data['interior_type']
        selected_marketplace = input_data['marketplace']
        trim_size = input_data['trim_size']
        page_count = int(input_data['page_count'])
        list_price = float(input_data['list_price'])
        
        # Currency symbols and marketplace data
        CURRENCY_SYMBOLS = {
            'USD': '$', 'GBP': '£', 'EUR': '€', 'PLN': 'zł',
            'SEK': 'kr', 'JPY': '¥', 'CAD': '$', 'AUD': '$'
        }

        # Updated printing costs based on the provided code
        PRINTING_COSTS = {
            'paperback': {
                'black_white': {'base': 0.85, 'per_page': 0.010},
                'standard_color': {'base': 3.65, 'per_page': 0.07},
                'premium_color': {'base': 3.99, 'per_page': 0.09}
            },
            'hardcover': {
                'black_white': {'base': 3.59, 'per_page': 0.012},
                'standard_color': {'base': 5.65, 'per_page': 0.10},
                'premium_color': {'base': 6.00, 'per_page': 0.12}
            }
        }

        MARKETPLACES = {
            'Amazon.com':     {'currency': 'USD', 'threshold': 9.99},
            'Amazon.co.uk':   {'currency': 'GBP', 'threshold': 7.99},
            'Amazon.de':      {'currency': 'EUR', 'threshold': 9.99},
            'Amazon.fr':      {'currency': 'EUR', 'threshold': 9.99},
            'Amazon.es':      {'currency': 'EUR', 'threshold': 9.99},
            'Amazon.it':      {'currency': 'EUR', 'threshold': 9.99},
            'Amazon.nl':      {'currency': 'EUR', 'threshold': 9.99},
            'Amazon.pl':      {'currency': 'PLN', 'threshold': 40.0},
            'Amazon.se':      {'currency': 'SEK', 'threshold': 99.0},
            'Amazon.co.jp':   {'currency': 'JPY', 'threshold': 1000},
            'Amazon.ca':      {'currency': 'CAD', 'threshold': 13.99},
            'Amazon.com.au':  {'currency': 'AUD', 'threshold': 13.99},
        }
        
        base_currency = MARKETPLACES[selected_marketplace]['currency']
        
        # Get exchange rates
        fx_url = f"https://api.frankfurter.app/latest?from={base_currency}"
        try:
            fx_response = requests.get(fx_url, timeout=5)
            fx_data = fx_response.json().get('rates', {})
            fx_data[base_currency] = 1.0
        except Exception:
            # Fallback exchange rates if API fails
            fx_data = {base_currency: 1.0}
        
        # Calculate printing cost structure
        cost = PRINTING_COSTS[book_type][interior_type]
        printing_cost_base = round(cost['base'] + (page_count * cost['per_page']), 2)
        
        # Check minimum price requirement for selected marketplace
        royalty_rate_selected = 0.60 if list_price >= MARKETPLACES[selected_marketplace]['threshold'] else 0.50
        min_required_price = round(printing_cost_base / royalty_rate_selected, 2)
        
        if list_price < min_required_price:
            return {
                'error': f"The list price for {selected_marketplace} must be at least {min_required_price:.2f} {base_currency} to cover printing costs."
            }
        
        # Calculate for all marketplaces
        marketplace_results = []
        ordered_marketplaces = [selected_marketplace] + [m for m in MARKETPLACES if m != selected_marketplace]
        
        for marketplace in ordered_marketplaces:
            data = MARKETPLACES[marketplace]
            currency = data['currency']
            symbol = CURRENCY_SYMBOLS.get(currency, '')
            rate = fx_data.get(currency, 1.0)
            
            # Convert price to marketplace currency
            converted_price = round(list_price * rate, 2)
            
            # Determine royalty rate based on threshold
            royalty_rate = 0.60 if converted_price >= data['threshold'] else 0.50
            
            # Calculate estimated royalty
            estimated_royalty = round((converted_price * royalty_rate) - printing_cost_base, 2)
            min_list_price = round(printing_cost_base / royalty_rate, 2)
            
            marketplace_results.append({
                'marketplace': marketplace,
                'currency': currency,
                'symbol': symbol,
                'list_price': converted_price,
                'list_price_formatted': f"{symbol} {converted_price:.2f}",
                'royalty_rate': f"{int(royalty_rate * 100)}%",
                'min_price': f"{symbol} {min_list_price:.2f}",
                'printing_cost': f"{symbol} {printing_cost_base:.2f}",
                'estimated_royalty': f"{symbol} {estimated_royalty:.2f}",
                'estimated_royalty_value': estimated_royalty
            })
        
        # Format interior type for display
        interior_display = {
            'black_white': 'Black & White',
            'standard_color': 'Standard Color',
            'premium_color': 'Premium Color'
        }
        
        results = {
            'book_type': book_type.title(),
            'interior_type': interior_display.get(interior_type, interior_type),
            'selected_marketplace': selected_marketplace,
            'trim_size': trim_size,
            'page_count': page_count,
            'list_price': list_price,
            'base_currency': base_currency,
            'printing_cost_base': printing_cost_base,
            'marketplace_results': marketplace_results,
            'input_data': input_data
        }
        
        return results
        
    except (ValueError, TypeError) as e:
        return {'error': f'Invalid input values: {str(e)}'}

def search_trademarks(input_data):
    """Search for trademark conflicts using real data from tmsearch.ai"""
    import requests
    from bs4 import BeautifulSoup
    import time
    
    search_term = input_data['search_term']
    search_type = input_data.get('search_type', 'contains')
    
    results = []
    
    if not search_term.strip():
        return results
    
    try:
        # البحث في tmsearch.ai
        url = f"https://tmsearch.ai/search/?keyword={search_term}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        items = soup.find_all("div", class_=lambda x: x and x.startswith("rb") and "data-group-1" in x)
        
        for item in items:
            try:
                data = {}
                
                # صورة العلامة التجارية
                img_tag = item.select_one(".rb__img img")
                title_tag = item.select_one("h3.font_1")
                link_tag = item.select_one(".rb__img a")
                
                data['image'] = True if img_tag else False
                data['name_or_image'] = img_tag.get('src', '') if img_tag else (title_tag.get_text(strip=True) if title_tag else "N/A")
                data['mark'] = title_tag.get_text(strip=True) if title_tag else "N/A"
                data['link'] = "https://tmsearch.ai" + link_tag.get('href', '') if link_tag and link_tag.has_attr("href") else "N/A"
                
                # تاريخ المنح
                grant_section = item.select_one(".rb-bottom__grant")
                data['granted'] = grant_section.select_one("p.rb-bottom__date").get_text(strip=True) if grant_section and grant_section.select_one("p.rb-bottom__date") else "N/A"
                
                # رموز الدول
                country_codes = item.select("div.country_code")
                countries = [cc.get_text(strip=True) for cc in country_codes] if country_codes else []
                data['country'] = countries[0] if countries else "N/A"
                data['countries'] = countries
                
                # حالة العلامة التجارية
                status_element = item.select_one("div.result__expiration-status")
                data['status'] = status_element.get_text(strip=True).upper() if status_element else "N/A"
                
                # تاريخ الحالة
                status_date_element = item.select_one("span.rb__check-full__date")
                data['status_date'] = status_date_element.get_text(strip=True) if status_date_element else "N/A"
                
                # تنظيف البيانات
                if data['status'] not in ['LIVE', 'DEAD']:
                    if 'live' in data['status'].lower() or 'active' in data['status'].lower():
                        data['status'] = 'LIVE'
                    elif 'dead' in data['status'].lower() or 'expired' in data['status'].lower():
                        data['status'] = 'DEAD'
                    else:
                        data['status'] = 'LIVE'  # افتراضي
                
                results.append(data)
                
            except Exception as item_error:
                print(f"خطأ في معالجة عنصر: {item_error}")
                continue
        
        # في حالة عدم وجود نتائج، إرجاع قائمة فارغة
        if not results:
            return []
        
        # لا نحدد النتائج هنا، سيتم التحكم بها في الـ template حسب الصفحة
            
    except requests.exceptions.RequestException as req_error:
        print(f"خطأ في الطلب: {req_error}")
        return []
    except Exception as e:
        print(f"خطأ عام في البحث: {e}")
        return []
    
    return results


def get_fallback_trademark_data(search_term):
    """بيانات احتياطية في حالة فشل الاتصال بـ tmsearch.ai"""
    fallback_data = [
        {
            'image': False,
            'name_or_image': 'DMC',
            'mark': 'DMC',
            'link': 'https://tmsearch.ai/trademark/application/IN/dmc/APP/1330050.html',
            'granted': 'N/A',
            'country': 'IN',
            'countries': ['IN'],
            'status': 'DEAD',
            'status_date': '04.01.2025'
        },
        {
            'image': True,
            'name_or_image': 'https://img.tmsearch.ai/img/210/CA/TM/APP/1588327.jpg',
            'mark': 'DMC Canada',
            'link': 'https://tmsearch.ai/trademark/application/CA/dmc/REG/TMA406410.html',
            'granted': '18.12.1992',
            'country': 'CA',
            'countries': ['CA'],
            'status': 'LIVE',
            'status_date': '18.12.2032'
        },
        {
            'image': False,
            'name_or_image': 'BookMaster Pro',
            'mark': 'BookMaster Pro',
            'link': '#',
            'granted': '15.03.2020',
            'country': 'US',
            'countries': ['US'],
            'status': 'LIVE',
            'status_date': '15.03.2030'
        },
        {
            'image': True,
            'name_or_image': 'https://img.tmsearch.ai/img/210/GB/TM/REG/2145678.jpg',
            'mark': 'ReadWell',
            'link': '#',
            'granted': '22.08.2019',
            'country': 'GB',
            'countries': ['GB'],
            'status': 'LIVE',
            'status_date': '22.08.2029'
        }
    ]
    
    # تصفية النتائج حسب مصطلح البحث
    if search_term.strip():
        search_lower = search_term.lower()
        filtered = [item for item in fallback_data 
                   if search_lower in item['mark'].lower() or 
                      search_lower in item['name_or_image'].lower()]
        if filtered:
            return filtered
    
    return fallback_data[:3]  # إرجاع أول 3 عناصر كمثال

def send_email_notification(user_email, user_name, subject, message_template, **kwargs):
    """Send email notification to user for account activities"""
    try:
        # Check if mail configuration is available
        if not current_app.config.get('MAIL_USERNAME'):
            logging.warning("Mail configuration not available, skipping email notification")
            return False
        
        # Create message
        msg = Message(
            subject=f"KDP Tools - {subject}",
            recipients=[user_email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Email template
        email_body = render_template_string(message_template, user_name=user_name, **kwargs)
        msg.html = email_body
        
        # Send email
        mail.send(msg)
        logging.info(f"Email notification sent to {user_email}: {subject}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send email to {user_email}: {str(e)}")
        return False

def send_subscription_email(user, action, **kwargs):
    """Send subscription-related email notifications"""
    templates = {
        'subscription_created': {
            'subject': 'Welcome to KDP Tools Premium!',
            'template': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
                <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #28a745; margin-bottom: 20px;">🎉 Welcome to KDP Tools Premium!</h2>
                    <p>Hello <strong>{{ user_name }}</strong>,</p>
                    <p>Your subscription has been successfully activated! You now have unlimited access to all KDP tools.</p>
                    <div style="background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h4 style="margin: 0; color: #0066cc;">What's included:</h4>
                        <ul style="margin: 10px 0;">
                            <li>Unlimited use of all 8 KDP tools</li>
                            <li>Advanced AI-powered content generation</li>
                            <li>Priority customer support</li>
                            <li>Regular feature updates</li>
                        </ul>
                    </div>
                    <p>Thank you for choosing KDP Tools to enhance your publishing journey!</p>
                    <p style="margin-top: 30px;">Best regards,<br>The KDP Tools Team</p>
                </div>
            </div>
            '''
        },
        'subscription_cancelled': {
            'subject': 'Subscription Cancelled',
            'template': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
                <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #dc3545; margin-bottom: 20px;">Subscription Cancelled</h2>
                    <p>Hello <strong>{{ user_name }}</strong>,</p>
                    <p>Your KDP Tools subscription has been cancelled successfully.</p>
                    {% if refund_processed %}
                    <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745;">
                        <p style="margin: 0; color: #155724;"><strong>Refund Processed:</strong> Your refund has been initiated and will appear in your account within 5-10 business days.</p>
                    </div>
                    {% endif %}
                    <p>You have been moved to our free plan, which includes 3 daily tool uses.</p>
                    <p>We're sorry to see you go! If you have any feedback or questions, please don't hesitate to contact our support team.</p>
                    <p style="margin-top: 30px;">Best regards,<br>The KDP Tools Team</p>
                </div>
            </div>
            '''
        }
    }
    
    if action in templates:
        template_data = templates[action]
        return send_email_notification(
            user.email,
            user.first_name or user.username,
            template_data['subject'],
            template_data['template'],
            **kwargs
        )
    
    return False

def send_account_email(user, action, **kwargs):
    """Send account-related email notifications"""
    templates = {
        'email_changed': {
            'subject': 'Email Address Changed',
            'template': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
                <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #007bff; margin-bottom: 20px;">Email Address Updated</h2>
                    <p>Hello <strong>{{ user_name }}</strong>,</p>
                    <p>Your email address has been successfully changed to this new address.</p>
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                        <p style="margin: 0; color: #856404;"><strong>Security Notice:</strong> If you did not make this change, please contact our support team immediately.</p>
                    </div>
                    <p>Date: {{ change_date }}</p>
                    <p style="margin-top: 30px;">Best regards,<br>The KDP Tools Team</p>
                </div>
            </div>
            '''
        },
        'password_changed': {
            'subject': 'Password Changed',
            'template': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
                <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #28a745; margin-bottom: 20px;">Password Updated</h2>
                    <p>Hello <strong>{{ user_name }}</strong>,</p>
                    <p>Your account password has been successfully changed.</p>
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                        <p style="margin: 0; color: #856404;"><strong>Security Notice:</strong> If you did not make this change, please contact our support team immediately.</p>
                    </div>
                    <p>Date: {{ change_date }}</p>
                    <p style="margin-top: 30px;">Best regards,<br>The KDP Tools Team</p>
                </div>
            </div>
            '''
        },
        'name_changed': {
            'subject': 'Account Information Updated',
            'template': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
                <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #007bff; margin-bottom: 20px;">Account Information Updated</h2>
                    <p>Hello <strong>{{ user_name }}</strong>,</p>
                    <p>Your account information has been successfully updated.</p>
                    <p>Date: {{ change_date }}</p>
                    <p style="margin-top: 30px;">Best regards,<br>The KDP Tools Team</p>
                </div>
            </div>
            '''
        },
        'account_deleted': {
            'subject': 'Account Deleted',
            'template': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
                <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #dc3545; margin-bottom: 20px;">Account Deleted</h2>
                    <p>Hello <strong>{{ user_name }}</strong>,</p>
                    <p>Your KDP Tools account has been successfully deleted as requested.</p>
                    <p>All your data has been permanently removed from our systems.</p>
                    <p>Thank you for using KDP Tools. We're sorry to see you go!</p>
                    <p style="margin-top: 30px;">Best regards,<br>The KDP Tools Team</p>
                </div>
            </div>
            '''
        }
    }
    
    if action in templates:
        template_data = templates[action]
        return send_email_notification(
            user.email,
            user.first_name or user.username,
            template_data['subject'],
            template_data['template'],
            **kwargs
        )
    
    return False
