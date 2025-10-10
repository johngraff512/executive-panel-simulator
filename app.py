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
# AI CONFIGURATION AND INITIALIZATION
# ============================================================================

# Initialize OpenAI client with robust error handling
openai_client = None
openai_available = False

# Configuration for AI features - optimized for faster generation
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
    """Generate AI questions - OPTIMIZED for speed with more variety per executive"""
    if not openai_available:
        return generate_role_specific_templates(executive_role, company_name, industry, report_type, detailed_analysis.get("key_details", []), previously_asked_questions)
    
    print(f"⚡ Generating DIVERSE {executive_role} questions for {company_name}...")
    
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
        
        # Enhanced prompt for MORE DIVERSE questions per executive
        prompt_data = {
            'messages': [
                {
                    "role": "system",
                    "content": f"You are a {executive_role}. Generate 6 DIVERSE questions about {company_name} from your {focus} perspective. Each question should focus on different aspects of the report. Be concise but specific."
                },
                {
                    "role": "user",
                    "content": f"""Company: {company_name} | Industry: {industry} | Role: {executive_role}

Key details: {', '.join(key_details[:4])}

Report excerpt:
{report_content[:1500]}

Generate exactly 6 DIFFERENT questions that:
1. Reference specific report details
2. Each focuses on a DIFFERENT aspect of {focus}
3. Vary your questioning approach (assumptions, risks, execution, metrics, alternatives, etc.)
4. Start with varied openings: "In your analysis...", "Your plan shows...", "Looking at...", "How do you...", "What happens if...", "Why did you..."

Format as numbered list:"""
                }
            ],
            'max_tokens': 500,  # Increased slightly for more variety
            'temperature': 0.5  # Higher for more diversity
        }
        
        response_text = call_openai_with_timeout(prompt_data, timeout=12)  # Slightly longer for quality
        
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
                print(f"✅ Generated {len(unique_questions)} DIVERSE AI questions for {executive_role}")
                return unique_questions[:6]  # Return up to 6 questions for variety
            else:
                print(f"⚠️ Using templates for {executive_role} due to deduplication")
                return generate_role_specific_templates(executive_role, company_name, industry, report_type, key_details, previously_asked_questions)[:6]
        else:
            print(f"❌ AI timeout for {executive_role}, using templates")
            return generate_role_specific_templates(executive_role, company_name, industry, report_type, detailed_analysis.get("key_details", []), previously_asked_questions)[:6]
            
    except Exception as e:
        print(f"❌ AI failed for {executive_role}: {e}")
        return generate_role_specific_templates(executive_role, company_name, industry, report_type, detailed_analysis.get("key_details", []), previously_asked_questions)[:6]

def generate_role_specific_templates(executive_role, company_name, industry, report_type, key_themes, previously_asked_questions=[]):
    """Generate template questions - EXPANDED with 6 diverse questions each"""
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
    
    print(f"⚠️ Using diverse templates for {executive_role}")
    
    # EXPANDED templates - 6 diverse questions each for variety
    role_templates = {
        'CEO': [
            f"Looking at {company_name}'s long-term vision, what happens if the {industry} industry shifts completely?",
            f"What's {company_name}'s sustainable competitive moat that competitors can't replicate?",
            f"How does {company_name}'s approach create shareholder value differently than competitors?",
            f"Looking at {theme}, what's your exit strategy if this doesn't achieve market leadership?",
            f"What would convince the board to double down on this {report_type.lower()} if results are mixed?",
            f"How do you prioritize {company_name}'s strategic initiatives when resources are limited?"
        ],
        'CFO': [
            f"Walk me through {company_name}'s cash conversion cycle - when do we see positive cash flow?",
            f"Your CAPEX assumptions - what if interest rates double and funding costs skyrocket?",
            f"What's the contribution margin for {company_name}'s core revenue streams?",
            f"How sensitive is profitability to a 20% increase in your largest cost component?",
            f"Show me the scenario analysis - what's the downside case for {company_name}'s finances?",
            f"How do you validate these financial projections against {industry} benchmarks?"
        ],
        'CTO': [
            f"What's {company_name}'s technical architecture - can it handle 10x growth without rebuilding?",
            f"How do your technology choices compare to industry standards in {industry}?",
            f"What's the migration path if your core technology becomes obsolete?",
            f"How does the tech infrastructure support international expansion?",
            f"What's your strategy for technical debt and system modernization at {company_name}?",
            f"How do you ensure {company_name}'s platform stays secure as you scale?"
        ],
        'CMO': [
            f"What's {company_name}'s customer acquisition cost vs lifetime value ratio?",
            f"How are you differentiating from established players in consumer perception?",
            f"What channels drive the highest quality leads for {company_name}?",
            f"How do you measure brand equity and prove you're winning mindshare?",
            f"What's your customer retention strategy as {company_name} scales?",
            f"How does {company_name} build viral growth and organic customer advocacy?"
        ],
        'COO': [
            f"What's {company_name}'s operational leverage - how does throughput scale?",
            f"Your supply chain - what happens if your primary supplier has a disruption?",
            f"How do you maintain quality as {company_name} scales 5x in {industry}?",
            f"What KPIs tell you when operations are breaking down before customers notice?",
            f"How do you balance automation vs. human operations as {company_name} grows?",
            f"What's your contingency plan if key operational processes fail at {company_name}?"
        ]
    }
    
    questions = role_templates.get(executive_role, [])
    return questions[:6]  # Return exactly 6 questions for variety

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
    
    ai_mode = "AI-No-Repeat Smart Selection" if openai_available else "Demo Mode"
    
    transcript = f"""
AI EXECUTIVE PANEL SIMULATOR - {ai_mode}
SESSION TRANSCRIPT
====================================

Company: {company_name}
Industry: {industry}
Report Type: {report_type}
Session Date: {session_date}
Executives Present: {', '.join(selected_executives)}
AI Enhancement: {'Enabled - Diverse Content-Driven Questions with No Repeats' if openai_available else 'Template-based'}

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

# ============================================================================
# SESSION HEALTH MONITORING (NEW FIXES)
# ============================================================================

def get_session_size():
    '''Calculate approximate session size in bytes'''
    try:
        session_data = dict(session)
        return len(json.dumps(session_data, default=str))
    except:
        return 0

def check_session_health():
    '''Check if session is healthy and not corrupted'''
    try:
        required_keys = ['company_name', 'current_question_count', 'conversation_history']
        for key in required_keys:
            if key not in session:
                return False, f"Missing session key: {key}"
        
        session_size = get_session_size()
        if session_size > 3500:  # Warn before 4KB limit
            return False, f"Session size too large: {session_size} bytes"
            
        return True, "Session healthy"
    except Exception as e:
        return False, f"Session check error: {str(e)}"

# ============================================================================
# FLASK ROUTES (MUST COME AFTER APP INITIALIZATION)
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
        question_limit = request.form.get('question-limit', '10')
        time_limit = request.form.get('time-limit', '10')
        
        if not all([company_name, industry, selected_executives]):
            return jsonify({'status': 'error', 'error': 'Missing required form data'})
        
        report_content = extract_text_from_pdf(file)
        if not report_content:
            return jsonify({'status': 'error', 'error': 'Could not extract text from PDF. Please ensure it\'s a text-based PDF.'})
        
        # Fast AI analysis
        detailed_analysis = analyze_report_with_ai_robust(report_content, company_name, industry, report_type)
        
        # OPTIMIZED session data storage - REDUCED SIZE TO PREVENT COOKIE OVERFLOW
        session['company_name'] = company_name
        session['industry'] = industry
        session['report_type'] = report_type
        session['selected_executives'] = selected_executives
        session['report_content'] = report_content[:500]  # REDUCED from 1500 to 500
        session['detailed_analysis'] = {'key_details': detailed_analysis.get('key_details', [])[:3]}  # REDUCED from 6 to 3
        session['conversation_history'] = []
        session['session_type'] = session_type
        session['question_limit'] = question_limit
        session['time_limit'] = time_limit
        session['session_start_time'] = datetime.now().isoformat()
        session['current_question_count'] = 0
        
        key_details = detailed_analysis.get("key_details", [])
        
        return jsonify({
            'status': 'success',
            'message': f'Report analyzed! {"Diverse AI-powered questions with no repeats" if openai_available else "Template-based questions"} ready.',
            'executives': selected_executives,
            'ai_enabled': openai_available,
            'key_details': key_details[:3]  # Return only 3 to reduce size
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
        
        # Generate questions SEQUENTIALLY - OPTIMIZED with MORE variety per executive
        all_questions = {}
        all_previous_questions = []
        
        print(f"⚡ Generating 6 diverse questions each for {len(selected_executives)} executives...")
        
        for i, exec_role in enumerate(selected_executives):
            try:
                questions = generate_ai_questions_optimized(
                    report_content, exec_role, company_name, industry, report_type, detailed_analysis, all_previous_questions
                )
                
                all_questions[exec_role] = questions
                all_previous_questions.extend(questions[:2])  # Add first 2 to avoid list
                print(f"✅ {len(questions)} questions generated for {exec_role} ({i+1}/{len(selected_executives)})")
                
            except Exception as e:
                print(f"❌ Error generating questions for {exec_role}: {e}")
                # Use templates as fallback
                template_questions = generate_role_specific_templates(exec_role, company_name, industry, report_type, detailed_analysis.get("key_details", []), all_previous_questions)
                all_questions[exec_role] = template_questions
        
        # DON'T STORE generated_questions in session to reduce session size
        # Instead generate questions on-demand
        
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
            
            # TRIM conversation history to prevent session overflow
            conversation_history.append({
                'type': 'question',
                'executive': first_exec,
                'question': first_questions[0],
                'timestamp': datetime.now().isoformat()
            })
            session['conversation_history'] = conversation_history[-10:]  # Keep only last 10 entries
            
            # Store only essential question data, not all questions
            session['current_questions'] = {exec: questions[:3] for exec, questions in all_questions.items()}  # Store only 3 per exec
            
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
        current_questions = session.get('current_questions', {})
        current_question_count = session.get('current_question_count', 0)
        
        # SESSION CORRUPTION DETECTION
        is_healthy, health_message = check_session_health()
        if not is_healthy:
            print(f"⚠️ Session health issue: {health_message}")
            return jsonify({'status': 'error', 'error': f'Session data corrupted: {health_message}. Please restart session.'})
        
        # Add student response
        conversation_history.append({
            'type': 'response',
            'student_response': student_response,
            'timestamp': datetime.now().isoformat()
        })
        
        # CRITICAL FIX: Check limit BEFORE generating next question
        # and increment counter BEFORE the check
        next_question_count = current_question_count + 1
        
        if session.get('session_type', 'questions') == 'questions':
            question_limit = int(session.get('question_limit', 10))
            if next_question_count > question_limit:  # Use next count, not current
                # End session
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
                
                # Update session with minimal data to avoid cookie overflow
                session['conversation_history'] = conversation_history[-10:]  # Keep only last 10 entries
                session['current_question_count'] = next_question_count
                
                return jsonify({
                    'status': 'success',
                    'follow_up': closing_question,
                    'session_ending': True
                })
        
        # Get all previously asked questions for deduplication
        asked_questions = [msg.get('question', '') for msg in conversation_history if msg.get('type') == 'question']
        
        # CIRCUIT BREAKER: If last 3 questions are identical, force session end
        if len(asked_questions) >= 3 and asked_questions[-1] == asked_questions[-2] == asked_questions[-3]:
            company_name = session.get('company_name', 'Your Company')
            closing_message = f"Thank you for your presentation. The session has ended due to technical issues."
            
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
        
        # Find next available question
        next_question = None
        next_executive = None
        
        # Try each executive in round-robin order
        exec_start_index = selected_executives.index(get_next_executive(selected_executives, conversation_history))
        
        for i in range(len(selected_executives)):
            exec_index = (exec_start_index + i) % len(selected_executives)
            exec_role = selected_executives[exec_index]
            exec_questions = current_questions.get(exec_role, [])
            
            # Find first unused question for this executive
            for question in exec_questions:
                if question not in asked_questions:
                    next_question = question
                    next_executive = exec_role
                    break
                    
            if next_question:
                break
        
        # Fallback question generation if no questions available
        if not next_question:
            next_executive = get_next_executive(selected_executives, conversation_history)
            company_name = session.get('company_name', 'your company')
            next_question = f"What is your final recommendation for {company_name}? (Question #{next_question_count})"
        
        # Update session with minimal data to prevent cookie overflow
        session['current_question_count'] = next_question_count
        
        # Only keep essential conversation history to reduce session size
        conversation_history.append({
            'type': 'question',
            'executive': next_executive,
            'question': next_question,
            'timestamp': datetime.now().isoformat()
        })
        
        # Trim conversation history to prevent cookie overflow
        session['conversation_history'] = conversation_history[-15:]  # Keep only last 15 entries
        
        follow_up = {
            'executive': next_executive,
            'name': get_executive_name(next_executive),
            'title': next_executive,
            'question': next_question,
            'timestamp': datetime.now().isoformat()
        }
        
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
        
        ai_suffix = "_AI_No_Repeats" if openai_available else "_Demo"
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
            'optimization': 'no_repeats_with_variety_and_circuit_breaker',
            'session_size': get_session_size(),
            'session_health': check_session_health(),
            'session_data': {
                'company_name': session.get('company_name', 'NOT SET'),
                'industry': session.get('industry', 'NOT SET'),
                'report_type': session.get('report_type', 'NOT SET'),
                'has_report_content': bool(session.get('report_content')),
                'report_content_length': len(session.get('report_content', '')),
                'detailed_analysis': session.get('detailed_analysis', {}),
                'current_question_count': session.get('current_question_count', 0),
                'conversation_history_length': len(session.get('conversation_history', [])),
                'current_questions_count': {
                    exec: len(questions) if questions else 0
                    for exec, questions in session.get('current_questions', {}).items()
                },
                'asked_questions': [msg.get('question', '')[:50] + '...' for msg in session.get('conversation_history', []) if msg.get('type') == 'question'][-5:]  # Show last 5 asked questions
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

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 AI Executive Panel Simulator Starting...")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"⚡ AI Enhancement: {'Enabled - NO REPEAT QUESTIONS with Smart Selection & Circuit Breaker' if openai_available else 'Disabled (Demo Mode)'}")
    print(f"🌐 Running on port: {port}")
    print(f"🛡️ Session fixes applied: Limit check fix, Circuit breaker, Session health monitoring")
    print("="*50)
    
    app.run(debug=debug_mode, port=port, host='0.0.0.0')