import os
import tempfile
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, Response
import PyPDF2
import openai
import tempfile
from werkzeug.utils import secure_filename
import shutil

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-railway-deployment')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Audio extensions
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_AUDIO_EXTENSIONS = {'webm', 'mp3', 'wav', 'm4a', 'ogg'}
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # Increase to 25MB for audio files

# Initialize OpenAI client
openai_client = None
openai_available = False

try:
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        openai_client = openai.OpenAI(api_key=api_key)
        openai_available = True
        print("✅ OpenAI API key found - AI-powered questions enabled")
    else:
        print("⚠️ No OpenAI API key found - running in demo mode")
except Exception as e:
    print(f"❌ OpenAI initialization failed: {e}")
    openai_available = False

# Audio functions
def allowed_audio_file(filename):
    """Check if uploaded file is an allowed audio format"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

def transcribe_audio_whisper(audio_file_path):
    """Transcribe audio using OpenAI Whisper API"""
    if not openai_available:
        return "[Audio transcription unavailable - AI not enabled]"
    
    try:
        print(f"🎤 Starting transcription of {audio_file_path}...")
        
        with open(audio_file_path, 'rb') as audio_file:
            transcription = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                language="en",
                response_format="text"
            )
        
        print(f"✅ Transcription successful: {transcription[:100]}...")
        return transcription
        
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return f"[Transcription failed: {str(e)}]"

# PDF Processing Functions
def extract_text_from_pdf(pdf_file):
    """Extract text content from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text_content = ""
        
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                text_content += page.extract_text() + "\n"
            except Exception as e:
                print(f"Error reading page {page_num}: {e}")
                continue
        
        return text_content.strip()
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

def analyze_report_with_ai(report_content, company_name, industry, report_type):
    """Use OpenAI to analyze report content and extract key themes"""
    if not openai_available or not openai_client:
        # Fallback to basic analysis
        return analyze_report_themes_basic(report_content)
    
    try:
        prompt = f"""
        Analyze this business report for {company_name} in the {industry} industry.
        Report type: {report_type}
        
        Extract 5-7 key strategic themes, challenges, or opportunities that executives would want to question.
        Focus on areas that need deeper analysis or clarification.
        
        Report content:
        {report_content[:3000]}...
        
        Return only a Python list of themes, like:
        ["market expansion strategy", "financial projections", "competitive positioning"]
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a business analyst extracting key themes from reports."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.3
        )
        
        # Parse the response to extract themes
        themes_text = response.choices[0].message.content.strip()
        
        # Try to extract list from response
        import ast
        try:
            themes = ast.literal_eval(themes_text)
            if isinstance(themes, list):
                return themes[:6]  # Limit to 6 themes
        except:
            pass
            
        # Fallback: split by lines or commas
        themes = []
        for line in themes_text.split('\n'):
            line = line.strip('- "[]')
            if line and len(line) > 5:
                themes.append(line)
        
        return themes[:6] if themes else ["your strategic approach"]
        
    except Exception as e:
        print(f"AI analysis failed: {e}")
        return analyze_report_themes_basic(report_content)

def analyze_report_themes_basic(report_content):
    """Basic keyword-based theme extraction (fallback)"""
    if not report_content or len(report_content) < 100:
        return ["your main proposal"]
    
    themes = []
    theme_keywords = {
        'digital transformation': ['digital', 'technology', 'automation', 'AI'],
        'market expansion': ['expand', 'growth', 'market', 'international'],
        'cost reduction': ['cost', 'efficiency', 'savings', 'optimize'],
        'new product launch': ['product', 'launch', 'innovation', 'development'],
        'customer experience': ['customer', 'experience', 'satisfaction', 'service'],
        'sustainability': ['sustainable', 'green', 'environment', 'ESG'],
        'financial strategy': ['revenue', 'profit', 'investment', 'funding'],
        'competitive strategy': ['competition', 'competitor', 'market share', 'differentiation']
    }
    
    content_lower = report_content.lower()
    for theme, keywords in theme_keywords.items():
        if any(keyword in content_lower for keyword in keywords):
            themes.append(theme)
    
    return themes[:5] if themes else ["your strategic approach"]

def generate_ai_questions(report_content, executive_role, company_name, industry, report_type, key_themes):
    """Generate AI-powered questions based on report analysis"""
    
    if not openai_available or not openai_client:
        # Fallback to template-based questions
        return generate_template_questions(executive_role, company_name, industry, report_type, key_themes)
    
    try:
        # Create role-specific context
        role_contexts = {
            'CEO': 'strategic vision, market positioning, competitive advantage, long-term growth, stakeholder value',
            'CFO': 'financial performance, cash flow, profitability, investment returns, financial risks, capital allocation',
            'CTO': 'technology architecture, scalability, technical risks, innovation, development timeline, data security',
            'CMO': 'market positioning, customer acquisition, brand strategy, marketing ROI, customer retention',
            'COO': 'operational efficiency, process optimization, supply chain, quality control, execution capabilities'
        }
        
        role_context = role_contexts.get(executive_role, 'business strategy and operations')
        themes_str = ', '.join(key_themes[:4])
        
        prompt = f"""
        You are a senior {executive_role} reviewing a {report_type} for {company_name} in the {industry} industry.
        
        Key themes identified: {themes_str}
        
        As a {executive_role}, generate 7 challenging but fair questions that focus on {role_context}.
        Questions should:
        - Be specific to the {industry} industry
        - Reference the key themes when relevant
        - Challenge assumptions and require detailed responses
        - Be appropriate for a {executive_role} to ask
        - Include follow-up probes for deeper analysis
        
        Report excerpt:
        {report_content[:2000]}...
        
        Return exactly 7 questions as a numbered list:
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are an experienced {executive_role} asking strategic questions about business presentations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        questions_text = response.choices[0].message.content.strip()
        
        # Parse questions from response
        questions = []
        for line in questions_text.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove numbering and clean up
                question = line.split('.', 1)[-1].strip()
                question = question.split(')', 1)[-1].strip()
                question = question.lstrip('- •').strip()
                if len(question) > 20:  # Valid question
                    questions.append(question)
        
        return questions[:7] if questions else generate_template_questions(executive_role, company_name, industry, report_type, key_themes)
        
    except Exception as e:
        print(f"AI question generation failed for {executive_role}: {e}")
        return generate_template_questions(executive_role, company_name, industry, report_type, key_themes)

def generate_template_questions(executive_role, company_name, industry, report_type, key_themes):
    """Generate template-based questions (fallback)"""
    
    theme = key_themes[0] if key_themes else "your strategy"
    
    role_templates = {
        'CEO': [
            f"Looking at your {report_type.lower()} for {company_name}, what's the biggest strategic risk in the {industry} sector that you haven't addressed?",
            f"Your approach to {theme} is interesting, but how does it differentiate {company_name} from established players in {industry}?",
            f"If the {industry} market conditions change significantly, what's your pivot strategy?",
            f"How do you plan to scale {theme} while maintaining competitive advantage in {industry}?",
            f"What would trigger you to completely rethink your {industry} strategy?",
            f"Looking at {company_name}'s position, what's your sustainable competitive moat?",
            f"How does this {report_type.lower()} align with broader {industry} industry trends?"
        ],
        'CFO': [
            f"Your financial projections for {company_name} seem aggressive for the {industry} sector - what's driving these assumptions?",
            f"I'm concerned about cash flow in your {theme} initiative. How will you fund this without diluting equity?",
            f"Your cost structure appears optimistic for {industry}. What if operating costs increase by 30%?",
            f"How did you validate the revenue assumptions for {company_name} in the {industry} market?",
            f"What's your plan if {company_name} needs 50% more capital than projected?",
            f"How will you measure ROI on your {theme} investments?",
            f"What financial metrics will determine success or failure of this {industry} strategy?"
        ],
        'CTO': [
            f"Your technology approach for {company_name} raises scalability concerns. How will this work at enterprise scale in {industry}?",
            f"What's your biggest technical risk in implementing {theme}, and how are you mitigating it?",
            f"The {industry} sector has specific compliance requirements - how does your tech stack address these?",
            f"What happens if your core technical assumptions about {theme} prove incorrect?",
            f"How does {company_name}'s technology compare to industry standards in {industry}?",
            f"What's your technical debt strategy as you scale this {industry} solution?",
            f"How will you handle data security and privacy in the {industry} context?"
        ],
        'CMO': [
            f"Your customer acquisition strategy for {company_name} in {industry} seems ambitious - how will you actually reach these customers?",
            f"I don't see strong differentiation in your {theme} value proposition. What makes you unique in {industry}?",
            f"Your marketing budget assumptions - are these based on actual {industry} benchmarks?",
            f"How do you plan to compete against established brands in the {industry} market?",
            f"What's your customer retention strategy beyond initial acquisition in {industry}?",
            f"How will you measure marketing ROI for {company_name}'s {theme} initiative?",
            f"What customer feedback have you gathered about your {industry} approach?"
        ],
        'COO': [
            f"The operational plan for {company_name}'s {theme} looks complex - what's your biggest execution risk?",
            f"How will you scale operations while maintaining quality in the {industry} sector?",
            f"Your timeline seems aggressive - what if key milestones are delayed in this {industry} rollout?",
            f"How have you validated your supply chain assumptions for the {industry} market?",
            f"What operational metrics will you track, and what are your targets for {theme}?",
            f"How will you manage quality control as {company_name} grows in {industry}?",
            f"What's your contingency plan if operations don't scale as expected?"
        ]
    }
    
    questions = role_templates.get(executive_role, [])
    return questions[:7] if questions else [f"Can you elaborate on your {theme} approach for {company_name}?"]

def get_executive_name(role):
    """Get executive name by role"""
    names = {
        'CEO': 'Sarah Chen',
        'CFO': 'Michael Rodriguez', 
        'CTO': 'Dr. Lisa Wang',
        'CMO': 'James Thompson',
        'COO': 'Rebecca Johnson'
    }
    return names.get(role, 'Executive')

def get_next_executive(selected_executives, conversation_history):
    """Determine which executive should ask the next question"""
    
    exec_question_count = {}
    for exec_role in selected_executives:
        exec_question_count[exec_role] = len([
            msg for msg in conversation_history 
            if msg.get('type') == 'question' and msg.get('executive') == exec_role
        ])
    
    if not conversation_history:
        return 'CEO' if 'CEO' in selected_executives else selected_executives[0]
    
    min_questions = min(exec_question_count.values())
    candidates = [exec for exec, count in exec_question_count.items() if count == min_questions]
    
    if len(candidates) > 1:
        last_exec = None
        for msg in reversed(conversation_history):
            if msg.get('type') == 'question':
                last_exec = msg.get('executive')
                break
        
        if last_exec in candidates:
            try:
                current_index = candidates.index(last_exec)
                next_index = (current_index + 1) % len(candidates)
                return candidates[next_index]
            except ValueError:
                pass
    
    return candidates[0] if candidates else selected_executives[0]

def check_session_limit(session_data):
    """Check if session has reached its limit"""
    session_type = session_data.get('session_type', 'questions')
    conversation_history = session_data.get('conversation_history', [])
    session_start = session_data.get('session_start_time')
    
    if session_type == 'questions':
        question_limit = int(session_data.get('question_limit', 10))
        question_count = len([msg for msg in conversation_history if msg.get('type') == 'question'])
        return question_count >= question_limit
    
    elif session_type == 'time' and session_start:
        time_limit = int(session_data.get('time_limit', 10))
        start_time = datetime.fromisoformat(session_start)
        elapsed = datetime.now() - start_time
        return elapsed.total_seconds() >= (time_limit * 60)
    
    return False

def generate_closing_message(company_name, report_type):
    """Generate a professional closing message from the CEO"""
    closing_messages = [
        f"Thank you for presenting your {report_type.lower()} for {company_name}. You've given our executive team excellent insights to consider. Your strategic thinking is impressive, and we appreciate the thorough analysis.",
        f"This has been a productive discussion about {company_name}. Your {report_type.lower()} demonstrates solid strategic planning, and the team has gained valuable perspectives from your presentation.",
        f"Excellent work on your {report_type.lower()} for {company_name}. You've addressed our key concerns with thoughtful responses. The executive team will incorporate several of your insights into our strategic discussions."
    ]
    return random.choice(closing_messages)

def generate_transcript(session_data):
    """Generate a formatted transcript of the executive panel session"""
    company_name = session_data.get('company_name', 'Your Company')
    industry = session_data.get('industry', 'Technology')
    report_type = session_data.get('report_type', 'Business Plan')
    selected_executives = session_data.get('selected_executives', [])
    responses = session_data.get('responses', [])
    questions = session_data.get('questions', [])
    
    session_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    ai_mode = "AI-Enhanced Topic Diversity" if openai_available else "Demo Mode"
    
    transcript = f"""
AI EXECUTIVE PANEL SIMULATOR - {ai_mode}
SESSION TRANSCRIPT
====================================

Company: {company_name}
Industry: {industry}
Report Type: {report_type}
Session Date: {session_date}
Executives Present: {', '.join(selected_executives)}
AI Enhancement: {'Enabled - Diverse Topic Coverage with Audio Support' if openai_available else 'Template-based'}

====================================
PRESENTATION TRANSCRIPT
====================================

"""

    for i, (question, response) in enumerate(zip(questions, responses), 1):
        transcript += f"QUESTION {i}\n"
        transcript += f"{question.get('name', 'Executive')} ({question.get('executive', 'Executive')}):\n"
        transcript += f"{question.get('question', 'Question not recorded')}\n\n"
        
        transcript += f"STUDENT RESPONSE:\n"
        
        # Handle both string responses (text) and dict responses (audio)
        if isinstance(response, dict):
            transcript += f"{response.get('text', 'Response not recorded')}\n"
            if response.get('type') == 'audio':
                transcript += f"[Response provided via audio recording]\n"
        else:
            transcript += f"{response}\n"
        
        transcript += "\n" + "-" * 50 + "\n\n"
    
    transcript += "====================================\n"
    transcript += "END OF TRANSCRIPT\n"
    transcript += "====================================\n"
    transcript += f"Generated by AI Executive Panel Simulator ({ai_mode})\n"
    transcript += f"Total Questions Asked: {len(questions)}\n"
    
    # Count audio vs text responses
    audio_count = sum(1 for r in responses if isinstance(r, dict) and r.get('type') == 'audio')
    text_count = len(responses) - audio_count
    if audio_count > 0:
        transcript += f"Audio Responses: {audio_count} | Text Responses: {text_count}\n"
    
    return transcript
    
def generate_transcript_pdf(session_data):
    """Generate a professionally formatted PDF transcript"""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from io import BytesIO
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='#BF5700',  # UT Orange
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#BF5700',
        spaceAfter=10,
        spaceBefore=12
    )
    
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    question_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontSize=11,
        leftIndent=20,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    
    response_style = ParagraphStyle(
        'ResponseStyle',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=20,
        spaceAfter=12
    )
    
    # Get session data
    company_name = session_data.get('company_name', 'Your Company')
    industry = session_data.get('industry', 'Technology')
    report_type = session_data.get('report_type', 'Business Plan')
    selected_executives = session_data.get('selected_executives', [])
    responses = session_data.get('responses', [])
    questions = session_data.get('questions', [])
    
    session_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    ai_mode = "AI-Enhanced Topic Diversity" if openai_available else "Demo Mode"
    
    # Add title
    elements.append(Paragraph("AI EXECUTIVE PANEL SIMULATOR", title_style))
    elements.append(Paragraph(f"Session Transcript - {ai_mode}", info_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add session information
    elements.append(Paragraph("SESSION INFORMATION", heading_style))
    elements.append(Paragraph(f"<b>Company:</b> {company_name}", info_style))
    elements.append(Paragraph(f"<b>Industry:</b> {industry}", info_style))
    elements.append(Paragraph(f"<b>Report Type:</b> {report_type}", info_style))
    elements.append(Paragraph(f"<b>Session Date:</b> {session_date}", info_style))
    elements.append(Paragraph(f"<b>Executives Present:</b> {', '.join(selected_executives)}", info_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Add presentation transcript
    elements.append(Paragraph("PRESENTATION TRANSCRIPT", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    for i, (question, response) in enumerate(zip(questions, responses), 1):
        # Question
        exec_name = question.get('name', 'Executive')
        exec_role = question.get('executive', 'Executive')
        question_text = question.get('question', 'Question not recorded')
        
        elements.append(Paragraph(f"<b>QUESTION {i}</b>", question_style))
        elements.append(Paragraph(f"{exec_name} ({exec_role}):", info_style))
        elements.append(Paragraph(question_text, response_style))
        
        # Response
        elements.append(Paragraph("<b>STUDENT RESPONSE:</b>", question_style))
        elements.append(Paragraph(response, response_style))
        elements.append(Spacer(1, 0.2*inch))
    
    # Add footer
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("END OF TRANSCRIPT", heading_style))
    elements.append(Paragraph(f"Generated by AI Executive Panel Simulator ({ai_mode})", info_style))
    elements.append(Paragraph(f"Total Questions Asked: {len(questions)}", info_style))
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and return it
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# Routes
@app.route('/')
def index():
    return render_template('index.html', ai_enabled=openai_available)

@app.route('/setup_session', methods=['POST'])
def setup_session():
    try:
        if 'report-pdf' not in request.files:
            return jsonify({'status': 'error', 'error': 'No PDF file uploaded'})
        
        file = request.files['report-pdf']
        if file.filename == '':
            return jsonify({'status': 'error', 'error': 'No file selected'})
        
        company_name = request.form.get('company-name', '')
        industry = request.form.get('industry', '')
        report_type = request.form.get('report-type', 'Business Plan')
        selected_executives = request.form.getlist('executives')
        session_type = request.form.get('session-type', 'questions')
        question_limit = request.form.get('question-limit', '10')
        time_limit = request.form.get('time-limit', '10')
        
        if not all([company_name, industry, selected_executives]):
            return jsonify({'status': 'error', 'error': 'Missing required form data'})
        
        report_content = extract_text_from_pdf(file)
        
        if not report_content:
            return jsonify({'status': 'error', 'error': 'Could not extract text from PDF. Please ensure it\'s a text-based PDF.'})
        
        # AI-powered analysis
        key_themes = analyze_report_with_ai(report_content, company_name, industry, report_type)
        
        session['company_name'] = company_name
        session['industry'] = industry
        session['report_type'] = report_type
        session['selected_executives'] = selected_executives
        session['report_content'] = report_content[:5000]
        session['key_themes'] = key_themes
        session['conversation_history'] = []
        session['session_type'] = session_type
        session['question_limit'] = question_limit
        session['time_limit'] = time_limit
        session['session_start_time'] = datetime.now().isoformat()
        session['used_questions'] = {exec: [] for exec in selected_executives}
        
        return jsonify({
            'status': 'success',
            'message': f'Report analyzed successfully! Found {len(report_content)} characters of content. {"AI-powered" if openai_available else "Template-based"} questions generated.',
            'executives': selected_executives,
            'ai_enabled': openai_available,
            'key_themes': key_themes[:3]
        })
        
    except Exception as e:
        print(f"Setup session error: {e}")
        return jsonify({'status': 'error', 'error': f'Error processing upload: {str(e)}'})

@app.route('/start_presentation', methods=['POST'])
def start_presentation():
    try:
        if 'report_content' not in session:
            return jsonify({'status': 'error', 'error': 'No report uploaded. Please start over.'})
        
        selected_executives = session.get('selected_executives', [])
        company_name = session.get('company_name', '')
        industry = session.get('industry', '')
        report_type = session.get('report_type', '')
        report_content = session.get('report_content', '')
        key_themes = session.get('key_themes', [])
        conversation_history = session.get('conversation_history', [])
        
        if not selected_executives:
            return jsonify({'status': 'error', 'error': 'No executives selected'})
        
        # Generate AI-powered questions for all executives
        all_questions = {}
        for exec_role in selected_executives:
            questions = generate_ai_questions(
                report_content, exec_role, company_name, industry, report_type, key_themes
            )
            all_questions[exec_role] = questions
        
        session['generated_questions'] = all_questions
        
        first_exec = get_next_executive(selected_executives, conversation_history)
        first_questions = all_questions.get(first_exec, [])
        
        if first_questions:
            question_data = {
                'executive': first_exec,
                'name': get_executive_name(first_exec),
                'title': first_exec,
                'question': first_questions[0],
                'timestamp': datetime.now().isoformat()
            }
            
            used_questions = session.get('used_questions', {})
            if first_exec not in used_questions:
                used_questions[first_exec] = []
            used_questions[first_exec].append(0)
            session['used_questions'] = used_questions
            
            conversation_history.append({
                'type': 'question',
                'executive': first_exec,
                'question': first_questions[0],
                'timestamp': datetime.now().isoformat()
            })
            session['conversation_history'] = conversation_history
            
            return jsonify({
                'status': 'success',
                'initial_questions': [question_data],
                'ai_enabled': openai_available
            })
        
        return jsonify({'status': 'error', 'error': 'No questions generated'})
        
    except Exception as e:
        print(f"Start presentation error: {e}")
        return jsonify({'status': 'error', 'error': f'Error starting presentation: {str(e)}'})

@app.route('/respond_to_executive', methods=['POST'])
def respond_to_executive():
    try:
        data = request.get_json()
        student_response = data.get('response', '')
        current_executive = data.get('executive_role', '')
        
        if not student_response or not current_executive:
            return jsonify({'status': 'error', 'error': 'Missing response or executive role'})
        
        selected_executives = session.get('selected_executives', [])
        conversation_history = session.get('conversation_history', [])
        generated_questions = session.get('generated_questions', {})
        used_questions = session.get('used_questions', {})
        
        conversation_history.append({
            'type': 'response',
            'student_response': student_response,
            'timestamp': datetime.now().isoformat()
        })
        
        session_data = {
            'session_type': session.get('session_type', 'questions'),
            'question_limit': session.get('question_limit', '10'),
            'time_limit': session.get('time_limit', '10'),
            'conversation_history': conversation_history,
            'session_start_time': session.get('session_start_time')
        }
        
        if check_session_limit(session_data):
            company_name = session.get('company_name', 'Your Company')
            report_type = session.get('report_type', 'presentation')
            closing_message = generate_closing_message(company_name, report_type)
            
            closing_question = {
                'executive': 'CEO',
                'name': get_executive_name('CEO'),
                'title': 'CEO',
                'question': closing_message,
                'is_closing': True,
                'timestamp': datetime.now().isoformat()
            }
            
            conversation_history.append({
                'type': 'closing',
                'executive': 'CEO',
                'message': closing_message,
                'timestamp': datetime.now().isoformat()
            })
            
            session['conversation_history'] = conversation_history
            
            return jsonify({
                'status': 'success',
                'follow_up': closing_question,
                'session_ending': True
            })
        
        next_executive = get_next_executive(selected_executives, conversation_history)
        next_questions = generated_questions.get(next_executive, [])
        exec_used_questions = used_questions.get(next_executive, [])
        
        available_questions = [
            (i, q) for i, q in enumerate(next_questions) 
            if i not in exec_used_questions
        ]
        
        if available_questions:
            question_index, next_question = random.choice(available_questions)
            exec_used_questions.append(question_index)
            used_questions[next_executive] = exec_used_questions
            session['used_questions'] = used_questions
        else:
            follow_ups = [
                "That's interesting. Can you provide a specific example?",
                "How would you measure success for that approach?",
                "What would you do if that strategy doesn't work as expected?",
                "Can you walk us through the implementation timeline?",
                "What resources would you need to execute that plan?"
            ]
            next_question = random.choice(follow_ups)
        
        follow_up = {
            'executive': next_executive,
            'name': get_executive_name(next_executive),
            'title': next_executive,
            'question': next_question,
            'timestamp': datetime.now().isoformat()
        }
        
        conversation_history.append({
            'type': 'question',
            'executive': next_executive,
            'question': next_question,
            'timestamp': datetime.now().isoformat()
        })
        
        session['conversation_history'] = conversation_history
        
        return jsonify({
            'status': 'success',
            'follow_up': follow_up
        })
        
    except Exception as e:
        print(f"Respond to executive error: {e}")
        return jsonify({'status': 'error', 'error': f'Error generating follow-up: {str(e)}'})

@app.route('/end_session', methods=['POST'])
def end_session():
    try:
        conversation_history = session.get('conversation_history', [])
        company_name = session.get('company_name', 'Your Company')
        report_type = session.get('report_type', 'presentation')
        session_type = session.get('session_type', 'questions')
        
        questions_asked = len([msg for msg in conversation_history if msg.get('type') == 'question'])
        responses_given = len([msg for msg in conversation_history if msg.get('type') == 'response'])
        
        summary = {
            'total_questions': questions_asked,
            'total_responses': responses_given,
            'company_name': company_name,
            'presentation_topic': report_type,
            'executives_involved': session.get('selected_executives', []),
            'session_type': session_type,
            'session_limit': session.get('question_limit' if session_type == 'questions' else 'time_limit', 'Not set'),
            'ai_enabled': openai_available
        }
        
        return jsonify({
            'status': 'success',
            'summary': summary
        })
        
    except Exception as e:
        print(f"End session error: {e}")
        return jsonify({'status': 'error', 'error': f'Error ending session: {str(e)}'})

@app.route('/download_transcript', methods=['GET'])
def download_transcript():
    try:
        session_data = get_session_data()
        if not session_data:
            return jsonify({'status': 'error', 'error': 'No session data for transcript'})
        
        # Generate PDF transcript
        pdf_content = generate_transcript_pdf(session_data)
        
        company_name = session_data.get('company_name', 'Company')
        session_date = datetime.now().strftime("%Y%m%d_%H%M")
        
        safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_company_name = safe_company_name.replace(' ', '_')
        
        ai_suffix = "_AI_TopicDiverse" if openai_available else "_Demo"
        filename = f"{safe_company_name}_Executive_Panel_Transcript{ai_suffix}_{session_date}.pdf"
        
        response = Response(
            pdf_content,
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
        
        return response
        
    except Exception as e:
        print(f"Download transcript error: {e}")
        return jsonify({'status': 'error', 'error': f'Error generating transcript: {str(e)}'})


# Logo serving route (if logo is in root directory)
@app.route('/mccombs-logo.jpg')
def serve_logo():
    """Serve the McCombs logo from the root directory"""
    try:
        from flask import send_file
        import os
        logo_path = os.path.join(os.getcwd(), 'mccombs-logo.jpg')
        return send_file(logo_path, mimetype='image/jpeg')
    except Exception as e:
        print(f"Error serving logo: {e}")
        return "Logo not found", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 AI Executive Panel Simulator Starting...")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"🤖 AI Enhancement: {'Enabled' if openai_available else 'Disabled (Demo Mode)'}")
    print(f"🌐 Running on port: {port}")
    print("="*50)
    
    app.run(debug=debug_mode, port=port, host='0.0.0.0')

# Audio routes
@app.route('/respond_to_executive_audio', methods=['POST'])
def respond_to_executive_audio():
    """Handle audio response submission with transcription"""
    try:
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({'status': 'error', 'error': 'No audio file provided'})
        
        audio_file = request.files['audio']
        current_executive = request.form.get('executive_role', '')
        
        if audio_file.filename == '':
            return jsonify({'status': 'error', 'error': 'No file selected'})
        
        # Validate file type
        if not allowed_audio_file(audio_file.filename):
            return jsonify({'status': 'error', 'error': 'Invalid audio file format. Please use webm, mp3, wav, m4a, or ogg.'})
        
        # Save audio file temporarily
        filename = secure_filename(f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        audio_file.save(filepath)
        
        print(f"📁 Audio file saved: {filepath} ({os.path.getsize(filepath)} bytes)")
        
        # Transcribe audio to text
        transcription = transcribe_audio_whisper(filepath)
        
        if not transcription or transcription.startswith('['):
            # Clean up and return error
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'status': 'error', 'error': 'Failed to transcribe audio. Please try again or use text input.'})
        
        # Get session data
        session_data = get_session_data()
        if not session_data:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'status': 'error', 'error': 'Session data lost. Please restart session.'})
        
        selected_executives = session_data.get('selected_executives', [])
        current_question_count = session_data.get('current_question_count', 0)
        question_limit = session_data.get('question_limit', 10)
        all_key_details = session_data.get('key_details', [])
        used_topics = session_data.get('used_topics', [])
        
        # Add response to session data (store as dict with transcription)
        session_data['responses'].append({
            'text': transcription,
            'type': 'audio',
            'timestamp': datetime.now().isoformat()
        })
        
        # Check limit BEFORE generating next question
        next_question_count = current_question_count + 1
        
        if next_question_count > question_limit:
            # End session
            company_name = session_data.get('company_name', 'Your Company')
            report_type = session_data.get('report_type', 'presentation')
            closing_message = generate_closing_message(company_name, report_type)
            
            closing_question = {
                'executive': 'CEO',
                'name': get_executive_name('CEO'),
                'title': 'CEO',
                'question': closing_message,
                'is_closing': True,
                'timestamp': datetime.now().isoformat()
            }
            
            session_data['current_question_count'] = next_question_count
            store_session_data(session_data)
            
            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return jsonify({
                'status': 'success',
                'transcription': transcription,
                'follow_up': closing_question,
                'session_ending': True
            })
        
        # Generate next question
        next_executive = get_next_executive(selected_executives, next_question_count)
        company_name = session_data.get('company_name', '')
        industry = session_data.get('industry', '')
        report_type = session_data.get('report_type', '')
        report_content = session_data.get('report_content', '')
        
        next_question, selected_topic = generate_ai_questions_with_topic_diversity(
            report_content, next_executive, company_name, industry, report_type, 
            all_key_details, used_topics, next_question_count
        )
        
        follow_up = {
            'executive': next_executive,
            'name': get_executive_name(next_executive),
            'title': next_executive,
            'question': next_question,
            'timestamp': datetime.now().isoformat()
        }
        
        # Update session data
        session_data['current_question_count'] = next_question_count
        session_data['questions'].append(follow_up)
        session_data['used_topics'].append(selected_topic)
        store_session_data(session_data)
        
        # Clean up temp file
        if os.path.exists(filepath):
            os.remove(filepath)
        
        print(f"🎯 {next_executive} asking question #{next_question_count}")
        print(f"📊 Memory session size: {len(str(session_data))} bytes")
        
        return jsonify({
            'status': 'success',
            'transcription': transcription,
            'follow_up': follow_up
        })
        
    except Exception as e:
        print(f"❌ Audio response error: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up any temp files
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({'status': 'error', 'error': f'Error processing audio: {str(e)}'})
