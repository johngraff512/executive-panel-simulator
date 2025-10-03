import os
import tempfile
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, Response
from flask_session import Session
import PyPDF2

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-for-development')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

Session(app)

# Check if OpenAI is available
try:
    import openai
    openai_available = True
    openai.api_key = os.environ.get('OPENAI_API_KEY')
except ImportError:
    openai_available = False

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

def analyze_report_themes(report_content):
    """Extract key themes and topics from the report"""
    if not report_content or len(report_content) < 100:
        return ["your main proposal"]
    
    # Simple keyword-based theme extraction
    themes = []
    
    # Common business themes to look for
    theme_keywords = {
        'digital transformation': ['digital', 'technology', 'automation', 'AI'],
        'market expansion': ['expand', 'growth', 'market', 'international'],
        'cost reduction': ['cost', 'efficiency', 'savings', 'optimize'],
        'new product launch': ['product', 'launch', 'innovation', 'development'],
        'customer experience': ['customer', 'experience', 'satisfaction', 'service'],
        'sustainability': ['sustainable', 'green', 'environment', 'ESG']
    }
    
    content_lower = report_content.lower()
    
    for theme, keywords in theme_keywords.items():
        if any(keyword in content_lower for keyword in keywords):
            themes.append(theme)
    
    return themes[:3] if themes else ["your main strategy"]

def generate_contextual_questions(report_content, executive_role, company_name, industry, report_type):
    """Generate questions based on actual report content"""
    
    # Extract key themes from the report
    key_themes = analyze_report_themes(report_content)
    
    # Role-specific question templates based on content
    role_templates = {
        'CEO': [
            f"I've reviewed your {report_type.lower()} for {company_name}. What's the biggest strategic risk you haven't addressed?",
            f"Your vision for {company_name} is interesting, but how does it differentiate from competitors in {industry}?",
            f"I notice you mention {key_themes[0]}. How do you plan to execute this at scale?",
            f"What would you do if your main assumption about {industry} market conditions proves wrong?",
            f"How does this strategy align with broader {industry} industry trends?",
            f"Looking at your {report_type.lower()}, what's your biggest competitive advantage?",
            f"If you had to pivot this strategy in 6 months, what would trigger that decision?"
        ],
        'CFO': [
            f"Looking at your financial projections for {company_name}, what's driving your revenue assumptions?",
            f"I'm concerned about your cash flow timeline. How will you bridge funding gaps?",
            f"Your cost structure seems optimistic for the {industry} sector. Can you justify these numbers?",
            f"What's your plan if you need 50% more capital than projected?",
            f"How did you validate your market size assumptions for {industry}?",
            f"What are your key financial metrics, and what targets are you setting?",
            f"How will you manage working capital as {company_name} scales?"
        ],
        'CTO': [
            f"Your technology approach for {company_name} raises some questions. How scalable is this solution?",
            f"What's your biggest technical risk, and how are you mitigating it?",
            f"I don't see much about your technical team. Who's going to build this?",
            f"How does your technology stack compare to industry standards in {industry}?",
            f"What happens if your key technical assumptions prove incorrect?",
            f"How will you handle data security and privacy for {company_name}?",
            f"What's your technology roadmap for the next 18 months?"
        ],
        'CMO': [
            f"Your customer acquisition strategy for {company_name} seems ambitious. How will you reach these customers?",
            f"I'm not seeing strong differentiation in your value proposition. What makes you unique in {industry}?",
            f"Your marketing budget assumptions - are these based on actual {industry} benchmarks?",
            f"How do you plan to compete against established players in {industry}?",
            f"What's your customer retention strategy beyond initial acquisition?",
            f"How will you measure marketing ROI for {company_name}?",
            f"What customer feedback have you gotten on your {industry} approach?"
        ],
        'COO': [
            f"The operational plan for {company_name} looks complex. What's your biggest execution risk?",
            f"How will you scale operations while maintaining quality in the {industry} sector?",
            f"I'm concerned about your timeline. What if key milestones are delayed?",
            f"Your supply chain assumptions - how have you validated these for {industry}?",
            f"What operational metrics will you track, and what are your targets?",
            f"How will you manage quality control as {company_name} grows?",
            f"What's your contingency plan if operations don't scale as expected?"
        ]
    }
    
    # Select and randomize questions based on report content
    questions = role_templates.get(executive_role, [])
    return questions

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
    
    # Count questions asked by each executive
    exec_question_count = {}
    for exec_role in selected_executives:
        exec_question_count[exec_role] = len([
            msg for msg in conversation_history 
            if msg.get('type') == 'question' and msg.get('executive') == exec_role
        ])
    
    # Always start with CEO
    if not conversation_history:
        return 'CEO' if 'CEO' in selected_executives else selected_executives[0]
    
    # Find executive who has asked fewest questions
    min_questions = min(exec_question_count.values())
    candidates = [exec for exec, count in exec_question_count.items() if count == min_questions]
    
    # If multiple candidates, rotate through them
    if len(candidates) > 1:
        # Get last executive who asked a question
        last_exec = None
        for msg in reversed(conversation_history):
            if msg.get('type') == 'question':
                last_exec = msg.get('executive')
                break
        
        # Find next executive in rotation
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
        time_limit = int(session_data.get('time_limit', 10))  # minutes
        start_time = datetime.fromisoformat(session_start)
        elapsed = datetime.now() - start_time
        return elapsed.total_seconds() >= (time_limit * 60)
    
    return False

def generate_closing_message(company_name, report_type):
    """Generate a professional closing message from the CEO"""
    closing_messages = [
        f"Thank you for presenting your {report_type.lower()} for {company_name}. You've given our executive team some excellent insights and ideas to consider. Your strategic thinking is impressive, and we appreciate the thorough analysis you've provided.",
        f"This has been a very productive discussion about {company_name}. Your {report_type.lower()} demonstrates solid strategic planning, and the executive team has gained valuable perspectives from your presentation. We'll be discussing these ideas further in our upcoming strategic planning sessions.",
        f"Excellent work on your {report_type.lower()} for {company_name}. You've addressed our key concerns and provided thoughtful responses to our questions. The executive team is impressed with your analysis and will be incorporating several of your insights into our strategic discussions."
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
    
    # Format session start time
    if session_start:
        start_time = datetime.fromisoformat(session_start)
        session_date = start_time.strftime("%B %d, %Y at %I:%M %p")
    else:
        session_date = "Date not recorded"
    
    transcript = f"""
AI EXECUTIVE PANEL SIMULATOR
SESSION TRANSCRIPT
====================================

Company: {company_name}
Industry: {industry}
Report Type: {report_type}
Session Date: {session_date}
Executives Present: {', '.join(selected_executives)}

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
    transcript += f"Generated by AI Executive Panel Simulator\n"
    transcript += f"Total Questions Asked: {question_number - 1}\n"
    transcript += f"Executives Participated: {len(selected_executives)}\n"
    
    return transcript

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/setup_session', methods=['POST'])
def setup_session():
    try:
        # Handle file upload
        if 'report-pdf' not in request.files:
            return jsonify({'status': 'error', 'error': 'No PDF file uploaded'})
        
        file = request.files['report-pdf']
        if file.filename == '':
            return jsonify({'status': 'error', 'error': 'No file selected'})
        
        # Extract form data
        company_name = request.form.get('company-name', '')
        industry = request.form.get('industry', '')
        report_type = request.form.get('report-type', 'Business Plan')
        selected_executives = request.form.getlist('executives')
        session_type = request.form.get('session-type', 'questions')
        question_limit = request.form.get('question-limit', '10')
        time_limit = request.form.get('time-limit', '10')
        
        if not all([company_name, industry, selected_executives]):
            return jsonify({'status': 'error', 'error': 'Missing required form data'})
        
        # Process PDF
        report_content = extract_text_from_pdf(file)
        
        if not report_content:
            return jsonify({'status': 'error', 'error': 'Could not extract text from PDF. Please ensure it\'s a text-based PDF.'})
        
        # Store session data
        session['company_name'] = company_name
        session['industry'] = industry
        session['report_type'] = report_type
        session['selected_executives'] = selected_executives
        session['report_content'] = report_content[:5000]  # Store first 5000 chars
        session['conversation_history'] = []
        session['session_type'] = session_type
        session['question_limit'] = question_limit
        session['time_limit'] = time_limit
        session['session_start_time'] = datetime.now().isoformat()
        session['used_questions'] = {exec: [] for exec in selected_executives}
        
        return jsonify({
            'status': 'success',
            'message': f'Report analyzed successfully! Found {len(report_content)} characters of content.',
            'executives': selected_executives
        })
        
    except Exception as e:
        print(f"Setup session error: {e}")
        return jsonify({'status': 'error', 'error': f'Error processing upload: {str(e)}'})

@app.route('/start_presentation', methods=['POST'])
def start_presentation():
    try:
        if 'report_content' not in session:
            return jsonify({'status': 'error', 'error': 'No report uploaded. Please start over.'})
        
        # Get session data
        selected_executives = session.get('selected_executives', [])
        company_name = session.get('company_name', '')
        industry = session.get('industry', '')
        report_type = session.get('report_type', '')
        report_content = session.get('report_content', '')
        conversation_history = session.get('conversation_history', [])
        
        if not selected_executives:
            return jsonify({'status': 'error', 'error': 'No executives selected'})
        
        # Generate questions for all executives
        all_questions = {}
        for exec_role in selected_executives:
            questions = generate_contextual_questions(
                report_content, exec_role, company_name, industry, report_type
            )
            all_questions[exec_role] = questions
        
        session['generated_questions'] = all_questions
        
        # Get first executive (always CEO if available)
        first_exec = get_next_executive(selected_executives, conversation_history)
        first_questions = all_questions.get(first_exec, [])
        
        if first_questions:
            # Create first question
            question_data = {
                'executive': first_exec,
                'name': get_executive_name(first_exec),
                'title': first_exec,
                'question': first_questions[0],
                'timestamp': datetime.now().isoformat()
            }
            
            # Track question usage
            used_questions = session.get('used_questions', {})
            if first_exec not in used_questions:
                used_questions[first_exec] = []
            used_questions[first_exec].append(0)  # Track question index
            session['used_questions'] = used_questions
            
            # Add to conversation history
            conversation_history.append({
                'type': 'question',
                'executive': first_exec,
                'question': first_questions[0],
                'timestamp': datetime.now().isoformat()
            })
            session['conversation_history'] = conversation_history
            
            return jsonify({
                'status': 'success',
                'initial_questions': [question_data]
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
        
        # Get session data
        selected_executives = session.get('selected_executives', [])
        conversation_history = session.get('conversation_history', [])
        generated_questions = session.get('generated_questions', {})
        used_questions = session.get('used_questions', {})
        
        # Add student response to history
        conversation_history.append({
            'type': 'response',
            'student_response': student_response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Check if session should end
        session_data = {
            'session_type': session.get('session_type', 'questions'),
            'question_limit': session.get('question_limit', '10'),
            'time_limit': session.get('time_limit', '10'),
            'conversation_history': conversation_history,
            'session_start_time': session.get('session_start_time')
        }
        
        if check_session_limit(session_data):
            # End session with CEO closing
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
        
        # Get next executive
        next_executive = get_next_executive(selected_executives, conversation_history)
        next_questions = generated_questions.get(next_executive, [])
        exec_used_questions = used_questions.get(next_executive, [])
        
        # Find an unused question
        available_questions = [
            (i, q) for i, q in enumerate(next_questions) 
            if i not in exec_used_questions
        ]
        
        if available_questions:
            question_index, next_question = random.choice(available_questions)
            
            # Track usage
            exec_used_questions.append(question_index)
            used_questions[next_executive] = exec_used_questions
            session['used_questions'] = used_questions
            
        else:
            # Generate a generic follow-up if we've run out of questions
            follow_ups = [
                f"That's interesting. Can you provide a specific example?",
                f"How would you measure success for that approach?",
                f"What would you do if that strategy doesn't work as expected?",
                f"Can you walk us through the implementation timeline?",
                f"What resources would you need to execute that plan?"
            ]
            next_question = random.choice(follow_ups)
        
        # Create follow-up question
        follow_up = {
            'executive': next_executive,
            'name': get_executive_name(next_executive),
            'title': next_executive,
            'question': next_question,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add to conversation history
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
        
        # Count questions and responses
        questions_asked = len([msg for msg in conversation_history if msg.get('type') == 'question'])
        responses_given = len([msg for msg in conversation_history if msg.get('type') == 'response'])
        
        summary = {
            'total_questions': questions_asked,
            'total_responses': responses_given,
            'company_name': company_name,
            'presentation_topic': report_type,
            'executives_involved': session.get('selected_executives', []),
            'session_type': session_type,
            'session_limit': session.get('question_limit' if session_type == 'questions' else 'time_limit', 'Not set')
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
        # Generate transcript from session data
        transcript_content = generate_transcript(session)
        
        # Get session info for filename
        company_name = session.get('company_name', 'Company')
        session_date = datetime.now().strftime("%Y%m%d_%H%M")
        
        # Clean company name for filename
        safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_company_name = safe_company_name.replace(' ', '_')
        
        filename = f"{safe_company_name}_Executive_Panel_Transcript_{session_date}.txt"
        
        # Return file as download
        response = Response(
            transcript_content,
            mimetype='text/plain',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
        return response
        
    except Exception as e:
        print(f"Download transcript error: {e}")
        return jsonify({'status': 'error', 'error': f'Error generating transcript: {str(e)}'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 AI Executive Panel Simulator Starting...")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"🔧 Demo mode: {not openai_available}")
    print(f"🌐 Running on port: {port}")
    print("="*50)
    
    app.run(debug=debug_mode, port=port, host='0.0.0.0')