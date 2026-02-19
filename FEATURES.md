# AI Executive Panel Simulator - Features & Functionality

**Version 2.0** - Enhanced with comprehensive PDF analysis, modern UI, and intelligent question generation

---

## Overview

The AI Executive Panel Simulator is an educational tool designed for Strategic Management courses that simulates a realistic executive panel review session. Students upload their business plans or strategic reports, and AI-powered executives ask challenging, specific questions that probe their recommendations, analyses, and assumptions.

---

## Core Features

### 1. Comprehensive PDF Analysis

#### Hybrid Parsing System
The simulator uses a multi-method approach to extract complete document content:

- **PyMuPDF (fitz)**: Fast text extraction and embedded image detection from all pages
- **pdfplumber**: Advanced table detection and structured data extraction
- **OpenAI Vision API (GPT-4o)**: Analyzes charts, graphs, diagrams, and visual content

#### Full Document Coverage
- **Complete text extraction**: No character limits - analyzes entire document regardless of length
- **Top 10 image analysis**: Automatically identifies and analyzes the 10 largest/most important embedded images
- **All tables extracted**: Captures financial data, projections, and structured information
- **High-detail analysis**: Vision API uses "high" detail mode for maximum accuracy on charts and graphs

#### What Gets Analyzed
- Text content from all pages
- Financial tables and data grids
- Charts and graphs (bar, line, pie, etc.)
- Diagrams and process flows
- Business model canvases
- Competitive matrices
- Any other visual elements

---

### 2. Intelligent Question Generation

#### Strategic Recommendation Extraction
Instead of asking generic questions, the system identifies:

**Strategic Recommendations**: Specific actions/initiatives the student proposes
- Market entry or expansion plans
- Product/service development initiatives
- Operational improvements or changes
- Partnership or acquisition proposals
- Resource allocation decisions

**Key Analyses**: Supporting analyses that justify their strategy
- Market size/opportunity calculations
- Competitive positioning assessments
- Financial projections and assumptions
- Customer segmentation or targeting
- SWOT or capability analyses

**Critical Assumptions**: Underlying beliefs that can be challenged
- Market growth rates
- Customer adoption assumptions
- Cost or revenue assumptions
- Competitive response assumptions

#### Challenging Question Style
Executive questions now:
- **Directly reference** specific proposals from the report (with numbers and details)
- **Challenge** assumptions, feasibility, competitive dynamics, or ROI
- **Probe for gaps** in analysis or overlooked risks
- **Push students** to defend their strategic choices

**Example Questions:**
- "You're projecting 40% market share in year two, but what's your plan if competitors drop prices by 30%?"
- "Your customer acquisition cost analysis assumes organic growth, but how will you actually reach enterprise customers without a sales team?"
- "You recommend entering the Asian market next year, but what specific capabilities do you currently have for international expansion?"

---

### 3. Optional Web Research Integration

#### Real-Time Company Context
When enabled, the system uses the Tavily API to research:
- Recent company news and developments
- Market position and competitive landscape
- Industry trends and dynamics
- Recent competitor actions

#### Enhanced Question Relevance
Web research context gets injected into question generation, enabling executives to ask questions like:
- "Given your competitor's recent product launch, how will your go-to-market strategy differentiate you?"
- "I see the market contracted 15% last quarter - how does that affect your growth projections?"

---

### 4. Modern Wizard-Based UI

#### Step-by-Step Configuration
**Step 1: Upload Your Report**
- Drag-and-drop PDF upload
- Preset configurations (Full Panel, Financial Focus, etc.)
- Quick-start templates

**Step 2: Enter Company Details**
- Company name and industry selection
- Report type specification
- Context for personalized questions

**Step 3: Configure Executive Panel**
- Select 1-5 executives for your panel
- Modern animated executive cards
- Visual feedback on selection

**Step 4: Launch Session**
- Review your configuration
- Optional web research toggle
- Follow-up questions toggle
- Question limit configuration

#### Visual Progress Tracking
- 4-step progress indicator with descriptive labels
- Clear visual feedback on current step
- Validation before proceeding
- Smooth transitions between steps

---

### 5. Executive Panel Session

#### Five Distinct Executive Personas

**CEO - Sarah Chen**
- **Focus**: Strategic vision, overall business direction, long-term growth
- **Style**: Visionary, direct, occasionally challenging
- **Typical Questions**: Market positioning, competitive advantage, stakeholder value

**CFO - Michael Rodriguez**
- **Focus**: Financial viability, revenue models, costs, profitability
- **Style**: Analytical, data-driven, skeptical of assumptions
- **Typical Questions**: Revenue projections, cost structure, ROI justification

**CTO - Dr. Lisa Kincaid**
- **Focus**: Technical feasibility, technology infrastructure, innovation
- **Style**: Detailed, technical, forward-thinking
- **Typical Questions**: Implementation complexity, scalability, technical risks

**CMO - James Thompson**
- **Focus**: Market positioning, customer acquisition, competitive differentiation
- **Style**: Creative, customer-focused, enthusiastic
- **Typical Questions**: Customer perception, market response, brand positioning

**COO - Rebecca Johnson**
- **Focus**: Operational efficiency, process optimization, execution
- **Style**: Practical, process-focused, results-oriented
- **Typical Questions**: Implementation plans, resource requirements, operational impact

#### Active Executive Highlighting
During the session:
- Current speaking executive is highlighted with visual indicators
- Orange arrow (▶) shows who's asking
- Subtle background glow and border
- Smooth animations and transitions
- Helps students track who's questioning them

#### Text-to-Speech (TTS) Support
- Optional voice audio for executive questions
- Voice-matched to each executive personality
- 500-character limit for natural delivery
- Toggle on/off during session

---

### 6. Intelligent Follow-Up Questions

#### Context-Aware Follow-Ups
The system analyzes student responses and determines if clarification is needed:
- Detects vague or incomplete answers
- Identifies when new concerns are raised
- Only asks follow-ups when warranted (every other question)
- Natural conversation flow

#### Strategic Management Terminology
All questions follow proper academic terminology:
- **"Strategy"** (singular) for overall business strategy or integrated set of choices
- **"Strategic initiatives"** or **"actions"** for specific programs or activities
- Avoids misusing "strategies" (plural) to refer to tactics
- Aligns with Strategic Management course pedagogy

---

### 7. Session Summary & Analytics

#### Post-Session Review
After completing the panel session:
- **Hero section** with completion celebration
- **Session statistics**: Number of questions asked, executives participated
- **Company and report details**: Quick reference to what was reviewed
- **Modern card-based layout**: Clean, professional summary view

#### Two Restart Options

**Same Company New Session**
- Keeps company details and report
- Returns to executive selection (Step 3)
- Useful for trying different executive combinations

**Start Over Completely**
- Fresh session from scratch
- Returns to PDF upload (Step 1)
- New company and report

---

### 8. Technical Features

#### Database Integration
- **SQLite database**: Persistent storage of sessions and questions
- **Session tracking**: Company name, industry, report type, timestamp
- **Question history**: All questions and responses stored
- **Executive participation**: Track which executives asked which questions

#### Performance Optimization
- **Gunicorn configuration**: 300-second timeout for long PDF analysis
- **Graceful shutdown**: Prevents worker crashes during processing
- **2 workers**: Handles concurrent sessions
- **Keep-alive**: Maintains connections during long operations

#### File Handling
- **50MB file limit**: Supports large, detailed business plans
- **Secure uploads**: Temporary file processing and cleanup
- **Multiple format support**: PDF parsing with multiple engines

#### Analysis Time Estimation
- **Realistic expectations**: Shows "1-3 minutes" for comprehensive analysis
- **Progress feedback**: "Analyzing your report..." screen
- **Ready to launch**: Confirmation before starting panel (no immediate launch)

---

### 9. Responsive & Modern Design

#### Tailwind CSS Integration
- Modern utility-first styling (tw- prefix)
- Doesn't conflict with existing Bootstrap
- Smooth animations and transitions
- Professional gradient effects

#### Mobile-Responsive Layout
- Works on desktop, tablet, and mobile devices
- Responsive wizard navigation
- Touch-friendly executive selection
- Optimized for all screen sizes

#### Visual Design Elements
- **Texas Orange theme**: University of Texas branding (#BF5700)
- **Card-based layouts**: Modern, clean information hierarchy
- **Gradient headers**: Professional polish
- **Smooth animations**: Fade-ins, slides, pulse effects
- **Visual feedback**: Active states, hover effects, transitions

---

### 10. Educational Alignment

#### Strategic Management Focus
Designed specifically for Strategic Management courses:
- Challenges students on strategic recommendations
- Probes underlying analyses and assumptions
- Teaches proper strategic terminology
- Simulates real executive panel dynamics

#### Learning Outcomes
Students practice:
- **Defending strategic choices**: Justify recommendations with evidence
- **Thinking on their feet**: Respond to unexpected challenges
- **Handling executive pressure**: Professional communication under scrutiny
- **Identifying weak spots**: Recognize gaps in their analysis
- **Strategic thinking**: Connect recommendations to business outcomes

#### Safe Practice Environment
- **Low stakes**: Practice without real consequences
- **Immediate feedback**: Learn from tough questions
- **Unlimited attempts**: Try different approaches
- **Realistic simulation**: Authentic executive panel experience

---

## Configuration Options

### At Setup Time
- **Question Limit**: Control number of questions (default: 10)
- **Allow Follow-ups**: Enable/disable intelligent follow-up questions
- **Enable Web Research**: Add real-time company/market context
- **Executive Selection**: Choose 1-5 executives for your panel
- **Preset Configurations**: Quick templates for common scenarios

### Presets Available
1. **Full Panel**: All 5 executives (comprehensive review)
2. **Financial Focus**: CEO + CFO (financial scrutiny)
3. **Strategy & Ops**: CEO + COO (execution focus)
4. **Tech Review**: CEO + CTO (innovation focus)
5. **Market Analysis**: CEO + CMO (customer/market focus)

---

## System Requirements

### Required
- Python 3.8+
- OpenAI API key (for GPT-4 Turbo and Vision API)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Optional
- Tavily API key (for web research feature)
- Heroku or similar platform (for deployment)

### Python Dependencies
- Flask (web framework)
- OpenAI (GPT-4 and Vision API)
- PyMuPDF / fitz (PDF text extraction)
- pdfplumber (table extraction)
- pdf2image (image processing)
- Pillow (image handling)
- gunicorn (production server)
- python-dotenv (environment variables)
- tavily-python (web research)

---

## File Structure

```
executive-panel-simulator/
├── app_v2.py                    # Main Flask application (current version)
├── requirements.txt             # Python dependencies
├── Procfile                     # Gunicorn configuration
├── .env                        # Environment variables (API keys)
├── templates/
│   └── index.html              # Single-page application UI
├── static/
│   ├── ceo.jpg                 # Executive headshots
│   ├── cfo.jpg
│   ├── cto.jpg
│   ├── cmo.jpg
│   └── coo.jpg
├── sessions.db                 # SQLite database
├── README.md                   # Setup and usage guide
└── FEATURES.md                 # This document
```

---

## API Integration Details

### OpenAI APIs Used

**GPT-4 Turbo (gpt-4-turbo-preview)**
- Document analysis and key detail extraction
- Question generation
- Follow-up question evaluation

**GPT-4o (Vision)**
- Image and chart analysis
- Visual content extraction
- Graph and diagram interpretation

**TTS-1 (Text-to-Speech)**
- Voice generation for executive questions
- Executive-specific voice matching

### Tavily API (Optional)
- Real-time web search
- Company and market research
- News and trend aggregation

---

## Performance Characteristics

### Analysis Time
- **Text extraction**: 2-5 seconds (all pages)
- **Table extraction**: 3-8 seconds (depends on complexity)
- **Vision API**: 5-15 seconds per image (up to 10 images)
- **Web research**: 10-20 seconds (if enabled)
- **Total analysis**: 1-3 minutes for comprehensive report

### Question Generation
- **Per question**: 2-4 seconds
- **With follow-up evaluation**: 4-6 seconds
- **TTS generation**: 1-2 seconds per question

### Session Length
- Typical session: 5-15 minutes
- Depends on: number of questions, student response time, follow-ups

---

## Best Practices for Students

### Before Your Session
1. **Upload a complete report**: Include all analyses, recommendations, and supporting data
2. **Include visuals**: Charts, graphs, and tables make for better questions
3. **Choose relevant executives**: Select based on your report's focus
4. **Enable web research**: Get questions based on current market conditions

### During Your Session
1. **Read questions carefully**: Executives reference specific details from your report
2. **Defend with data**: Use numbers and evidence from your analysis
3. **Address assumptions**: Be prepared to justify underlying beliefs
4. **Think strategically**: Connect answers back to overall business strategy
5. **Be honest**: If you don't know, acknowledge it and explain your approach

### After Your Session
1. **Review all questions**: Identify patterns in what was challenged
2. **Strengthen weak areas**: Address gaps executives identified
3. **Update your report**: Incorporate insights from tough questions
4. **Practice again**: Try different executive combinations

---

## Version History

### Version 2.0 (Current)
- Comprehensive PDF analysis with Vision API
- Intelligent question generation targeting specific recommendations
- Modern wizard-based UI with step-by-step flow
- Executive highlighting during sessions
- Web research integration
- Strategic Management terminology alignment
- Full document analysis (no truncation)
- 10 image analysis (up from 5)

### Version 1.0
- Basic PDF text extraction
- Generic question generation
- Simple form-based UI
- 5 executive personas
- Session storage

---

## Future Enhancement Possibilities

### Short-term
- Export session transcripts (PDF/DOCX)
- Email summary reports
- Performance scoring and rubrics
- Instructor dashboard

### Long-term
- Voice input for student responses
- Video presentation analysis
- Multi-student team sessions
- LMS integration (Canvas, Blackboard, etc.)
- Custom executive personas
- Industry-specific knowledge bases

---

## Support & Documentation

### For Setup Help
See [README.md](README.md) for installation and configuration instructions.

### For Questions
- Review this document for feature details
- Check code comments in `app_v2.py`
- Test with sample PDFs first
- Verify API key configuration

---

Built for Strategic Management education at The University of Texas at Austin
