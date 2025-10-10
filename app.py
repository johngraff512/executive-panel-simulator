# This file contains the key fixes for the AI Executive Simulator issues
# Apply these changes to the main app.py file


# SOLUTION 1: Fix the session limit check logic
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

        # SESSION CORRUPTION DETECTION
        if not conversation_history or len(conversation_history) == 0:
            return jsonify({'status': 'error', 'error': 'Session data corrupted. Please restart session.'})

        # Find next question with circuit breaker for repeated questions
        asked_questions = [msg.get('question', '') for msg in conversation_history if msg.get('type') == 'question']

        # Circuit breaker: If last 3 questions are identical, force session end
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
            exec_questions = generated_questions.get(exec_role, [])

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


# SOLUTION 2: Reduce session data size during setup
@app.route('/setup_session', methods=['POST'])
def setup_session():
    try:
        # ... existing file and form processing ...

        # Minimize session data storage
        session['company_name'] = company_name
        session['industry'] = industry
        session['report_type'] = report_type
        session['selected_executives'] = selected_executives
        session['report_content'] = report_content[:500]  # Drastically reduce stored content
        session['detailed_analysis'] = {'key_details': detailed_analysis.get('key_details', [])[:3]}  # Reduce stored details
        session['conversation_history'] = []
        session['session_type'] = session_type
        session['question_limit'] = question_limit
        session['time_limit'] = time_limit
        session['session_start_time'] = datetime.now().isoformat()
        session['current_question_count'] = 0

        # Don't store generated_questions in session initially - generate on demand

        return jsonify({
            'status': 'success',
            'message': f'Report analyzed! Ready for questions.',
            'executives': selected_executives,
            'ai_enabled': openai_available,
            'key_details': detailed_analysis.get("key_details", [])[:3]
        })

    except Exception as e:
        print(f"Setup session error: {e}")
        return jsonify({'status': 'error', 'error': f'Error processing upload: {str(e)}'})


# SOLUTION 3: Add session size monitoring
def get_session_size():
    '''Calculate approximate session size in bytes'''
    try:
        import json
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
