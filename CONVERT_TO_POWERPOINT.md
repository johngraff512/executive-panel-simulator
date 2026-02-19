# Converting to PowerPoint - Step-by-Step Guide

## Quick Summary

I've created `PRESENTATION_MARP.md` which is formatted for easy conversion to PowerPoint. Here are your best options:

---

## Option 1: Marp CLI (Recommended - Best Quality)

### Step 1: Install Marp CLI

**macOS**:
```bash
npm install -g @marp-team/marp-cli
```

**Windows**:
```bash
npm install -g @marp-team/marp-cli
```

**Linux**:
```bash
npm install -g @marp-team/marp-cli
```

### Step 2: Convert to PowerPoint

```bash
cd /home/user/executive-panel-simulator
marp PRESENTATION_MARP.md --pptx -o AI_Executive_Panel_Presentation.pptx
```

### Step 3: Customize in PowerPoint

1. Open the generated `.pptx` file in PowerPoint
2. Apply University of Texas template if available
3. Add your name and presentation date
4. Insert screenshots from VISUAL_OVERVIEW guide
5. Adjust colors to match Texas Orange (#BF5700)

**Benefits**:
- ✅ Cleanest conversion
- ✅ Maintains formatting
- ✅ Editable in PowerPoint
- ✅ One command

---

## Option 2: Marp for VS Code (Visual + Export)

### Step 1: Install VS Code Extension

1. Open Visual Studio Code
2. Go to Extensions (Cmd+Shift+X or Ctrl+Shift+X)
3. Search for "Marp for VS Code"
4. Install the extension

### Step 2: Preview and Export

1. Open `PRESENTATION_MARP.md` in VS Code
2. Click the "Marp" icon in the upper right (or Cmd+K V / Ctrl+K V)
3. See live preview of slides
4. Click the three dots menu → Export Slide Deck
5. Choose "PPTX" format
6. Save as `AI_Executive_Panel_Presentation.pptx`

**Benefits**:
- ✅ Visual preview while editing
- ✅ See slides as you edit
- ✅ Easy export
- ✅ No command line needed

---

## Option 3: Online Markdown to PowerPoint Converters

### Markdown to Slides (Online)

**Website**: https://www.markdowntoslides.com/

1. Go to the website
2. Copy content from `PRESENTATION_MARP.md`
3. Paste into the editor
4. Adjust any formatting
5. Export as PowerPoint

**OR**

**Website**: https://md2googleslides.com/

1. Upload `PRESENTATION_MARP.md`
2. Convert to Google Slides
3. Download as PowerPoint from Google Slides

---

## Option 4: Manual Creation (If Tools Don't Work)

### Quick Steps:

1. **Open PowerPoint**
2. **Create Texas Orange theme**:
   - Design → Colors → Customize Colors
   - Set Accent 1 to Texas Orange (#BF5700)
   - Set Accent 2 to Texas Charcoal (#333D29)

3. **Use PRESENTATION.md as outline**:
   - Each H1 heading = new slide
   - Copy bullet points
   - Format as needed

4. **Add slide numbers**: Insert → Slide Number

5. **Insert screenshots**: Use placeholders, add images when captured

**Time estimate**: 1-2 hours for full deck

---

## Option 5: Google Slides First (Then Export)

### Using Google Slides:

1. Open Google Slides: slides.google.com
2. Create new presentation
3. Import markdown content section by section
4. Format with UT branding
5. File → Download → Microsoft PowerPoint (.pptx)

**Benefits**:
- ✅ Cloud-based
- ✅ Easy collaboration
- ✅ Auto-save
- ✅ Exports to PowerPoint

---

## Customization Checklist

After converting to PowerPoint, customize:

### Branding:
- [ ] Apply University of Texas template (if available)
- [ ] Set primary color to Texas Orange (#BF5700)
- [ ] Set secondary color to Texas Charcoal (#333D29)
- [ ] Add UT logo to title slide
- [ ] Add McCombs logo if desired

### Content:
- [ ] Add your name to title slide
- [ ] Add presentation date
- [ ] Update contact information on final slides
- [ ] Insert screenshots (use SCREENSHOT_GUIDE.md)
- [ ] Add any specific examples from your course

### Design:
- [ ] Check font sizes (readable from back of room)
- [ ] Ensure consistent formatting across slides
- [ ] Add slide numbers
- [ ] Add footer with presentation title (optional)
- [ ] Test animations (keep minimal for professionalism)

### Demo Preparation:
- [ ] Mark Slide 14 as "switch to live demo"
- [ ] Add slide notes for demo steps
- [ ] Prepare backup screenshots in case demo fails

---

## Recommended PowerPoint Settings

### Font Sizes:
- **Title**: 44pt
- **Headings**: 32pt
- **Body text**: 24pt
- **Bullet points**: 20-24pt

### Colors:
- **Texas Orange**: #BF5700 (headings, accents)
- **Texas Charcoal**: #333D29 (subheadings)
- **Dark Gray**: #333333 (body text)
- **Light Gray**: #666666 (secondary text)

### Layout:
- **Title slide**: Centered, large
- **Content slides**: Left-aligned headings, bullet points
- **Tables**: Use grid lines sparingly
- **Images**: Full-width or 2-column layout

---

## Testing Your Presentation

### Before Presenting:

1. **Test on venue equipment**:
   - Different resolution might affect layout
   - Test laptop connection to projector
   - Check slide transitions

2. **Review in presentation mode**:
   - Press F5 to start from beginning
   - Check that all text is readable
   - Verify images display correctly

3. **Practice demo transition**:
   - Practice switching from slides to browser
   - Have simulator URL bookmarked
   - Test returning to slides after demo

4. **Print speaker notes**:
   - Use SPEAKER_NOTES.md content
   - Add to PowerPoint notes section
   - Print as backup reference

---

## Troubleshooting

### Problem: Marp CLI not converting properly

**Solution 1**: Update Marp
```bash
npm update -g @marp-team/marp-cli
```

**Solution 2**: Try PDF first, then convert to PowerPoint
```bash
marp PRESENTATION_MARP.md --pdf -o temp.pdf
# Then use PDF to PowerPoint converter online
```

### Problem: Formatting looks wrong in PowerPoint

**Solution**:
1. Use PowerPoint's "Reset" feature on each slide
2. Manually adjust spacing
3. Use consistent master slide template

### Problem: Tables not converting well

**Solution**:
1. Convert markdown table to PowerPoint table manually
2. Use PowerPoint's table design features
3. Simplify complex tables into multiple slides

### Problem: Can't install Marp (no npm)

**Solution**:
1. Install Node.js first: https://nodejs.org/
2. Then install Marp CLI
3. Or use Option 3 (online converters)

---

## Quick Start Command

If you have Marp CLI installed, run this one command:

```bash
cd /home/user/executive-panel-simulator && marp PRESENTATION_MARP.md --pptx --allow-local-files -o AI_Executive_Panel_Presentation.pptx
```

This will create `AI_Executive_Panel_Presentation.pptx` ready to customize!

---

## Additional Resources

**Marp Documentation**: https://marp.app/
**Marp CLI GitHub**: https://github.com/marp-team/marp-cli
**PowerPoint Tips**: https://support.microsoft.com/en-us/powerpoint

**University of Texas Branding**: https://brand.utexas.edu/
**McCombs Branding**: https://www.mccombs.utexas.edu/about/brand

---

## Need Help?

If you encounter issues:

1. Check that Node.js is installed: `node --version`
2. Check that Marp is installed: `marp --version`
3. Try online converters as backup
4. Manual creation takes 1-2 hours but always works

---

## Final Checklist

Before your presentation:

- [ ] PowerPoint file created and customized
- [ ] UT/McCombs branding applied
- [ ] Screenshots inserted (when captured)
- [ ] Contact information updated
- [ ] Demo prepared and tested
- [ ] Backup PDF created (File → Save As → PDF)
- [ ] Speaker notes added to slides
- [ ] Tested on presentation equipment
- [ ] Backup laptop ready

**Good luck with your presentation!**
