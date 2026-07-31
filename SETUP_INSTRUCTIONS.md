# Smart Vitamin Assessment Tool - Setup Instructions

**For: Choices Pharmacy**  
**Version: 4.2.2**

---

## 🚀 EASIEST WAY - Use Online (Recommended)

**NO INSTALLATION NEEDED!**

Just visit: https://smart-vitamin.streamlit.app

Everything works in your browser. Skip to "Testing" section below.

---

## 💻 LOCAL INSTALLATION (If you prefer to run locally)

### Step 1: Install Python

1. Download Python from: https://www.python.org/downloads/
2. Choose **Python 3.10 or higher**
3. **IMPORTANT:** Check "Add Python to PATH" during installation
4. Click Install

**Verify installation:**
Open Command Prompt (Windows) or Terminal (Mac/Linux):
```bash
python --version
```
Should show: `Python 3.10.x` or higher ✓

### Step 2: Download the App Files

**Option A: Using Git (Recommended)**
```bash
git clone https://github.com/mostafashahin-sketch/smart-vitamin.git
cd smart-vitamin
```

**Option B: Manual Download**
1. Download from GitHub as ZIP
2. Extract to a folder (e.g., `C:\vitamin-app\`)
3. Open Command Prompt in that folder

### Step 3: Install Dependencies

In the Command Prompt/Terminal, run:
```bash
pip install -r requirements.txt
```

This installs:
- streamlit==1.36.0
- pandas==2.1.4
- python-dateutil==2.8.2

### Step 4: Run the App

```bash
streamlit run smart_vitamin_assessment_v4_enhanced_natmed.py
```

**Expected output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### Step 5: Open in Browser

The browser should open automatically. If not:
- Click the URL in terminal, OR
- Manually go to: http://localhost:8501

---

## 🐛 Troubleshooting Local Installation

### Problem: "Python not found"
**Solution:**
1. Python not installed - download from python.org
2. Not added to PATH:
   - Uninstall Python
   - Reinstall, check "Add Python to PATH"
   - Restart Command Prompt

### Problem: "streamlit not found"
**Solution:**
```bash
pip install streamlit==1.36.0
```

### Problem: "Port 8501 already in use"
**Solution:**
```bash
streamlit run smart_vitamin_assessment_v4_enhanced_natmed.py --server.port 8502
```

Then go to: http://localhost:8502

### Problem: "ModuleNotFoundError"
**Solution:**
```bash
pip install -r requirements.txt
```

Reinstall all dependencies.

### Problem: App loads but shows blank page
**Solution:**
1. Close the app (Ctrl + C)
2. Clear cache:
   ```bash
   python -m streamlit cache clear
   ```
3. Restart app

---

## ✅ TESTING THE APP

### Test Case 1: Young Male with Hypertension + Diabetes
**Scenario:**
- Age: 40
- Sex: Male
- Height: 170 cm
- Weight: 75 kg
- Medications: Ramipril, Metformin, Jardiance, Ozempic, Basaglar
- Conditions: Hypertension, Type 2 Diabetes

**Expected Result:**
- ❌ NO Calcium (only for F50+ or bone conditions)
- ✅ Magnesium (Grade A)
- ✅ Vitamin B12 (Grade A) - Metformin depletion risk
- ✅ Omega-3 (Grade B)

**What to check:**
- Calcium should NOT appear
- Magnesium should be Grade A at top
- B12 recommended dose shown
- All 4 tabs working

---

### Test Case 2: Pregnant Female with Comorbidities
**Scenario:**
- Age: 55
- Sex: Female
- Height: 170 cm
- Weight: 75 cm
- Pregnancy Status: **Pregnant (1st)** ← KEY
- Medications: Levothyroxine, Labetalol
- Conditions: Hypertension, Hypothyroidism

**Expected Result:**
- ✅ Folic Acid (Grade A) - pregnancy-related
- ✅ Iron (Grade A)
- ✅ Calcium (Grade A) - pregnancy-related
- ✅ Vitamin D3 (Grade A)
- ✅ Omega-3 (Grade B)
- ✅ Magnesium (Grade B)
- ✅ Selenium (Grade A) - hypothyroidism
- ✅ Zinc (Grade B) - hypothyroidism

**What to check:**
- **Folic Acid must appear** (critical!)
- At least 8 nutrients showing
- Calcium present (not filtered out because of pregnancy)
- Grade A nutrients at top
- Drug Interactions tab shows:
  - Levothyroxine needs 4-6 hours separation from Calcium & Iron

---

### Test Case 3: Post-Menopausal Female with Osteoporosis
**Scenario:**
- Age: 65
- Sex: Female
- Height: 165 cm
- Weight: 68 kg
- Pregnancy Status: Not applicable
- Medications: Alendronate, Calcium supplement
- Conditions: Osteoporosis

**Expected Result:**
- ✅ Calcium (Grade A) - bone condition (also F65)
- ✅ Vitamin D3 (Grade A)
- ✅ Vitamin K2 (Grade B)
- ✅ Magnesium (Grade B)

**What to check:**
- Calcium present (both reasons: F65 + osteoporosis)
- Vitamin K2 included (bone health)
- All Grade A at top

---

### Test Case 4: Male with Gout
**Scenario:**
- Age: 50
- Sex: Male
- Height: 175 cm
- Weight: 90 kg
- Medications: Allopurinol
- Conditions: Gout

**Expected Result:**
- ✅ Magnesium (Grade A)
- ✅ Vitamin C (Grade B)
- ✅ Quercetin (Grade B)
- ✅ Omega-3 (Grade B)
- ❌ NO Calcium

**What to check:**
- Quercetin appears (gout-specific)
- No Calcium (male without bone issues)
- Magnesium first (Grade A)

---

## 📋 Features to Verify

### Basic Functionality
- [ ] Patient info inputs work (age +/- buttons, dropdowns)
- [ ] Medications text area accepts input
- [ ] Conditions multiselect works
- [ ] Custom condition input works
- [ ] Generate Recommendations button works
- [ ] All 4 tabs accessible

### Recommendations Tab
- [ ] Nutrients sorted by Grade (A→B→C)
- [ ] Color-coded headers (🟢🟡🟠)
- [ ] Each nutrient expandable
- [ ] Shows: Grade, DRI, Dose, Mechanism, Forms, Monitoring
- [ ] Side effects warning appears (if applicable)

### Drug Interactions Tab
- [ ] NatMed Pro data displays
- [ ] Interaction severity shown
- [ ] Clinical guidance readable
- [ ] Timing requirements clear

### Evidence Tab
- [ ] References display correctly
- [ ] CPhA citations shown
- [ ] NatMed Pro credits present

### Edge Cases
- [ ] Pregnancy + comorbidities shows Folic Acid
- [ ] Calcium not over-recommended for young males
- [ ] All nutrient fields complete (no missing data)
- [ ] Multiple conditions combine nutrients correctly

---

## 🎯 Sign-Off Checklist

After testing, verify:

- [ ] All 4 test cases pass
- [ ] No error messages
- [ ] Recommendations clinically appropriate
- [ ] Evidence grades correct
- [ ] UI clear and intuitive
- [ ] All buttons functional
- [ ] Can be used without instructions

**If all checks pass:** ✅ Ready for production!

---

## 📞 Support

**During Setup:**
- Email: mostafa.shahin@example.com
- Include: Screenshot of error, what you tried

**During Testing:**
- Report findings to: Mostafa Shahin
- Include: Test case name, expected vs actual result

**Questions About Recommendations:**
- Contact Fabina Kara (Choices Pharmacy)
- Contact Mostafa Shahin (Clinical Lead)

---

## 🚀 Next Steps After Testing

1. **Feedback Collection**
   - User testing results
   - Clinical accuracy review
   - UI/UX feedback

2. **Updates & Fixes**
   - Address any issues found
   - Add suggestions
   - Optimize performance

3. **Staff Training**
   - How to enter patient info
   - How to interpret results
   - How to use drug interactions data

4. **Production Deployment**
   - Choices Pharmacy staff get access
   - Patient consultations begin
   - Track outcomes

---

## 📊 System Requirements

**For Online Version:**
- Any modern web browser
- Internet connection
- No installation needed

**For Local Version:**
- Windows 10/11, Mac OS 10.14+, or Linux
- Python 3.8 or higher
- 500 MB disk space
- Internet connection (for first install)

---

**Version: 4.2.2**  
**Last Updated: July 31, 2026**  
**Status: Ready for Testing**
