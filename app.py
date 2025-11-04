import os
import tempfile
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, Response
from werkzeug.utils import secure_filename
import PyPDF2
import openai
import pytz
CST = pytz.timezone('America/Chicago')

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-railway-deployment')
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB for audio files

# Audio upload configuration
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_AUDIO_EXTENSIONS = {'webm', 'mp3', 'wav', 'm4a', 'ogg'}

# Initialize OpenAI client
openai_client = None
openai_available = False

try:
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        # Simple initialization for openai >= 1.0.0
        openai_client = openai.OpenAI(api_key=api_key)
        openai_available = True
        print("✅ OpenAI API key found - AI-powered questions enabled")
    else:
        print("⚠️  No OpenAI API key found - running in demo mode")
except Exception as e:
    print(f"❌ OpenAI initialization failed: {e}")
    import traceback
    traceback.print_exc()  # This will help debug
    openai_available = False

# In-memory session storage (avoids cookie size issues)
session_storage = {}

def get_session_id():
    """Get or create a session ID for the current user"""
    if 'sid' not in session:
        import uuid
        session['sid'] = str(uuid.uuid4())
    return session['sid']

def get_session_data():
    """Retrieve session data from memory"""
    sid = get_session_id()
    return session_storage.get(sid, {})

def store_session_data(data):
    """Store session data in memory"""
    sid = get_session_id()
    session_storage[sid] = data
    
def clear_session_data():
    """Clear session data from memory"""
    sid = get_session_id()
    if sid in session_storage:
        del session_storage[sid]

# PDF Processing Functions
def extract_text_from_pdf(pdf_file):
    """Extract text content from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text_content = ""
        
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                text_content += page.extract_text()
            except Exception as e:
                print(f"Error reading page {page_num + 1}: {e}")
        
        return text_content.strip()
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return None

def analyze_document_with_ai(document_text, company_name, industry, report_type):
    """Use OpenAI to extract key details from document"""
    if not openai_available or not openai_client:
        return generate_template_key_details(company_name, industry, report_type)
    
    try:
        prompt = f"""Analyze this {report_type} document for {company_name} in the {industry} industry.
        
Extract 10-12 diverse key details that cover different business areas:
- Financial aspects (revenue, costs, profitability)
- Market and competition
- Core resources, capabilities and competencies
- Operations and processes
- Technology and innovation
- Strategic initiatives
- Risks and challenges

Format each as a brief statement (1-2 sentences max).
Return as a JSON array of strings.

Document:
{document_text[:4000]}"""

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert business analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        import json
        key_details = json.loads(response.choices[0].message.content)
        print(f"📊 Extracted {len(key_details)} key details from document")
        return key_details[:12]
        
    except Exception as e:
        print(f"AI analysis error: {e}")
        return generate_template_key_details(company_name, industry, report_type)

def generate_template_key_details(company_name, industry, report_type):
    """Generate template key details when AI is unavailable"""
    return [
        f"{company_name}'s revenue model and pricing strategy",
        f"Target market segments in {industry}",
        f"Competitive positioning and differentiation",
        f"Operational efficiency and cost structure",
        f"Technology infrastructure and digital capabilities",
        f"Growth strategy and expansion plans",
        f"Key partnerships and strategic alliances",
        f"Market share and customer acquisition",
        f"Risk factors and mitigation strategies",
        f"Innovation initiatives and R&D investments",
        f"Sustainability and ESG considerations",
        f"Financial projections and performance metrics"
    ]

# Executive Management
EXECUTIVE_NAMES = {
    'CEO': 'Sarah Chen',
    'CFO': 'Michael Rodriguez',
    'CTO': 'Rebecca Johnson',
    'CMO': 'David Kim',
    'COO': 'Jennifer Martinez'
}

def get_executive_name(role):
    """Get the name for an executive role"""
    return EXECUTIVE_NAMES.get(role, role)

def get_next_executive(selected_executives, current_count):
    """Rotate through executives evenly"""
    if not selected_executives:
        return 'CEO'
    index = (current_count - 1) % len(selected_executives)
    return selected_executives[index]

# Question Generation
def generate_ai_questions_with_topic_diversity(report_content, executive, company_name, 
                                               industry, report_type, all_key_details, 
                                               used_topics, question_number):
    """Generate AI questions ensuring topic diversity"""
    if not openai_available or not openai_client:
        return generate_template_question(executive, question_number), f"topic_{question_number}"
    
    # Get unused topics
    unused_topics = [topic for i, topic in enumerate(all_key_details) if i not in used_topics]
    
    if not unused_topics:
        # All topics used, recycle
        unused_topics = all_key_details
        used_topics.clear()
    
    selected_topic = random.choice(unused_topics)
    topic_index = all_key_details.index(selected_topic)
    
    try:
        role_focus = {
            'CEO': 'strategic vision, overall business direction, and long-term growth',
            'CFO': 'financial viability, revenue models, costs, and profitability',
            'CTO': 'technical feasibility, technology infrastructure, and innovation',
            'CMO': 'market positioning, customer acquisition, and competitive differentiation',
            'COO': 'operational efficiency, process optimization, and execution'
        }
        
        focus = role_focus.get(executive, 'business strategy')
        
        prompt = f"""You are the {executive} of a company evaluating this {report_type} from {company_name} in the {industry} industry.

Focus on this specific aspect: {selected_topic}

Your role focuses on: {focus}

Generate ONE challenging, specific question about this aspect. The question should:
- Be direct and conversational (as if speaking to the presenter)
- Reference specific details when possible
- Challenge assumptions or ask for justification
- Be answerable based on a strategic business plan
- Be 1-2 sentences max

Return ONLY the question text, no preamble."""

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"You are the {executive} asking tough business questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=150
        )
        
        question = response.choices[0].message.content.strip()
        print(f"🎯 {executive} Q#{question_number} on topic: {selected_topic[:50]}...")
        return question, topic_index
        
    except Exception as e:
        print(f"Question generation error: {e}")
        return generate_template_question(executive, question_number), topic_index

def generate_template_question(executive, question_number):
    """Generate template question when AI unavailable"""
    templates = {
        'CEO': [
            "How does this strategy align with our long-term vision?",
            "What are the key risks to this approach?",
            "How will this create sustainable competitive advantage?"
        ],
        'CFO': [
            "What are the financial implications of this plan?",
            "How will this impact our profit margins?",
            "What's the expected ROI timeline?"
        ],
        'CTO': [
            "What technology infrastructure is required?",
            "How scalable is this technical solution?",
            "What are the technical risks?"
        ],
        'CMO': [
            "How will this resonate with our target market?",
            "What's our differentiation strategy?",
            "How will we measure marketing effectiveness?"
        ],
        'COO': [
            "How will we execute this operationally?",
            "What resources are needed?",
            "What are the operational challenges?"
        ]
    }
    
    questions = templates.get(executive, templates['CEO'])
    return questions[(question_number - 1) % len(questions)]

def generate_closing_message(company_name, report_type):
    """Generate closing message"""
    messages = [
        f"Thank you for presenting your {report_type} for {company_name}. Your responses demonstrate strategic thinking.",
        f"Excellent presentation of {company_name}'s strategy. You've addressed our key concerns well.",
        f"Thank you for the comprehensive overview. Your {report_type} shows promise for {company_name}."
    ]
    return random.choice(messages)

# Audio Processing Functions
def allowed_audio_file(filename):
    """Check if uploaded file is an allowed audio format"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

def transcribe_audio_whisper(audio_file_path):
    """Transcribe audio using OpenAI Whisper API"""
    if not openai_available or not openai_client:
        return "[Audio transcription unavailable - AI not enabled]"
    
    try:
        print(f"🎤 Starting transcription of {audio_file_path}...")
        
        with open(audio_file_path, 'rb') as audio_file:
            transcription = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
        
        print(f"✅ Transcription successful: {transcription.text[:100]}...")
        return transcription.text
        
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return f"[Transcription failed: {str(e)}]"

# Routes
@app.route('/')
def index():
    """Render main page"""
    clear_session_data()
    return render_template('index.html', ai_available=openai_available)

@app.route('/upload_report', methods=['POST'])
def upload_report():
    """Handle PDF upload and analysis"""
    try:
        if 'report' not in request.files:
            return jsonify({'status': 'error', 'error': 'No file uploaded'})
        
        file = request.files['report']
        if file.filename == '':
            return jsonify({'status': 'error', 'error': 'No file selected'})
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'status': 'error', 'error': 'Please upload a PDF file'})
        
        company_name = request.form.get('company_name', 'Your Company')
        industry = request.form.get('industry', 'Technology')
        report_type = request.form.get('report_type', 'Business Plan')
        selected_executives = request.form.getlist('executives[]')
        
        if not selected_executives:
            return jsonify({'status': 'error', 'error': 'Please select at least one executive'})
        
        # Extract text from PDF
        print(f"📄 Processing PDF for {company_name}...")
        report_content = extract_text_from_pdf(file)
        
        if not report_content:
            return jsonify({'status': 'error', 'error': 'Could not extract text from PDF'})
        
        print(f"✅ Extracted {len(report_content)} characters from PDF")
        
        # Analyze document
        key_details = analyze_document_with_ai(report_content, company_name, industry, report_type)
        
        # Generate first question
        first_executive = selected_executives[0]
        first_question, first_topic = generate_ai_questions_with_topic_diversity(
            report_content, first_executive, company_name, industry, report_type,
            key_details, [], 1
        )
        
        first_q = {
            'executive': first_executive,
            'name': get_executive_name(first_executive),
            'title': first_executive,
            'question': first_question,
            'timestamp': datetime.now(CST).isoformat()
        }
        
        # Store in memory
        session_data = {
            'company_name': company_name,
            'industry': industry,
            'report_type': report_type,
            'selected_executives': selected_executives,
            'report_content': report_content[:10000],  # Store first 10k chars
            'key_details': key_details,
            'questions': [first_q],
            'responses': [],
            'used_topics': [first_topic],
            'current_question_count': 1,
            'question_limit': int(request.form.get('question_limit', 10))
        }
        
        store_session_data(session_data)
        
        print(f"🎯 {first_executive} asking first question")
        print(f"📊 Memory session size: {len(str(session_data))} bytes")
        
        return jsonify({
            'status': 'success',
            'first_question': first_q,
            'ai_mode': 'enabled' if openai_available else 'demo'
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': f'Error processing file: {str(e)}'})

@app.route('/respond_to_executive', methods=['POST'])
def respond_to_executive():
    """Handle student text response"""
    try:
        data = request.get_json()
        response_text = data.get('response', '').strip()
        
        if not response_text:
            return jsonify({'status': 'error', 'error': 'Please provide a response'})
        
        session_data = get_session_data()
        if not session_data:
            return jsonify({'status': 'error', 'error': 'Session data lost. Please restart.'})
        
        # Add response
        session_data['responses'].append({
            'text': response_text,
            'timestamp': datetime.now(CST).isoformat(),
            'type': 'text',
        })
        
        selected_executives = session_data.get('selected_executives', [])
        current_count = session_data.get('current_question_count', 0)
        question_limit = session_data.get('question_limit', 10)
        
        next_count = current_count + 1
        
        # Check if session should end
        if next_count > question_limit:
            company_name = session_data.get('company_name', 'Your Company')
            report_type = session_data.get('report_type', 'presentation')
            closing_message = generate_closing_message(company_name, report_type)
            
            session_data['current_question_count'] = next_count
            store_session_data(session_data)
            
            return jsonify({
                'status': 'success',
                'follow_up': {
                    'executive': 'CEO',
                    'name': get_executive_name('CEO'),
                    'title': 'CEO',
                    'question': closing_message,
                    'timestamp': datetime.now(CST).isoformat(),  # ✅ ADD THIS LINE
                    'is_closing': True
                },
                'session_ending': True
            })
        
        # Generate next question
        next_exec = get_next_executive(selected_executives, next_count)
        key_details = session_data.get('key_details', [])
        used_topics = session_data.get('used_topics', [])
        
        next_question, next_topic = generate_ai_questions_with_topic_diversity(
            session_data.get('report_content', ''),
            next_exec,
            session_data.get('company_name', ''),
            session_data.get('industry', ''),
            session_data.get('report_type', ''),
            key_details,
            used_topics,
            next_count
        )
        
        follow_up = {
            'executive': next_exec,
            'name': get_executive_name(next_exec),
            'title': next_exec,
            'question': next_question,
            'timestamp': datetime.now(CST).isoformat()
        }
        
        session_data['current_question_count'] = next_count
        session_data['questions'].append(follow_up)
        session_data['used_topics'].append(next_topic)
        store_session_data(session_data)
        
        print(f"🎯 {next_exec} asking question #{next_count}")
        
        return jsonify({
            'status': 'success',
            'follow_up': follow_up
        })
        
    except Exception as e:
        print(f"Response error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': f'Error processing response: {str(e)}'})

@app.route('/respond_to_executive_audio', methods=['POST'])
def respond_to_executive_audio():
    """Handle audio response with transcription"""
    try:
        if 'audio' not in request.files:
            return jsonify({'status': 'error', 'error': 'No audio file provided'})
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({'status': 'error', 'error': 'No file selected'})
        
        if not allowed_audio_file(audio_file.filename):
            return jsonify({'status': 'error', 'error': 'Invalid audio file format'})
        
        # Save audio temporarily
        filename = secure_filename(f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        audio_file.save(filepath)
        
        print(f"📁 Audio file saved: {filepath} ({os.path.getsize(filepath)} bytes)")
        
        # Transcribe audio
        transcription = transcribe_audio_whisper(filepath)
        
        if not transcription or transcription.startswith('['):
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'status': 'error', 'error': 'Failed to transcribe audio'})
        
        # Get session data
        session_data = get_session_data()
        if not session_data:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'status': 'error', 'error': 'Session data lost. Please restart.'})
        
        # Add response
        session_data['responses'].append({
            'text': transcription,
            'type': 'audio',
            'timestamp': datetime.now(CST).isoformat(),
        })
        
        selected_executives = session_data.get('selected_executives', [])
        current_count = session_data.get('current_question_count', 0)
        question_limit = session_data.get('question_limit', 10)
        
        next_count = current_count + 1
        
        # Check if session should end
        if next_count > question_limit:
            company_name = session_data.get('company_name', 'Your Company')
            report_type = session_data.get('report_type', 'presentation')
            closing_message = generate_closing_message(company_name, report_type)
            
            session_data['current_question_count'] = next_count
            store_session_data(session_data)
            
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return jsonify({
                'status': 'success',
                'transcription': transcription,
                'follow_up': {
                    'executive': 'CEO',
                    'name': get_executive_name('CEO'),
                    'title': 'CEO',
                    'question': closing_message,
                    'timestamp': datetime.now(CST).isoformat(),  # ✅ ADD THIS LINE
                    'is_closing': True
                },
                'session_ending': True
            })
        
        # Generate next question
        next_exec = get_next_executive(selected_executives, next_count)
        key_details = session_data.get('key_details', [])
        used_topics = session_data.get('used_topics', [])
        
        next_question, next_topic = generate_ai_questions_with_topic_diversity(
            session_data.get('report_content', ''),
            next_exec,
            session_data.get('company_name', ''),
            session_data.get('industry', ''),
            session_data.get('report_type', ''),
            key_details,
            used_topics,
            next_count
        )
        
        follow_up = {
            'executive': next_exec,
            'name': get_executive_name(next_exec),
            'title': next_exec,
            'question': next_question,
            'timestamp': datetime.now(CST).isoformat()
        }
        
        session_data['current_question_count'] = next_count
        session_data['questions'].append(follow_up)
        session_data['used_topics'].append(next_topic)
        store_session_data(session_data)
        
        # Clean up temp file
        if os.path.exists(filepath):
            os.remove(filepath)
        
        print(f"🎯 {next_exec} asking question #{next_count}")
        
        return jsonify({
            'status': 'success',
            'transcription': transcription,
            'follow_up': follow_up
        })
        
    except Exception as e:
        print(f"Audio response error: {e}")
        import traceback
        traceback.print_exc()
        
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({'status': 'error', 'error': f'Error processing audio: {str(e)}'})

@app.route('/end_session', methods=['POST'])
def end_session():
    """End session and return summary data"""
    try:
        session_data = get_session_data()
        if not session_data:
            return jsonify({'status': 'error', 'error': 'No session data'})
        
        company_name = session_data.get('company_name', 'Your Company')
        report_type = session_data.get('report_type', 'Business Plan')
        questions = session_data.get('questions', [])
        responses = session_data.get('responses', [])
        question_limit = session_data.get('question_limit', 10)
        selected_executives = session_data.get('selected_executives', [])
        
        # Count audio vs text responses
        audio_count = sum(1 for r in responses if isinstance(r, dict) and r.get('type') == 'audio')
        text_count = len(responses) - audio_count
        
        # Get unique executives who asked questions
        executives_involved = []
        for q in questions:
            exec_name = q.get('name', 'Unknown')
            if exec_name not in executives_involved:
                executives_involved.append(exec_name)
        
        summary = {
            'company_name': company_name,
            'presentation_topic': report_type,
            'session_type': 'questions',
            'session_limit': question_limit,
            'total_questions': len(questions),
            'total_responses': len(responses),
            'audio_responses': audio_count,
            'text_responses': text_count,
            'executives_involved': executives_involved  # ✅ Added this field
        }
        
        return jsonify({
            'status': 'success',
            'summary': summary
        })
        
    except Exception as e:
        print(f"End session error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/download_transcript', methods=['GET'])
def download_transcript():
    """Generate and download session transcript as PDF with timestamps"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from io import BytesIO
        from datetime import datetime
        
        session_data = get_session_data()
        if not session_data:
            return "No session data available", 404
        
        company_name = session_data.get('company_name', 'Your Company')
        report_type = session_data.get('report_type', 'Business Plan')
        industry = session_data.get('industry', 'Technology')
        questions = session_data.get('questions', [])  # ← NEW
        responses = session_data.get('responses', [])  # ← NEW
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Container for PDF elements
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#BF5700'),  # UT Orange
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333F48'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        exec_style = ParagraphStyle(
            'Executive',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#BF5700'),
            fontName='Helvetica-Bold',
            spaceAfter=6
        )
        
        timestamp_style = ParagraphStyle(
            'Timestamp',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            spaceAfter=4
        )
        
        question_style = ParagraphStyle(
            'Question',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=20,
            spaceAfter=8
        )
        
        response_style = ParagraphStyle(
            'Response',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=40,
            spaceAfter=12,
            textColor=colors.HexColor('#333333')
        )
        
        # Title
        story.append(Paragraph("Executive Panel Session Transcript", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Session Details Table
        session_data_table = [
            ['Company:', company_name],
            ['Industry:', industry],
            ['Report Type:', report_type],
            ['Session Date:', datetime.now().strftime('%B %d, %Y')],
            ['Questions:', str(len(questions))]
        ]
        
        t = Table(session_data_table, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333F48')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3*inch))
        
        # Conversation Transcript
        story.append(Paragraph("Conversation Transcript", header_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Process conversation history
        # Process Q&A pairs
        for i, (question, response) in enumerate(zip(questions, responses), 1):
            # Executive question
            exec_name = question.get('name', 'Executive')
            exec_title = question.get('title', '')
            question_text = question.get('question', '')
            timestamp = question.get('timestamp', '')
            
            # Format timestamp
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%I:%M:%S %p')
                except:
                    formatted_time = timestamp
            else:
                formatted_time = ''
            
            # Add executive name and title
            story.append(Paragraph(
                f"<b>{exec_name}</b> ({exec_title})",
                exec_style
            ))
            
            # Add timestamp
            if formatted_time:
                story.append(Paragraph(
                    f"<i>{formatted_time}</i>",
                    timestamp_style
                ))
            
            # Add question
            story.append(Paragraph(
                f"Q: {question_text}",
                question_style
            ))
        
        # User response
        # User response - handle both string and dict formats
        response_text = ''
        response_mode = 'text'
        response_timestamp = ''

        if isinstance(response, dict):
            response_text = response.get('text', '')
            response_mode = response.get('type', 'text') 
            response_timestamp = response.get('timestamp', '')
        elif isinstance(response, str):
            response_text = response
        
        # Format response timestamp
        if response_timestamp:
            try:
                dt = datetime.fromisoformat(response_timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%I:%M:%S %p')
            except:
                formatted_time = response_timestamp
            
            story.append(Paragraph(
                f"<i>{formatted_time}</i>",
                timestamp_style
            ))
        
        # Indicate if audio response
        if response_mode == 'audio':
            story.append(Paragraph(
                f"A: [Audio Response] {response_text}",
                response_style
            ))
        else:
            story.append(Paragraph(
                f"A: {response_text}",
                response_style
            ))
        
        story.append(Spacer(1, 0.1*inch))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Generate filename
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{company_name.replace(' ', '_')}_Executive_Panel_Transcript_{timestamp_str}"
        
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}.pdf"'
            }
        )
        
    except Exception as e:
        print(f"Transcript generation error: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generating transcript: {str(e)}", 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'ai_available': openai_available,
        'active_sessions': len(session_storage)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
