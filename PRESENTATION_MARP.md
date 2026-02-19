---
marp: true
theme: default
paginate: true
backgroundColor: #fff
backgroundImage: url('https://marp.app/assets/hero-background.svg')
style: |
  section {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }
  h1 {
    color: #BF5700;
  }
  h2 {
    color: #333D29;
  }
  .columns {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
  }
---

<!-- _class: lead -->

# AI Executive Panel Simulator
## Transforming Strategic Management Education Through AI

**McCombs School of Business**
University of Texas at Austin

---

# Presentation Outline

- The Challenge in Strategic Management Education
- Our AI-Powered Solution
- Student Value Proposition
- How It Works
- **Live Demonstration**
- Impact & Future Directions

---

<!-- _class: lead -->

# The Strategic Management Presentation Challenge

---

# What Our Students Face

**The Reality**:
- Required to present business plans to simulated executive panels
- Must defend strategic choices, analyses, and assumptions
- Need practice before high-stakes presentations
- Limited access to experienced executives

**The Problem**:
- ❌ Live executive panels don't scale
- ❌ Peer feedback lacks executive-level scrutiny
- ❌ Students get only 1-2 practice opportunities
- ❌ No way to practice 24/7 on demand
- ❌ Difficult to ensure consistent rigor across all students

> *"Students need more than one shot to learn how to defend their strategic thinking."*

---

# Traditional Approaches & Limitations

| Approach | Benefits | Limitations |
|----------|----------|-------------|
| **Live Executive Panels** | Authentic, Real expertise | Expensive, Doesn't scale |
| **Peer Review** | Accessible, Collaborative | Lacks executive perspective |
| **Instructor Feedback** | Expert guidance | Time-intensive, Limited availability |
| **Self-Practice** | Convenient | No challenge, No feedback |

**The Gap**: Students need **realistic, rigorous, on-demand practice**

---

<!-- _class: lead -->

# Our Solution

---

# AI Executive Panel Simulator
## On-Demand Executive Practice, Powered by AI

**What It Does**:
- ✅ Analyzes complete business plans (text, tables, charts, images)
- ✅ Generates challenging questions targeting specific recommendations
- ✅ Simulates 5 distinct executive personas
- ✅ Provides unlimited practice 24/7
- ✅ Scales to entire classes

**Key Innovation**:
AI reads their actual report and challenges their specific strategic choices

> *"You're projecting 40% market share in year two, but what's your plan if competitors drop prices by 30%?"*

---

# Why Students Love It

<div class="columns">
<div>

**🎯 Realistic Practice**
- Face tough questions about actual recommendations
- Experience executive dynamics safely
- Defend choices with specific data

**⏰ Available 24/7**
- Practice whenever ready
- No scheduling constraints
- Unlimited attempts

</div>
<div>

**📊 Comprehensive Analysis**
- Reads entire business plan (150+ pages)
- Analyzes charts, tables, visual data
- Understands specific context

**💡 Learning Through Challenge**
- Identifies gaps in analysis
- Exposes weak assumptions
- Pushes deeper strategic thinking

</div>
</div>

---

# Pedagogical Benefits

<div class="columns">
<div>

**For Students**:
- ✅ Practice strategic communication
- ✅ Defend recommendations with evidence
- ✅ Build confidence
- ✅ Identify weak spots early
- ✅ Master proper terminology

</div>
<div>

**For Instructors**:
- ✅ Scalable for large classes
- ✅ Consistent, rigorous questioning
- ✅ Supplements live presentations
- ✅ Encourages deeper thinking
- ✅ Frees time for high-value interactions

</div>
</div>

---

<!-- _class: lead -->

# How It Works

---

# The Student Experience
## 4-Step Process

**1. Upload Business Plan** 📄
Drag-and-drop PDF (up to 50MB), choose preset configurations

**2. Provide Company Context** 🏢
Company name, industry, report type

**3. Select Executive Panel** 👔
Choose 1-5 executives with distinct expertise

**4. Launch Panel Session** 🚀
AI analyzes report (1-3 min), executives ask challenging questions

---

# Behind the Scenes: AI Analysis

**Hybrid Parsing System**:

**1. Text Extraction** (PyMuPDF)
165,000+ characters processed, complete documents

**2. Table Extraction** (pdfplumber)
496 tables captured in test case

**3. Visual Analysis** (GPT-4o Vision)
Top 10 charts/graphs analyzed for data and trends

**4. Strategic Extraction** (GPT-4 Turbo)
Identifies recommendations, analyses, and assumptions

---

# Intelligent Question Generation

**Traditional Approach** (Generic):
- "What's your market strategy?"
- "How will you acquire customers?"

**Our Approach** (Targeted):
- "You're projecting 40% market share in year two, but what's your plan if competitors drop prices by 30%?"
- "Your CAC analysis assumes organic growth, but how will you reach enterprise customers without a sales team?"
- "You recommend entering Asia next year, but what specific capabilities support international expansion?"

**The Difference**: References **actual numbers and proposals** from their report

---

# Meet the Executive Panel

**👔 CEO - Sarah Chen**
Strategic vision, competitive advantage, long-term growth

**💰 CFO - Michael Rodriguez**
Financial viability, ROI, profitability (analytical, skeptical)

**💻 CTO - Dr. Lisa Kincaid**
Technical feasibility, scalability, innovation

**📢 CMO - James Thompson**
Market positioning, customer acquisition, differentiation

**⚙️ COO - Rebecca Johnson**
Operations, efficiency, execution (practical, results-oriented)

---

# Version 2.0: Modern Interface

**Wizard-Based Setup**:
- 4-step guided configuration
- Visual progress tracking
- Preset panel configurations
- Drag-and-drop upload

**During Session**:
- Executive highlighting (active speaker)
- Conversation history tracking
- Professional headshots
- Smooth animations

**After Session**:
- Summary statistics
- Retry options (same company or fresh start)

---

# Advanced Capabilities

**🌐 Optional Web Research**
Real-time company/market context from Tavily API

**🔄 Intelligent Follow-ups**
AI analyzes responses, generates clarifying questions

**🔊 Text-to-Speech**
Optional voice for executive questions

**📚 Strategic Terminology Alignment**
Proper use of "strategy" vs "strategic initiatives"

---

<!-- _class: lead -->

# Live Demonstration

**Demo Flow** (~10 minutes):
1. Upload & Setup
2. Analysis Process
3. Panel Session
4. Session Summary

---

<!-- This slide is minimal - for live demo -->

# 🎬 Live Demo

## See It In Action

[Switch to live simulator]

---

# Technical Architecture

**Technology Stack**:
- Backend: Flask (Python) + Gunicorn
- AI: GPT-4 Turbo, GPT-4o Vision, TTS-1
- PDF: PyMuPDF, pdfplumber, pdf2image
- Database: SQLite
- Frontend: JavaScript + Tailwind CSS + Bootstrap
- Deployment: Heroku (globally accessible)

**Performance**:
- 150+ page documents in 1-3 minutes
- Handles concurrent sessions
- 300-second timeout for complex analysis

---

# Implementation & Adoption

**Quick Setup for Instructors**:

**Integration Options**:
- Share web link (no installation)
- Embed in Canvas/LMS
- Assign as homework

**Student Onboarding**:
- 5-minute orientation video
- No technical skills required

**Recommended Use Cases**:
- Pre-presentation practice (1-2 weeks before)
- Competition preparation
- Office hours supplement
- Self-directed learning

---

# Early Results & Student Feedback

**Pilot Observations**:

**Student Confidence** ⬆️
More prepared, reduced anxiety, better thinking on feet

**Question Quality** ⬆️
Better data preparation, thorough assumption analysis

**Strategic Thinking** ⬆️
Deeper scenario consideration, recognize weak spots early

**Student Quote**:
> *"I thought my analysis was solid until the CFO asked about my revenue assumptions. It made me go back and really justify my projections. That preparation saved me during the actual presentation."*

---

# Why This Approach?

| Solution | Scale | Realism | Available | Cost | Personal |
|----------|-------|---------|-----------|------|----------|
| Live Panels | ❌ Low | ✅ High | ❌ Limited | 💰💰💰 | ✅ High |
| Peer Review | ✅ High | ❌ Low | ✅ High | 💚 Free | ⚠️ Med |
| Instructor Q&A | ❌ Low | ✅ High | ⚠️ Med | 💰 Med | ✅ High |
| Generic AI | ✅ High | ⚠️ Med | ✅ High | 💰 Low | ❌ Low |
| **Our Simulator** | ✅ **High** | ✅ **High** | ✅ **High** | 💰 **Low** | ✅ **High** |

**Unique Value**: Combines scalability of AI with personalization of live panels

---

# Lessons Learned & Challenges

**Challenges Addressed**:

**Rate Limiting** ⚠️
Large documents exceeded API limits
→ Intelligent truncation (first 40%, middle 20%, last 40%)

**Question Quality** 📊
Early versions too generic
→ Extract specific recommendations first, then target questions

**Strategic Terminology** 📚
AI misused "strategies" for tactics
→ Explicit prompting for proper terminology

**User Experience** 🎨
Single-form overwhelming
→ 4-step wizard with visual progress

---

# Future Directions

**Short-Term** (Next 6 months):
- 📊 Performance scoring
- 📧 Session transcripts
- 🎓 Instructor dashboard
- 📱 Mobile optimization

**Medium-Term** (6-12 months):
- 🎤 Voice input
- 🎬 Video presentation analysis
- 👥 Team sessions
- 🔗 Deep LMS integration

**Long-Term** (12+ months):
- 🧠 Custom executive personas
- 📚 Industry knowledge bases
- 🌍 Multi-language support
- 🤖 Adaptive difficulty

---

# Research Opportunities

**Potential Research Questions**:

**Learning Effectiveness**:
Does AI practice improve live presentation performance?

**Skill Development**:
Which strategic thinking skills improve most?

**Technology Acceptance**:
What factors drive student adoption?

**Comparative Studies**:
AI practice vs peer practice vs no practice

**Data Available**: Session logs, usage patterns, question types, response quality

---

# Cost & Sustainability

**Ongoing Costs** (Per Semester):

**OpenAI API**: ~$2-5 per student
(Based on 3-5 sessions, 10 questions each, 150-page reports)

**Hosting**: ~$25-50/month
(Heroku, ~$100-200 per semester)

**Total Per Student**: ~$4-7 per semester

**Compare**:
- Live executive panels: $500-1000 per session
- Textbooks: $200-300 per student
- Simulation software: $50-100 per student

**Sustainability**: Highly scalable, minimal marginal cost

---

# Broader Applications

**Potential Use Cases Across McCombs**:

<div class="columns">
<div>

**Finance**
Investment pitches, Analyst Q&A

**Marketing**
Campaign proposals, Brand strategy

**Entrepreneurship**
Investor pitches, Accelerator prep

</div>
<div>

**Operations**
Process improvements, Vendor selection

**Leadership**
Crisis communication, Ethical decisions

**Cross-Disciplinary**
Capstone projects, Case competitions

</div>
</div>

---

# Getting Involved

## Spring 2026 Pilot Program 🚀

**We Provide**:
- ✅ Access to hosted simulator
- ✅ Student orientation materials
- ✅ Instructor training
- ✅ Technical support
- ✅ Usage analytics

**We Need**:
- Course section (any size)
- Assignment integration point
- Student feedback collection
- Usage data sharing (anonymized)

**Contact**: [your.email@mccombs.utexas.edu]

---

<!-- _class: lead -->

# Key Takeaways

---

# Summary

**The Challenge**:
Students need realistic practice but live panels don't scale

**Our Solution**:
AI-powered simulator with document-aware, specific questioning

**The Innovation**:
Not generic chatbot—persona-driven, pedagogically aligned

**The Impact**:
Unlimited practice, consistent rigor, builds confidence and strategic thinking

**The Opportunity**:
Pilot with your course, contribute to research, refine an innovative tool

---

<!-- _class: lead -->

# Questions & Discussion

**Thank you!**

Contact:
[Your Name]
[Email]
[Office Hours]

---

<!-- BACKUP SLIDES -->

---

# Sample Questions by Executive

**CEO - Strategic Vision**:
"Your plan assumes steady growth, but what's your strategy if we enter a recession?"

**CFO - Financial Rigor**:
"Your break-even shows month 18, but you've allocated only 6 months runway. What if acquisition takes longer?"

**CTO - Technical Feasibility**:
"You're proposing custom platform. What's the build vs buy analysis?"

**CMO - Market Positioning**:
"You claim differentiation on service, but budget shows no support team. How will this manifest?"

**COO - Operational Execution**:
"You're projecting 10x growth in year two. What processes need to scale and how?"

---

# Privacy & Data Security

**Student Data Protection**:
- ✅ No long-term storage of business plans
- ✅ Temporary processing with cleanup
- ✅ Session-based isolation
- ✅ Anonymous usage analytics only

**OpenAI API**:
- Business plans sent for analysis
- Not used for model training
- In-transit encryption (HTTPS)

**FERPA Compliance**:
- No PII stored
- Aggregated instructor data only

---

# Accessibility & Inclusion

**Current Features**:
- ✅ Responsive design (desktop/tablet/mobile)
- ✅ Keyboard navigation
- ✅ Screen reader compatible (WCAG 2.1 AA)
- ✅ Text-to-speech

**Planned**:
- 🔄 Voice input
- 🔄 Adjustable text sizes
- 🔄 Dyslexia-friendly fonts
- 🔄 Multi-language support

**Benefits for Diverse Learners**:
ESL students, introverted students, students with anxiety, remote students

---

# END

**Questions?**

Document these materials:
- FEATURES.md - Complete feature reference
- VISUAL_OVERVIEW.md - Screenshot guide
- PRESENTATION.md - Full slide deck
- SPEAKER_NOTES.md - Delivery guide

Repository: [GitHub URL]
