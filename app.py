import os
import tempfile
import random
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from flask import Flask, render_template, request, jsonify, session, Response
import PyPDF2
import openai

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-railway-deployment')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize OpenAI client - ROBUST VERSION WITH TIMEOUT MANAGEMENT
openai_client = None
openai_available = False

# Configuration for AI features
AI_TIMEOUT = 20  # seconds - shorter timeout to prevent worker kills
AI_MAX_RETRIES = 2
AI_ENABLED = True  # Toggle to easily disable if needed

try:
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key and AI_ENABLED:
        openai.api_key = api_key
        openai_available = True
        print("✅ OpenAI API key found - AI-powered questions enabled with timeout management")
    else:
        print("⚠️ AI disabled or no API key found - running in demo mode")
except ImportError as e:
    print(f"❌ OpenAI library not available: {e}")
    openai_available = False
except Exception as e:
    print(f"❌ OpenAI initialization failed: {e}")
    openai_available = False

def call_openai_with_timeout(prompt_data, timeout=AI_TIMEOUT):
    """Make OpenAI API call with timeout protection"""
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

def analyze_report_with_ai_robust(report_content, company_name, industry, report_type):
    """Robust AI analysis with timeout protection and fallback"""
    if not openai_available:
        return analyze_report_themes_basic(report_content)
    
    print(f"🤖 Starting AI analysis for {company_name} in {industry}...")
    
    try:
        # Concise prompt for faster processing
        prompt_data = {
            'messages': [
                {
                    "role": "system", 
                    "content": f"Extract 5 specific details from this {report_type} that executives would question. Focus on numbers, timelines, assumptions, and concrete claims. Respond with only a JSON object."
                },
                {
                    "role": "user", 
                    "content": f"""Company: {company_name} | Industry: {industry}
                    
Report (first 3000 chars):
{report_content[:3000]}

Return JSON:
{{"key_details": ["detail 1", "detail 2", "detail 3", "detail 4", "detail 5"]}}"""
                }
            ],
            'max_tokens': 300,  # Reduced for faster response
            'temperature': 0.2
        }
        
        response_text = call_openai_with_timeout(prompt_data, timeout=15)
        
        if response_text:
            try:
                # Try to parse JSON
                analysis = json.loads(response_text)
                print(f"✅ AI analysis completed for {company_name}")
                return {
                    "key_details": analysis.get("key_details", [])[:5],
                    "financial_claims": [],
                    "strategic_initiatives": [],
                    "assumptions": [],
                    "risks_mentioned": []
                }
            except json.JSONDecodeError:
                # Fallback: extract lines as details
                lines = [line.strip() for line in response_text.split('\n') if line.strip() and len(line.strip()) > 10]
                details = [line.strip('- "[]') for line in lines[:5]]
                print(f"⚠️ AI response parsed as text for {company_name}")
                return {"key_details": details, "financial_claims": [], "strategic_initiatives": [], "assumptions": [], "risks_mentioned": []}
        else:
            print(f"❌ AI analysis timed out for {company_name}, using fallback")
            return analyze_report_themes_basic(report_content)
        
    except Exception as e:
        print(f"❌ AI analysis failed for {company_name}: {e}")
        return analyze_report_themes_basic(report_content)

def analyze_report_themes_basic(report_content):
    """Basic keyword-based theme extraction (fallback)"""
    if not report_content or len(report_content) < 100:
        return {"key_details": ["your main proposal"], "financial_claims": [], "strategic_initiatives": [], "assumptions": [], "risks_mentioned": []}
    
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
    
    return {"key_details": themes[:5] if themes else ["your strategic approach"], "financial_claims": [], "strategic_initiatives": [], "assumptions": [], "risks_mentioned": []}

def generate_ai_questions_robust(report_content, executive_role, company_name, industry, report_type, detailed_analysis):
    """Generate AI questions with robust error handling and timeout protection"""
    
    if not openai_available:
        return generate_template_questions(executive_role, company_name, industry, report_type, detailed_analysis.get("key_details", []))
    
    print(f"🎯 Generating {executive_role} questions for {company_name}...")
    
    try:
        # Role-specific focus
        role_focuses = {
            'CEO': 'strategic vision and competitive advantage',
            'CFO': 'financial assumptions and profitability',
            'CTO': 'technical feasibility and scalability',
            'CMO': 'market positioning and customer acquisition',
            'COO': 'operational execution and implementation'
        }
        
        focus = role_focuses.get(executive_role, 'strategic approach')
        key_details = detailed_analysis.get("key_details", [])
        
        # Streamlined prompt for faster processing
        prompt_data = {
            'messages': [
                {
                    "role": "system", 
                    "content": f"You are a {executive_role} asking specific questions about {company_name}. Reference ONLY content from their {report_type}. Never mention Tesla, Apple, or other companies not in the report."
                },
                {
                    "role": "user", 
                    "content": f"""Company: {company_name} | Industry: {industry} | Your role: {executive_role}
Focus on: {focus}

Key details found: {', '.join(key_details[:3])}

Report content:
{report_content[:2000]}

Generate exactly 5 specific questions that:
1. Reference details from {company_name}'s {report_type}
2. Challenge assumptions about {focus}
3. Start with "In your {report_type}..." or "Your analysis states..."

Format as numbered list:"""
                }
            ],
            'max_tokens': 600,  # Reduced for speed
            'temperature': 0.4
        }
        
        response_text = call_openai_with_timeout(prompt_data, timeout=15)
        
          if response_text:
            # Parse questions with RELAXED validation
            questions = []
            forbidden_terms = ['tesla', 'apple', 'google', 'amazon', 'microsoft', 'facebook', 'meta']
            
            for line in response_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Clean up question
                    question = line.split('.', 1)[-1].strip()
                    question = question.split(')', 1)[-1].strip()
                    question = question.lstrip('- •').strip()
                    
                    # RELAXED validation - only check length and forbidden terms
                    if (len(question) > 30 and 
                        not any(term in question.lower() for term in forbidden_terms)):
                        questions.append(question)
            
            if len(questions) >= 2:  # Reduced from 3 to 2
                print(f"✅ Generated {len(questions)} AI questions for {executive_role}")
                return questions[:5]
            else:
                print(f"⚠️ Only {len(questions)} valid AI questions for {executive_role}, using templates")
                return generate_template_questions(executive_role, company_name, industry, report_type, key_details)
        else:
            print(f"❌ AI question generation timed out for {executive_role}")
            return generate_template_questions(executive_role, company_name, industry, report_type, detailed_analysis.get("key_details", []))
        
    except Exception as e:
        print(f"❌ AI question generation failed for {executive_role}: {e}")
        return generate_template_questions(executive_role, company_name, industry, report_type, detailed_analysis.get("key_details", []))

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
    conversation_history = session_data.get('conversation_history', [])
    company_name = session_data.get('company_name', 'Your Company')
    industry = session_data.get('industry', 'Technology')
    report_type = session_data.get('report_type', 'Business Plan')
    selected_executives = session_data.get('selected_executives', [])
    session_start = session_data.get('session_start_time', '')
    
    if session_start:
        start_time = datetime.fromisoformat(session_start)
        session_date = start_time.strftime("%B %d, %Y at %I:%M %p")
    else:
        session_date = "Date not recorded"
    
    ai_mode = "AI-Enhanced (Robust)" if openai_available else "Demo Mode"
    
    transcript = f"""
AI EXECUTIVE PANEL SIMULATOR - {ai_mode}
SESSION TRANSCRIPT
====================================

Company: {company_name}
Industry: {industry}
Report Type: {report_type}
Session Date: {session_date}
Executives Present: {', '.join(selected_executives)}
AI Enhancement: {'Enabled - Content-Driven Questions with Timeout Management' if openai_available else 'Template-based'}

====================================
PRESENTATION TRANSCRIPT
====================================

"""
    
    question_number = 1
    
    for entry in conversation_history:
        if entry.get('type') == 'question':
            executive_name = get_executive_name(entry.get('executive', 'Executive'))
            executive_role = entry.get('executive', 'Executive')
            question = entry.get('question', 'Question not recorded')
            timestamp = entry.get('timestamp', '')
            
            if timestamp:
                time_str = datetime.fromisoformat(timestamp).strftime("%I:%M %p")
            else:
                time_str = "Time not recorded"
            
            transcript += f"QUESTION {question_number} [{time_str}]\n"
            transcript += f"{executive_name} ({executive_role}):\n"
            transcript += f"{question}\n\n"
            
        elif entry.get('type') == 'response':
            student_response = entry.get('student_response', 'Response not recorded')
            timestamp = entry.get('timestamp', '')
            
            if timestamp:
                time_str = datetime.fromisoformat(timestamp).strftime("%I:%M %p")
            else:
                time_str = "Time not recorded"
            
            transcript += f"STUDENT RESPONSE [{time_str}]:\n"
            transcript += f"{student_response}\n\n"
            transcript += "-" * 50 + "\n\n"
            question_number += 1
            
        elif entry.get('type') == 'closing':
            executive_name = get_executive_name(entry.get('executive', 'CEO'))
            executive_role = entry.get('executive', 'CEO')
            closing_message = entry.get('message', 'Session ended')
            timestamp = entry.get('timestamp', '')
            
            if timestamp:
                time_str = datetime.fromisoformat(timestamp).strftime("%I:%M %p")
            else:
                time_str = "Time not recorded"
            
            transcript += f"SESSION CLOSING [{time_str}]\n"
            transcript += f"{executive_name} ({executive_role}):\n"
            transcript += f"{closing_message}\n\n"
    
    transcript += "====================================\n"
    transcript += "END OF TRANSCRIPT\n"
    transcript += "====================================\n"
    transcript += f"Generated by AI Executive Panel Simulator ({ai_mode})\n"
    transcript += f"Total Questions Asked: {question_number - 1}\n"
    transcript += f"Executives Participated: {len(selected_executives)}\n"
    if openai_available:
        transcript += f"AI Enhancement: OpenAI GPT-4o-mini with Robust Timeout Management\n"
    
    return transcript

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
        
        # Robust AI-powered analysis with timeout protection
        detailed_analysis = analyze_report_with_ai_robust(report_content, company_name, industry, report_type)
        
        session['company_name'] = company_name
        session['industry'] = industry
        session['report_type'] = report_type
        session['selected_executives'] = selected_executives
        session['report_content'] = report_content[:2000]  # Reduced to fix cookie size issue
        session['detailed_analysis'] = {'key_details': detailed_analysis.get('key_details', [])[:3]}  # Store only essential data
        session['conversation_history'] = []
        session['session_type'] = session_type
        session['question_limit'] = question_limit
        session['time_limit'] = time_limit
        session['session_start_time'] = datetime.now().isoformat()
        session['used_questions'] = {exec: [] for exec in selected_executives}
        
        # Show what was extracted for debugging
        key_details = detailed_analysis.get("key_details", [])[:3]
        
        return jsonify({
            'status': 'success',
            'message': f'Report analyzed successfully! Found {len(report_content)} characters of content. {"AI-enhanced content-driven (robust)" if openai_available else "Template-based"} questions generated.',
            'executives': selected_executives,
            'ai_enabled': openai_available,
            'key_details': key_details  # Show specific details extracted
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
        detailed_analysis = session.get('detailed_analysis', {})  # Use detailed analysis instead of themes
        conversation_history = session.get('conversation_history', [])
        
        if not selected_executives:
            return jsonify({'status': 'error', 'error': 'No executives selected'})
        
        # Generate robust AI-powered questions for all executives
        all_questions = {}
        for exec_role in selected_executives:
            questions = generate_ai_questions_robust(
                report_content, exec_role, company_name, industry, report_type, detailed_analysis
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
        transcript_content = generate_transcript(session)
        
        company_name = session.get('company_name', 'Company')
        session_date = datetime.now().strftime("%Y%m%d_%H%M")
        
        safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_company_name = safe_company_name.replace(' ', '_')
        
        ai_suffix = "_AI_Robust" if openai_available else "_Demo"
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
    """Debug route to see what AI analysis is producing"""
    try:
        debug_info = {
            'openai_available': openai_available,
            'ai_timeout': AI_TIMEOUT,
            'session_data': {
                'company_name': session.get('company_name', 'NOT SET'),
                'industry': session.get('industry', 'NOT SET'),
                'report_type': session.get('report_type', 'NOT SET'),
                'has_report_content': bool(session.get('report_content')),
                'report_content_length': len(session.get('report_content', '')),
                'report_content_preview': session.get('report_content', '')[:500] + '...' if session.get('report_content') else 'NO CONTENT',
                'has_detailed_analysis': bool(session.get('detailed_analysis')),
                'detailed_analysis': session.get('detailed_analysis', {}),
                'has_generated_questions': bool(session.get('generated_questions')),
                'generated_questions_sample': {
                    exec: questions[:2] if questions else []  # Show first 2 questions per exec
                    for exec, questions in session.get('generated_questions', {}).items()
                }
            }
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e)})

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
    print(f"🤖 AI Enhancement: {'Enabled - Robust Content-Driven Questions with Timeout Management' if openai_available else 'Disabled (Demo Mode)'}")
    print(f"🌐 Running on port: {port}")
    print("="*50)
    
    app.run(debug=debug_mode, port=port, host='0.0.0.0')