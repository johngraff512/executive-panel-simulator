"""
Executive Panel Simulator - Version 2
Enhanced with:
- 50MB file limit with Vision API support for charts/visualizations
- SQLite database for persistent storage
- Configurable follow-up questions
- Optional web research for company background
- Executive headshot images
"""

import os
import tempfile
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, Response
from werkzeug.utils import secure_filename
import PyPDF2
import fitz  # PyMuPDF
import pdfplumber
import openai
import pytz
import base64
import requests
from bs4 import BeautifulSoup
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image
import io
from io import BytesIO
import json

# Import database module
import database as db

CST = pytz.timezone('America/Chicago')

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-railway-deployment')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # ✅ 50MB for larger files

# Upload configuration
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_AUDIO_EXTENSIONS = {'webm', 'mp3', 'wav', 'm4a', 'ogg'}

# Initialize OpenAI client
openai_client = None
openai_available = False

try:
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        openai_client = openai.OpenAI(api_key=api_key)
        openai_available = True
        print("✅ OpenAI API key found - AI-powered questions enabled")
    else:
        print("⚠️  No OpenAI API key found - running in demo mode")
except Exception as e:
    print(f"❌ OpenAI initialization failed: {e}")
    import traceback
    traceback.print_exc()
    openai_available = False

# Executive Management
EXECUTIVE_NAMES = {
    'CEO': 'Sarah Chen',
    'CFO': 'Michael Rodriguez',
    'CTO': 'Dr. Lisa Kincaid',
    'CMO': 'James Thompson',
    'COO': 'Rebecca Johnson'
}

EXECUTIVE_IMAGE_MAPPING = {
    'CEO': 'sarah_chen',
    'CFO': 'michael_rodriguez',
    'CTO': 'lisa_kincaid',
    'CMO': 'james_thompson',
    'COO': 'rebecca_johnson'
}

def get_session_id():
    """Get or create a session ID for the current user"""
    if 'sid' not in session:
        import uuid
        session['sid'] = str(uuid.uuid4())
    return session['sid']

def get_executive_name(role):
    """Get the name for an executive role"""
    return EXECUTIVE_NAMES.get(role, role)

def get_executive_image(role):
    """Get the image filename for an executive"""
    return EXECUTIVE_IMAGE_MAPPING.get(role, 'sarah_chen')

def get_next_executive(selected_executives, current_count):
    """Rotate through executives evenly"""
    if not selected_executives:
        return 'CEO'
    index = (current_count - 1) % len(selected_executives)
    return selected_executives[index]

# ========== NEW: Vision API for PDF Analysis ==========
def analyze_pdf_with_vision(pdf_path, company_name, industry, report_type):
    """
    Analyze PDF using Vision API to extract text AND visual elements
    Returns comprehensive analysis including charts, graphs, tables, etc.
    """
    if not openai_available or not openai_client:
        return None, None

    try:
        print(f"🔍 Analyzing PDF with Vision API...")

        # Convert PDF to images (first 3 pages to manage costs and time)
        images = convert_from_path(pdf_path, first_page=1, last_page=3)
        print(f"📄 Converted {len(images)} pages to images")

        all_analysis = []

        # Analyze each page with Vision API
        for i, img in enumerate(images[:3], 1):  # Limit to first 3 pages for speed
            print(f"   Analyzing page {i}...")

            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            # Encode image to base64
            img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

            # Call Vision API (using gpt-4o which supports vision)
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Analyze this page from a {report_type} for {company_name} in the {industry} industry. Extract key business insights, data points from charts/graphs/tables, and strategic information. Be specific and comprehensive."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}",
                                    "detail": "low"  # Use "low" for faster processing
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500  # Reduced for faster response
            )

            page_analysis = response.choices[0].message.content
            all_analysis.append(f"Page {i}: {page_analysis}")
            print(f"   ✅ Page {i} analyzed")

        # Combine all analysis
        full_analysis = "\n\n".join(all_analysis)
        print(f"✅ Vision analysis complete: {len(full_analysis)} characters")

        return full_analysis, len(images)

    except Exception as e:
        print(f"❌ Vision API error: {e}")
        import traceback
        traceback.print_exc()
        return None, None

# ========== Enhanced PDF Processing with PyMuPDF + pdfplumber ==========
def extract_text_and_images_with_pymupdf(pdf_bytes):
    """Extract text and images using PyMuPDF (fast and comprehensive)"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_content = ""
        images = []

        print(f"📄 Processing {len(doc)} pages with PyMuPDF...")

        for page_num, page in enumerate(doc):
            # Extract text with better formatting
            page_text = page.get_text("text")
            text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"

            # Extract images from this page
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    images.append({
                        'page': page_num + 1,
                        'index': img_index,
                        'bytes': image_bytes,
                        'ext': image_ext,
                        'size': len(image_bytes)
                    })
                except Exception as e:
                    print(f"⚠️ Could not extract image {img_index} from page {page_num + 1}: {e}")

        print(f"✅ PyMuPDF: Extracted {len(text_content)} chars of text and {len(images)} images")
        return text_content.strip(), images

    except Exception as e:
        print(f"❌ PyMuPDF extraction error: {e}")
        import traceback
        traceback.print_exc()
        return None, []

def extract_tables_with_pdfplumber(pdf_bytes):
    """Extract tables using pdfplumber (best table detection)"""
    try:
        tables_data = []

        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            print(f"📊 Scanning {len(pdf.pages)} pages for tables with pdfplumber...")

            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()

                if tables:
                    for table_index, table in enumerate(tables):
                        if table and len(table) > 0:
                            tables_data.append({
                                'page': page_num + 1,
                                'index': table_index,
                                'data': table,
                                'rows': len(table),
                                'cols': len(table[0]) if table else 0
                            })

        print(f"✅ pdfplumber: Found {len(tables_data)} tables")
        return tables_data

    except Exception as e:
        print(f"❌ pdfplumber table extraction error: {e}")
        import traceback
        traceback.print_exc()
        return []

def analyze_images_with_vision(images, max_images=5):
    """Analyze important embedded images using OpenAI Vision API"""
    if not openai_available or not openai_client:
        print("⚠️ OpenAI not available - skipping image analysis")
        return []

    if not images:
        return []

    try:
        # Sort images by size and take the largest ones (likely most important)
        sorted_images = sorted(images, key=lambda x: x['size'], reverse=True)
        images_to_analyze = sorted_images[:max_images]

        print(f"🖼️ Analyzing {len(images_to_analyze)} embedded images with Vision API...")

        image_descriptions = []

        for img in images_to_analyze:
            try:
                # Convert image bytes to base64
                img_b64 = base64.b64encode(img['bytes']).decode('utf-8')

                # Determine image format
                mime_type = f"image/{img['ext']}" if img['ext'] in ['png', 'jpeg', 'jpg', 'gif', 'webp'] else "image/png"

                # Analyze with Vision API
                response = openai_client.chat.completions.create(
                    model="gpt-4o",  # Using GPT-4o for vision
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image from a business report. Describe what it shows (chart, graph, diagram, etc.), extract any visible data or trends, and explain its business significance. Be concise but thorough."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{img_b64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }],
                    max_tokens=500
                )

                description = response.choices[0].message.content
                image_descriptions.append({
                    'page': img['page'],
                    'description': description
                })

                print(f"✅ Analyzed embedded image from page {img['page']}")

            except Exception as e:
                print(f"⚠️ Could not analyze image from page {img['page']}: {e}")

        return image_descriptions

    except Exception as e:
        print(f"❌ Vision API error: {e}")
        import traceback
        traceback.print_exc()
        return []

def format_tables_for_analysis(tables_data):
    """Format extracted tables into readable text for AI analysis"""
    if not tables_data:
        return "No tables found in document."

    formatted = f"\n\n=== TABLES EXTRACTED ({len(tables_data)} found) ===\n"

    for table_info in tables_data:
        formatted += f"\n--- Table on Page {table_info['page']} ({table_info['rows']} rows × {table_info['cols']} cols) ---\n"

        table = table_info['data']
        # Format as markdown-style table
        for row_idx, row in enumerate(table[:10]):  # Limit to first 10 rows per table
            if row:
                formatted += " | ".join([str(cell) if cell else "" for cell in row]) + "\n"

        if len(table) > 10:
            formatted += f"... ({len(table) - 10} more rows)\n"

    return formatted

def format_images_for_analysis(image_descriptions):
    """Format image descriptions for AI analysis"""
    if not image_descriptions:
        return "No embedded images analyzed."

    formatted = f"\n\n=== IMAGES/CHARTS ANALYZED ({len(image_descriptions)} found) ===\n"

    for img in image_descriptions:
        formatted += f"\n--- Image/Chart on Page {img['page']} ---\n"
        formatted += f"{img['description']}\n"

    return formatted

def comprehensive_pdf_extraction(pdf_file, analyze_images_flag=True):
    """
    Comprehensive PDF extraction combining PyMuPDF, pdfplumber, and Vision API

    Returns:
        dict: {
            'text': str,
            'tables': list,
            'images': list,
            'image_descriptions': list,
            'combined_content': str  # Formatted for AI analysis
        }
    """
    print("\n" + "="*60)
    print("🚀 Starting Comprehensive PDF Extraction")
    print("="*60)

    # Read PDF bytes once
    pdf_file.seek(0)
    pdf_bytes = pdf_file.read()

    # Step 1: Extract text and images with PyMuPDF
    pdf_file.seek(0)
    text_content, images = extract_text_and_images_with_pymupdf(pdf_bytes)

    # Step 2: Extract tables with pdfplumber
    tables_data = extract_tables_with_pdfplumber(pdf_bytes)

    # Step 3: Analyze embedded images with Vision API (optional, can be disabled for cost savings)
    image_descriptions = []
    if analyze_images_flag and images:
        image_descriptions = analyze_images_with_vision(images, max_images=10)

    # Step 4: Combine everything into formatted content for AI analysis
    combined_content = f"""
=== DOCUMENT TEXT CONTENT ===
{text_content}

{format_tables_for_analysis(tables_data)}

{format_images_for_analysis(image_descriptions)}
"""

    print("\n" + "="*60)
    print("✅ Comprehensive PDF Extraction Complete")
    print(f"   📝 Text: {len(text_content)} characters")
    print(f"   📊 Tables: {len(tables_data)} found")
    print(f"   🖼️ Images: {len(images)} extracted, {len(image_descriptions)} analyzed")
    print(f"   📦 Combined content: {len(combined_content)} characters")
    print("="*60 + "\n")

    return {
        'text': text_content,
        'tables': tables_data,
        'images': images,
        'image_descriptions': image_descriptions,
        'combined_content': combined_content
    }

# ========== Legacy PDF Processing (kept for backward compatibility) ==========
def extract_text_from_pdf(pdf_file):
    """Extract text content from uploaded PDF file (Legacy - use comprehensive_pdf_extraction instead)"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text_content = ""

        for page_num, page in enumerate(pdf_reader.pages):
            try:
                text_content += page.extract_text()
            except Exception as e:
                print(f"Error reading page {page_num + 1}: {e}")

        return text_content.strip()
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return None

def analyze_document_with_ai(document_text, vision_analysis, company_name, industry, report_type):
    """
    Use OpenAI to extract strategic recommendations and analyses from document
    Enhanced to identify specific proposals and analyses that can be challenged
    """
    if not openai_available or not openai_client:
        return generate_template_key_details(company_name, industry, report_type)

    try:
        # Intelligently truncate to stay under token limits (~20K tokens ≈ 80K chars)
        # Priority: beginning, end, and middle sections for comprehensive coverage
        MAX_TEXT_CHARS = 60000  # ~15K tokens
        MAX_VISION_CHARS = 20000  # ~5K tokens

        truncated_text = document_text
        if len(document_text) > MAX_TEXT_CHARS:
            # Take first 40%, last 40%, and sample from middle 20%
            first_part = document_text[:int(MAX_TEXT_CHARS * 0.4)]
            last_part = document_text[-int(MAX_TEXT_CHARS * 0.4):]
            middle_start = len(document_text) // 2 - int(MAX_TEXT_CHARS * 0.1)
            middle_part = document_text[middle_start:middle_start + int(MAX_TEXT_CHARS * 0.2)]
            truncated_text = f"{first_part}\n\n... [middle section] ...\n\n{middle_part}\n\n... [continuing] ...\n\n{last_part}"
            print(f"⚠️ Large document truncated: {len(document_text)} → {len(truncated_text)} chars for analysis")

        truncated_vision = vision_analysis
        if vision_analysis and len(vision_analysis) > MAX_VISION_CHARS:
            truncated_vision = vision_analysis[:MAX_VISION_CHARS] + "... [truncated]"
            print(f"⚠️ Vision analysis truncated: {len(vision_analysis)} → {len(truncated_vision)} chars")

        combined_content = f"TEXT CONTENT:\n{truncated_text}\n\n"
        if truncated_vision:
            combined_content += f"VISUAL ANALYSIS:\n{truncated_vision}"

        prompt = f"""Analyze this {report_type} document for {company_name} in the {industry} industry.

This document includes extracted text content, structured tables, and analyzed images/charts.

Your goal is to identify SPECIFIC STRATEGIC RECOMMENDATIONS and KEY ANALYSES that executives can challenge or clarify.

Extract 12-15 items that fall into these categories:

1. STRATEGIC RECOMMENDATIONS (specific actions/initiatives proposed):
   - Market entry or expansion plans
   - Product/service development initiatives
   - Operational improvements or changes
   - Partnership or acquisition proposals
   - Resource allocation decisions
   - Format: "Recommendation: [what they propose] - [brief justification given]"

2. KEY ANALYSES PERFORMED (analyses that support their strategy):
   - Market size/opportunity calculations
   - Competitive positioning assessments
   - Financial projections and assumptions
   - Customer segmentation or targeting
   - SWOT or capability analyses
   - Format: "Analysis: [what they analyzed] - [key finding or assumption]"

3. CRITICAL ASSUMPTIONS (underlying beliefs that could be challenged):
   - Market growth rates
   - Customer adoption assumptions
   - Cost or revenue assumptions
   - Competitive response assumptions
   - Format: "Assumption: [what they assume] - [impact if wrong]"

For each item:
- Be SPECIFIC - cite actual proposals, numbers, or findings from the document
- Reference data from tables and charts when available
- Make items questionable/challengeable (not just facts)
- Include enough detail that an executive can form a tough question

Return ONLY a JSON object: {{"key_details": ["detail1", "detail2", ...]}}

Document:
{combined_content}"""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert strategy consultant who identifies specific recommendations and analyses in business plans that executives would challenge. Extract concrete, specific items that can be questioned. You must return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000
        )

        result = json.loads(response.choices[0].message.content)
        key_details = result.get('key_details', [])
        print(f"📊 Extracted {len(key_details)} strategic recommendations and analyses for executive questioning")
        return key_details[:15]

    except Exception as e:
        print(f"AI analysis error: {e}")
        import traceback
        traceback.print_exc()
        return generate_template_key_details(company_name, industry, report_type)

def generate_template_key_details(company_name, industry, report_type):
    """Generate template key details when AI is unavailable - formatted as recommendations and analyses"""
    return [
        f"Recommendation: {company_name} proposes entering new market segments in {industry} - based on current capabilities",
        f"Analysis: Target market sizing and opportunity assessment - projects significant growth potential",
        f"Recommendation: Implement new pricing strategy to improve margins - competitive positioning approach",
        f"Assumption: Customer adoption rate will reach 25% within 18 months - critical for revenue projections",
        f"Analysis: Competitive landscape assessment - identifies key differentiators and gaps",
        f"Recommendation: Invest in technology infrastructure upgrades - required for scaling operations",
        f"Analysis: Financial projections show profitability in year 2 - assumes 30% annual growth",
        f"Assumption: Market growth rate of 15% annually - underpins revenue forecasts",
        f"Recommendation: Form strategic partnerships to accelerate market entry - reduces time to market",
        f"Analysis: Resource requirements and operational costs - detailed breakdown of investments needed",
        f"Assumption: Limited competitive response in first 12 months - window of opportunity",
        f"Recommendation: Launch customer acquisition campaign targeting early adopters - phased rollout plan"
    ]

# ========== NEW: Web Research ==========
def research_company_online(company_name):
    """
    Research company information from the web
    Returns: Dictionary with company data from various sources
    """
    if not openai_available:
        return None

    try:
        print(f"🌐 Researching {company_name} online...")

        # Use OpenAI to search and summarize company information
        search_prompt = f"""Research and provide a comprehensive summary about {company_name} including:
- Company overview and business model
- Recent news or developments (last 6 months)
- Financial performance (if publicly available)
- Industry position and competitors
- Strategic initiatives or challenges

Provide factual, verifiable information. If you don't have current information, indicate what's uncertain."""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a business research analyst providing factual company information."},
                {"role": "user", "content": search_prompt}
            ],
            temperature=0.5,
            max_tokens=600
        )

        research_summary = response.choices[0].message.content
        print(f"✅ Research complete: {len(research_summary)} characters")

        return {
            'company_name': company_name,
            'summary': research_summary,
            'researched_at': datetime.now(CST).isoformat()
        }

    except Exception as e:
        print(f"❌ Web research error: {e}")
        return None

# ========== Question Generation ==========
def generate_ai_questions_with_topic_diversity(report_content, executive, company_name,
                                               industry, report_type, all_key_details,
                                               used_topics, question_number, company_research=None,
                                               conversation_history=None):
    """
    Generate AI questions ensuring topic diversity
    Now enhanced with company research context and conversation history
    """
    if not openai_available or not openai_client:
        return generate_template_question(executive, question_number), f"topic_{question_number}"

    # Get unused topics
    unused_topics = [topic for i, topic in enumerate(all_key_details) if i not in used_topics]

    if not unused_topics:
        # All topics used, recycle
        unused_topics = all_key_details
        used_topics.clear()

    selected_topic = random.choice(unused_topics)
    topic_index = all_key_details.index(selected_topic)

    try:
        role_focus = {
            'CEO': 'strategic vision, overall business direction, and long-term growth',
            'CFO': 'financial viability, revenue models, costs, and profitability',
            'CTO': 'technical feasibility, technology infrastructure, and innovation',
            'CMO': 'market positioning, customer acquisition, and competitive differentiation',
            'COO': 'operational efficiency, process optimization, and execution'
        }

        focus = role_focus.get(executive, 'business strategy')

        # Add research context if available
        research_context = ""
        if company_research:
            research_context = f"\nRecent company research: {company_research.get('summary', '')[:300]}"

        # Format conversation history for context
        conversation_context = ""
        if conversation_history and len(conversation_history) > 0:
            conversation_context = "\n\nPREVIOUS CONVERSATION:\n"
            for i, qa in enumerate(conversation_history[-5:], 1):  # Last 5 Q&As
                conversation_context += f"\nQ{i} ({qa['executive']}): {qa['question']}\n"
                conversation_context += f"A{i}: {qa['response'][:200]}{'...' if len(qa['response']) > 200 else ''}\n"

            # Extract topics already covered
            covered_topics = set()
            for qa in conversation_history:
                # Simple keyword extraction from questions
                if 'market' in qa['question'].lower():
                    covered_topics.add('market analysis')
                if 'financial' in qa['question'].lower() or 'revenue' in qa['question'].lower():
                    covered_topics.add('financial projections')
                if 'customer' in qa['question'].lower():
                    covered_topics.add('customer acquisition')

            if covered_topics:
                conversation_context += f"\nTopics already discussed: {', '.join(covered_topics)}\n"

        prompt = f"""You are the {executive} of a company evaluating this {report_type} from {company_name} in the {industry} industry.

The presenter has made this specific recommendation or analysis:
{selected_topic}

Your role focuses on: {focus}{research_context}{conversation_context}

Generate ONE tough, probing question that CHALLENGES or CLARIFIES this specific recommendation/analysis. Your question should:

1. DIRECTLY REFERENCE what they proposed or analyzed (use specifics from the topic above)
2. NOT repeat topics already covered in previous questions (if any are listed above)
3. Build on or reference the presenter's previous responses when relevant
4. Challenge one of these aspects:
   - The underlying assumptions or logic
   - The feasibility or resource requirements
   - The competitive response or market dynamics
   - The financial projections or ROI
   - Alternative approaches they didn't consider
   - Risk factors they may have overlooked
   - Inconsistencies with their previous answers

5. Be direct and conversational (as if speaking to the presenter face-to-face)
6. Push them to defend or clarify their thinking
7. Be 1-2 sentences maximum

IMPORTANT - Strategic Management terminology:
- Use "strategy" (singular) for overall business strategy or integrated set of choices
- Use "strategic initiatives", "actions", or "initiatives" for specific programs or activities
- Avoid using "strategies" (plural) to refer to individual actions or tactics
- Examples: "What strategic initiatives..." ✓  "What strategies are you implementing..." ✗

Examples of good challenging questions:
- "You're projecting 40% market share in year two, but what's your plan if competitors drop prices by 30%?"
- "Your customer acquisition cost analysis assumes organic growth, but how will you actually reach enterprise customers without a sales team?"
- "You recommend entering the Asian market next year, but what specific capabilities do you currently have for international expansion?"

Return ONLY the question text, no preamble or explanation."""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are a tough, experienced {executive} evaluating a business plan. Your job is to identify weak spots, challenge assumptions, and push presenters to think deeper. Reference specific details from their proposal and ask pointed questions that expose gaps in their thinking. Use precise strategic management terminology: 'strategy' for overall direction, 'strategic initiatives' or 'actions' for specific programs."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=200
        )

        question = response.choices[0].message.content.strip()
        print(f"🎯 {executive} Q#{question_number} on topic: {selected_topic[:50]}...")
        return question, topic_index

    except Exception as e:
        print(f"Question generation error: {e}")
        return generate_template_question(executive, question_number), topic_index

# ========== NEW: Follow-up Question Generation ==========
def should_ask_followup(response_text, original_question, executive, question_number):
    """
    Determine if a follow-up question is warranted based on response quality
    Only asks follow-ups every other question (even question numbers)
    """
    # Only allow follow-ups on even question numbers
    if question_number % 2 != 0:
        return False, None

    if not openai_available or not openai_client or len(response_text) < 20:
        return False, None

    try:
        prompt = f"""You are the {executive} who just asked: "{original_question}"

The presenter responded: "{response_text}"

Analyze if this response adequately addresses the question. Consider if you (the {executive}) would have a natural follow-up question to clarify or dig deeper.

Return ONLY a JSON object with this exact structure:
{{
    "needs_followup": true,
    "reason": "brief reason why followup is needed",
    "followup_question": "the specific follow-up question"
}}

OR if no follow-up is needed:
{{
    "needs_followup": false,
    "reason": "response was adequate",
    "followup_question": null
}}

Only request a follow-up if the response is vague, incomplete, or raises new concerns."""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an executive deciding if clarification is needed. You must return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=200
        )

        result = json.loads(response.choices[0].message.content)

        if result.get('needs_followup') and result.get('followup_question'):
            print(f"🔄 Follow-up warranted: {result.get('reason')}")
            return True, result.get('followup_question')

        return False, None

    except Exception as e:
        print(f"Follow-up analysis error: {e}")
        return False, None

def generate_template_question(executive, question_number):
    """Generate template question when AI unavailable"""
    templates = {
        'CEO': [
            "How does this strategy align with our long-term vision?",
            "What are the key risks to this approach?",
            "How will this create sustainable competitive advantage?"
        ],
        'CFO': [
            "What are the financial implications of this plan?",
            "How will this impact our profit margins?",
            "What's the expected ROI timeline?"
        ],
        'CTO': [
            "What technology infrastructure is required?",
            "How scalable is this technical solution?",
            "What are the technical risks?"
        ],
        'CMO': [
            "How will this resonate with our target market?",
            "What's our differentiation strategy?",
            "How will we measure marketing effectiveness?"
        ],
        'COO': [
            "How will we execute this operationally?",
            "What resources are needed?",
            "What are the operational challenges?"
        ]
    }

    questions = templates.get(executive, templates['CEO'])
    return questions[(question_number - 1) % len(questions)]

def generate_closing_message(company_name, report_type):
    """Generate closing message"""
    messages = [
        f"Thank you for presenting your {report_type} for {company_name}. Your responses demonstrate strategic thinking.",
        f"Excellent presentation of {company_name}'s strategy. You've addressed our key concerns well.",
        f"Thank you for the comprehensive overview. Your {report_type} shows promise for {company_name}."
    ]
    return random.choice(messages)

# ========== TTS and Audio ==========
def generate_tts_audio(text, executive_name):
    """Generate TTS audio and return as base64 data URL"""
    if not openai_available or not openai_client:
        return None

    try:
        voice_mapping = {
            'Sarah Chen': 'nova',
            'Michael Rodriguez': 'onyx',
            'Dr. Lisa Kincaid': 'shimmer',
            'James Thompson': 'fable',
            'Rebecca Johnson': 'alloy'
        }
        voice = voice_mapping.get(executive_name, 'alloy')

        print(f"🎙️ Pre-generating TTS for {executive_name}")

        # Generate TTS (removed signal-based timeout as it conflicts with Gunicorn workers)
        tts_response = openai_client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text[:500]
        )

        audio_data = base64.b64encode(tts_response.content).decode('utf-8')
        tts_url = f"data:audio/mpeg;base64,{audio_data}"

        print(f"✅ TTS pre-generated ({len(audio_data)} bytes)")
        return tts_url

    except TimeoutError:
        print(f"⚠️ TTS timeout - skipping pre-generation")
        return None
    except Exception as e:
        print(f"⚠️ TTS pre-generation failed: {e}")
        return None

def allowed_audio_file(filename):
    """Check if uploaded file is an allowed audio format"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

def transcribe_audio_whisper(audio_file_path):
    """Transcribe audio using OpenAI Whisper API"""
    if not openai_available or not openai_client:
        return "[Audio transcription unavailable - AI not enabled]"

    try:
        print(f"🎤 Starting transcription of {audio_file_path}...")

        with open(audio_file_path, 'rb') as audio_file:
            transcription = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )

        print(f"✅ Transcription successful: {transcription.text[:100]}...")
        return transcription.text

    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return f"[Transcription failed: {str(e)}]"

# ========== ROUTES ==========
@app.route('/')
def index():
    """Render main page"""
    sid = get_session_id()
    # Don't clear session data - it's persistent in DB now
    return render_template('index.html', ai_available=openai_available)

@app.route('/upload_report', methods=['POST'])
def upload_report():
    """
    Handle PDF upload and analysis
    Now with Vision API support and optional web research
    """
    try:
        if 'report' not in request.files:
            return jsonify({'status': 'error', 'error': 'No file uploaded'})

        file = request.files['report']
        if file.filename == '':
            return jsonify({'status': 'error', 'error': 'No file selected'})

        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'status': 'error', 'error': 'Please upload a PDF file'})

        # Get form data
        company_name = request.form.get('company_name', 'Your Company')
        industry = request.form.get('industry', 'Technology')
        report_type = request.form.get('report_type', 'Business Plan')
        selected_executives = request.form.getlist('executives[]')
        question_limit = int(request.form.get('question_limit', 10))
        allow_followups = request.form.get('allow_followups', 'false') == 'true'
        enable_web_research = request.form.get('enable_web_research', 'false') == 'true'

        if not selected_executives:
            return jsonify({'status': 'error', 'error': 'Please select at least one executive'})

        print(f"📄 Processing PDF for {company_name}...")
        print(f"   Settings: followups={allow_followups}, research={enable_web_research}")

        # Save PDF temporarily for Vision API
        filename = secure_filename(file.filename)
        temp_pdf_path = os.path.join(UPLOAD_FOLDER, f"temp_{datetime.now().timestamp()}_{filename}")
        file.save(temp_pdf_path)

        try:
            # Extract comprehensive content from PDF (text, tables, embedded images)
            file.seek(0)  # Reset file pointer
            extraction_result = comprehensive_pdf_extraction(file, analyze_images_flag=True)

            if not extraction_result or not extraction_result['combined_content']:
                return jsonify({'status': 'error', 'error': 'Could not extract content from PDF'})

            # Get the enriched combined content (includes text, tables, and embedded image analysis)
            report_text = extraction_result['combined_content']

            print(f"✅ Comprehensive extraction complete: {len(report_text)} characters")
            print(f"   📊 Tables: {len(extraction_result['tables'])}, 🖼️ Images: {len(extraction_result['images'])} (analyzed: {len(extraction_result['image_descriptions'])})")

            # OPTIONAL: Also analyze full PDF pages with Vision API for additional context
            # This adds full-page visual analysis on top of embedded image analysis
            vision_analysis = None
            vision_analysis, page_count = analyze_pdf_with_vision(
                temp_pdf_path, company_name, industry, report_type
            )

            # Combine comprehensive extraction with optional full-page vision analysis
            full_content = report_text  # Already includes text + tables + embedded images
            if vision_analysis:
                full_content += f"\n\nADDITIONAL PAGE-LEVEL VISUAL ANALYSIS:\n{vision_analysis}"

            # NEW: Optional web research
            company_research = None
            if enable_web_research:
                company_research = research_company_online(company_name)

            # Analyze document to extract key details
            key_details = analyze_document_with_ai(
                report_text, vision_analysis, company_name, industry, report_type
            )

            # Generate first question
            first_executive = selected_executives[0]
            first_question, first_topic = generate_ai_questions_with_topic_diversity(
                full_content, first_executive, company_name, industry, report_type,
                key_details, [], 1, company_research,
                conversation_history=[]  # First question, no history yet
            )

            # Generate TTS for first question
            exec_name = get_executive_name(first_executive)
            first_tts_url = generate_tts_audio(first_question, exec_name)

            # Create session in database
            sid = get_session_id()
            db.create_session(
                session_id=sid,
                company_name=company_name,
                industry=industry,
                report_type=report_type,
                selected_executives=selected_executives,
                report_content=full_content,
                key_details=key_details,
                question_limit=question_limit,
                allow_followups=allow_followups,
                enable_web_research=enable_web_research,
                company_research=company_research
            )

            # Add first question to database
            db.add_question(
                session_id=sid,
                executive=first_executive,
                executive_name=exec_name,
                question_text=first_question,
                is_followup=False
            )

            # Update session with first topic used
            db.update_session(sid, used_topics=[first_topic], current_question_count=1)

            print(f"🎯 {first_executive} asking first question")
            print(f"💾 Session {sid} created in database")

            return jsonify({
                'status': 'success',
                'first_question': {
                    'executive': first_executive,
                    'name': exec_name,
                    'title': first_executive,
                    'question': first_question,
                    'timestamp': datetime.now(CST).isoformat(),
                    'tts_url': first_tts_url,
                    'image': get_executive_image(first_executive)  # NEW: Add headshot
                },
                'ai_mode': 'enabled' if openai_available else 'demo',
                'research_enabled': enable_web_research and company_research is not None
            })

        finally:
            # Clean up temp PDF file
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

    except Exception as e:
        print(f"Upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': f'Error processing file: {str(e)}'})

@app.route('/respond_to_executive', methods=['POST'])
def respond_to_executive():
    """
    Handle student text response
    Now with follow-up question support
    """
    try:
        # Get response data
        data = request.get_json()
        response_text = data.get('response', '').strip()

        if not response_text:
            return jsonify({'status': 'error', 'error': 'Please provide a response'})

        # Get session data from database
        sid = get_session_id()
        session_data = db.get_session(sid)

        if not session_data:
            return jsonify({'status': 'error', 'error': 'Session data lost. Please restart.'})

        # Store the response
        db.add_response(sid, response_text, 'text')
        print(f"📊 Stored text response for session {sid}")

        # Get current state
        current_count = session_data['current_question_count']
        question_limit = session_data['question_limit']
        allow_followups = session_data['allow_followups']

        # Get the last question asked
        questions = db.get_questions(sid)
        last_question = questions[-1] if questions else None

        # NEW: Check if follow-up is needed
        followup_needed = False
        followup_question = None

        if allow_followups and last_question and not last_question['is_followup']:
            followup_needed, followup_question = should_ask_followup(
                response_text,
                last_question['question_text'],
                last_question['executive'],
                current_count
            )

        # If follow-up is needed, ask it
        if followup_needed and followup_question:
            exec_name = last_question['executive_name']
            exec_role = last_question['executive']

            # Add follow-up question to database
            db.add_question(
                session_id=sid,
                executive=exec_role,
                executive_name=exec_name,
                question_text=followup_question,
                is_followup=True
            )

            # Generate TTS for follow-up
            tts_url = generate_tts_audio(followup_question, exec_name)

            print(f"🔄 {exec_role} asking follow-up question")

            return jsonify({
                'status': 'success',
                'follow_up': {
                    'executive': exec_role,
                    'name': exec_name,
                    'title': exec_role,
                    'question': followup_question,
                    'timestamp': datetime.now(CST).isoformat(),
                    'tts_url': tts_url,
                    'image': get_executive_image(exec_role),
                    'is_followup': True
                },
                'session_ending': False
            })

        # Otherwise, proceed to next question
        next_count = current_count + 1

        # Check if session should end
        if next_count > question_limit:
            print(f"✅ Session complete ({current_count}/{question_limit})")

            company_name = session_data['company_name']
            report_type = session_data['report_type']
            closing_message = generate_closing_message(company_name, report_type)

            tts_url = generate_tts_audio(closing_message, "Sarah Chen")

            db.update_session(sid, current_question_count=next_count)

            return jsonify({
                'status': 'success',
                'follow_up': {
                    'executive': 'CEO',
                    'name': get_executive_name('CEO'),
                    'title': 'CEO',
                    'question': closing_message,
                    'timestamp': datetime.now(CST).isoformat(),
                    'is_closing': True,
                    'tts_url': tts_url,
                    'image': get_executive_image('CEO')
                },
                'session_ending': True
            })

        # Generate next question
        selected_executives = session_data['selected_executives']
        next_exec = get_next_executive(selected_executives, next_count)
        key_details = session_data['key_details']
        used_topics = session_data['used_topics']
        company_research = session_data.get('company_research')

        # Get conversation history for context
        conversation_history = db.get_conversation_history(sid, limit=5)

        next_question, next_topic = generate_ai_questions_with_topic_diversity(
            session_data['report_content'],
            next_exec,
            session_data['company_name'],
            session_data['industry'],
            session_data['report_type'],
            key_details,
            used_topics,
            next_count,
            company_research,
            conversation_history=conversation_history
        )

        exec_name = get_executive_name(next_exec)
        tts_url = generate_tts_audio(next_question, exec_name)

        # Add question to database
        db.add_question(
            session_id=sid,
            executive=next_exec,
            executive_name=exec_name,
            question_text=next_question,
            is_followup=False
        )

        # Update session
        used_topics.append(next_topic)
        db.update_session(sid, used_topics=used_topics, current_question_count=next_count)

        print(f"🎯 {next_exec} asking question #{next_count}")

        return jsonify({
            'status': 'success',
            'follow_up': {
                'executive': next_exec,
                'name': exec_name,
                'title': next_exec,
                'question': next_question,
                'timestamp': datetime.now(CST).isoformat(),
                'tts_url': tts_url,
                'image': get_executive_image(next_exec)
            }
        })

    except Exception as e:
        print(f"Response error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': f'Error processing response: {str(e)}'})

@app.route('/respond_to_executive_audio', methods=['POST'])
def respond_to_executive_audio():
    """Handle audio response with transcription"""
    try:
        if 'audio' not in request.files:
            return jsonify({'status': 'error', 'error': 'No audio file provided'})

        audio_file = request.files['audio']

        if audio_file.filename == '':
            return jsonify({'status': 'error', 'error': 'No file selected'})

        if not allowed_audio_file(audio_file.filename):
            return jsonify({'status': 'error', 'error': 'Invalid audio file format'})

        # Save audio temporarily
        filename = secure_filename(f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        audio_file.save(filepath)

        try:
            # Transcribe audio
            transcription = transcribe_audio_whisper(filepath)

            if not transcription or transcription.startswith('['):
                return jsonify({'status': 'error', 'error': 'Failed to transcribe audio'})

            # Get session data
            sid = get_session_id()
            session_data = db.get_session(sid)

            if not session_data:
                return jsonify({'status': 'error', 'error': 'Session data lost. Please restart.'})

            # Store the response
            db.add_response(sid, transcription, 'audio')
            print(f"📊 Stored audio response for session {sid}")

            # Get current state
            current_count = session_data['current_question_count']
            question_limit = session_data['question_limit']
            allow_followups = session_data['allow_followups']

            # Get the last question asked
            questions = db.get_questions(sid)
            last_question = questions[-1] if questions else None

            # Check if follow-up is needed
            followup_needed = False
            followup_question = None

            if allow_followups and last_question and not last_question['is_followup']:
                followup_needed, followup_question = should_ask_followup(
                    transcription,
                    last_question['question_text'],
                    last_question['executive'],
                    current_count
                )

            # If follow-up is needed, ask it
            if followup_needed and followup_question:
                exec_name = last_question['executive_name']
                exec_role = last_question['executive']

                db.add_question(
                    session_id=sid,
                    executive=exec_role,
                    executive_name=exec_name,
                    question_text=followup_question,
                    is_followup=True
                )

                tts_url = generate_tts_audio(followup_question, exec_name)

                print(f"🔄 {exec_role} asking follow-up question")

                return jsonify({
                    'status': 'success',
                    'transcription': transcription,
                    'follow_up': {
                        'executive': exec_role,
                        'name': exec_name,
                        'title': exec_role,
                        'question': followup_question,
                        'timestamp': datetime.now(CST).isoformat(),
                        'tts_url': tts_url,
                        'image': get_executive_image(exec_role),
                        'is_followup': True
                    },
                    'session_ending': False
                })

            # Otherwise, proceed to next question or end session
            next_count = current_count + 1

            if next_count > question_limit:
                company_name = session_data['company_name']
                report_type = session_data['report_type']
                closing_message = generate_closing_message(company_name, report_type)

                tts_url = generate_tts_audio(closing_message, "Sarah Chen")
                db.update_session(sid, current_question_count=next_count)

                return jsonify({
                    'status': 'success',
                    'transcription': transcription,
                    'follow_up': {
                        'executive': 'CEO',
                        'name': get_executive_name('CEO'),
                        'title': 'CEO',
                        'question': closing_message,
                        'timestamp': datetime.now(CST).isoformat(),
                        'is_closing': True,
                        'tts_url': tts_url,
                        'image': get_executive_image('CEO')
                    },
                    'session_ending': True
                })

            # Generate next question
            selected_executives = session_data['selected_executives']
            next_exec = get_next_executive(selected_executives, next_count)
            key_details = session_data['key_details']
            used_topics = session_data['used_topics']
            company_research = session_data.get('company_research')

            # Get conversation history for context
            conversation_history = db.get_conversation_history(sid, limit=5)

            next_question, next_topic = generate_ai_questions_with_topic_diversity(
                session_data['report_content'],
                next_exec,
                session_data['company_name'],
                session_data['industry'],
                session_data['report_type'],
                key_details,
                used_topics,
                next_count,
                company_research,
                conversation_history=conversation_history
            )

            exec_name = get_executive_name(next_exec)
            tts_url = generate_tts_audio(next_question, exec_name)

            db.add_question(
                session_id=sid,
                executive=next_exec,
                executive_name=exec_name,
                question_text=next_question,
                is_followup=False
            )

            used_topics.append(next_topic)
            db.update_session(sid, used_topics=used_topics, current_question_count=next_count)

            print(f"🎯 {next_exec} asking question #{next_count}")

            return jsonify({
                'status': 'success',
                'transcription': transcription,
                'follow_up': {
                    'executive': next_exec,
                    'name': exec_name,
                    'title': next_exec,
                    'question': next_question,
                    'timestamp': datetime.now(CST).isoformat(),
                    'tts_url': tts_url,
                    'image': get_executive_image(next_exec)
                }
            })

        finally:
            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)

    except Exception as e:
        print(f"Audio response error: {e}")
        import traceback
        traceback.print_exc()

        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)

        return jsonify({'status': 'error', 'error': f'Error processing audio: {str(e)}'})

@app.route('/generate_tts', methods=['POST'])
def generate_tts():
    """Generate text-to-speech audio for executive questions"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        voice = data.get('voice', 'alloy')

        if not text:
            return jsonify({'status': 'error', 'error': 'No text provided'})

        if not openai_available or not openai_client:
            return jsonify({'status': 'error', 'error': 'TTS not available'})

        print(f"🎙️ Generating TTS with voice: {voice}")

        response = openai_client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            speed=1.0
        )

        audio_content = response.content
        print(f"✅ Generated {len(audio_content)} bytes of audio")

        return Response(
            audio_content,
            mimetype='audio/mpeg',
            headers={
                'Content-Disposition': 'inline; filename=question.mp3',
                'Cache-Control': 'no-cache'
            }
        )

    except Exception as e:
        print(f"❌ TTS Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/end_session', methods=['POST'])
def end_session():
    """End session and return summary data"""
    try:
        sid = get_session_id()
        session_data = db.get_session(sid)

        if not session_data:
            return jsonify({'status': 'error', 'error': 'No session data'})

        questions = db.get_questions(sid)
        responses = db.get_responses(sid)

        # Count audio vs text responses
        audio_count = sum(1 for r in responses if r['response_type'] == 'audio')
        text_count = len(responses) - audio_count

        # Get unique executives
        executives_involved = []
        for q in questions:
            exec_name = q['executive_name']
            if exec_name not in executives_involved:
                executives_involved.append(exec_name)

        summary = {
            'company_name': session_data['company_name'],
            'presentation_topic': session_data['report_type'],
            'session_type': 'questions',
            'session_limit': session_data['question_limit'],
            'total_questions': len(questions),
            'total_responses': len(responses),
            'audio_responses': audio_count,
            'text_responses': text_count,
            'executives_involved': executives_involved
        }

        return jsonify({
            'status': 'success',
            'summary': summary
        })

    except Exception as e:
        print(f"End session error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/download_transcript', methods=['GET'])
def download_transcript():
    """Generate and download session transcript as PDF"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER
        from io import BytesIO

        sid = get_session_id()
        session_data = db.get_session(sid)

        if not session_data:
            return "No session data available", 404

        questions = db.get_questions(sid)
        responses = db.get_responses(sid)

        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#BF5700'),
            spaceAfter=30,
            alignment=TA_CENTER
        )

        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333F48'),
            spaceAfter=12,
            spaceBefore=12
        )

        exec_style = ParagraphStyle(
            'Executive',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#BF5700'),
            fontName='Helvetica-Bold',
            spaceAfter=6
        )

        timestamp_style = ParagraphStyle(
            'Timestamp',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            spaceAfter=4
        )

        question_style = ParagraphStyle(
            'Question',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=20,
            spaceAfter=8
        )

        response_style = ParagraphStyle(
            'Response',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=40,
            spaceAfter=12,
            textColor=colors.HexColor('#333333')
        )

        # Title
        story.append(Paragraph("Executive Panel Session Transcript", title_style))
        story.append(Spacer(1, 0.2*inch))

        # Session Details
        session_data_table = [
            ['Company:', session_data['company_name']],
            ['Industry:', session_data['industry']],
            ['Report Type:', session_data['report_type']],
            ['Session Date:', datetime.now().strftime('%B %d, %Y')],
            ['Questions:', str(len(questions))]
        ]

        t = Table(session_data_table, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333F48')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3*inch))

        # Conversation
        story.append(Paragraph("Conversation Transcript", header_style))
        story.append(Spacer(1, 0.1*inch))

        for i, (question, response) in enumerate(zip(questions, responses), 1):
            # Question
            story.append(Paragraph(
                f"<b>{question['executive_name']}</b> ({question['executive']})",
                exec_style
            ))

            if question.get('timestamp'):
                try:
                    dt = datetime.fromisoformat(question['timestamp'].replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%I:%M:%S %p')
                    story.append(Paragraph(f"<i>{formatted_time}</i>", timestamp_style))
                except:
                    pass

            followup_marker = " [Follow-up]" if question.get('is_followup') else ""
            story.append(Paragraph(f"Q{followup_marker}: {question['question_text']}", question_style))

            # Response
            if response.get('timestamp'):
                try:
                    dt = datetime.fromisoformat(response['timestamp'].replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%I:%M:%S %p')
                    story.append(Paragraph(f"<i>{formatted_time}</i>", timestamp_style))
                except:
                    pass

            response_marker = " [Audio Response]" if response['response_type'] == 'audio' else ""
            story.append(Paragraph(f"A{response_marker}: {response['response_text']}", response_style))
            story.append(Spacer(1, 0.1*inch))

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        # Generate filename
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{session_data['company_name'].replace(' ', '_')}_Transcript_{timestamp_str}.pdf"

        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        print(f"Transcript generation error: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generating transcript: {str(e)}", 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    stats = db.get_session_stats()
    return jsonify({
        'status': 'healthy',
        'ai_available': openai_available,
        'database': stats
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
