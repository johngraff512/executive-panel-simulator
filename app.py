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

# Configuration for AI features - OPTIMIZED FOR FASTER GENERATION
AI_TIMEOUT = 12  # Reduced from 20 to 12 seconds for faster generation
AI_MAX_RETRIES = 2
AI_ENABLED = True  # Toggle to easily disable if needed

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

def call_openai_with_timeout(prompt_data, timeout=AI_TIMEOUT):
    """Make OpenAI API call with timeout protection - OPTIMIZED"""
    def make_api_call():
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=prompt_data['messages'],
                max_tokens=prompt_data.get('max_tokens', 600),  # Reduced from 800
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
    """Enhanced AI analysis - OPTIMIZED for faster generation"""
    if not openai_available:
        return analyze_report_themes_basic(report_content)
    
    print(f"🤖 Starting FAST AI analysis for {company_name} in {industry}...")
    
    try:
        # Optimized prompt for faster processing
        prompt_data = {
            'messages': [
                {
                    "role": "system", 
                    "content": f"Extract 6-8 key details from this {report_type} that executives would question. Return concise JSON only."
                },
                {
                    "role": "user", 
                    "content": f"""Company: {company_name} | Industry: {industry}

Report content (first 3000 chars):
{report_content[:3000]}

Return JSON:
{{"key_details": ["detail 1", "detail 2", "detail 3", "detail 4", "detail 5", "detail 6"]}}"""
                }
            ],
            'max_tokens': 400,  # Reduced for faster response
            'temperature': 0.2
        }
        
        response_text = call_openai_with_timeout(prompt_data, timeout=10)  # Reduced timeout
        
        if response_text:
            try:
                import json
                analysis = json.loads(response_text)
                details = analysis.get("key_details", [])[:8]
                print(f"✅ FAST AI analysis completed for {company_name} - extracted {len(details)} details")
                return {
                    "key_details": details,
                    "financial_claims": [],
                    "strategic_initiatives": [],
                    "assumptions": [],
                    "risks_mentioned": []
                }
            except json.JSONDecodeError:
                lines = [line.strip() for line in response_text.split('\n') if line.strip() and len(line.strip()) > 15]
                details = [line.strip('- "[]') for line in lines[:6]]
                print(f"⚠️ AI response parsed as text for {company_name} - extracted {len(details)} details")
                return {"key_details": details, "financial_claims": [], "strategic_initiatives": [], "assumptions": [], "risks_mentioned": []}
        else:
            print(f"❌ AI analysis timed out for {company_name}, using fallback")
            return analyze_report_themes_basic(report_content)
        
    except Exception as e:
        print(f"❌ AI analysis failed for {company_name}: {e}")
        return analyze_report_themes_basic(report_content)

def analyze_report_themes_basic(report_content):
    """Enhanced basic keyword-based theme extraction (fallback)"""
    if not report_content or len(report_content) < 100:
        return {"key_details": ["your main proposal"], "financial_claims": [], "strategic_initiatives": [], "assumptions": [], "risks_mentioned": []}
    
    themes = []
    theme_keywords = {
        'digital transformation': ['digital', 'technology', 'automation', 'AI', 'software', 'platform'],
        'market expansion': ['expand', 'growth', 'market', 'international', 'new markets'],
        'cost reduction': ['cost', 'efficiency', 'savings', 'optimize', 'reduce'],
        'new product launch': ['product', 'launch', 'innovation', 'development'],
        'customer experience': ['customer', 'experience', 'satisfaction', 'service', 'user'],
        'sustainability': ['sustainable', 'green', 'environment', 'ESG'],
        'financial strategy': ['revenue', 'profit', 'investment', 'funding', 'capital'],
        'competitive strategy': ['competition', 'competitor', 'market share', 'differentiation']
    }
    
    content_lower = report_content.lower()
    for theme, keywords in theme_keywords.items():
        if any(keyword in content_lower for keyword in keywords):
            themes.append(theme)
    
    return {"key_details": themes[:6] if themes else ["your strategic approach", "market positioning"], "financial_claims": [], "strategic_initiatives": [], "assumptions": [], "risks_mentioned": []}

def generate_ai_questions_optimized(report_content, executive_role, company_name, industry, report_type, detailed_analysis, previously_asked_questions=[]):
    """Generate AI questions - OPTIMIZED for speed with fewer API calls"""
    
    if not openai_available:
        return generate_role_specific_templates(executive_role, company_name, industry, report_type, detailed_analysis.get("key_details", []), previously_asked_questions)
    
    print(f"⚡ Generating FAST {executive_role} questions for {company_name}...")
    
    try:
        # Role-specific focus
        role_focuses = {
            'CEO': 'strategic vision and competitive positioning',
            'CFO': 'financial analysis and capital structure',
            'CTO': 'technical architecture and scalability',
            'CMO': 'value proposition and market penetration',
            'COO': 'operational processes and execution'
        }
        
        focus = role_focuses.get(executive_role, 'strategic approach')
        key_details = detailed_analysis.get("key_details", [])
        
        # Optimized prompt for faster generation
        prompt_data = {
            'messages': [
                {
                    "role": "system", 
                    "content": f"You are a {executive_role}. Generate 4 specific questions about {company_name} from your {focus} perspective. Be concise."
                },
                {
                    "role": "user", 
                    "content": f"""Company: {company_name} | Industry: {industry} | Role: {executive_role}

Key details: {', '.join(key_details[:3])}

Report excerpt:
{report_content[:1500]}

Generate exactly 4 questions that:
1. Reference specific report details
2. Focus on {focus}
3. Start with "In your analysis..." or "Your plan shows..."

Format as numbered list:"""
                }
            ],
            'max_tokens': 400,  # Reduced for speed
            'temperature': 0.4
        }
        
        response_text = call_openai_with_timeout(prompt_data, timeout=10)  # Reduced timeout
        
        if response_text:
            # Parse questions quickly
            questions = []
            
            for line in response_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    question = line.split('.', 1)[-1].strip()
                    question = question.split(')', 1)[-1].strip()
                    question = question.lstrip('- •').strip()
                    
                    if len(question) > 20:
                        questions.append(question)
            
            # Minimal deduplication - only check for nearly identical questions
            unique_questions = []
            for question in questions:
                is_unique = True
                for prev_q in previously_asked_questions[-3:]:  # Only check last 3
                    # Only filter if 90%+ identical
                    q_words = set(question.lower().split())
                    prev_words = set(prev_q.lower().split())
                    
                    if len(q_words) > 0 and len(prev_words) > 0:
                        overlap_ratio = len(q_words.intersection(prev_words)) / max(len(q_words), len(prev_words))
                        if overlap_ratio > 0.9:  # Only filter if 90%+ identical
                            is_unique = False
                            break
                
                if is_unique:
                    unique_questions.append(question)
            
            if unique_questions:
                print(f"✅ Generated {len(unique_questions)} FAST AI questions for {executive_role}")
                return unique_questions[:4]  # Return up to 4 questions
            else:
                print(f"⚠️ Using templates for {executive_role} due to deduplication")
                return generate_role_specific_templates(executive_role, company_name, industry, report_type, key_details, previously_asked_questions)[:4]
        else:
            print(f"❌ AI timeout for {executive_role}, using templates")
            return generate_role_specific_templates(executive_role, company_name, industry, report_type, detailed_analysis.get("key_details", []), previously_asked_questions)[:4]
        
    except Exception as e:
        print(f"❌ AI failed for {executive_role}: {e}")
        return generate_role_specific_templates(executive_role, company_name, industry, report_type, detailed_analysis.get("key_details", []), previously_asked_questions)[:4]

def generate_role_specific_templates(executive_role, company_name, industry, report_type, key_themes, previously_asked_questions=[]):
    """Generate template questions - OPTIMIZED with 4 questions each"""
    
    # Extract theme properly
    if key_themes and len(key_themes) > 0:
        if isinstance(key_themes, list):
            theme = key_themes[0] if key_themes[0] else "your strategy"
        else:
            theme = str(key_themes)
    else:
        theme = "your strategy"
    
    theme = str(theme).strip().strip('"').strip("'")
    if not theme or theme == "key_details" or theme.startswith("key_details") or len(theme) < 3:
        theme = f"{company_name}'s strategic approach"
    
    print(f"⚠️ Using optimized templates for {executive_role}")
    
    # OPTIMIZED templates - 4 questions each for speed
    role_templates = {
        'CEO': [
            f"Looking at {company_name}'s long-term vision, what happens if the {industry} industry shifts completely?",
            f"What's {company_name}'s sustainable competitive moat that competitors can't replicate?",
            f"How does {company_name}'s approach create shareholder value differently than competitors?",
            f"Looking at {theme}, what's your exit strategy if this doesn't achieve market leadership?"
        ],
        'CFO': [
            f"Walk me through {company_name}'s cash conversion cycle - when do we see positive cash flow?",
            f"Your CAPEX assumptions - what if interest rates double and funding costs skyrocket?",
            f"What's the contribution margin for {company_name}'s core revenue streams?",
            f"How sensitive is profitability to a 20% increase in your largest cost component?"
        ],
        'CTO': [
            f"What's {company_name}'s technical architecture - can it handle 10x growth without rebuilding?",
            f"How do your technology choices compare to industry standards in {industry}?",
            f"What's the migration path if your core technology becomes obsolete?",
            f"How does the tech infrastructure support international expansion?"
        ],
        'CMO': [
            f"What's {company_name}'s customer acquisition cost vs lifetime value ratio?",
            f"How are you differentiating from established players in consumer perception?",
            f"What channels drive the highest quality leads for {company_name}?",
            f"How do you measure brand equity and prove you're winning mindshare?"
        ],
        'COO': [
            f"What's {company_name}'s operational leverage - how does throughput scale?",
            f"Your supply chain - what happens if your primary supplier has a disruption?",
            f"How do you maintain quality as {company_name} scales 5x in {industry}?",
            f"What KPIs tell you when operations are breaking down before customers notice?"
        ]
    }
    
    questions = role_templates.get(executive_role, [])
    return questions[:4]  # Return exactly 4 questions

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
    current_question_count = session_data.get('current_question_count', 0)
    
    if session_type == 'questions':
        question_limit = int(session_data.get('question_limit', 10))
        return current_question_count >= question_limit
    
    elif session_type == 'time':
        session_start = session_data.get('session_start_time')
        if session_start:
            time_limit = int(session_data.get('time_limit', 10))
            start_time = datetime.fromisoformat(session_start)
            elapsed = datetime.now() - start_time
            return elapsed.total_seconds() >= (time_limit * 60)
    
    return False

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
    
    ai_mode = "AI-Optimized Fast Generation" if openai_available else "Demo Mode"
    
    transcript = f"""
AI EXECUTIVE PANEL SIMULATOR - {ai_mode}
SESSION TRANSCRIPT
====================================

Company: {company_name}
Industry: {industry}
Report Type: {report_type}
Session Date: {session_date}
Executives Present: {', '.join(selected_executives)}
AI Enhancement: {'Enabled - Fast Content-Driven Questions' if openai_available else 'Template-based'}

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
        
        # Fast AI analysis
        detailed_analysis = analyze_report_with_ai_robust(report_content, company_name, industry, report_type)
        
        # Optimized session data storage
        session['company_name'] = company_name
        session['industry'] = industry
        session['report_type'] = report_type
        session['selected_executives'] = selected_executives
        session['report_content'] = report_content[:1500]  # Reduced to 1500 for speed
        session['detailed_analysis'] = {'key_details': detailed_analysis.get('key_details', [])[:6]}
        session['conversation_history'] = []
        session['session_type'] = session_type
        session['question_limit'] = question_limit
        session['time_limit'] = time_limit
        session['session_start_time'] = datetime.now().isoformat()
        session['current_question_count'] = 0
        
        key_details = detailed_analysis.get("key_details", [])
        
        return jsonify({
            'status': 'success',
            'message': f'Report analyzed! {"Fast AI-powered questions" if openai_available else "Template-based questions"} ready.',
            'executives': selected_executives,
            'ai_enabled': openai_available,
            'key_details': key_details
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
        detailed_analysis = session.get('detailed_analysis', {})
        conversation_history = session.get('conversation_history', [])
        
        if not selected_executives:
            return jsonify({'status': 'error', 'error': 'No executives selected'})
        
        # Generate questions SEQUENTIALLY to avoid timeouts - OPTIMIZED
        all_questions = {}
        all_previous_questions = []
        
        print(f"⚡ Generating questions for {len(selected_executives)} executives...")
        
        for i, exec_role in enumerate(selected_executives):
            try:
                questions = generate_ai_questions_optimized(
                    report_content, exec_role, company_name, industry, report_type, detailed_analysis, all_previous_questions
                )
                all_questions[exec_role] = questions
                all_previous_questions.extend(questions[:2])  # Add first 2 to avoid list
                
                print(f"✅ Questions generated for {exec_role} ({i+1}/{len(selected_executives)})")
                
            except Exception as e:
                print(f"❌ Error generating questions for {exec_role}: {e}")
                # Use templates as fallback
                template_questions = generate_role_specific_templates(exec_role, company_name, industry, report_type, detailed_analysis.get("key_details", []), all_previous_questions)
                all_questions[exec_role] = template_questions
        
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
            
            session['current_question_count'] = 1
            
            conversation_history.append({
                'type': 'question',
                'executive': first_exec,
                'question': first_questions[0],
                'timestamp': datetime.now().isoformat()
            })
            session['conversation_history'] = conversation_history
            
            print(f"🚀 Presentation started with {first_exec} question")
            
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
        current_question_count = session.get('current_question_count', 0)
        
        # Add student response
        conversation_history.append({
            'type': 'response',
            'student_response': student_response,
            'timestamp': datetime.now().isoformat()
        })
        
        session['conversation_history'] = conversation_history
        
        # Check session limit
        if session.get('session_type', 'questions') == 'questions':
            question_limit = int(session.get('question_limit', 10))
            if current_question_count >= question_limit:
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
        
        # Get next question
        next_executive = get_next_executive(selected_executives, conversation_history)
        next_questions = generated_questions.get(next_executive, [])
        
        if next_questions and len(next_questions) > 0:
            # Simple cycling through available questions
            base_index = (current_question_count - 1) % len(next_questions)
            next_question = next_questions[base_index]
        else:
            # Fallback questions
            fallback_questions = {
                'CEO': f"What's the biggest strategic risk to {session.get('company_name', 'your company')}?",
                'CFO': f"Walk me through the financial metrics for {session.get('company_name', 'your company')}.",
                'CTO': f"How does the technical architecture support {session.get('company_name', 'your company')}'s growth?",
                'CMO': f"What's your customer acquisition strategy for {session.get('company_name', 'your company')}?",
                'COO': f"How do you execute this strategy operationally at {session.get('company_name', 'your company')}?"
            }
            next_question = fallback_questions.get(next_executive, f"Can you elaborate on your {session.get('report_type', 'strategy').lower()}?")
        
        # Update question count
        current_question_count += 1
        session['current_question_count'] = current_question_count
        
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
        
        ai_suffix = "_AI_Fast_Optimized" if openai_available else "_Demo"
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
            'optimization': 'speed_optimized',
            'session_data': {
                'company_name': session.get('company_name', 'NOT SET'),
                'industry': session.get('industry', 'NOT SET'),
                'report_type': session.get('report_type', 'NOT SET'),
                'has_report_content': bool(session.get('report_content')),
                'report_content_length': len(session.get('report_content', '')),
                'detailed_analysis': session.get('detailed_analysis', {}),
                'current_question_count': session.get('current_question_count', 0),
                'conversation_history_length': len(session.get('conversation_history', [])),
                'generated_questions_count': {
                    exec: len(questions) if questions else 0
                    for exec, questions in session.get('generated_questions', {}).items()
                }
            }
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 AI Executive Panel Simulator Starting...")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"⚡ AI Enhancement: {'Enabled - SPEED OPTIMIZED for Fast Generation' if openai_available else 'Disabled (Demo Mode)'}")
    print(f"🌐 Running on port: {port}")
    print("="*50)
    
    app.run(debug=debug_mode, port=port, host='0.0.0.0')