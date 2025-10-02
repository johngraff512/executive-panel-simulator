# Create a simple startup script
startup_script = """#!/bin/bash

# AI Executive Panel Simulator - Quick Start Script

echo "🚀 Starting AI Executive Panel Simulator..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo "📝 Copying template..."
    cp .env.template .env
    echo
    echo "🔧 Please edit .env and add your OpenAI API key:"
    echo "   OPENAI_API_KEY=sk-your-actual-api-key-here"
    echo
    echo "Then run this script again."
    exit 1
fi

# Start the application
echo "✅ Starting the application..."
echo "🌐 Open your browser to: http://localhost:5000"
echo
python app.py
"""

with open('start.sh', 'w') as f:
    f.write(startup_script)

# Make it executable (on Unix systems)
import os
try:
    os.chmod('start.sh', 0o755)
    print("Created executable start.sh script")
except:
    print("Created start.sh script (may need to make executable manually)")

# Create a Windows batch file too
windows_script = """@echo off
echo Starting AI Executive Panel Simulator...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is required but not installed.
    echo Please install Python 3.8 or higher and try again.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\\Scripts\\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check for .env file
if not exist ".env" (
    echo No .env file found!
    echo Copying template...
    copy .env.template .env
    echo.
    echo Please edit .env and add your OpenAI API key:
    echo    OPENAI_API_KEY=sk-your-actual-api-key-here
    echo.
    echo Then run this script again.
    pause
    exit /b 1
)

REM Start the application
echo Starting the application...
echo Open your browser to: http://localhost:5000
echo.
python app.py
pause
"""

with open('start.bat', 'w') as f:
    f.write(windows_script)

print("Created start.bat for Windows users")

# Create a simple demo data file
demo_data = """# Demo Companies and Scenarios for AI Executive Panel Simulator

## Technology Companies

### Tesla Inc.
- Industry: Electric Vehicles & Clean Energy
- Scenario: "Expanding Tesla's Supercharger network to rural areas"
- Key Concerns: Infrastructure costs, market demand, competition

### Apple Inc.  
- Industry: Consumer Electronics
- Scenario: "Launching Apple's first AR/VR headset product line"
- Key Concerns: Market readiness, pricing strategy, content ecosystem

### Microsoft Corporation
- Industry: Software & Cloud Services  
- Scenario: "Integrating AI across all Microsoft Office products"
- Key Concerns: User adoption, competitive response, data privacy

## Healthcare Companies

### Johnson & Johnson
- Industry: Pharmaceuticals & Medical Devices
- Scenario: "Digital health platform for chronic disease management"
- Key Concerns: Regulatory approval, data security, physician adoption

### Pfizer Inc.
- Industry: Pharmaceuticals
- Scenario: "Expanding vaccine production capacity globally"
- Key Concerns: Manufacturing scale, supply chain, regulatory compliance

## Financial Services

### JPMorgan Chase
- Industry: Banking & Financial Services
- Scenario: "Launching cryptocurrency trading for retail customers"  
- Key Concerns: Regulatory compliance, risk management, customer education

### Goldman Sachs
- Industry: Investment Banking
- Scenario: "AI-powered investment advisory for mass market clients"
- Key Concerns: Regulatory oversight, technology reliability, fee structure

## Retail Companies

### Amazon
- Industry: E-commerce & Cloud Computing
- Scenario: "Amazon's expansion into healthcare delivery services"
- Key Concerns: Regulatory barriers, logistics complexity, competitive response

### Walmart Inc.
- Industry: Retail
- Scenario: "Implementing autonomous delivery robots nationwide"
- Key Concerns: Technology costs, public acceptance, regulatory approval

## Sample Executive Questions by Role

### CEO Questions
- How does this initiative align with our 10-year strategic vision?
- What competitive advantages does this create that are sustainable?
- How will this impact our company culture and employee engagement?
- What's the potential market size and our realistic capture rate?

### CFO Questions  
- What's the total investment required over the next 3 years?
- What assumptions are you making about revenue recognition?
- How does this impact our debt-to-equity ratio and credit ratings?
- What's the sensitivity analysis on key financial assumptions?

### CTO Questions
- What's the technical architecture and scalability plan?
- How do we handle data security and privacy compliance?
- What are the integration requirements with existing systems?
- What's the disaster recovery and business continuity plan?

### CMO Questions
- Who is our target customer segment and what's their journey?
- How do we differentiate from competitors in the messaging?
- What's the go-to-market strategy and channel plan?  
- How do we measure success and customer satisfaction?

### COO Questions
- What's the operational impact on our current processes?
- How do we manage the change management across all departments?
- What training and support do our teams need?
- What's the implementation timeline and key milestones?
"""

with open('demo_scenarios.md', 'w') as f:
    f.write(demo_data)

print("Created demo_scenarios.md with sample companies and questions")

print("\\n" + "="*60)
print("🎉 AI Executive Panel Simulator Complete Setup")
print("="*60)
print("\\nFiles created:")
print("- app.py (Main Flask application)")
print("- templates/index.html (Web interface)")
print("- static/css/style.css (Styling)")
print("- static/js/app.js (Frontend logic)")  
print("- requirements.txt (Dependencies)")
print("- .env.template (Configuration template)")
print("- README.md (Documentation)")
print("- start.sh (Unix startup script)")
print("- start.bat (Windows startup script)")
print("- demo_scenarios.md (Sample content)")
print("\\n🚀 Quick Start:")
print("1. chmod +x start.sh && ./start.sh  (Unix/Mac)")
print("2. start.bat  (Windows)")
print("3. Or manually: pip install -r requirements.txt && python app.py")