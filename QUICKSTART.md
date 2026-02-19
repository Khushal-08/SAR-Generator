# 🚀 SAR GENERATOR - QUICK START GUIDE

## YOU'RE ALMOST THERE! Follow these steps:

---

## STEP 1: Organize Your Files (2 minutes)

Your project should look like this:

```
sar-generator/
├── data/
│   ├── sample_alerts.json                    ← Move here
│   ├── sar_templates/
│   │   └── base_template.txt                 ← Move here
│   └── knowledge_base/
│       ├── money_laundering_typologies.txt   ← Move here
│       └── pmla_guidelines.txt               ← Move here
├── app.py                                     ← Move here
├── sar_generator.py                           ← Move here
├── audit_trail.py                             ← Move here
├── requirements.txt                           ← Move here
└── create_structure.py                        ← Already have
```

### Move files to correct locations:
```bash
# First, create the structure
python create_structure.py

# Then move files
mv sample_alerts.json data/
mv base_template.txt data/sar_templates/
mv money_laundering_typologies.txt data/knowledge_base/
mv pmla_guidelines.txt data/knowledge_base/

# Move Python files to root
mv app.py .
mv sar_generator.py .
mv audit_trail.py .
mv requirements.txt .
```

---

## STEP 2: Verify Setup (1 minute)

### Check files are in place:
```bash
ls data/sample_alerts.json
ls data/sar_templates/base_template.txt
ls data/knowledge_base/money_laundering_typologies.txt
ls data/knowledge_base/pmla_guidelines.txt
ls app.py sar_generator.py audit_trail.py
```

All should exist! ✓

---

## STEP 3: Test SAR Generator (2 minutes)

```bash
# Test the core generator
python sar_generator.py
```

**Expected output:**
```
================================================================================
SAR GENERATOR - TEST MODE
================================================================================

✓ Loaded 10 sample alerts

================================================================================
GENERATING SAR FOR FIRST ALERT
================================================================================

🔄 Initializing SAR Generator with model: llama3.2
✓ LLM initialized successfully
✓ Loaded template: data/sar_templates/base_template.txt
✓ Loaded typologies: data/knowledge_base/money_laundering_typologies.txt
✓ Loaded regulations: data/knowledge_base/pmla_guidelines.txt

📄 Generating full SAR report for ALT-2026-001

🔄 Generating SAR for Alert: ALT-2026-001
  ⏳ Generating narrative with LLM...
  ✓ Narrative generated
  ✓ SAR generation complete

✓ Full SAR report generated

================================================================================
GENERATED SAR:
================================================================================
SUSPICIOUS ACTIVITY REPORT...[shows preview]

✅ TEST COMPLETE - SAR Generator is working!
```

### If you see errors:

**Error: "ollama: command not found"**
→ Install Ollama from https://ollama.ai/download

**Error: "Model not found"**
→ Download model: `ollama pull llama3.2`

**Error: "Connection refused"**
→ Start Ollama: `ollama serve`

---

## STEP 4: Run Streamlit App (1 minute)

```bash
streamlit run app.py
```

**What you should see:**
1. Browser opens automatically to http://localhost:8501
2. SAR Generator interface loads
3. You see "SAR Narrative Generator with Audit Trail" header
4. Sidebar shows system status
5. Sample alerts available in dropdown

---

## STEP 5: Generate Your First SAR (30 seconds)

In the Streamlit interface:

1. **Select a sample alert** from dropdown
   - Choose: "ALT-2026-001: Rapid Funds Movement"

2. **Click "🚀 Generate SAR"**
   - Wait 8-12 seconds
   - Watch the spinner

3. **See the magic happen!**
   - Generated SAR appears on right side
   - Shows "✅ SAR Generated in 8.2 seconds!"
   - Full narrative, indicators, typology analysis

4. **View Audit Trail**
   - Click "🔍 View Audit Trail" tab
   - See complete decision logic
   - Download audit report

---

## TROUBLESHOOTING

### Problem: Black screen in Streamlit
**Solution:** You didn't create app.py yet. Download and place app.py in root folder.

### Problem: "ModuleNotFoundError: No module named 'langchain'"
**Solution:** 
```bash
pip install -r requirements.txt
```

### Problem: "FileNotFoundError: data/sample_alerts.json"
**Solution:** Move files to correct folders (see Step 1)

### Problem: LLM generation fails
**Solution:**
```bash
# Make sure Ollama is running
ollama serve

# In another terminal, test model
ollama run llama3.2

# If works, try app again
streamlit run app.py
```

### Problem: Generation takes forever
**Solution:** 
- First generation is slow (model loading)
- Subsequent ones are faster (8-12 seconds)
- If still slow, your machine might be underpowered
- Try: `ollama pull llama3.2:3b` (smaller model)

---

## NEXT STEPS

### For Demo Video:
1. Practice generating 2-3 different SARs
2. Show the audit trail feature
3. Demonstrate editing capability
4. Time yourself (should be ~8 seconds)

### For Presentation:
1. Take screenshots of each screen
2. Record video of generation process
3. Export sample SAR as PDF
4. Export audit trail report

### For Submission:
1. Create GitHub repo (optional)
2. Add README.md
3. Upload all files
4. Include demo video link in PowerPoint

---

## EXPECTED TIMELINE

- ✅ Setup & file organization: 5 minutes
- ✅ First SAR generation: 2 minutes  
- ✅ Test all features: 10 minutes
- ✅ Practice demo: 15 minutes
- ✅ Record video: 30 minutes
- ✅ Screenshots: 15 minutes

**Total: ~1.5 hours to fully demo-ready!**

---

## SUCCESS CRITERIA

✓ Streamlit app loads without errors
✓ Can select sample alerts
✓ SAR generates in 8-15 seconds
✓ Narrative looks professional
✓ Audit trail shows decision logic
✓ Can download SAR and audit report
✓ UI looks clean and functional

---

## YOU'VE GOT THIS! 🚀

If stuck, the most common issue is:
1. Ollama not running → `ollama serve`
2. Files in wrong folders → Check Step 1
3. Dependencies not installed → `pip install -r requirements.txt`

Now go build something amazing! 💪
