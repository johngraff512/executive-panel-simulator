# AI Executive Panel Simulator - Version 2

## Overview
Version 2 introduces substantial enhancements to the AI Executive Panel Simulator, enabling more comprehensive analysis of student reports and more realistic executive interactions.

## New Features

### 1. Enhanced File Handling (50MB with Vision API)

**What's New:**
- File size limit increased from 16MB to 50MB
- Vision API integration to analyze charts, graphs, and visualizations
- Comprehensive document analysis combining text AND visual elements

**Technical Implementation:**
- Uses OpenAI Vision API (GPT-4 Vision) to process PDF pages as images
- Analyzes first 5 pages with Vision API to extract insights from charts/visualizations
- Combines text extraction (PyPDF2) with visual analysis for comprehensive understanding
- Dependencies: `pdf2image`, `Pillow`

**Benefits:**
- Students can submit richer, more detailed reports with extensive visualizations
- AI can understand data from charts, graphs, tables, and infographics
- Questions based on both narrative content and data visualizations

**Code Location:**
- `app_v2.py`: `analyze_pdf_with_vision()` function (lines 90-140)

---

### 2. SQLite Database for Persistent Storage

**What's New:**
- Persistent session storage across server restarts
- Organized database schema for sessions, questions, and responses
- Ability to track historical data and statistics

**Technical Implementation:**
- SQLite database (`executive_simulator.db`)
- Three main tables:
  - `sessions`: Company info, report content, configuration
  - `questions`: Executive questions with timestamps and follow-up markers
  - `responses`: Student responses with text/audio type markers
- Database module: `database.py`

**Benefits:**
- Sessions persist across server restarts
- Better data organization and retrieval
- Foundation for future analytics features
- Scalable to PostgreSQL if needed

**Code Location:**
- `database.py`: Complete database module with all CRUD operations
- `app_v2.py`: Uses `db.` prefix for all database operations

---

### 3. Configurable Follow-up Questions

**What's New:**
- Executives can ask intelligent follow-up questions if responses need clarification
- Configurable via checkbox in setup phase
- Limited to 1 follow-up per question, only on even question numbers

**Technical Implementation:**
- AI analyzes response quality and completeness
- Determines if the specific executive would naturally ask a follow-up
- Follow-ups marked with badge in UI
- Stored in database with `is_followup` flag

**Benefits:**
- More realistic executive interactions
- Encourages students to provide complete, thoughtful responses
- Simulates real Q&A dynamics

**Configuration:**
- Setup form: "Allow Follow-up Questions" checkbox
- Behavior: Maximum 1 follow-up per original question
- Frequency: Only triggers on even question numbers (2, 4, 6, etc.)

**Code Location:**
- `app_v2.py`: `should_ask_followup()` function (lines 350-390)
- `app_v2.py`: Follow-up logic in `/respond_to_executive` route (lines 714-758)

---

### 4. Optional Web Research for Company Background

**What's New:**
- AI can research the company online before generating questions
- Provides more informed, contextual questions based on real company data
- Configurable via checkbox in setup phase

**Technical Implementation:**
- Uses OpenAI to research and summarize company information
- Gathers: company overview, recent news, financial performance, industry position
- Research summary stored in database
- Used as context when generating questions

**Benefits:**
- More relevant questions for real companies
- Incorporates current events and market conditions
- Better preparation for realistic case discussions

**Configuration:**
- Setup form: "Enable Web Research" checkbox
- Best for: Real companies (public or well-known private)
- Optional: Works fine without research for fictional companies

**Code Location:**
- `app_v2.py`: `research_company_online()` function (lines 225-250)

---

### 5. Executive Headshot Images

**What's New:**
- Professional headshot images for each executive
- Displayed alongside questions in the conversation
- Visual identification of current speaker

**Executives:**
- **Sarah Chen** (CEO) - Orange avatar with "SC"
- **Michael Rodriguez** (CFO) - Blue avatar with "MR"
- **Dr. Lisa Kincaid** (CTO) - Purple avatar with "LK"
- **James Thompson** (CMO) - Green avatar with "JT"
- **Rebecca Johnson** (COO) - Brown avatar with "RJ"

**Implementation:**
- Placeholder images: Colored circles with initials (created automatically)
- AI-generated option: Script to generate photorealistic headshots with DALL-E 3
- Images stored in `/static/images/executives/`

**To Generate AI Headshots:**
```bash
# Ensure OPENAI_API_KEY is set in environment
python generate_headshots.py
```

**Code Location:**
- Images: `/static/images/executives/*.png`
- Generator script: `generate_headshots.py`
- Placeholder script: `create_placeholder_headshots.py`
- Frontend display: `templates/index.html` (lines 1056-1078)
- CSS: `templates/index.html` (lines 344-390)

---

## Updated Architecture

### File Structure
```
executive-panel-simulator/
├── app.py                          # Original version (kept for reference)
├── app_v2.py                       # Version 2 with all new features
├── database.py                     # SQLite database module
├── generate_headshots.py           # DALL-E 3 headshot generator
├── create_placeholder_headshots.py # Placeholder headshot generator
├── executive_simulator.db          # SQLite database (created at runtime)
├── requirements.txt                # Updated dependencies
├── Procfile                        # Updated to use app_v2
├── templates/
│   └── index.html                  # Updated UI with new features
└── static/
    └── images/
        └── executives/             # Executive headshot images
            ├── sarah_chen.png
            ├── michael_rodriguez.png
            ├── lisa_kincaid.png
            ├── james_thompson.png
            └── rebecca_johnson.png
```

### New Dependencies
```
pdf2image==1.16.3    # PDF to image conversion for Vision API
Pillow==10.1.0       # Image processing
beautifulsoup4==4.12.2  # Web scraping (future enhancement)
requests==2.31.0     # HTTP requests
lxml==4.9.3          # HTML parsing
```

### API Costs Consideration
Version 2 features increase OpenAI API usage:
- **Vision API**: ~$0.01-0.03 per report (5 pages analyzed)
- **Follow-up questions**: ~$0.001 per follow-up
- **Web research**: ~$0.002 per company research
- **DALL-E 3 headshots**: ~$0.04 per headshot (one-time cost)

**Typical session cost**: $0.02-0.05 (vs. ~$0.01 in Version 1)

---

## Migration from Version 1

### Automatic Migration
Version 2 runs alongside Version 1. To switch:

1. **Backend**: Procfile already updated to use `app_v2.py`
2. **Database**: Created automatically on first run
3. **Images**: Placeholder headshots created automatically

### To Keep Using Version 1
Edit `Procfile`:
```
web: gunicorn app:app -b 0.0.0.0:$PORT
```

---

## Configuration Guide

### Setup Phase Options

**Standard Options (Version 1):**
- Company Name
- Industry
- Report Type
- Executive Panel Selection (2-5 executives)
- Session Limit (6, 10, 15, or 20 questions)

**New Options (Version 2):**
- ✅ **Allow Follow-up Questions**: Enable intelligent follow-ups (recommended for advanced students)
- ✅ **Enable Web Research**: Research real companies online (recommended for case studies on real firms)

### Recommended Settings

**For Fictional Companies / Startups:**
- Follow-ups: Optional (can be enabled)
- Web Research: Disabled (no online data available)

**For Real Company Case Studies:**
- Follow-ups: Enabled (more realistic)
- Web Research: Enabled (incorporates current context)

**For Practice Sessions:**
- Follow-ups: Disabled (faster sessions)
- Web Research: Disabled (focus on submitted content only)

---

## User Experience Improvements

### Visual Enhancements
1. **Executive Headshots**: Easier visual identification of speakers
2. **Follow-up Badges**: Clear indication of follow-up questions
3. **Improved Message Layout**: Better spacing and visual hierarchy

### Functional Improvements
1. **Larger Files**: Support for comprehensive reports with many charts
2. **Smarter Questions**: Context from both text and visualizations
3. **More Realistic**: Follow-ups create authentic Q&A dynamics
4. **Current Context**: Web research ensures questions reflect recent events

### Performance
- Vision API: Adds ~5-10 seconds to initial upload
- Database: Slightly faster than in-memory for large sessions
- Overall: Comparable speed to Version 1

---

## Troubleshooting

### Issue: "Vision API analysis failed"
**Solution**: Vision API is optional. Text analysis will continue without it.

### Issue: "Database error"
**Solution**: Delete `executive_simulator.db` to recreate fresh database.

### Issue: "Headshots not displaying"
**Solution**: Run `python create_placeholder_headshots.py` to regenerate placeholders.

### Issue: "File too large" with 30MB file
**Solution**: Check `app_v2.py` line 17 - MAX_CONTENT_LENGTH should be 50MB.

### Issue: "Web research not working"
**Solution**: Ensure OPENAI_API_KEY is set. Research fails gracefully if unavailable.

---

## Future Enhancements (Potential Version 3)

1. **Multi-language Support**: Questions and responses in multiple languages
2. **Custom Executives**: Allow users to define custom executive roles
3. **Session Analytics**: Dashboard showing performance metrics
4. **Video Responses**: Support for video question delivery
5. **Collaborative Sessions**: Multiple students in same panel
6. **LLM Fine-tuning**: Industry-specific questioning styles

---

## Credits

**Version 2 Development:**
- Enhanced PDF processing with Vision API
- SQLite database architecture
- Intelligent follow-up question system
- Web research integration
- Executive headshot system

**Original Concept:**
McCombs School of Business - AI-Enhanced Business Education

---

## Support

For issues or questions about Version 2:
1. Check this documentation
2. Review `app_v2.py` inline comments
3. Consult database schema in `database.py`

---

**Version**: 2.0
**Release Date**: December 2025
**Compatibility**: Backward compatible with Version 1 reports
