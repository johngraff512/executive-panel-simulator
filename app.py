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
AI_TIMEOUT = 12
AI_MAX_RETRIES = 2
AI_ENABLED = True

try:
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key and AI_ENABLED:
        openai.api_key = api_key
        openai_available = True
        print("✅ OpenAI API key found - AI-powered questions enabled with optimized timeouts")
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
                max_tokens=prompt_data.get('max_tokens', 600),
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

def analyze_report_with_ai_robust(report_content, company_name, industry, report_type):
    """Enhanced AI analysis - OPTIMIZED for faster generation"""
    if not openai_available:
        return {"key_details": [f"{company_name}'s strategy"]}
    
    print(f"🤖 Starting FAST AI analysis for {company_name} in {industry}...")
    
    try:
        prompt_data = {
            'messages': [
                {
                    "role": "system",
                    "content": f"Extract 3-4 key details from this {report_type} that executives would question. Return concise JSON only."
                },
                {
                    "role": "user", 
                    "content": f"""Company: {company_name} | Industry: {industry}

Report content (first 2000 chars):
{report_content[:2000]}

Return JSON:
{{"key_details": ["detail 1", "detail 2", "detail 3"]}}"""
                }
            ],
            'max_tokens': 200,
            'temperature': 0.2
        }
        
        response_text = call_openai_with_timeout(prompt_data, timeout=8)
        
        if response_text:
            try:
                analysis = json.loads(response_text)
                details = analysis.get("key_details", [])[:3]
                print(f"✅ FAST AI analysis completed for {company_name} - extracted {len(details)} details")
                return {"key_details": details}
            except json.JSONDecodeError:
                lines = [line.strip() for line in response_text.split('\n') if line.strip() and len(line.strip()) > 15]
                details = [line.strip('- "[]') for line in lines[:3]]
                print(f"⚠️ AI response parsed as text for {company_name} - extracted {len(details)} details")
                return {"key_details": details}
        else:
            print(f"❌ AI analysis timed out for {company_name}, using fallback")
            return {"key_details": [f"{company_name}'s strategic approach"]}
            
    except Exception as e:
        print(f"❌ AI analysis failed for {company_name}: {e}")
        return {"key_details": [f"{company_name}'s strategy"]}

def generate_ai_questions_on_demand(report_content, executive_role, company_name, industry, report_type, key_details, question_number):
    """Generate AI questions on-demand without storing - MEMORY EFFICIENT"""
    if not openai_available:
        return generate_template_question(executive_role, company_name, question_number)
    
    try:
        role_focuses = {
            'CEO': 'strategic vision',
            'CFO': 'financial analysis', 
            'CTO': 'technical architecture',
            'CMO': 'market strategy',
            'COO': 'operations'
        }
        
        focus = role_focuses.get(executive_role, 'strategic approach')
        detail = key_details[0] if key_details else f"{company_name}'s approach"
        
        prompt_data = {
            'messages': [
                {
                    "role": "system",
                    "content": f"You are a {executive_role}. Ask 1 specific question about {detail} from your {focus} perspective."
                },
                {
                    "role": "user",
                    "content": f"""Company: {company_name} | Industry: {industry} | Question #{question_number}

Key detail: {detail}

Generate 1 specific question about this detail that a {executive_role} would ask. Start with varied openings like "In your analysis...", "Your plan shows...", "How do you...", etc.

Question:"""
                }
            ],
            'max_tokens': 150,
            'temperature': 0.4
        }
        
        response_text = call_openai_with_timeout(prompt_data, timeout=8)
        
        if response_text and len(response_text.strip()) > 20:
            return response_text.strip()
        else:
            return generate_template_question(executive_role, company_name, question_number)
            
    except Exception as e:
        print(f"❌ AI question generation failed for {executive_role}: {e}")
        return generate_template_question(executive_role, company_name, question_number)

def generate_template_question(executive_role, company_name, question_number):
    """Generate template questions as fallback"""
    templates = {
        'CEO': [
            f"What's {company_name}'s sustainable competitive advantage?",
            f"How does this strategy create long-term shareholder value?",
            f"What's your contingency plan if market conditions change?"
        ],
        'CFO': [
            f"Walk me through {company_name}'s path to profitability.",
            f"What's the cash flow timeline for this initiative?",
            f"How sensitive are these projections to market volatility?"
        ],
        'CTO': [
            f"How does {company_name}'s technical architecture support scale?",
            f"What's your technology risk mitigation strategy?",
            f"How do you stay ahead of technical debt as you grow?"
        ],
        'CMO': [
            f"What's {company_name}'s customer acquisition strategy?",
            f"How do you measure brand equity and market position?",
            f"What's your retention strategy as the market matures?"
        ],
        'COO': [
            f"How does {company_name} maintain quality while scaling?",
            f"What operational metrics indicate performance issues?",
            f"What's your supply chain risk management approach?"
        ]
    }
    
    role_questions = templates.get(executive_role, templates['CEO'])
    return role_questions[(question_number - 1) % len(role_questions)]

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
        f"Thank you for presenting your {report_type.lower()} for {company_name}. You've given our executive team excellent insights to consider.",
        f"This has been a productive discussion about {company_name}. Your strategic thinking demonstrates solid planning.",
        f"Excellent work on your {report_type.lower()} for {company_name}. The executive team appreciates your thorough analysis."
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
    ai_mode = "AI-Optimized Lightweight" if openai_available else "Demo Mode"
    
    transcript = f"""
AI EXECUTIVE PANEL SIMULATOR - {ai_mode}
SESSION TRANSCRIPT
====================================

Company: {company_name}
Industry: {industry}
Report Type: {report_type}
Session Date: {session_date}
Executives Present: {', '.join(selected_executives)}
AI Enhancement: {'Enabled - On-Demand Generation' if openai_available else 'Template-based'}

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

# ============================================================================
# FLASK ROUTES (ULTRA-LIGHTWEIGHT SESSION APPROACH)
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
        
        # Fast AI analysis
        detailed_analysis = analyze_report_with_ai_robust(report_content, company_name, industry, report_type)
        
        # ULTRA-LIGHTWEIGHT session storage - only store essentials in memory
        session_data = {
            'company_name': company_name,
            'industry': industry,
            'report_type': report_type,
            'selected_executives': selected_executives,
            'report_content': report_content,  # Store full content in memory, not cookies
            'key_details': detailed_analysis.get('key_details', []),
            'session_type': session_type,
            'question_limit': question_limit,
            'time_limit': time_limit,
            'session_start_time': datetime.now().isoformat(),
            'current_question_count': 0,
            'questions': [],  # Store questions asked
            'responses': []   # Store responses given
        }
        
        store_session_data(session_data)
        
        # Only store session ID in cookie (tiny size)
        print(f"📊 Cookie session size: {len(session.get('sid', ''))} bytes")
        
        return jsonify({
            'status': 'success',
            'message': f'Report analyzed! {"AI-powered on-demand questions" if openai_available else "Template-based questions"} ready.',
            'executives': selected_executives,
            'ai_enabled': openai_available,
            'key_details': detailed_analysis.get('key_details', [])[:2]  # Return only 2 for display
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
        key_details = session_data.get('key_details', [])
        
        if not selected_executives:
            return jsonify({'status': 'error', 'error': 'No executives selected'})
        
        # Generate first question on-demand
        first_exec = selected_executives[0]  # Start with first executive
        first_question = generate_ai_questions_on_demand(
            report_content, first_exec, company_name, industry, report_type, key_details, 1
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
        store_session_data(session_data)
        
        print(f"🚀 Presentation started with {first_exec} question")
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
        current_executive = data.get('executive_role', '')
        
        if not student_response:
            return jsonify({'status': 'error', 'error': 'Missing response'})
        
        session_data = get_session_data()
        if not session_data:
            return jsonify({'status': 'error', 'error': 'Session data lost. Please restart session.'})
        
        selected_executives = session_data.get('selected_executives', [])
        current_question_count = session_data.get('current_question_count', 0)
        question_limit = session_data.get('question_limit', 10)
        
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
        
        # CIRCUIT BREAKER: Check for repeated responses (simple check)
        responses = session_data.get('responses', [])
        if len(responses) >= 3 and responses[-1] == responses[-2] == responses[-3]:
            company_name = session_data.get('company_name', 'Your Company')
            closing_message = f"Thank you for your presentation. The session has ended."
            
            return jsonify({
                'status': 'success',
                'follow_up': {
                    'executive': 'CEO',
                    'name': get_executive_name('CEO'),
                    'title': 'CEO', 
                    'question': closing_message,
                    'is_closing': True,
                    'timestamp': datetime.now().isoformat()
                },
                'session_ending': True
            })
        
        # Generate next question on-demand
        next_executive = get_next_executive(selected_executives, next_question_count)
        company_name = session_data.get('company_name', '')
        industry = session_data.get('industry', '')
        report_type = session_data.get('report_type', '')
        report_content = session_data.get('report_content', '')
        key_details = session_data.get('key_details', [])
        
        next_question = generate_ai_questions_on_demand(
            report_content, next_executive, company_name, industry, report_type, key_details, next_question_count
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
        store_session_data(session_data)
        
        print(f"🎯 {next_executive} asking question #{next_question_count}")
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
        
        summary = {
            'total_questions': questions_asked,
            'total_responses': responses_given,
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
        
        transcript_content = generate_transcript(session_data)
        company_name = session_data.get('company_name', 'Company')
        session_date = datetime.now().strftime("%Y%m%d_%H%M")
        
        safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_company_name = safe_company_name.replace(' ', '_')
        
        ai_suffix = "_AI_Lightweight" if openai_available else "_Demo"
        filename = f"{safe_company_name}_Executive_Panel_Transcript{ai_suffix}_{session_date}.txt"
        
        response = Response(
            transcript_content,
            mimetype='text/plain',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
        
        return response
        
    except Exception as e:
        print(f"Download transcript error: {e}")
        return jsonify({'status': 'error', 'error': f'Error generating transcript: {str(e)}'})

@app.route('/debug_ai', methods=['GET'])
def debug_ai():
    """Debug route to see session status"""
    try:
        session_data = get_session_data()
        cookie_size = len(session.get('sid', ''))
        memory_size = len(str(session_data)) if session_data else 0
        
        debug_info = {
            'openai_available': openai_available,
            'session_approach': 'in_memory_lightweight',
            'cookie_size_bytes': cookie_size,
            'memory_size_bytes': memory_size,
            'total_sessions_active': len(SESSIONS),
            'session_data_summary': {
                'company_name': session_data.get('company_name', 'NOT SET') if session_data else 'NO SESSION',
                'current_question_count': session_data.get('current_question_count', 0) if session_data else 0,
                'questions_stored': len(session_data.get('questions', [])) if session_data else 0,
                'responses_stored': len(session_data.get('responses', [])) if session_data else 0,
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
    print(f"⚡ AI Enhancement: {'Enabled - ON-DEMAND Generation (Ultra-Lightweight)' if openai_available else 'Disabled (Demo Mode)'}")
    print(f"🌐 Running on port: {port}")
    print(f"💾 Session Storage: In-Memory (bypasses 4KB cookie limit)")
    print(f"🛡️ All fixes applied: Limit check, Circuit breaker, Ultra-lightweight storage")
    print("="*50)
    
    app.run(debug=debug_mode, port=port, host='0.0.0.0')