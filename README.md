# AI Executive Panel Simulator

An interactive web application that simulates company executives during student presentations using AI agents.

## Features

- **Multiple Executive Personas**: CEO, CFO, CTO, CMO, COO with distinct personalities
- **Dynamic Questioning**: AI-generated questions based on presentation content
- **Realistic Interactions**: Interruptions, follow-ups, and role-specific concerns
- **Session Analytics**: Performance tracking and detailed feedback
- **Responsive Design**: Works on desktop and mobile devices

## Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.template` to `.env` and add your OpenAI API key:

```bash
cp .env.template .env
```

Edit `.env` and add your API key:
```
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

### 3. Run the Application

```bash
python app.py
```

Open your browser to `http://localhost:5000`

## Usage Instructions

### For Students:
1. **Setup**: Enter company name, select industry, describe your presentation
2. **Executive Panel**: Choose which executives to include (2-5 recommended)
3. **Present**: AI executives will ask questions during your presentation
4. **Respond**: Answer questions in real-time with specific details
5. **Review**: Get detailed feedback and areas for improvement

### For Instructors:
- Monitor student sessions through conversation logs
- Customize executive personalities and question types
- Add company-specific context and industry knowledge
- Export session data for grading and assessment

## Executive Personas

### CEO - Sarah Chen
- **Focus**: Strategy, vision, competitive advantage
- **Style**: Visionary, direct, occasionally challenging
- **Questions**: Market positioning, long-term viability, stakeholder value

### CFO - Michael Rodriguez  
- **Focus**: Financial metrics, ROI, risk management
- **Style**: Analytical, data-driven, skeptical
- **Questions**: Cost justification, revenue impact, financial projections

### CTO - Dr. Lisa Wang
- **Focus**: Technical feasibility, scalability, innovation
- **Style**: Detailed, technical, forward-thinking
- **Questions**: Implementation complexity, technical debt, security

### CMO - James Thompson
- **Focus**: Customer impact, market positioning, brand
- **Style**: Creative, customer-focused, enthusiastic
- **Questions**: Customer perception, market response, differentiation

### COO - Rebecca Johnson
- **Focus**: Operations, implementation, efficiency
- **Style**: Practical, process-focused, results-oriented
- **Questions**: Operational impact, resource allocation, timelines

## Customization

### Adding New Executives
Edit `app.py` and add new personas to the `ExecutiveAgent.personas` dictionary:

```python
'ROLE': {
    'name': 'Executive Name',
    'title': 'Full Title',
    'personality': 'Key traits',
    'focus_areas': ['Area1', 'Area2'],
    'communication_style': 'How they communicate',
    'typical_concerns': ['Concern1', 'Concern2'],
    'interruption_likelihood': 0.6,  # 0.0 to 1.0
    'question_types': ['type1', 'type2']
}
```

### Modifying Question Banks
Update the `questions_bank` dictionary in the `generate_question` method to add industry-specific or role-specific questions.

### Integrating Real AI
Replace the mock question generation with actual OpenAI API calls:

```python
def generate_question(self, context: str, question_type: str = 'general') -> str:
    persona = self.personas.get(self.role, {})

    prompt = f'''
    You are {persona['name']}, the {persona['title']} of {self.company_context['name']}.
    Your personality: {persona['personality']}
    Your focus areas: {', '.join(persona['focus_areas'])}

    The student just presented: {context}

    Ask a thoughtful, challenging question that a real {self.role} would ask.
    Keep it professional but probe for specifics.
    '''

    response = openai.Completion.create(
        engine="gpt-4",
        prompt=prompt,
        max_tokens=150,
        temperature=0.7
    )

    return response.choices[0].text.strip()
```

## Technical Architecture

- **Backend**: Flask web framework with session management
- **Frontend**: Bootstrap 5, vanilla JavaScript, responsive design  
- **AI Integration**: OpenAI GPT API for question generation
- **Data Storage**: Session-based (can be extended to database)
- **Styling**: Custom CSS with executive-specific theming

## File Structure

```
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.template         # Environment configuration template
├── templates/
│   └── index.html        # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── app.js        # Frontend JavaScript
└── README.md            # This file
```

## Development Notes

### Current Implementation
- Uses predefined question banks for fast prototyping
- Simulates AI responses without external API calls
- Stores data in Flask sessions (temporary)

### Production Enhancements
1. **Real AI Integration**: Connect to OpenAI, Claude, or other LLMs
2. **Database Storage**: Save sessions, conversations, and analytics
3. **User Authentication**: Student/instructor login system
4. **Advanced Analytics**: Performance tracking, improvement metrics
5. **Multi-tenancy**: Support multiple classes and institutions
6. **Real-time Features**: WebSocket support for live presentations

## Troubleshooting

### Common Issues
- **Port 5000 in use**: Change port in `app.py` or kill existing processes
- **API Key errors**: Verify `.env` file setup and valid OpenAI key
- **Session errors**: Clear browser cache and restart server
- **Style issues**: Check static file serving and Bootstrap CDN

### Performance Tips
- Use local AI models for faster responses in development
- Implement caching for frequently asked questions
- Optimize conversation history storage
- Add pagination for long sessions

## Educational Benefits

- **Realistic Practice**: Simulates actual boardroom dynamics
- **Safe Environment**: Students can make mistakes without consequences
- **Unlimited Practice**: Available 24/7 for student preparation
- **Personalized Feedback**: Tailored suggestions for improvement
- **Scalable**: Handles multiple student sessions simultaneously

## Future Enhancements

- Voice interaction capabilities
- Video presentation analysis
- Industry-specific executive knowledge bases
- Integration with learning management systems
- Multiplayer sessions with student teams
- Advanced analytics and reporting

## License

This project is for educational use. Modify and distribute freely for academic purposes.

## Support

For questions or issues:
1. Check the troubleshooting section
2. Review the code comments
3. Test with different browsers
4. Verify API key configuration

---

Built with ❤️ for better business education
