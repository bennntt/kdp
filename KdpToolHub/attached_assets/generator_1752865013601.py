# app/routes/generator/generator.py
import requests
import time
import re

from faker import Faker
import random

LANG_COUNTRY_MAP = {
    "English (US)": "en_US",
    "English (UK)": "en_GB",
    "French (France)": "fr_FR",
    "German (Germany)": "de_DE",
    "Spanish (Spain)": "es_ES",
}

PREFIXES = {
    "en_US": ['Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'Rev.', 'Sir', 'Lady'],
    "en_GB": ['Dr', 'Mr', 'Mrs', 'Ms', 'Prof', 'Rev', 'Sir', 'Lady'],
    "fr_FR": ['M.', 'Mme', 'Dr', 'Prof', 'Mlle'],
    "de_DE": ['Herr', 'Frau', 'Dr.', 'Prof.'],
    "es_ES": ['Sr.', 'Sra.', 'Dr.', 'Prof.'],
}

SUFFIXES = {
    "en_US": ['Jr.', 'Sr.', 'II', 'III', 'PhD', 'MD', 'Esq.'],
    "en_GB": ['Jr', 'Sr', 'II', 'III', 'PhD', 'MD'],
    "fr_FR": ['Jr', 'Sr', 'II', 'III'],
    "de_DE": ['Jr', 'Sr', 'II', 'III'],
    "es_ES": ['Jr', 'Sr', 'II', 'III'],
}

GROQ_API_KEY = "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"
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

FORBIDDEN_WORDS = {"free", "bestseller", "gift", "notebook", "ebook", "download"}
FORBIDDEN_SYMBOLS_TITLE = set('"\' :;\\/|<>*?=+{}[]()#@&%')
FORBIDDEN_SYMBOLS_SUBTITLE = set('"\' ;\\/|<>*?=+{}[]()#@&%')


def ai(prompt, retries=3, delay=2):
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
                print("❌ فشل الاتصال بعد عدة محاولات.")
    return None


def is_valid_text(text, max_length, forbidden_words, forbidden_symbols, min_length=1, check_space=True,
                  banned_starts=()):
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


def _generate_title_once(book_name, book_type, book_lang, keywords=None, user_title=None):
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
    raw_response = re.sub(r'^(here i.*?:\s*)', '', raw_response.strip(), flags=re.I)
    if not raw_response:
        return None
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


def generate_title(book_name, book_type, book_lang, keywords=None, user_title=None, retries=3):
    for _ in range(retries):
        title = _generate_title_once(book_name, book_type, book_lang, keywords, user_title)
        if title is not None:
            return title
    return None


def _generate_subtitle_once(book_name, book_type, book_lang, title_text="", keywords=None):
    max_total = 200
    title_length = len(title_text.strip())
    subtitle_limit = max_total - title_length
    if subtitle_limit <= 0:
        print("❌ لا توجد مساحة للعناوين الفرعية.")
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

You are an AI specialized in generating high-quality, compliant Amazon KDP subtitles.

📘 Book Information:
- Book Name: "{book_name}"
- Book Type: "{book_type}"
- Book Language: "{book_lang}"
- Keywords: "{keywords or 'general'}"
- Main Title: "{title_text}" (Length: {title_length} characters)

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
Return only the clean and final title. Nothing else.
Return ONLY the clean subtitle — one line only — with no extra text, quotes, or formatting.
The line must be complete and should not be cut off mid-sentence.
""".strip()

    raw_response = ai(prompt)
    raw_response = re.sub(r'^(here i.*?:\s*)', '', raw_response.strip(), flags=re.I)
    if not raw_response:
        return None
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


def generate_subtitle(book_name, book_type, book_lang, title_text="", keywords=None, retries=3):
    for _ in range(retries):
        subtitle = _generate_subtitle_once(book_name, book_type, book_lang, title_text, keywords)
        if subtitle is not None:
            return subtitle
    return None


def generate_author_name(language="English (US)", country="United States", gender=None,
                         include_prefix=False, include_middle_name=False, include_suffix=False):
    locale = LANG_COUNTRY_MAP.get(language, "en_US")
    fake = Faker(locale)

    prefix = random.choice(PREFIXES.get(locale, [])) if include_prefix else ''
    suffix = random.choice(SUFFIXES.get(locale, [])) if include_suffix else ''

    if gender == 'male':
        first_name = fake.first_name_male()
    elif gender == 'female':
        first_name = fake.first_name_female()
    else:
        first_name = fake.first_name()

    middle_name = fake.first_name() if include_middle_name else ''
    last_name = fake.last_name()

    return {
        "Prefix": prefix,
        "First Name": first_name,
        "Middle Name": middle_name,
        "Last Name": last_name,
        "Suffix": suffix
    }


def _generate_description_once(product, binding_type, interior_type, page_count, interior_trim_size, keywords, language, length_level=3):
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


""".strip()

    raw_response = ai(prompt)
    raw_response = re.sub(r'^(here i.*?:\s*)', '', raw_response.strip(), flags=re.I).replace("*","")

    return raw_response.strip() if raw_response else None


def generate_description(product,binding_type,interior_type,page_count,interior_trim_size, keywords, language, length_level=3, retries=3):
    for _ in range(retries):
        desc = _generate_description_once(product,binding_type,interior_type,page_count,interior_trim_size, keywords, language, length_level)
        if desc:
            return desc
    return None




if __name__ == "__main__":
    description = generate_description(
        product="Alphabet Tracing Worksheets for Kids A-Z",
        binding_type="Paperback",
        interior_type="Black & White Interior with White Paper",
        page_count="120",
        interior_trim_size="8.5 x 11 in",
        keywords="pdf png eps svg, stencil silhouette, vector vinyl, geometric background, square pattern svg, argyle pattern svg, diamond pattern, tumbler template, checkered pattern, argyle diamond print, argyle cut file, argyle cricut file, argyle stencil",
        language="en",
        length_level=3
    )
    print(description)
