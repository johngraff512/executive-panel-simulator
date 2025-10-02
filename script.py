# Create the main Flask application file
app_py = """
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import os
import json
import random
from datetime import datetime
import openai
from typing import Dict, List, Any

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# You'll need to set your OpenAI API key
# os.environ['OPENAI_API_KEY'] = 'your-openai-api-key'
# openai.api_key = os.environ.get('OPENAI_API_KEY')

class ExecutiveAgent:
    def __init__(self, role: str, company_context: Dict, student_presentation: Dict):
        self.role = role
        self.company_context = company_context
        self.student_presentation = student_presentation
        self.conversation_history = []
        
        # Define executive personas
        self.personas = {
            'CEO': {
                'name': 'Sarah Chen',
                'title': 'Chief Executive Officer',
                'personality': 'Visionary, strategic, big-picture thinker',
                'focus_areas': ['Vision', 'Strategy', 'Competitive Advantage', 'Leadership'],
                'communication_style': 'Direct, inspiring, occasionally challenging',
                'typical_concerns': ['Market position', 'Long-term viability', 'Stakeholder value'],
                'interruption_likelihood': 0.7,
                'question_types': ['strategic', 'vision', 'competitive']
            },
            'CFO': {
                'name': 'Michael Rodriguez',
                'title': 'Chief Financial Officer', 
                'personality': 'Analytical, risk-aware, numbers-focused',
                'focus_areas': ['ROI', 'Financial Risk', 'Budget Impact', 'Cash Flow'],
                'communication_style': 'Precise, data-driven, skeptical',
                'typical_concerns': ['Cost justification', 'Revenue impact', 'Financial metrics'],
                'interruption_likelihood': 0.8,
                'question_types': ['financial', 'risk', 'metrics']
            },
            'CTO': {
                'name': 'Dr. Lisa Wang',
                'title': 'Chief Technology Officer',
                'personality': 'Detail-oriented, innovative, technical',
                'focus_areas': ['Technical Feasibility', 'Scalability', 'Innovation', 'Security'],
                'communication_style': 'Thorough, technical, forward-thinking',
                'typical_concerns': ['Implementation complexity', 'Technical debt', 'Scalability'],
                'interruption_likelihood': 0.6,
                'question_types': ['technical', 'scalability', 'innovation']
            },
            'CMO': {
                'name': 'James Thompson',
                'title': 'Chief Marketing Officer',
                'personality': 'Creative, customer-centric, trend-aware',
                'focus_areas': ['Customer Impact', 'Market Positioning', 'Brand', 'Growth'],
                'communication_style': 'Enthusiastic, customer-focused, creative',
                'typical_concerns': ['Customer perception', 'Market response', 'Competitive differentiation'],
                'interruption_likelihood': 0.5,
                'question_types': ['customer', 'market', 'brand']
            },
            'COO': {
                'name': 'Rebecca Johnson',
                'title': 'Chief Operations Officer',
                'personality': 'Practical, process-focused, execution-oriented',
                'focus_areas': ['Implementation', 'Operations', 'Efficiency', 'Process'],
                'communication_style': 'Practical, systematic, results-oriented',
                'typical_concerns': ['Operational impact', 'Implementation timeline', 'Resource allocation'],
                'interruption_likelihood': 0.6,
                'question_types': ['operations', 'implementation', 'resources']
            }
        }
    
    def get_persona_info(self) -> Dict:
        return self.personas.get(self.role, {})
    
    def generate_question(self, context: str, question_type: str = 'general') -> str:
        # In a real implementation, this would call OpenAI API
        # For now, we'll use predefined questions based on role and context
        
        persona = self.personas.get(self.role, {})
        questions_bank = {
            'CEO': {
                'strategic': [
                    f"How does this proposal align with our long-term strategic vision for {self.company_context.get('industry', 'the industry')}?",
                    "What competitive advantages does this create for us over the next 3-5 years?",
                    "How will this impact our position in the market relative to our key competitors?",
                    "What's the strategic rationale behind this approach versus other alternatives?"
                ],
                'vision': [
                    f"How does this fit into our vision of becoming the leading {self.company_context.get('industry', 'company')} company?",
                    "What's the bigger picture impact on our company culture and values?",
                    "How will this initiative position us for future opportunities?",
                ],
                'competitive': [
                    "What's stopping our competitors from doing the same thing?",
                    "How does this differentiate us in ways that are difficult to replicate?",
                    "What first-mover advantages are we capturing here?"
                ]
            },
            'CFO': {
                'financial': [
                    f"What's the expected ROI on this {self.student_presentation.get('budget_estimate', 'investment')}?",
                    "Can you walk me through the financial projections and key assumptions?",
                    "How does this impact our cash flow over the next 12-24 months?",
                    "What's the break-even timeline for this initiative?"
                ],
                'risk': [
                    "What are the primary financial risks we should be concerned about?",
                    "How have you stress-tested these numbers against different market scenarios?",
                    "What's our contingency plan if the revenue projections don't materialize?",
                    "How does this affect our debt-to-equity ratio and credit ratings?"
                ],
                'metrics': [
                    "Which KPIs will we use to measure success?",
                    "How will this show up in our quarterly earnings reports?",
                    "What's the impact on our gross and net margins?"
                ]
            },
            'CTO': {
                'technical': [
                    f"Is this technically feasible with our current {self.company_context.get('tech_stack', 'technology infrastructure')}?",
                    "What are the key technical dependencies and risks?",
                    "How will this integrate with our existing systems and processes?",
                    "What's the technology roadmap for implementing this?"
                ],
                'scalability': [
                    "How does this solution scale as we grow from X to Y customers?",
                    "What are the performance implications at scale?",
                    "How do we handle peak loads and system reliability?",
                    "What's the long-term technical maintenance overhead?"
                ],
                'innovation': [
                    "How does this leverage emerging technologies in our space?",
                    "What innovations are we building that create technical moats?",
                    "How do we stay ahead of technological disruption with this approach?"
                ]
            },
            'CMO': {
                'customer': [
                    f"How will our {self.company_context.get('target_customer', 'key customers')} perceive this change?",
                    "What's the customer journey impact of this initiative?",
                    "How does this improve customer satisfaction and retention?",
                    "What customer segments are we targeting with this approach?"
                ],
                'market': [
                    "What's our go-to-market strategy for this initiative?",
                    f"How does this position us in the {self.company_context.get('industry', 'market')} landscape?",
                    "What market research supports this direction?",
                    "How do we measure market acceptance and adoption?"
                ],
                'brand': [
                    "How does this align with our brand promise and values?",
                    "What's the messaging strategy around this initiative?",
                    "How do we communicate this to different stakeholder groups?"
                ]
            },
            'COO': {
                'operations': [
                    "How do we operationalize this across all departments and locations?",
                    "What's the impact on our current operational processes?",
                    "How do we maintain business continuity during implementation?",
                    "What operational metrics will change as a result?"
                ],
                'implementation': [
                    "What's the detailed implementation timeline and milestones?",
                    "Who are the key stakeholders and what are their responsibilities?",
                    "How do we manage change management across the organization?",
                    "What's the training and support plan for affected employees?"
                ],
                'resources': [
                    "What resources do we need to allocate for successful execution?",
                    "How does this impact our current team structure and hiring plans?",
                    "What external partnerships or vendors do we need?",
                    "How do we prioritize this against other operational initiatives?"
                ]
            }
        }
        
        role_questions = questions_bank.get(self.role, {})
        type_questions = role_questions.get(question_type, [])
        
        if not type_questions:
            # Fallback to any questions for this role
            all_questions = []
            for q_list in role_questions.values():
                all_questions.extend(q_list)
            type_questions = all_questions
        
        if type_questions:
            return random.choice(type_questions)
        
        return f"As the {persona.get('title', self.role)}, I'd like to understand more about this proposal. Can you elaborate on the key implications for our organization?"
    
    def should_interrupt(self, presentation_progress: float) -> bool:
        persona = self.personas.get(self.role, {})
        base_likelihood = persona.get('interruption_likelihood', 0.5)
        
        # Adjust likelihood based on presentation progress
        if presentation_progress < 0.3:  # Early in presentation
            return random.random() < (base_likelihood * 0.7)
        elif presentation_progress > 0.8:  # Near end
            return random.random() < (base_likelihood * 1.2)
        else:
            return random.random() < base_likelihood

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/setup_session', methods=['POST'])
def setup_session():
    data = request.json
    
    # Store session data
    session['company_name'] = data.get('company_name', '')
    session['industry'] = data.get('industry', '')
    session['presentation_topic'] = data.get('presentation_topic', '')
    session['selected_executives'] = data.get('selected_executives', [])
    session['conversation_history'] = []
    session['session_id'] = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Initialize executive agents
    company_context = {
        'name': session['company_name'],
        'industry': session['industry']
    }
    
    student_presentation = {
        'topic': session['presentation_topic']
    }
    
    session['executives'] = {}
    for exec_role in session['selected_executives']:
        agent = ExecutiveAgent(exec_role, company_context, student_presentation)
        session['executives'][exec_role] = {
            'persona': agent.get_persona_info(),
            'conversation_count': 0
        }
    
    return jsonify({'status': 'success', 'session_id': session['session_id']})

@app.route('/start_presentation', methods=['POST'])
def start_presentation():
    if 'selected_executives' not in session:
        return jsonify({'error': 'Session not initialized'}), 400
    
    # Generate initial executive questions
    questions = []
    
    for exec_role in session['selected_executives']:
        agent = ExecutiveAgent(exec_role, 
                             {'name': session['company_name'], 'industry': session['industry']},
                             {'topic': session['presentation_topic']})
        
        question = agent.generate_question("Initial presentation", "general")
        
        questions.append({
            'executive': exec_role,
            'name': agent.get_persona_info().get('name', exec_role),
            'title': agent.get_persona_info().get('title', exec_role),
            'question': question,
            'timestamp': datetime.now().isoformat()
        })
    
    # Store in conversation history
    session['conversation_history'] = questions
    session.permanent = True
    
    return jsonify({
        'status': 'success',
        'initial_questions': questions
    })

@app.route('/respond_to_executive', methods=['POST'])
def respond_to_executive():
    data = request.json
    student_response = data.get('response', '')
    executive_role = data.get('executive_role', '')
    
    if 'conversation_history' not in session:
        return jsonify({'error': 'Session not initialized'}), 400
    
    # Add student response to history
    session['conversation_history'].append({
        'type': 'student_response',
        'executive': executive_role,
        'response': student_response,
        'timestamp': datetime.now().isoformat()
    })
    
    # Generate follow-up question or comment
    agent = ExecutiveAgent(executive_role, 
                         {'name': session['company_name'], 'industry': session['industry']},
                         {'topic': session['presentation_topic']})
    
    # Determine question type based on response content
    question_type = 'general'
    if any(word in student_response.lower() for word in ['cost', 'budget', 'revenue', 'profit']):
        question_type = 'financial' if executive_role == 'CFO' else 'general'
    elif any(word in student_response.lower() for word in ['customer', 'market', 'user']):
        question_type = 'customer' if executive_role == 'CMO' else 'market'
    elif any(word in student_response.lower() for word in ['technical', 'system', 'technology']):
        question_type = 'technical' if executive_role == 'CTO' else 'general'
    
    follow_up = agent.generate_question(student_response, question_type)
    
    follow_up_response = {
        'executive': executive_role,
        'name': agent.get_persona_info().get('name', executive_role),
        'title': agent.get_persona_info().get('title', executive_role),
        'question': follow_up,
        'type': 'follow_up',
        'timestamp': datetime.now().isoformat()
    }
    
    session['conversation_history'].append(follow_up_response)
    session.permanent = True
    
    return jsonify({
        'status': 'success',
        'follow_up': follow_up_response
    })

@app.route('/get_conversation_history')
def get_conversation_history():
    history = session.get('conversation_history', [])
    return jsonify({'conversation_history': history})

@app.route('/end_session', methods=['POST'])
def end_session():
    # Generate session summary and feedback
    conversation_count = len([item for item in session.get('conversation_history', []) 
                            if item.get('type') != 'student_response'])
    
    summary = {
        'session_id': session.get('session_id'),
        'company_name': session.get('company_name'),
        'presentation_topic': session.get('presentation_topic'),
        'executives_involved': session.get('selected_executives', []),
        'total_interactions': conversation_count,
        'session_duration': 'N/A',  # Would calculate in real implementation
        'feedback': generate_session_feedback()
    }
    
    return jsonify({'status': 'success', 'summary': summary})

def generate_session_feedback():
    # Analyze conversation history to provide feedback
    history = session.get('conversation_history', [])
    student_responses = [item for item in history if item.get('type') == 'student_response']
    
    feedback = {
        'overall_performance': 'Good engagement with executive questions',
        'strengths': [
            'Responded to all executive inquiries',
            'Maintained professional tone throughout',
            'Addressed multiple stakeholder concerns'
        ],
        'areas_for_improvement': [
            'Consider providing more specific metrics and data',
            'Anticipate follow-up questions better',
            'Develop clearer implementation timelines'
        ],
        'executive_feedback': {}
    }
    
    # Add role-specific feedback
    for exec_role in session.get('selected_executives', []):
        agent = ExecutiveAgent(exec_role, {}, {})
        persona = agent.get_persona_info()
        
        feedback['executive_feedback'][exec_role] = {
            'name': persona.get('name', exec_role),
            'focus_areas_addressed': persona.get('focus_areas', []),
            'suggestions': f"Focus more on {', '.join(persona.get('focus_areas', [])[:2])} in future presentations"
        }
    
    return feedback

if __name__ == '__main__':
    app.run(debug=True, port=5000)
"""

# Save the Flask app
with open('app.py', 'w') as f:
    f.write(app_py)

print("Created app.py - Main Flask application file")