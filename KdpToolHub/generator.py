# KDP Tools Generator Functions
import random
import requests
import re
import time
import os

# GROQ API Configuration
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

FORBIDDEN_WORDS = {"free", "bestseller", "gift", "notebook", "ebook", "download"}
FORBIDDEN_SYMBOLS_TITLE = set('"\' :;\\/|<>*?=+{}[]()#@&%')
FORBIDDEN_SYMBOLS_SUBTITLE = set('"\' ;\\/|<>*?=+{}[]()#@&%')

def ai(prompt, retries=3, delay=2):
    """Make request to GROQ API"""
    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY not found in environment variables.")
        return None
        
    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
    }
    for attempt in range(retries):
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=HEADERS,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.RequestException:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print("❌ Failed to connect to GROQ API after multiple attempts.")
    return None

def is_valid_text(text, max_length, forbidden_words, forbidden_symbols, min_length=1, check_space=True, banned_starts=()):
    """Validate generated text"""
    if len(text) > max_length or len(text) < min_length:
        return False
    text_lower = text.lower()
    for word in forbidden_words:
        if word in text_lower:
            return False
    for ch in forbidden_symbols:
        if ch != ' ' and ch in text:
            return False
    if check_space and ' ' not in text:
        return False
    for start in banned_starts:
        if text_lower.startswith(start):
            return False
    if "'" in text or '"' in text:
        return False
    return True

# Language to locale mapping
LANG_COUNTRY_MAP = {
    "English": "en_US",
    "Arabic": "ar_SA",
    "French": "fr_FR", 
    "Spanish": "es_ES",
    "German": "de_DE",
    "Italian": "it_IT",
    "Portuguese": "pt_BR",
    "Russian": "ru_RU",
    "Chinese": "zh_CN",
    "Japanese": "ja_JP"
}

# Prefixes by locale
PREFIXES = {
    "en_US": ['Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'Rev.', 'Sir', 'Lady'],
    "ar_SA": ['د.', 'أ.', 'أستاذ', 'دكتور', 'الشيخ'],
    "fr_FR": ['M.', 'Mme', 'Dr', 'Prof', 'Mlle'],
    "de_DE": ['Herr', 'Frau', 'Dr.', 'Prof.'],
    "es_ES": ['Sr.', 'Sra.', 'Dr.', 'Prof.'],
    "it_IT": ['Sig.', 'Sig.ra', 'Dott.', 'Prof.'],
    "pt_BR": ['Sr.', 'Sra.', 'Dr.', 'Prof.'],
    "ru_RU": ['Г-н', 'Г-жа', 'Д-р', 'Проф.'],
    "zh_CN": ['先生', '女士', '博士', '教授'],
    "ja_JP": ['さん', '様', '博士', '教授']
}

# Suffixes by locale
SUFFIXES = {
    "en_US": ['Jr.', 'Sr.', 'II', 'III', 'PhD', 'MD', 'Esq.'],
    "ar_SA": ['الابن', 'الأب', 'الثاني', 'الثالث', 'دكتوراه'],
    "fr_FR": ['Jr', 'Sr', 'II', 'III'],
    "de_DE": ['Jr', 'Sr', 'II', 'III'],
    "es_ES": ['Jr', 'Sr', 'II', 'III'],
    "it_IT": ['Jr', 'Sr', 'II', 'III'],
    "pt_BR": ['Jr', 'Sr', 'II', 'III'],
    "ru_RU": ['мл.', 'ст.', 'II', 'III'],
    "zh_CN": ['小', '老', '二世', '三世'],
    "ja_JP": ['ジュニア', 'シニア', '二世', '三世']
}

# Name databases by locale and gender
NAMES_DATABASE = {
    "en_US": {
        "male_first": ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Christopher", "Charles", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua", "Kenneth", "Kevin", "Brian", "George", "Edward", "Ronald", "Timothy", "Jason", "Jeffrey", "Ryan"],
        "female_first": ["Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen", "Nancy", "Lisa", "Betty", "Helen", "Sandra", "Donna", "Carol", "Ruth", "Sharon", "Michelle", "Laura", "Sarah", "Kimberly", "Deborah", "Dorothy", "Lisa", "Nancy", "Karen", "Betty", "Helen"],
        "last": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]
    },
    "ar_SA": {
        "male_first": ["محمد", "أحمد", "علي", "حسن", "عبدالله", "عبدالرحمن", "خالد", "سعد", "عمر", "يوسف", "فهد", "عبدالعزيز", "تركي", "ناصر", "سلطان", "بندر", "طلال", "وليد", "عادل", "ماجد", "سلمان", "فيصل", "عثمان", "إبراهيم", "زياد", "طارق", "هشام", "نواف", "رائد", "كريم"],
        "female_first": ["فاطمة", "عائشة", "خديجة", "زينب", "مريم", "سارة", "نورا", "لينا", "دينا", "ريم", "منى", "سمية", "هند", "لطيفة", "أمل", "نادية", "ليلى", "سعاد", "هالة", "رانيا", "شيماء", "روان", "جود", "لمى", "أسماء", "رهف", "غادة", "سلمى", "دانة", "يارا"],
        "last": ["العتيبي", "المطيري", "الدوسري", "القحطاني", "الغامدي", "الزهراني", "الشهري", "العنزي", "الحربي", "السهلي", "الشمري", "العمري", "البقمي", "الجهني", "الرشيدي", "آل سعود", "آل مكتوم", "آل ثاني", "آل نهيان", "آل صباح", "العبدالله", "الأحمد", "المحمد", "الإبراهيم", "الخالد", "العلي", "الحسن", "السلمان", "الفيصل", "النجار"]
    },
    "fr_FR": {
        "male_first": ["Pierre", "Jean", "Michel", "Philippe", "Alain", "Nicolas", "Christophe", "Laurent", "Frédéric", "David", "Stéphane", "Olivier", "Julien", "Sébastien", "Thierry", "Pascal", "Vincent", "François", "Antoine", "Mathieu", "Alexandre", "Romain", "Thomas", "Maxime", "Fabrice", "Benjamin", "Grégory", "Cédric", "Emmanuel", "Ludovic"],
        "female_first": ["Marie", "Françoise", "Monique", "Catherine", "Nathalie", "Isabelle", "Sylvie", "Martine", "Christine", "Valérie", "Brigitte", "Sandrine", "Céline", "Véronique", "Stéphanie", "Dominique", "Chantal", "Pascale", "Caroline", "Corinne", "Karine", "Laurence", "Sophie", "Patricia", "Virginie", "Delphine", "Émilie", "Julie", "Audrey", "Laetitia"],
        "last": ["Martin", "Bernard", "Thomas", "Petit", "Robert", "Richard", "Durand", "Dubois", "Moreau", "Laurent", "Simon", "Michel", "Lefebvre", "Leroy", "Roux", "David", "Bertrand", "Morel", "Fournier", "Girard", "Bonnet", "Dupont", "Lambert", "Fontaine", "Rousseau", "Vincent", "Muller", "Lefevre", "Faure", "Andre"]
    },
    "es_ES": {
        "male_first": ["Antonio", "José", "Manuel", "Francisco", "Juan", "David", "José Antonio", "José Luis", "Jesús", "Javier", "Francisco Javier", "Carlos", "Daniel", "Miguel", "Rafael", "Pedro", "José Manuel", "Ángel", "Alejandro", "Miguel Ángel", "José María", "Fernando", "Luis", "Sergio", "Pablo", "Jorge", "Alberto", "Juan Carlos", "Álvaro", "Diego"],
        "female_first": ["María Carmen", "María", "Carmen", "Josefa", "Isabel", "Ana María", "María Dolores", "María Pilar", "María Teresa", "Ana", "Francisca", "Laura", "Antonia", "Dolores", "María Angeles", "Cristina", "Marta", "María José", "María Isabel", "Pilar", "Concepción", "Manuela", "Rosa María", "Mercedes", "Paula", "Montserrat", "Susana", "Beatriz", "Raquel", "Rosario"],
        "last": ["García", "González", "Rodríguez", "Fernández", "López", "Martínez", "Sánchez", "Pérez", "Gómez", "Martín", "Jiménez", "Ruiz", "Hernández", "Díaz", "Moreno", "Muñoz", "Álvarez", "Romero", "Alonso", "Gutiérrez", "Navarro", "Torres", "Domínguez", "Vázquez", "Ramos", "Gil", "Ramírez", "Serrano", "Blanco", "Suárez"]
    },
    "de_DE": {
        "male_first": ["Thomas", "Michael", "Andreas", "Wolfgang", "Klaus", "Jürgen", "Günter", "Stefan", "Christian", "Uwe", "Werner", "Horst", "Frank", "Dieter", "Rainer", "Bernd", "Manfred", "Peter", "Heinz", "Martin", "Hans", "Gerhard", "Helmut", "Walter", "Alexander", "Matthias", "Markus", "Harald", "Norbert", "Georg"],
        "female_first": ["Ursula", "Sabine", "Petra", "Gabriele", "Monika", "Andrea", "Brigitte", "Christine", "Barbara", "Angelika", "Ingrid", "Martina", "Claudia", "Stefanie", "Birgit", "Susanne", "Silke", "Heike", "Karin", "Doris", "Nicole", "Anja", "Katrin", "Simone", "Sandra", "Gudrun", "Renate", "Christa", "Gisela", "Iris"],
        "last": ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann", "Schäfer", "Koch", "Bauer", "Richter", "Klein", "Wolf", "Schröder", "Neumann", "Schwarz", "Zimmermann", "Braun", "Krüger", "Hofmann", "Hartmann", "Lange", "Schmitt", "Werner", "Schmitz", "Krause", "Meier"]
    }
}

def generate_author_name(language="English", country="United States", gender="male",
                        include_prefix=False, include_middle_name=False, include_suffix=False):
    """Generate author names based on language, country, and gender"""
    
    # Map language to locale
    locale = LANG_COUNTRY_MAP.get(language, "en_US")
    
    # Get names database for locale
    names_db = NAMES_DATABASE.get(locale, NAMES_DATABASE["en_US"])
    
    # Generate name components
    prefix = random.choice(PREFIXES.get(locale, PREFIXES["en_US"])) if include_prefix else ''
    suffix = random.choice(SUFFIXES.get(locale, SUFFIXES["en_US"])) if include_suffix else ''
    
    # Generate first name based on gender
    if gender.lower() == 'male':
        first_name = random.choice(names_db["male_first"])
    elif gender.lower() == 'female': 
        first_name = random.choice(names_db["female_first"])
    else:
        # Random gender if not specified
        all_names = names_db["male_first"] + names_db["female_first"]
        first_name = random.choice(all_names)
    
    # Generate middle name (random from first names)
    if include_middle_name:
        all_first = names_db["male_first"] + names_db["female_first"]
        middle_name = random.choice(all_first)
    else:
        middle_name = ''
    
    # Generate last name
    last_name = random.choice(names_db["last"])
    
    return {
        "Prefix": prefix,
        "First Name": first_name,
        "Middle Name": middle_name,
        "Last Name": last_name,
        "Suffix": suffix
    }

def generate_title(book_name, book_type, book_lang, keywords=None, user_title=None, retries=3):
    """Generate book title using GROQ AI"""
    for _ in range(retries):
        title = _generate_title_once(book_name, book_type, book_lang, keywords, user_title)
        if title is not None:
            return title
    return None

def _generate_title_once(book_name, book_type, book_lang, keywords=None, user_title=None):
    """Generate single title attempt"""
    if user_title:
        cleaned = user_title.strip()
        valid = is_valid_text(
            cleaned, 100, FORBIDDEN_WORDS, FORBIDDEN_SYMBOLS_TITLE,
            min_length=3, check_space=True,
            banned_starts=("here is", "this is", "title", "example", "optimized")
        )
        if valid:
            return cleaned

    prompt = f"""
You are an AI trained for generating ONLY valid and compliant Amazon KDP book titles.
You are a professional KDP product description writer. 
📘 Book Details:
- Book Name: "{book_name}"
- Book Type: "{book_type}"
- Language: "{book_lang}"
- Keywords: "{keywords or 'general'}"
❌ DO NOT start with:
- "Here is"
- "This is"
- "Sure"
- "Generated description"
- Any quotes, punctuation, or labels
🎯 Output Requirements (STRICT):
- Output ONLY a single valid book title.
- Do NOT include explanations, greetings, or formatting like "Title:".
- Do NOT use quotation marks, colons, or any punctuation.
- Do NOT add any introductory sentence like "Here is..." or "Sure!"
- The result MUST be a natural, catchy, SEO-friendly book title.
- If no keywords are provided, infer them from book name, type, and language.
- Title MUST be under 100 characters.
- MUST comply with Amazon KDP title rules:
  - NO misleading, keyword stuffing, or promotional words.
  - NO forbidden terms: "free", "bestseller", "notebook", "gift", etc.
  - NO ALL-CAPS or weird casing.

📌 Final Output:
Return only the clean and final title. Nothing else.
"""
    raw_response = ai(prompt)
    if not raw_response:
        return None
        
    raw_response = re.sub(r'^(here i.*?:\s*)', '', raw_response.strip(), flags=re.I)
    cleaned = raw_response.strip()
    if cleaned.lower().startswith("title:"):
        cleaned = cleaned[6:].strip()
    cleaned = cleaned.strip('"\' :')

    valid = is_valid_text(
        cleaned, 100, FORBIDDEN_WORDS, FORBIDDEN_SYMBOLS_TITLE,
        min_length=3, check_space=True,
        banned_starts=("here is", "this is", "title", "example", "optimized")
    )
    if valid:
        return cleaned
    return None

def generate_subtitle(book_name, book_type, book_lang, keywords=None, retries=3):
    """Generate book subtitle using GROQ AI"""
    for _ in range(retries):
        subtitle = _generate_subtitle_once(book_name, book_type, book_lang, keywords)
        if subtitle is not None:
            return subtitle
    return None

def _generate_subtitle_once(book_name, book_type, book_lang, keywords=None):
    """Generate single subtitle attempt"""
    max_total = 200
    title_length = len(book_name.strip())
    subtitle_limit = max_total - title_length
    if subtitle_limit <= 0:
        return None

    prompt = f"""
You are a professional KDP product subtitle writer. Generate a detailed, persuasive, and SEO-optimized book subtitle

⚠️ STRICT RULES: 
- Return ONLY the subtitle line, with NO introductions, greetings, or explanations.
- NO punctuation marks, quotes, colons, semicolons, line breaks, or formatting.
- Subtitle length MUST be between {max(subtitle_limit - 5, 30)} and {subtitle_limit} characters.
- NO forbidden words: free, bestseller, gift, notebook, ebook, download.
- Subtitle must be grammatically correct, natural, smooth, SEO-friendly, and complement the main title.
- NO keyword stuffing, spammy content, all caps, or weird casing.
- Output EXACTLY one clean subtitle line ONLY.

📘 Book Information:
- Book Name: "{book_name}"
- Book Type: "{book_type}"
- Book Language: "{book_lang}"
- Keywords: "{keywords or 'general'}"
- Main Title: "{book_name}" (Length: {title_length} characters)

🧠 Objective:
Generate one subtitle that:
- Complements the main title.
- Uses as much of the allowed subtitle character limit as possible: exactly {subtitle_limit} characters or within ±5 characters.
- Enhances discoverability and SEO.
- Is grammatically correct and reads smoothly.
❌ DO NOT start with:
- "Here is"
- "This is"
- "Sure"
- "Generated description"
- Any quotes, punctuation, or labels
🚫 Strict Rules:
- DO NOT include any of the following:
  - Intro phrases like "Subtitle:" or "Here is".
  - Quotation marks, punctuation marks (e.g., :, ;, ", ', etc.).
  - Line breaks, bullet points, or explanations.
- NO spammy, promotional, misleading, or keyword-stuffed content.
- MUST NOT contain forbidden words: "free", "bestseller", "gift", "notebook", "ebook", "download", etc.
- MUST NOT exceed {subtitle_limit} characters.
- MUST follow Amazon KDP content guidelines.

✅ Output Format:
Return only the clean and final subtitle. Nothing else.
Return ONLY the clean subtitle — one line only — with no extra text, quotes, or formatting.
The line must be complete and should not be cut off mid-sentence.
"""

    raw_response = ai(prompt)
    if not raw_response:
        return None
        
    raw_response = re.sub(r'^(here i.*?:\s*)', '', raw_response.strip(), flags=re.I)
    cleaned = raw_response.strip().split('\n')[0]
    cleaned = re.sub(r"^(subtitle:)", "", cleaned, flags=re.I).strip()
    cleaned = cleaned.strip('"\' :')

    valid = is_valid_text(
        cleaned, subtitle_limit, FORBIDDEN_WORDS, FORBIDDEN_SYMBOLS_SUBTITLE,
        min_length=30, check_space=False,
        banned_starts=("here is", "this is", "subtitle", "example", "optimized")
    )

    if valid:
        return cleaned
    return None

def generate_description(product, binding_type, interior_type, page_count, interior_trim_size, keywords, language, length_level=3, retries=3):
    """Generate book description using GROQ AI"""
    for _ in range(retries):
        desc = _generate_description_once(product, binding_type, interior_type, page_count, interior_trim_size, keywords, language, length_level)
        if desc:
            return desc
    return None

def _generate_description_once(product, binding_type, interior_type, page_count, interior_trim_size, keywords, language, length_level=3):
    """Generate single description attempt"""
    language_map = {
        "en": "English",
        "fr": "French", 
        "es": "Spanish",
        "de": "German",
        "ar": "Arabic"
    }
    language_label = language_map.get(language, "English")

    prompt = f"""
You are a professional KDP product description writer. Generate a detailed, persuasive, and SEO-optimized book description formatted exactly in HTML using only the allowed KDP styles:
Follow these strict rules:
- Format all paragraphs using <p> tags.
- Use <b> for section headings and product title.
- Use <i> only for emphasis.
- Use <ul><li> for lists, including Key Features.
- At the end, include the following Key Features in a bullet list with <li> and bold keys:

- Use <p> for paragraphs.
- Use <b> for bold text.
- Use <i> for italic text.
- Use <ul> and <li> for bulleted lists.
- Use heading tags <h4>, <h5>, <h6> if needed.
- Separate paragraphs with a blank line.
- The first paragraph must have the product name in bold and a strong benefit statement.
- Include multiple paragraphs describing the book, its uses, and benefits.
- Add a bullet list of key features with:
    - Binding Type: {binding_type}
    - Interior Type: {interior_type}
    - Page Count: {page_count}
    - Trim Size: {interior_trim_size}
- End with a warm, encouraging closing paragraph.
- No banned words (free, bestseller, gift, download, ebook, etc.) per KDP rules.
- Use natural, fluent {language_label}.

Input variables:
- product name: {product}
- keywords: {keywords}
❌ DO NOT start with:
- "Here is"
- "This is"
- "Sure"
- "Generated description"
- Any quotes, punctuation, or labels
❌ DO NOT use <div>, <span>, or any class or inline styles.

Output only the full HTML snippet.
"""

    raw_response = ai(prompt)
    if not raw_response:
        return None
        
    raw_response = re.sub(r'^(here i.*?:\s*)', '', raw_response.strip(), flags=re.I).replace("*","")
    return raw_response.strip()