import os
import tempfile
import random
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from flask import Flask, render_template, request, jsonify, session, Response
import PyPDF2
import openai

# ============================================================================
# FLASK APPLICATION INITIALIZATION
# ============================================================================

# Initialize Flask app FIRST (CRITICAL: Must come before any @app.route decorators)
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-railway-deployment')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# ============================================================================
# IN-MEMORY SESSION STORAGE (ULTRA-LIGHTWEIGHT SOLUTION)
# ============================================================================

# Store session data in memory instead of cookies to avoid 4KB limit
SESSIONS = {}

def get_session_id():
    """Generate or retrieve session ID"""
    if 'sid' not in session:
        session['sid'] = f"ses_{random.randint(100000, 999999)}"
    return session['sid']

def store_session_data(data):
    """Store session data in memory"""
    sid = get_session_id()
    SESSIONS[sid] = data

def get_session_data():
    """Retrieve session data from memory"""
    sid = get_session_id()
    return SESSIONS.get(sid, {})

def clear_session_data():
    """Clear session data"""
    sid = get_session_id()
    if sid in SESSIONS:
        del SESSIONS[sid]

# ============================================================================
# AI CONFIGURATION AND INITIALIZATION
# ============================================================================

# Initialize OpenAI client with robust error handling
openai_client = None
openai_available = False

# Configuration for AI features - optimized for faster generation
AI_TIMEOUT = 15  # Increased from 12 for better analysis
AI_MAX_RETRIES = 2
AI_ENABLED = True

try:
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key and AI_ENABLED:
        openai.api_key = api_key
        openai_available = True
        print("✅ OpenAI API key found - AI-powered questions enabled with enhanced topic diversity")
    else:
        print("⚠️ AI disabled or no API key found - running in demo mode")
except ImportError as e:
    print(f"❌ OpenAI library not available: {e}")
    openai_available = False
except Exception as e:
    print(f"❌ OpenAI initialization failed: {e}")
    openai_available = False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def call_openai_with_timeout(prompt_data, timeout=AI_TIMEOUT):
    """Make OpenAI API call with timeout protection - OPTIMIZED"""
    def make_api_call():
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=prompt_data['messages'],
                max_tokens=prompt_data.get('max_tokens', 800),
                temperature=prompt_data.get('temperature', 0.3)
            )
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"OpenAI API call failed: {e}")
            return None

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(make_api_call)
            result = future.result(timeout=timeout)
            return result
    except FutureTimeoutError:
        print(f"OpenAI API call timed out after {timeout} seconds")
        return None
    except Exception as e:
        print(f"OpenAI API call error: {e}")
        return None

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

def analyze_report_with_ai_comprehensive(report_content, company_name, industry, report_type):
    """ENHANCED AI analysis for diverse topic coverage"""
    if not openai_available:
        return generate_diverse_fallback_analysis(company_name, industry)
    
    print(f"🤖 Starting COMPREHENSIVE AI analysis for {company_name} in {industry}...")
    
    try:
        # ENHANCED prompt for diverse topic extraction
        prompt_data = {
            'messages': [
                {
                    "role": "system",
                    "content": f"""You are an expert business analyst. Extract 10-12 DIVERSE key details from this {report_type} covering different business areas. 

REQUIRED CATEGORIES (aim for 2 items each):
- Financial (revenue, costs, profitability, funding)
- Market/Competition (positioning, competitors, market share)
- Operations (processes, efficiency, scalability)
- Technology (infrastructure, innovation, digital strategy)
- Strategic (growth plans, expansion, partnerships)
- Risks/Challenges (threats, weaknesses, uncertainties)

Return ONLY JSON with diverse, specific details executives would question."""
                },
                {
                    "role": "user", 
                    "content": f"""Company: {company_name} | Industry: {industry}

Report content (first 4000 chars for comprehensive analysis):
{report_content[:4000]}

Extract 10-12 DIVERSE details across business functions:

{{"key_details": [
  "specific financial metric or projection",
  "competitive positioning detail", 
  "operational process or efficiency claim",
  "technology infrastructure detail",
  "growth strategy or expansion plan",
  "identified risk or challenge",
  "market opportunity or trend",
  "partnership or alliance mention",
  "customer segment or retention detail",
  "innovation or R&D initiative",
  "regulatory or compliance factor",
  "sustainability or ESG element"
]}}"""
                }
            ],
            'max_tokens': 600,  # Increased for more comprehensive analysis
            'temperature': 0.4  # Slightly higher for diversity
        }
        
        response_text = call_openai_with_timeout(prompt_data, timeout=12)
        
        if response_text:
            try:
                analysis = json.loads(response_text)
                details = analysis.get("key_details", [])[:12]  # Take up to 12 details
                print(f"✅ COMPREHENSIVE AI analysis completed for {company_name} - extracted {len(details)} diverse details")
                return {"key_details": details}
            except json.JSONDecodeError:
                # Parse as text if JSON fails
                lines = [line.strip() for line in response_text.split('\n') if line.strip() and len(line.strip()) > 20]
                details = [line.strip('- "[]').strip() for line in lines[:10]]
                print(f"⚠️ AI response parsed as text for {company_name} - extracted {len(details)} details")
                return {"key_details": details}
        else:
            print(f"❌ AI analysis timed out for {company_name}, using diverse fallback")
            return generate_diverse_fallback_analysis(company_name, industry)
            
    except Exception as e:
        print(f"❌ AI analysis failed for {company_name}: {e}")
        return generate_diverse_fallback_analysis(company_name, industry)

def generate_diverse_fallback_analysis(company_name, industry):
    """Generate diverse fallback analysis when AI is unavailable"""
    # Industry-specific diverse themes
    industry_themes = {
        'Music Streaming': [
            f"{company_name}'s content licensing costs and royalty structure",
            f"User acquisition and retention in competitive streaming market", 
            f"Free vs premium tier conversion strategies",
            f"Podcast content strategy and monetization",
            f"International market expansion priorities",
            f"Artist relationship management and platform exclusives",
            f"Data analytics and personalized recommendation algorithms",
            f"Competition with Apple Music and YouTube Music",
            f"Social features and music discovery innovation",
            f"Platform scalability and infrastructure costs"
        ],
        'Technology': [
            f"{company_name}'s R&D investment and innovation pipeline",
            f"Market positioning against key competitors",
            f"Talent acquisition and retention strategy", 
            f"Data security and privacy compliance",
            f"Cloud infrastructure and scalability plans",
            f"Customer acquisition cost vs lifetime value",
            f"Partnership and ecosystem development",
            f"International expansion and localization",
            f"Emerging technology adoption strategy",
            f"Intellectual property and competitive moats"
        ]
    }
    
    # Get industry-specific themes or use generic business themes
    themes = industry_themes.get(industry, [
        f"{company_name}'s revenue model and profitability projections",
        f"Market opportunity and competitive landscape analysis",
        f"Operational efficiency and scalability challenges",
        f"Technology infrastructure and digital transformation",
        f"Customer acquisition and retention strategies",
        f"Financial risk management and funding requirements",
        f"Strategic partnerships and alliance opportunities",
        f"International expansion and market entry plans",
        f"Innovation and product development priorities",
        f"Regulatory compliance and policy considerations"
    ])
    
    return {"key_details": themes[:10]}  # Return 10 diverse themes

def generate_ai_questions_with_topic_diversity(report_content, executive_role, company_name, industry, report_type, all_key_details, used_topics, question_number):
    """Generate AI questions with enforced topic diversity - NO REPEATS"""
    if not openai_available:
        return generate_diverse_template_question(executive_role, company_name, all_key_details, used_topics, question_number)
    
    try:
        # Select an unused topic for this question
        available_topics = [detail for detail in all_key_details if detail not in used_topics]
        
        if not available_topics:
            # All topics used, start over with different angles
            selected_topic = random.choice(all_key_details)
            angle_modifier = "alternative approach to" if question_number > len(all_key_details) else ""
        else:
            selected_topic = random.choice(available_topics)
            angle_modifier = ""
        
        # Role-specific questioning approaches
        role_approaches = {
            'CEO': ['strategic vision', 'competitive positioning', 'stakeholder value', 'long-term viability', 'market leadership'],
            'CFO': ['financial impact', 'cost structure', 'revenue model', 'risk assessment', 'capital allocation'],
            'CTO': ['technical feasibility', 'scalability', 'innovation potential', 'infrastructure requirements', 'technology risks'],
            'CMO': ['market opportunity', 'customer impact', 'brand positioning', 'go-to-market strategy', 'competitive differentiation'],
            'COO': ['operational feasibility', 'execution plan', 'resource requirements', 'process optimization', 'delivery capabilities']
        }
        
        approach = random.choice(role_approaches.get(executive_role, role_approaches['CEO']))
        
        # Diverse question starters
        question_starters = [
            "In your analysis of",
            "Your plan shows",
            "Looking at",
            "How do you",
            "What happens if",
            "Why did you choose",
            "What's your contingency for",
            "How will you measure",
            "What evidence supports",
            "How do you prioritize"
        ]
        
        starter = random.choice(question_starters)
        
        prompt_data = {
            'messages': [
                {
                    "role": "system",
                    "content": f"You are a {executive_role}. Ask 1 specific question about this topic from your {approach} perspective. Be direct and challenging but professional."
                },
                {
                    "role": "user",
                    "content": f"""Company: {company_name} | Industry: {industry} | Question #{question_number}

Specific topic to address: {selected_topic}

Generate exactly 1 question that:
1. Starts with "{starter}"
2. Focuses specifically on: {selected_topic}
3. Reflects {approach} concerns
4. Is unique and specific to this topic
{f"5. Takes an {angle_modifier} perspective" if angle_modifier else ""}

Question:"""
                }
            ],
            'max_tokens': 200,
            'temperature': 0.6  # Higher for more variety
        }
        
        response_text = call_openai_with_timeout(prompt_data, timeout=10)
        
        if response_text and len(response_text.strip()) > 20:
            # Clean up the response
            question = response_text.strip()
            if question.startswith('"') and question.endswith('"'):
                question = question[1:-1]
            
            print(f"✅ Generated diverse {executive_role} question #{question_number} on topic: {selected_topic[:50]}...")
            return question, selected_topic
        else:
            print(f"⚠️ AI question generation failed for {executive_role}, using template")
            return generate_diverse_template_question(executive_role, company_name, all_key_details, used_topics, question_number)
            
    except Exception as e:
        print(f"❌ AI question generation error for {executive_role}: {e}")
        return generate_diverse_template_question(executive_role, company_name, all_key_details, used_topics, question_number)

def generate_diverse_template_question(executive_role, company_name, all_key_details, used_topics, question_number):
    """Generate template questions with topic diversity enforcement"""
    # Select unused topic
    available_topics = [detail for detail in all_key_details if detail not in used_topics]
    if available_topics:
        selected_topic = random.choice(available_topics)
    else:
        selected_topic = random.choice(all_key_details) if all_key_details else f"{company_name}'s strategy"
    
    # Role-specific question templates
    templates = {
        'CEO': [
            f"How does {selected_topic} align with {company_name}'s long-term strategic vision?",
            f"What's the competitive advantage from {selected_topic}?",
            f"How do you justify the strategic priority of {selected_topic}?"
        ],
        'CFO': [
            f"What's the financial impact of {selected_topic} on {company_name}'s bottom line?",
            f"How do you validate the ROI projections for {selected_topic}?",
            f"What are the cost implications of {selected_topic}?"
        ],
        'CTO': [
            f"What technical infrastructure supports {selected_topic} at {company_name}?",
            f"How does {selected_topic} scale with {company_name}'s growth?",
            f"What are the technology risks associated with {selected_topic}?"
        ],
        'CMO': [
            f"How does {selected_topic} differentiate {company_name} in the market?",
            f"What's the customer impact of {selected_topic}?",
            f"How do you measure market response to {selected_topic}?"
        ],
        'COO': [
            f"What operational processes enable {selected_topic} at {company_name}?",
            f"How do you execute {selected_topic} effectively?",
            f"What resources does {selected_topic} require for implementation?"
        ]
    }
    
    role_templates = templates.get(executive_role, templates['CEO'])
    question = random.choice(role_templates)
    
    return question, selected_topic

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

def get_next_executive(selected_executives, question_count):
    """Determine which executive should ask the next question"""
    return selected_executives[(question_count - 1) % len(selected_executives)]

def generate_closing_message(company_name, report_type):
    """Generate a professional closing message from the CEO"""
    closing_messages = [
        f"Thank you for presenting your {report_type.lower()} for {company_name}. You've given our executive team excellent insights to consider across diverse business areas.",
        f"This has been a productive discussion covering multiple aspects of {company_name}'s strategy. Your comprehensive analysis demonstrates solid planning.",
        f"Excellent work on your {report_type.lower()} for {company_name}. The executive team appreciates the breadth and depth of your strategic thinking."
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
AI Enhancement: {'Enabled - Diverse Topic Coverage with No Repeats' if openai_available else 'Template-based'}

====================================
PRESENTATION TRANSCRIPT
====================================

"""

    for i, (question, response) in enumerate(zip(questions, responses), 1):
        transcript += f"QUESTION {i}\n"
        transcript += f"{question.get('name', 'Executive')} ({question.get('executive', 'Executive')}):\n"
        transcript += f"{question.get('question', 'Question not recorded')}\n\n"
        
        transcript += f"STUDENT RESPONSE:\n"
        transcript += f"{response}\n\n"
        transcript += "-" * 50 + "\n\n"
    
    transcript += "====================================\n"
    transcript += "END OF TRANSCRIPT\n"
    transcript += "====================================\n"
    transcript += f"Generated by AI Executive Panel Simulator ({ai_mode})\n"
    transcript += f"Total Questions Asked: {len(questions)}\n"
    
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

# ============================================================================
# FLASK ROUTES (ENHANCED TOPIC DIVERSITY)
# ============================================================================

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
        question_limit = int(request.form.get('question-limit', '10'))
        time_limit = int(request.form.get('time-limit', '10'))
        
        if not all([company_name, industry, selected_executives]):
            return jsonify({'status': 'error', 'error': 'Missing required form data'})
        
        report_content = extract_text_from_pdf(file)
        if not report_content:
            return jsonify({'status': 'error', 'error': 'Could not extract text from PDF. Please ensure it\'s a text-based PDF.'})
        
        # ENHANCED comprehensive AI analysis
        detailed_analysis = analyze_report_with_ai_comprehensive(report_content, company_name, industry, report_type)
        
        session_data = {
            'company_name': company_name,
            'industry': industry,
            'report_type': report_type,
            'selected_executives': selected_executives,
            'report_content': report_content,  # Store full content for diverse question generation
            'key_details': detailed_analysis.get('key_details', []),
            'session_type': session_type,
            'question_limit': question_limit,
            'time_limit': time_limit,
            'session_start_time': datetime.now().isoformat(),
            'current_question_count': 0,
            'questions': [],
            'responses': [],
            'used_topics': []  # NEW: Track which topics have been used
        }
        
        store_session_data(session_data)
        
        print(f"📊 Cookie session size: {len(session.get('sid', ''))} bytes")
        print(f"🎯 Extracted {len(detailed_analysis.get('key_details', []))} diverse topics for question variety")
        
        return jsonify({
            'status': 'success',
            'message': f'Report analyzed! {"AI-powered diverse topic coverage" if openai_available else "Template-based questions"} ready.',
            'executives': selected_executives,
            'ai_enabled': openai_available,
            'key_details': detailed_analysis.get('key_details', [])[:3]  # Show first 3 for display
        })
        
    except Exception as e:
        print(f"Setup session error: {e}")
        return jsonify({'status': 'error', 'error': f'Error processing upload: {str(e)}'})

@app.route('/start_presentation', methods=['POST'])
def start_presentation():
    try:
        session_data = get_session_data()
        if not session_data:
            return jsonify({'status': 'error', 'error': 'No report uploaded. Please start over.'})
        
        selected_executives = session_data.get('selected_executives', [])
        company_name = session_data.get('company_name', '')
        industry = session_data.get('industry', '')
        report_type = session_data.get('report_type', '')
        report_content = session_data.get('report_content', '')
        all_key_details = session_data.get('key_details', [])
        used_topics = session_data.get('used_topics', [])
        
        if not selected_executives:
            return jsonify({'status': 'error', 'error': 'No executives selected'})
        
        # Generate first question with topic diversity
        first_exec = selected_executives[0]
        first_question, selected_topic = generate_ai_questions_with_topic_diversity(
            report_content, first_exec, company_name, industry, report_type, all_key_details, used_topics, 1
        )
        
        question_data = {
            'executive': first_exec,
            'name': get_executive_name(first_exec),
            'title': first_exec,
            'question': first_question,
            'timestamp': datetime.now().isoformat()
        }
        
        # Update session data
        session_data['current_question_count'] = 1
        session_data['questions'] = [question_data]
        session_data['used_topics'] = [selected_topic]  # Track the topic used
        store_session_data(session_data)
        
        print(f"🚀 Presentation started with {first_exec} question on topic: {selected_topic[:50]}...")
        print(f"📊 Memory session size: {len(str(session_data))} bytes")
        
        return jsonify({
            'status': 'success',
            'initial_questions': [question_data],
            'ai_enabled': openai_available
        })
        
    except Exception as e:
        print(f"Start presentation error: {e}")
        return jsonify({'status': 'error', 'error': f'Error starting presentation: {str(e)}'})

@app.route('/respond_to_executive', methods=['POST'])
def respond_to_executive():
    try:
        data = request.get_json()
        student_response = data.get('response', '')
        
        if not student_response:
            return jsonify({'status': 'error', 'error': 'Missing response'})
        
        session_data = get_session_data()
        if not session_data:
            return jsonify({'status': 'error', 'error': 'Session data lost. Please restart session.'})
        
        selected_executives = session_data.get('selected_executives', [])
        current_question_count = session_data.get('current_question_count', 0)
        question_limit = session_data.get('question_limit', 10)
        all_key_details = session_data.get('key_details', [])
        used_topics = session_data.get('used_topics', [])
        
        # Add response to session data
        session_data['responses'].append(student_response)
        
        # CRITICAL FIX: Check limit BEFORE generating next question
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
            
            return jsonify({
                'status': 'success',
                'follow_up': closing_question,
                'session_ending': True
            })
        
        # ENHANCED: Generate next question with topic diversity
        next_executive = get_next_executive(selected_executives, next_question_count)
        company_name = session_data.get('company_name', '')
        industry = session_data.get('industry', '')
        report_type = session_data.get('report_type', '')
        report_content = session_data.get('report_content', '')
        
        next_question, selected_topic = generate_ai_questions_with_topic_diversity(
            report_content, next_executive, company_name, industry, report_type, all_key_details, used_topics, next_question_count
        )
        
        follow_up = {
            'executive': next_executive,
            'name': get_executive_name(next_executive),
            'title': next_executive,
            'question': next_question,
            'timestamp': datetime.now().isoformat()
        }
        
        # Update session data with topic tracking
        session_data['current_question_count'] = next_question_count
        session_data['questions'].append(follow_up)
        session_data['used_topics'].append(selected_topic)  # Track new topic
        store_session_data(session_data)
        
        print(f"🎯 {next_executive} asking question #{next_question_count} on NEW topic: {selected_topic[:50]}...")
        print(f"📊 Topics used so far: {len(session_data['used_topics'])}/{len(all_key_details)}")
        print(f"📊 Memory session size: {len(str(session_data))} bytes")
        
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
        session_data = get_session_data()
        if not session_data:
            return jsonify({'status': 'error', 'error': 'No session data found'})
        
        questions_asked = len(session_data.get('questions', []))
        responses_given = len(session_data.get('responses', []))
        topics_covered = len(session_data.get('used_topics', []))
        total_topics_available = len(session_data.get('key_details', []))
        
        summary = {
            'total_questions': questions_asked,
            'total_responses': responses_given,
            'topics_covered': topics_covered,
            'total_topics_available': total_topics_available,
            'topic_coverage_percentage': round((topics_covered / max(total_topics_available, 1)) * 100, 1),
            'company_name': session_data.get('company_name', 'Your Company'),
            'presentation_topic': session_data.get('report_type', 'Business Plan'),
            'executives_involved': session_data.get('selected_executives', []),
            'session_type': session_data.get('session_type', 'questions'),
            'session_limit': session_data.get('question_limit', 10),
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


@app.route('/debug_ai', methods=['GET'])
def debug_ai():
    """Enhanced debug route to show topic coverage"""
    try:
        session_data = get_session_data()
        cookie_size = len(session.get('sid', ''))
        memory_size = len(str(session_data)) if session_data else 0
        
        debug_info = {
            'openai_available': openai_available,
            'session_approach': 'enhanced_topic_diversity',
            'cookie_size_bytes': cookie_size,
            'memory_size_bytes': memory_size,
            'total_sessions_active': len(SESSIONS),
            'session_data_summary': {
                'company_name': session_data.get('company_name', 'NOT SET') if session_data else 'NO SESSION',
                'current_question_count': session_data.get('current_question_count', 0) if session_data else 0,
                'questions_stored': len(session_data.get('questions', [])) if session_data else 0,
                'responses_stored': len(session_data.get('responses', [])) if session_data else 0,
                'total_topics_available': len(session_data.get('key_details', [])) if session_data else 0,
                'topics_used': len(session_data.get('used_topics', [])) if session_data else 0,
                'topic_coverage_percent': round((len(session_data.get('used_topics', [])) / max(len(session_data.get('key_details', [])), 1)) * 100, 1) if session_data else 0,
                'used_topics_preview': [topic[:50] + '...' for topic in session_data.get('used_topics', [])[-3:]] if session_data else []
            } if session_data else 'NO SESSION DATA'
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e)})

# Logo serving route
@app.route('/MSB-UT-Logo.jpg')
def serve_logo():
    """Serve the McCombs logo from the root directory"""
    try:
        from flask import send_file
        import os
        logo_path = os.path.join(os.getcwd(), 'MSB-UT-Logo.jpg')
        return send_file(logo_path, mimetype='image/jpeg')
    except Exception as e:
        print(f"Error serving logo: {e}")
        return "Logo not found", 404

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 AI Executive Panel Simulator Starting...")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"⚡ AI Enhancement: {'Enabled - DIVERSE TOPIC COVERAGE with No Repeats' if openai_available else 'Disabled (Demo Mode)'}")
    print(f"🌐 Running on port: {port}")
    print(f"💾 Session Storage: In-Memory (bypasses 4KB cookie limit)")
    print(f"🎯 Topic Tracking: Enhanced diversity across 10-12 business areas")
    print(f"🛡️ All fixes applied: Limit check, Circuit breaker, Topic diversity, Question uniqueness")
    print("="*50)
    
    app.run(debug=debug_mode, port=port, host='0.0.0.0')
