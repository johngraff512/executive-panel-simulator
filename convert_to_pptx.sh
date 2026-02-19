#!/bin/bash

# Convert AI Executive Panel Simulator presentation to PowerPoint
# Usage: ./convert_to_pptx.sh

echo "=================================="
echo "Converting Presentation to PowerPoint"
echo "=================================="
echo ""

# Check if Marp CLI is installed
if ! command -v marp &> /dev/null
then
    echo "❌ Marp CLI not found"
    echo ""
    echo "To install Marp CLI, run:"
    echo "  npm install -g @marp-team/marp-cli"
    echo ""
    echo "Or use one of the alternative methods in CONVERT_TO_POWERPOINT.md"
    exit 1
fi

echo "✅ Marp CLI found"
echo ""

# Check if input file exists
if [ ! -f "PRESENTATION_MARP.md" ]; then
    echo "❌ PRESENTATION_MARP.md not found"
    echo "Make sure you're running this from the executive-panel-simulator directory"
    exit 1
fi

echo "✅ PRESENTATION_MARP.md found"
echo ""

# Convert to PowerPoint
echo "🔄 Converting to PowerPoint..."
echo ""

OUTPUT_FILE="AI_Executive_Panel_Presentation.pptx"

marp PRESENTATION_MARP.md --pptx --allow-local-files -o "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Success! PowerPoint file created:"
    echo "   $OUTPUT_FILE"
    echo ""
    echo "Next steps:"
    echo "1. Open the .pptx file in PowerPoint"
    echo "2. Apply University of Texas branding"
    echo "3. Add your name and presentation date"
    echo "4. Insert screenshots (see SCREENSHOT_GUIDE.md)"
    echo "5. Customize colors to Texas Orange (#BF5700)"
    echo ""
    echo "See CONVERT_TO_POWERPOINT.md for detailed customization instructions"
else
    echo ""
    echo "❌ Conversion failed"
    echo ""
    echo "Try these alternatives:"
    echo "1. Use Marp for VS Code extension (visual editor)"
    echo "2. Use online converter at https://www.markdowntoslides.com/"
    echo "3. Manually create slides using PRESENTATION.md as guide"
    echo ""
    echo "See CONVERT_TO_POWERPOINT.md for detailed instructions"
    exit 1
fi
