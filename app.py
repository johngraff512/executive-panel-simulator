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
                import json
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

def generate_ai_questions_robust_with_deduplication(report_content, executive_role, company_name, industry, report_type, detailed_analysis, previously_asked_questions=[]):
    """Generate AI questions with robust error handling, timeout protection, AND anti-repetition logic"""
    
    if not openai_available:
        return generate_role_specific_templates(executive_role, company_name, industry, report_type, detailed_analysis.get("key_details", []), previously_asked_questions)
    
    print(f"🎯 Generating {executive_role} questions for {company_name} (avoiding {len(previously_asked_questions)} previous questions)...")
    
    try:
        # Role-specific focus with UNIQUE angles
        role_focuses = {
            'CEO': 'strategic vision, competitive positioning, and long-term market leadership',
            'CFO': 'financial analysis, capital structure, and quantitative risk assessment',
            'CTO': 'technical architecture, scalability engineering, and innovation systems',
            'CMO': 'value proposition, customer loyalty, and market penetration',
            'COO': 'operational processes, supply chain optimization, and execution logistics'
        }
        
        focus = role_focuses.get(executive_role, 'strategic approach')
        key_details = detailed_analysis.get("key_details", [])
        
        # Create "avoid repetition" guidance for AI
        avoid_guidance = ""
        if previously_asked_questions:
            previous_topics = []
            for q in previously_asked_questions[-6:]:  # Look at last 6 questions only
                if 'cost' in q.lower() or 'financial' in q.lower() or 'revenue' in q.lower():
                    previous_topics.append('financial assumptions')
                if 'risk' in q.lower():
                    previous_topics.append('risk assessment')
                if 'implement' in q.lower() or 'execution' in q.lower():
                    previous_topics.append('implementation')
                if 'market' in q.lower() or 'customer' in q.lower():
                    previous_topics.append('market analysis')
                if 'competitive' in q.lower() or 'competition' in q.lower():
                    previous_topics.append('competitive strategy')
            
            if previous_topics:
                avoid_guidance = f"\n\nIMPORTANT: Previous executives already asked about: {', '.join(set(previous_topics))}. Ask about DIFFERENT aspects from your {executive_role} perspective."
        
        # Enhanced prompt for uniqueness - REMOVED company restrictions
        prompt_data = {
            'messages': [
                {
                    "role": "system", 
                    "content": f"You are a {executive_role} asking UNIQUE questions about {company_name} from your specific executive perspective. Reference ONLY their {report_type}. You may mention competitors or industry examples when relevant. Focus on {focus} - areas other executives wouldn't typically ask about."
                },
                {
                    "role": "user", 
                    "content": f"""Company: {company_name} | Industry: {industry} | Your role: {executive_role}
Your unique perspective: {focus}

Key details from report: {', '.join(key_details[:3])}

Report content:
{report_content[:2000]}{avoid_guidance}

Generate exactly 5 UNIQUE questions that:
1. Focus specifically on {focus}
2. Reference specific details from {company_name}'s {report_type}
3. Ask about aspects OTHER executives wouldn't typically cover
4. Start with "In your {report_type}..." or "Your analysis shows..."
5. May reference competitors or industry benchmarks when relevant

Format as numbered list:"""
                }
            ],
            'max_tokens': 600,
            'temperature': 0.5  # Slightly higher for more variety
        }
        
        response_text = call_openai_with_timeout(prompt_data, timeout=15)
        
        if response_text:
            # Parse and validate questions - REMOVED forbidden terms
            questions = []
            
            for line in response_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    question = line.split('.', 1)[-1].strip()
                    question = question.split(')', 1)[-1].strip()
                    question = question.lstrip('- •').strip()
                    
                    # Only check for minimum length
                    if len(question) > 30:
                        questions.append(question)
            
            # DEDUPLICATION CHECK: Compare with previous questions
            unique_questions = []
            for question in questions:
                is_unique = True
                for prev_q in previously_asked_questions:
                    # Check for topic overlap using key terms
                    q_words = set(question.lower().split())
                    prev_words = set(prev_q.lower().split())
                    common_words = q_words.intersection(prev_words)
                    # If >60% overlap in meaningful words, consider similar
                    meaningful_common = [w for w in common_words if len(w) > 4]
                    if len(meaningful_common) >= 3:
                        print(f"🔄 Filtered similar question: {question[:50]}...")
                        is_unique = False
                        break
                
                if is_unique:
                    unique_questions.append(question)
            
            if len(unique_questions) >= 2:
                print(f"✅ Generated {len(unique_questions)} unique AI questions for {executive_role}")
                return unique_questions[:5]
            else:
                print(f"⚠️ Only {len(unique_questions)} unique questions for {executive_role}, using role-specific templates")
                return generate_role_specific_templates(executive_role, company_name, industry, report_type, key_details, previously_asked_questions)
        else:
            print(f"❌ AI question generation timed out for {executive_role}")
            return generate_role_specific_templates(executive_role, company_name, industry, report_type, detailed_analysis.get("key_details", []), previously_asked_questions)
        
    except Exception as e:
        print(f"❌ AI question generation failed for {executive_role}: {e}")
        return generate_role_specific_templates(executive_role, company_name, industry, report_type, detailed_analysis.get("key_details", []), previously_asked_questions)

def generate_role_specific_templates(executive_role, company_name, industry, report_type, key_themes, previously_asked_questions=[]):
    """Generate highly differentiated template questions with anti-repetition logic - FIXED"""
    
    # FIX: Properly extract the theme from key_themes
    if key_themes and len(key_themes) > 0:
        # If key_themes is a list, take the first item
        if isinstance(key_themes, list):
            theme = key_themes[0] if key_themes[0] else "your strategy"
        else:
            theme = str(key_themes)
    else:
        theme = "your strategy"
    
    # Ensure theme is clean text (remove any JSON artifacts)
    theme = str(theme).strip().strip('"').strip("'")
    if not theme or theme == "key_details" or theme.startswith("key_details") or len(theme) < 3:
        theme = f"{company_name}'s strategic approach"
    
    print(f"🔍 Debug: Using theme '{theme}' for {executive_role} template questions")  # Debug logging
    
    # HIGHLY DIFFERENTIATED role templates - each executive focuses on completely different aspects
    role_templates = {
        'CEO': [
            f"Looking at {company_name}'s long-term vision, what happens if the {industry} industry paradigm shifts completely in 5 years?",
            f"The board will want to know: what's {company_name}'s sustainable competitive moat that competitors can't replicate?",
            f"If you had to defend this {report_type.lower()} to activist investors, what's your strongest strategic argument?",
            f"How does {company_name}'s approach create shareholder value differently than your top 3 competitors in {industry}?",
            f"What would convince me to choose {company_name} as a strategic partner over established {industry} leaders?",
            f"Looking at {theme}, what's your exit strategy if this doesn't achieve market leadership?",
            f"How do you plan to pivot {company_name} when the next industry disruption hits {industry}?"
        ],
        'CFO': [
            f"Walk me through {company_name}'s cash conversion cycle - how long before we see positive free cash flow?",
            f"Your CAPEX assumptions for {company_name} - what if interest rates double and funding costs skyrocket?",
            f"I need to see the unit economics: what's the contribution margin for {company_name}'s core revenue streams?",
            f"How sensitive is {company_name}'s profitability to a 20% increase in your largest cost component?",
            f"What's your debt-to-equity strategy, and how much dilution are shareholders facing with this {report_type.lower()}?",
            f"Show me the working capital requirements - what happens if customer payment terms extend by 30 days?",
            f"Your revenue recognition model for {industry} - are these projections compliant with current accounting standards?"
        ],
        'CTO': [
            f"What's {company_name}'s technical architecture - can it handle 10x user growth without rebuilding?",
            f"How do you feel our security and compliance compare to industry standards in {industry}?",
            f"What's the migration path if your core technology becomes obsolete or gets deprecated?",
            f"How are you handling data pipeline architecture and real-time processing for {company_name}'s operations?",
            f"What's your API strategy and how does it support {company_name}'s ecosystem partnerships in {industry}?",
            f"Your development velocity - what's preventing faster iteration cycles and continuous deployment?",
            f"How does {company_name}'s tech infrastructure support international expansion and regulatory compliance?"
        ],
        'CMO': [
            f"What's {company_name}'s customer lifetime value compare to {industry} benchmarks?",
            f"Your brand positioning strategy - how are we differentiating from established players in consumer perception?",
            f"What move by our competitors would have the biggest impact on our strategic position?",
            f"What metrics prove {company_name} is winning mindshare in {industry}?",
            f"How could we better communicate {company_name}'s core value proposition to key audience segments?",
            f"What are the risks that your proposed initiatives would alienate our core customer base?",
            f"How do we best personalize the customer experience across touchpoints for different segments of the {industry}?"
        ],
        'COO': [
            f"What's {company_name}'s operational leverage - how does throughput scale as you add capacity?",
            f"Your supply chain strategy - what happens if your primary supplier has a 6-month disruption?",
            f"How do you maintain quality standards as {company_name} scales operations in the {industry} market?",
            f"What's your talent acquisition strategy - can you hire fast enough to meet growth targets?",
            f"Your process automation roadmap - which manual operations get automated first and what's the ROI?",
            f"How does {company_name}'s operational model handle seasonal demand fluctuations in {industry}?",
            f"What key performance indicators tell you when {company_name}'s operations are breaking down before customers notice?"
        ]
    }
    
    questions = role_templates.get(executive_role, [])
    
    # Simple deduplication for templates - avoid questions with similar key terms
    if previously_asked_questions:
        filtered_questions = []
        for question in questions:
            is_unique = True
            for prev_q in previously_asked_questions:
                # Check for significant word overlap
                q_words = set([w.lower() for w in question.split() if len(w) > 4])
                prev_words = set([w.lower() for w in prev_q.split() if len(w) > 4])
                overlap = len(q_words.intersection(prev_words))
                if overlap >= 3:  # If 2+ significant words overlap, skip
                    is_unique = False
                    break
            if is_unique:
                filtered_questions.append(question)
        
        return filtered_questions[:7] if filtered_questions else questions[:7]
    
    return questions[:7]

def generate_template_questions(executive_role, company_name, industry, report_type, key_themes):
    """Generate template-based questions (fallback) - LEGACY VERSION FOR COMPATIBILITY"""
    return generate_role_specific_templates(executive_role, company_name, industry, report_type, key_themes, [])

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
    """Check if session has reached its limit - FIXED VERSION"""
    session_type = session_data.get('session_type', 'questions')
    conversation_history = session_data.get('conversation_history', [])
    session_start = session_data.get('session_start_time')
    current_question_count = session_data.get('current_question_count', 0)
    
    if session_type == 'questions':
        question_limit = int(session_data.get('question_limit', 10))
        print(f"🔢 Question count: {current_question_count}/{question_limit}")  # Debug logging
        return current_question_count >= question_limit
    
    elif session_type == 'time' and session_start:
        time_limit = int(session_data.get('time_limit', 10))
        start_time = datetime.fromisoformat(session_start)
        elapsed = datetime.now() - start_time
        elapsed_minutes = elapsed.total_seconds() / 60
        print(f"⏰ Time elapsed: {elapsed_minutes:.1f}/{time_limit} minutes")  # Debug logging
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
    
    ai_mode = "AI-Enhanced with Anti-Repetition" if openai_available else "Demo Mode"
    
    transcript = f"""
AI EXECUTIVE PANEL SIMULATOR - {ai_mode}
SESSION TRANSCRIPT
====================================

Company: {company_name}
Industry: {industry}
Report Type: {report_type}
Session Date: {session_date}
Executives Present: {', '.join(selected_executives)}
AI Enhancement: {'Enabled - Content-Driven Questions with Smart Deduplication' if openai_available else 'Template-based'}

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
        transcript += f"AI Enhancement: OpenAI GPT-4o-mini with Smart Anti-Repetition Logic\n"
    
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
        
        # DRASTICALLY reduce session data to prevent cookie overflow
        session['company_name'] = company_name
        session['industry'] = industry
        session['report_type'] = report_type
        session['selected_executives'] = selected_executives
        # CRITICAL: Store minimal data only
        session['report_content'] = report_content[:800]  # Reduced from 2000 to 800
        session['detailed_analysis'] = {'key_details': detailed_analysis.get('key_details', [])[:2]}  # Reduced from 3 to 2
        session['conversation_history'] = []
        session['session_type'] = session_type
        session['question_limit'] = question_limit
        session['time_limit'] = time_limit
        session['session_start_time'] = datetime.now().isoformat()
        # CRITICAL: Don't store used_questions in session - track separately
        session['current_question_count'] = 0  # Track count instead
        
        # Show what was extracted for debugging
        key_details = detailed_analysis.get("key_details", [])[:3]
        
        return jsonify({
            'status': 'success',
            'message': f'Report analyzed successfully! Found {len(report_content)} characters of content. {"AI-enhanced content-driven with anti-repetition" if openai_available else "Template-based"} questions generated.',
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
        
        # Generate robust AI-powered questions for all executives with deduplication
        all_questions = {}
        all_previous_questions = []  # Start with empty list
        
        for exec_role in selected_executives:
            questions = generate_ai_questions_robust_with_deduplication(
                report_content, exec_role, company_name, industry, report_type, detailed_analysis, all_previous_questions
            )
            all_questions[exec_role] = questions
            # Add these questions to previous list for next executive
            all_previous_questions.extend(questions)
        
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
            
            # Track first question
            session['current_question_count'] = 1
            
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
        current_question_count = session.get('current_question_count', 0)
        
        # Add student response to conversation
        conversation_history.append({
            'type': 'response',
            'student_response': student_response,
            'timestamp': datetime.now().isoformat()
        })
        
        session['conversation_history'] = conversation_history
        
        print(f"🔢 Question count: {current_question_count}")  # Debug logging
        
        # FIXED session limit check
        if session.get('session_type', 'questions') == 'questions':
            question_limit = int(session.get('question_limit', 10))
            if current_question_count >= question_limit:
                print(f"🏁 Session limit reached: {current_question_count}/{question_limit}")
                
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
        
        # Select next executive and question
        next_executive = get_next_executive(selected_executives, conversation_history)
        next_questions = generated_questions.get(next_executive, [])
        
        # ENHANCED question selection with deduplication - SMART ANTI-REPETITION
        if next_questions and len(next_questions) > 0:
            # Get all previously asked questions for deduplication
            all_previous_questions = [msg.get('question', '') for msg in conversation_history if msg.get('type') == 'question']
            
            # Use modulo but skip questions that are too similar to previous ones
            base_index = (current_question_count) % len(next_questions)
            
            # Try up to 3 different questions to find a unique one
            for attempt in range(min(3, len(next_questions))):
                question_index = (base_index + attempt) % len(next_questions)
                candidate_question = next_questions[question_index]
                
                # Check if this question is similar to previous ones
                is_unique = True
                for prev_q in all_previous_questions[-6:]:  # Only check last 6 questions
                    # Simple similarity check - significant word overlap
                    candidate_words = set([w.lower() for w in candidate_question.split() if len(w) > 4])
                    prev_words = set([w.lower() for w in prev_q.split() if len(w) > 4])
                    overlap = len(candidate_words.intersection(prev_words))
                    
                    if overlap >= 2:  # If 2+ significant words overlap, too similar
                        is_unique = False
                        break
                
                if is_unique:
                    next_question = candidate_question
                    print(f"🎯 {next_executive} asked unique question #{question_index+1}")
                    break
            else:
                # If all questions are similar, use the base question anyway
                next_question = next_questions[base_index]
                print(f"🔄 {next_executive} used fallback question #{base_index+1} (some similarity)")
        else:
            # Enhanced role-specific fallbacks with more variety - HIGHLY DIFFERENTIATED
            all_previous_questions = [msg.get('question', '') for msg in conversation_history if msg.get('type') == 'question']
            
            role_specific_fallbacks = {
                'CEO': [
                    f"What's the biggest strategic risk to {session.get('company_name', 'your company')} that keeps you up at night?",
                    f"If the {session.get('industry', 'market')} shifts dramatically, how does {session.get('company_name', 'your company')} pivot?",
                    f"What would make you completely change this {session.get('report_type', 'strategy').lower()} in 6 months?",
                    f"How does {session.get('company_name', 'your company')} create lasting competitive advantage?",
                    f"What's your vision for {session.get('company_name', 'your company')} in 5 years?"
                ],
                'CFO': [
                    f"Show me the specific financial metrics that prove {session.get('company_name', 'your company')} is succeeding.",
                    f"What's the cash flow timeline, and when do we break even?",
                    f"How do you validate these financial assumptions for the {session.get('industry', 'market')}?",
                    f"What happens if funding costs increase by 50%?",
                    f"Walk me through the unit economics of your core business model."
                ],
                'CTO': [
                    f"What's the technical architecture that supports {session.get('company_name', 'your company')}'s scaling?",
                    f"How does your technology stack compare to {session.get('industry', 'industry')} standards?",
                    f"What's your biggest technical risk, and how are you mitigating it?",
                    f"How does the platform handle 10x growth without breaking?",
                    f"What's your strategy for technical debt and system modernization?"
                ],
                'CMO': [
                    f"How do you actually acquire customers in the {session.get('industry', 'market')}?",
                    f"What makes {session.get('company_name', 'your company')} different from competitors in customer perception?",
                    f"What's your customer acquisition cost vs lifetime value?",
                    f"How do you measure and improve brand equity?",
                    f"What channels drive your highest-quality leads?"
                ],
                'COO': [
                    f"How do you actually execute this {session.get('report_type', 'strategy').lower()} operationally?",
                    f"What are the operational bottlenecks as {session.get('company_name', 'your company')} scales?",
                    f"How do you maintain quality while scaling operations?",
                    f"What operational metrics tell you the system is working?",
                    f"What's your contingency plan if operations break down?"
                ]
            }
            
            executive_fallbacks = role_specific_fallbacks.get(next_executive, [
                f"Can you elaborate on your approach to {session.get('report_type', 'strategy').lower()}?",
                f"What's the most critical success factor for {session.get('company_name', 'your company')}?",
                f"How do you measure success in this {session.get('industry', 'market')}?"
            ])
            
            # Use modulo to cycle through role-specific fallbacks
            fallback_index = (current_question_count) % len(executive_fallbacks)
            next_question = executive_fallbacks[fallback_index]
            print(f"🔄 {next_executive} using role-specific fallback #{fallback_index+1}")
        
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
        
        ai_suffix = "_AI_AntiRepetition_FIXED" if openai_available else "_Demo"
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
                'current_question_count': session.get('current_question_count', 0),
                'conversation_history_length': len(session.get('conversation_history', [])),
                'generated_questions_sample': {
                    exec: questions[:2] if questions else []  # Show first 2 questions per exec
                    for exec, questions in session.get('generated_questions', {}).items()
                },
                'anti_repetition_enabled': True,
                'company_restrictions_removed': True,
                'theme_bug_fixed': True
            }
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e)})

# Logo serving route (updated for new logo)
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
    print(f"🤖 AI Enhancement: {'Enabled - Robust Content-Driven Questions with Smart Anti-Repetition & Competitor Mentions (THEME BUG FIXED)' if openai_available else 'Disabled (Demo Mode)'}")
    print(f"🌐 Running on port: {port}")
    print("="*50)
    
    app.run(debug=debug_mode, port=port, host='0.0.0.0')