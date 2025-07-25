from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError
from models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please choose a different one.')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', 
                                   validators=[DataRequired(), EqualTo('password')])



class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=5, max=200)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10)])

# Tool Forms
class TitleGeneratorForm(FlaskForm):
    book_name = StringField('Book Name', validators=[DataRequired()])
    book_type = SelectField('Book Type', choices=[
        ('fiction', 'Fiction'),
        ('non-fiction', 'Non-Fiction'),
        ('romance', 'Romance'),
        ('mystery', 'Mystery'),
        ('fantasy', 'Fantasy'),
        ('sci-fi', 'Science Fiction'),
        ('biography', 'Biography'),
        ('self-help', 'Self Help'),
        ('business', 'Business'),
        ('cooking', 'Cooking'),
        ('health', 'Health & Fitness'),
        ('children', 'Children\'s Books')
    ], validators=[DataRequired()])
    language = SelectField('Language', choices=[
        ('english', 'English'),
        ('arabic', 'Arabic'),
        ('french', 'French'),
        ('spanish', 'Spanish'),
        ('german', 'German'),
        ('italian', 'Italian'),
        ('portuguese', 'Portuguese'),
        ('russian', 'Russian'),
        ('chinese', 'Chinese'),
        ('japanese', 'Japanese')
    ], validators=[DataRequired()])
    keywords = StringField('Keywords (Optional)', validators=[Optional()])

class SubtitleGeneratorForm(FlaskForm):
    title = StringField('Book Title', validators=[DataRequired()])
    book_type = SelectField('Book Type', choices=[
        ('fiction', 'Fiction'),
        ('non-fiction', 'Non-Fiction'),
        ('romance', 'Romance'),
        ('mystery', 'Mystery'),
        ('fantasy', 'Fantasy'),
        ('sci-fi', 'Science Fiction'),
        ('biography', 'Biography'),
        ('self-help', 'Self Help'),
        ('business', 'Business'),
        ('cooking', 'Cooking'),
        ('health', 'Health & Fitness'),
        ('children', 'Children\'s Books')
    ], validators=[DataRequired()])
    language = SelectField('Language', choices=[
        ('english', 'English'),
        ('arabic', 'Arabic'),
        ('french', 'French'),
        ('spanish', 'Spanish'),
        ('german', 'German'),
        ('italian', 'Italian'),
        ('portuguese', 'Portuguese'),
        ('russian', 'Russian'),
        ('chinese', 'Chinese'),
        ('japanese', 'Japanese')
    ], validators=[DataRequired()])
    keywords = StringField('Keywords (Optional)', validators=[Optional()])

class DescriptionGeneratorForm(FlaskForm):
    title = StringField('Book Title', validators=[DataRequired()])
    language = SelectField('Language', choices=[
        ('english', 'English'),
        ('arabic', 'Arabic'),
        ('french', 'French'),
        ('spanish', 'Spanish'),
        ('german', 'German'),
        ('italian', 'Italian'),
        ('portuguese', 'Portuguese'),
        ('russian', 'Russian'),
        ('chinese', 'Chinese'),
        ('japanese', 'Japanese')
    ], validators=[DataRequired()])
    keywords = StringField('Keywords (Optional)', validators=[Optional()])
    binding_type = SelectField('Binding Type', choices=[
        ('paperback', 'Paperback'),
        ('hardcover', 'Hardcover'),
        ('', 'Select Binding Type')
    ], validators=[Optional()])
    interior_type = SelectField('Interior Type', choices=[
        ('black_white', 'Black & White'),
        ('standard_color', 'Standard Color'),
        ('premium_color', 'Premium Color'),
        ('', 'Select Interior Type')
    ], validators=[Optional()])
    page_count = IntegerField('Page Count', validators=[Optional(), NumberRange(min=1, max=999)])
    interior_trim_size = SelectField('Interior Trim Size', choices=[
        ('5x8', '5 x 8 in'),
        ('5.5x8.5', '5.5 x 8.5 in'),
        ('6x9', '6 x 9 in'),
        ('7x10', '7 x 10 in'),
        ('8x10', '8 x 10 in'),
        ('8.5x11', '8.5 x 11 in'),
        ('', 'Select Trim Size')
    ], validators=[Optional()])
    description_length = IntegerField('Length of description', validators=[DataRequired(), NumberRange(min=1, max=3)], default=2)

class AuthorGeneratorForm(FlaskForm):
    language = SelectField('Language', choices=[
        ('english', 'English'),
        ('arabic', 'Arabic'),
        ('french', 'French'),
        ('spanish', 'Spanish'),
        ('german', 'German'),
        ('italian', 'Italian'),
        ('portuguese', 'Portuguese'),
        ('russian', 'Russian'),
        ('chinese', 'Chinese'),
        ('japanese', 'Japanese')
    ], validators=[DataRequired()])
    country = SelectField('Country', choices=[
        ('saudi_arabia', 'Saudi Arabia'),
        ('egypt', 'Egypt'),
        ('uae', 'United Arab Emirates'),
        ('jordan', 'Jordan'),
        ('lebanon', 'Lebanon'),
        ('morocco', 'Morocco'),
        ('tunisia', 'Tunisia'),
        ('algeria', 'Algeria'),
        ('iraq', 'Iraq'),
        ('syria', 'Syria'),
        ('palestine', 'Palestine'),
        ('kuwait', 'Kuwait'),
        ('qatar', 'Qatar'),
        ('bahrain', 'Bahrain'),
        ('oman', 'Oman'),
        ('yemen', 'Yemen'),
        ('usa', 'United States'),
        ('uk', 'United Kingdom'),
        ('canada', 'Canada'),
        ('australia', 'Australia'),
        ('germany', 'Germany'),
        ('france', 'France'),
        ('italy', 'Italy'),
        ('spain', 'Spain'),
        ('russia', 'Russia'),
        ('china', 'China'),
        ('japan', 'Japan'),
        ('india', 'India'),
        ('brazil', 'Brazil'),
        ('mexico', 'Mexico')
    ], validators=[DataRequired()])
    gender = SelectField('Gender', choices=[
        ('male', 'Male'),
        ('female', 'Female')
    ], validators=[DataRequired()], default='male')
    
    # Fields to generate (checkboxes)
    prefix = BooleanField('Prefix', default=False)
    first_name = BooleanField('First Name', default=True)
    middle_name = BooleanField('Middle Name', default=False)
    last_name = BooleanField('Last Name', default=True)
    suffix = BooleanField('Suffix', default=False)

class KeywordResearchForm(FlaskForm):
    topic = StringField('Topic/Subject', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('books', 'Books'),
        ('ebooks', 'eBooks'),
        ('kindle', 'Kindle'),
        ('fiction', 'Fiction'),
        ('non-fiction', 'Non-Fiction'),
        ('romance', 'Romance'),
        ('mystery', 'Mystery'),
        ('fantasy', 'Fantasy'),
        ('sci-fi', 'Science Fiction'),
        ('biography', 'Biography'),
        ('self-help', 'Self Help'),
        ('business', 'Business'),
        ('cooking', 'Cooking'),
        ('health', 'Health & Fitness'),
        ('children', 'Children\'s Books')
    ], validators=[DataRequired()])

class CategoryFinderForm(FlaskForm):
    title = StringField('Book Title', validators=[DataRequired()])
    description = TextAreaField('Book Description', validators=[DataRequired()])
    keywords = StringField('Keywords (comma separated)', validators=[DataRequired()])

class RoyaltyCalculatorForm(FlaskForm):
    book_type = SelectField('Book Type', choices=[
        ('paperback', 'Paperback'),
        ('hardcover', 'Hardcover')
    ], validators=[DataRequired()])
    interior_type = SelectField('Interior Type', choices=[
        ('black_white', 'Black & white'),
        ('standard_color', 'Standard color'),
        ('premium_color', 'Premium color')
    ], validators=[DataRequired()])
    marketplace = SelectField('Marketplace', choices=[
        ('Amazon.com', 'Amazon.com (USD)'),
        ('Amazon.co.uk', 'Amazon.co.uk (GBP)'),
        ('Amazon.de', 'Amazon.de (EUR)'),
        ('Amazon.fr', 'Amazon.fr (EUR)'),
        ('Amazon.es', 'Amazon.es (EUR)'),
        ('Amazon.it', 'Amazon.it (EUR)'),
        ('Amazon.nl', 'Amazon.nl (EUR)'),
        ('Amazon.ca', 'Amazon.ca (CAD)'),
        ('Amazon.com.au', 'Amazon.com.au (AUD)'),
        ('Amazon.co.jp', 'Amazon.co.jp (JPY)'),
        ('Amazon.pl', 'Amazon.pl (PLN)'),
        ('Amazon.se', 'Amazon.se (SEK)')
    ], validators=[DataRequired()])
    trim_size = SelectField('Trim Size', choices=[
        ('5x8', '5 x 8 (12.85 x 20.32 cm)'),
        ('5.25x8', '5.25 x 8 (13.34 x 20.32 cm)'),
        ('5.5x8.5', '5.5 x 8.5 (13.97 x 21.59 cm)'),
        ('6x9', '6 x 9 (15.24 x 22.86 cm)'),
        ('6.14x9.21', '6.14 x 9.21 (15.6 x 23.39 cm)'),
        ('6.69x9.61', '6.69 x 9.61 (17.0 x 24.4 cm)'),
        ('7x10', '7 x 10 (17.78 x 25.4 cm)'),
        ('7.44x9.69', '7.44 x 9.69 (18.9 x 24.61 cm)'),
        ('7.5x9.25', '7.5 x 9.25 (19.05 x 23.5 cm)'),
        ('8x10', '8 x 10 (20.32 x 25.4 cm)'),
        ('8.25x6', '8.25 x 6 (20.96 x 15.24 cm)'),
        ('8.25x8.25', '8.25 x 8.25 (20.96 x 20.96 cm)'),
        ('8.25x11', '8.25 x 11 (20.96 x 27.94 cm)'),
        ('8.5x8.5', '8.5 x 8.5 (21.59 x 21.59 cm)'),
        ('8.5x11', '8.5 x 11 (21.59 x 27.94 cm)'),
        ('8.27x11.69', '8.27 x 11.69 (21 x 29.7 cm)')
    ], validators=[DataRequired()])
    page_count = IntegerField('Page Count', validators=[DataRequired(), NumberRange(min=1, max=8000)])
    list_price = StringField('List Price ($)', validators=[DataRequired()])

class TrademarkSearchForm(FlaskForm):
    search_term = StringField('Search Term', validators=[DataRequired()])
    search_type = SelectField('Search Type', choices=[
        ('exact', 'Exact Match'),
        ('contains', 'Contains'),
        ('similar', 'Similar')
    ], validators=[DataRequired()])
