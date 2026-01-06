# Screenshot Capture Guide
## For AI Executive Panel Simulator v2.0 Visual Overview

This guide provides step-by-step instructions for capturing all screenshots needed for the visual overview document.

---

## Prerequisites

1. **Running Application**: Have the simulator running locally or on Heroku
2. **Sample PDF**: Use a real business plan (158 pages works great as test case)
3. **Browser Setup**:
   - Recommended: Chrome or Firefox
   - Window size: 1920x1080 or 1440x900
   - Hide bookmarks bar for clean captures
   - Close unnecessary tabs
4. **Screenshot Tool**:
   - macOS: Cmd+Shift+4, then Space to capture window
   - Windows: Windows+Shift+S for Snipping Tool
   - Linux: gnome-screenshot or similar

---

## Screenshot Sequence

### Phase 1: Wizard Setup (Screenshots 1-4)

#### Screenshot 1: Step 1 - Upload Your Report
**File name**: `01-step1-upload.png`

**How to capture**:
1. Navigate to the simulator homepage
2. You should see Step 1 active with the wizard progress indicator at top
3. Make sure visible:
   - "1. Upload Your Report" highlighted in progress bar
   - Drag-and-drop upload zone
   - All 5 preset buttons (Full Panel, Financial Focus, etc.)
   - Modern gradient styling
4. Capture the full viewport

**What it demonstrates**: Modern file upload with preset configurations

---

#### Screenshot 2: Step 2 - Enter Company Details
**File name**: `02-step2-company-details.png`

**How to capture**:
1. Upload a PDF and advance to Step 2
2. Fill in the form:
   - Company name: "Kohl's" (or your test company)
   - Industry: Select "Retail"
   - Report type: Select "Business Plan"
3. Make sure "2. Enter Company Details" is highlighted in progress bar
4. Capture the full viewport

**What it demonstrates**: Clean form design with company context entry

---

#### Screenshot 3: Step 3 - Configure Executive Panel
**File name**: `03-step3-executive-selection.png`

**How to capture**:
1. Advance to Step 3
2. Click to select 3-4 executives (e.g., CEO, CFO, CMO, COO)
3. Selected executives should have orange borders/highlighting
4. If possible, hover over one card to show hover effect
5. Make sure "3. Configure Executive Panel" is highlighted in progress bar
6. Capture the full viewport showing all 5 executive cards

**What it demonstrates**: Interactive executive selection with modern card design

---

#### Screenshot 4: Step 4 - Review & Launch
**File name**: `04-step4-review-launch.png`

**How to capture**:
1. Advance to Step 4
2. Ensure all configurations are visible:
   - Company name and industry shown
   - Selected executives listed
   - Configuration toggles (Web Research ON, Follow-ups ON)
   - Question limit visible (default: 10)
3. Make sure "4. Launch Session" is highlighted in progress bar
4. "Analyze Report and Launch Panel" button should be prominent
5. Capture the full viewport

**What it demonstrates**: Configuration review before launching panel

---

### Phase 2: Analysis Progress (Screenshots 5-6)

#### Screenshot 5: Analysis Progress Screen
**File name**: `05-analysis-progress.png`

**How to capture**:
1. Click "Analyze Report and Launch Panel"
2. Quickly capture the "Analyzing Your Report..." screen
3. Should show:
   - Spinner/loading animation
   - "This will take 1-3 minutes" message
   - Modern loading design
4. Timing is important - capture within first few seconds

**What it demonstrates**: Professional loading state with realistic time estimates

---

#### Screenshot 6: Ready to Launch Confirmation
**File name**: `06-ready-to-launch.png`

**How to capture**:
1. Wait for analysis to complete (1-3 minutes)
2. You should see "Your Panel is Ready!" screen
3. Should show:
   - Large green checkmark icon
   - "Your Panel is Ready!" heading
   - "Launch Executive Panel" button
   - Modern hero section styling
4. Capture the full viewport

**What it demonstrates**: Clear confirmation before starting questioning

---

### Phase 3: Panel Session (Screenshots 7-9)

#### Screenshot 7: Panel Session - Active Executive
**File name**: `07-panel-session-active.png`

**How to capture**:
1. Click "Launch Executive Panel" to start session
2. Wait for first question to appear
3. Make sure visible:
   - Left sidebar with all 5 executives
   - Active executive highlighted (orange arrow ▶, glow, border)
   - The executive's question displayed prominently
   - Student response input field
   - Modern gradient header
4. Capture the full viewport

**What it demonstrates**: Executive highlighting and live questioning interface

---

#### Screenshot 8: Challenging Question Example
**File name**: `08-challenging-question.png`

**How to capture**:
1. During the panel session, wait for a particularly specific/challenging question
2. Look for questions that reference actual numbers or recommendations
3. Example: "You're projecting 40% market share in year two, but what's your plan if competitors drop prices by 30%?"
4. Ensure the question is fully visible in the conversation area
5. Active executive should be highlighted
6. Capture the full viewport

**What it demonstrates**: Specific, data-driven questions that challenge assumptions

---

#### Screenshot 9: Conversation History
**File name**: `09-conversation-history.png`

**How to capture**:
1. Answer 3-4 questions during the session
2. Each time, type a response (can be brief) and submit
3. Scroll up slightly to show multiple Q&A exchanges
4. Make sure visible:
   - Several questions from different executives
   - Student responses
   - Scrollable conversation area
   - Current active executive highlighted
5. Capture the full viewport

**What it demonstrates**: Full conversation tracking and executive rotation

---

### Phase 4: Session Summary (Screenshots 10-12)

#### Screenshot 10: Process Diagram
**File name**: `10-process-diagram.png`

**Options**:
1. **Option A**: Create a flowchart using draw.io, Lucidchart, or similar
2. **Option B**: Capture log output showing the extraction process
3. **Option C**: Create a simple text diagram and screenshot it

**Suggested Flowchart** (if creating):
```
┌─────────────────┐
│   PDF Report    │
│  (158 pages)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│     AI Analysis Extracts:           │
│                                     │
│ • Recommendation: Enter Asian       │
│   market Q2 2024 - $5M revenue      │
│                                     │
│ • Analysis: Market sized at $50M    │
│   based on competitor data          │
│                                     │
│ • Assumption: 10% penetration       │
│   achievable in year 1              │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│    Question Generated:              │
│                                     │
│ "You're planning Asian market       │
│ entry in Q2 with $5M revenue,       │
│ but what specific capabilities      │
│ support 10% penetration?"           │
└─────────────────────────────────────┘
```

**What it demonstrates**: How recommendations become targeted questions

---

#### Screenshot 11: Session Summary Screen
**File name**: `11-session-summary.png`

**How to capture**:
1. Complete the panel session (answer all questions)
2. You should land on the summary screen
3. Make sure visible:
   - Large green checkmark at top
   - "Session Complete!" heading
   - Statistics card showing:
     - Questions asked
     - Executives participated
     - Company name
     - Industry
     - Report type
   - Modern card-based layout
   - Two restart buttons at bottom
4. Capture the full viewport

**What it demonstrates**: Professional summary with session analytics

---

#### Screenshot 12: Restart Options
**File name**: `12-restart-options.png`

**How to capture**:
1. On the summary screen, scroll to show the restart buttons
2. Capture a close-up of the two button cards:
   - "Same Company New Session"
   - "Start Over Completely"
3. Both should be clearly visible with their descriptions
4. Show the modern card styling

**What it demonstrates**: Two distinct paths for continuing practice

---

### Phase 5: Comparison & Details (Screenshots 13-14)

#### Screenshot 13: Version Comparison (Optional)
**File name**: `13-version-comparison.png`

**How to capture** (if v1.0 is available):
1. Open both versions side by side
2. Show the same feature (e.g., executive selection)
3. Left: Version 1.0 (basic checkboxes)
4. Right: Version 2.0 (modern cards)
5. Use split-screen or photo editing to create side-by-side

**What it demonstrates**: Dramatic UI/UX improvements

---

#### Screenshot 14: Vision Analysis Example
**File name**: `14-vision-analysis.png`

**How to capture**:
1. **Option A**: Find a business chart in your PDF
2. Capture the chart
3. Below it, add the Vision API's analysis (from logs or create example)

**Option B**: Create a composite image showing:
- Top: Sample chart (pie/bar/line graph from business context)
- Bottom: Text box with Vision API analysis like:
  ```
  VISION API ANALYSIS:
  "This bar chart compares quarterly revenue across four product lines.
  Product A leads with $2.3M (blue bar), while Product D trails at $0.8M.
  The chart shows consistent growth in Products A and B, supporting the
  recommendation to increase investment in these lines."
  ```

**What it demonstrates**: Vision AI's ability to extract business insights from charts

---

## Screenshot Checklist

Use this checklist to ensure you've captured everything:

- [ ] 01-step1-upload.png - Wizard Step 1
- [ ] 02-step2-company-details.png - Wizard Step 2
- [ ] 03-step3-executive-selection.png - Wizard Step 3
- [ ] 04-step4-review-launch.png - Wizard Step 4
- [ ] 05-analysis-progress.png - Loading screen
- [ ] 06-ready-to-launch.png - Confirmation screen
- [ ] 07-panel-session-active.png - Active session with highlighting
- [ ] 08-challenging-question.png - Specific question example
- [ ] 09-conversation-history.png - Multiple Q&As
- [ ] 10-process-diagram.png - Recommendation → Question flow
- [ ] 11-session-summary.png - Summary screen
- [ ] 12-restart-options.png - Restart buttons
- [ ] 13-version-comparison.png - Old vs New (optional)
- [ ] 14-vision-analysis.png - Chart analysis example

---

## Image Processing Tips

After capturing screenshots:

1. **Crop appropriately**:
   - Remove browser chrome if needed
   - Focus on the relevant UI elements
   - Maintain aspect ratio

2. **Resize if needed**:
   - Max width: 1200px for document embedding
   - Maintain readability

3. **Annotate if helpful**:
   - Add arrows pointing to key features
   - Use red boxes to highlight important elements
   - Add brief labels for clarity

4. **Optimize file size**:
   - PNG for UI screenshots (better quality)
   - Compress to reasonable size (< 500KB each)
   - Use tools like TinyPNG or ImageOptim

5. **Name consistently**:
   - Use provided filenames
   - Keep numbered sequence
   - Store in /static/screenshots/ folder

---

## Inserting Screenshots into VISUAL_OVERVIEW.md

Once you have all screenshots:

1. Create a `/static/screenshots/` directory
2. Place all images there
3. In VISUAL_OVERVIEW.md, replace placeholders like:
   ```markdown
   **[SCREENSHOT PLACEHOLDER - Capture the Step 1 screen]**
   ```

   With:
   ```markdown
   ![Step 1 - Upload Your Report](./static/screenshots/01-step1-upload.png)
   ```

4. Test that all images display correctly when viewing the markdown

---

## Quick Full Capture Session

**Time needed**: ~15-20 minutes

1. **Prep** (2 min): Open simulator, have PDF ready, clear browser
2. **Wizard** (3 min): Capture screenshots 1-4 while going through steps
3. **Analysis** (3 min): Capture screenshots 5-6 during processing
4. **Session** (5 min): Capture screenshots 7-9 during active panel
5. **Summary** (2 min): Capture screenshots 11-12 at end
6. **Special** (5 min): Create screenshots 10, 14, and optionally 13

---

## Questions or Issues?

If you encounter any problems:
- Make sure you're using the latest version from `claude/pdf-parsing-enhancement-3Zbsj`
- Check that all features are enabled (web research, follow-ups)
- Use a substantial PDF (50+ pages) for realistic examples
- Retake any screenshots that don't clearly show the feature

---

**Happy Documenting!**
