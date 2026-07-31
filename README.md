# 💊 Smart Vitamin Assessment Tool v4.2.2

**Evidence-based personalized nutrient recommendations for pharmacy patients**

For: **Choices Pharmacy**  
Lead Developer: **Mostafa Shahin (RPh, CDE, PhD)**  
Evidence Base: **Canadian Pharmacists Association (CPhA) + NatMed Pro (May 2025 & March 2025)**

---

## 🚀 Quick Start (No Installation)

**Try it online now:**
👉 https://smart-vitamin.streamlit.app

Just click the link - no installation needed!

---

## ✨ Features

### Patient Assessment
- Age, sex, height, weight (with BMI calculation)
- Pregnancy status support
- Current medications (with drug-induced nutrient depletions)
- Medical conditions (40+ available)
- Custom condition input

### Personalized Recommendations
- **Sorted by Evidence Grade:**
  - 🟢 Grade A (Strong Evidence) - at top
  - 🟡 Grade B (Moderate Evidence) - in middle
  - 🟠 Grade C (Weak Evidence) - at bottom
- **Smart Calcium Logic:**
  - Only recommended for: Female 50+, bone health conditions, or malabsorption issues
  - Not recommended for young males with HTN alone
- **Pregnancy Support:**
  - Folic Acid, Iron, Calcium, Vitamin D3, Omega-3
  - All three trimesters supported
- **18+ Nutrients** with:
  - Recommended dosing
  - Forms & sources
  - Monitoring guidelines
  - Mechanism of action
  - Side effects

### Drug Interactions & Depletions
- **NatMed Pro Integration (May 2025):**
  - 12+ supplements analyzed
  - Severity ratings: MAJOR/MODERATE/MINOR
  - Clinical guidance on timing and separation
- **Drug-Induced Nutrient Depletions:**
  - PPIs → Magnesium, B12, Calcium
  - Diuretics → Potassium, Magnesium
  - Metformin → B12
  - Levothyroxine → Calcium, Iron (timing critical)
  - And more...

### Evidence & Sources
- Full reference list
- Study citations
- Clinical guidelines
- CPhA recommendations
- NatMed Pro data

---

## 📊 Test Cases

Try these scenarios to verify accuracy:

### Test 1: 40M with Hypertension + Type 2 Diabetes
**Expected Output:**
- ❌ NO Calcium (only for F50+ or bone conditions)
- ✅ Magnesium (Grade A)
- ✅ Vitamin B12 (Grade A) - Metformin depletion risk
- ✅ Omega-3 (Grade B)

### Test 2: 55F Pregnant (1st Trimester), Hypertension, Hypothyroidism
**Expected Output:**
- ✅ Folic Acid (Grade A) - from Pregnancy Status
- ✅ Iron (Grade A)
- ✅ Calcium (Grade A) - from Pregnancy Status
- ✅ Vitamin D3 (Grade A)
- ✅ Omega-3 (Grade B)
- ✅ Magnesium (Grade B)
- ✅ Selenium (Grade A) - from Hypothyroidism
- ✅ Zinc (Grade B) - from Hypothyroidism

### Test 3: 60F with Osteoporosis
**Expected Output:**
- ✅ Calcium (Grade A) - bone health condition
- ✅ Vitamin D3 (Grade A)
- ✅ Vitamin K2 (Grade B)
- ✅ Magnesium (Grade B)

---

## 💻 Local Installation (Optional)

If you want to run locally instead of using the web version:

### Requirements
- Python 3.8+ (download from python.org)
- Windows/Mac/Linux

### Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run smart_vitamin_assessment_v4_enhanced_natmed.py

# 3. Opens at http://localhost:8501
```

---

## 📁 File Structure

```
smart-vitamin/
├── smart_vitamin_assessment_v4_enhanced_natmed.py  (Main app - 900+ lines)
├── requirements.txt                                 (Dependencies)
├── README.md                                        (This file)
├── .gitignore                                       (Git config)
└── SETUP_INSTRUCTIONS.md                           (Detailed setup guide)
```

---

## 🔧 Technical Stack

- **Framework:** Streamlit 1.36.0
- **Data:** Pandas 2.1.4
- **Language:** Python 3.8+
- **Deployment:** Streamlit Cloud (free)
- **Database:** JSON (local storage for assessments)

---

## 📋 App Structure (4 Tabs)

### Tab 1: Assessment
- Patient demographics
- Medications input (comma or line separated)
- 40+ medical conditions
- Custom condition support
- Generate Recommendations button

### Tab 2: Recommendations
- Nutrients sorted by Evidence Grade
- Expandable cards for each nutrient
- Evidence grade, DRI, recommended dose
- Mechanism, forms, monitoring, side effects

### Tab 3: Drug Interactions
- NatMed Pro drug-supplement interactions
- Drug-induced nutrient depletions
- Severity ratings & clinical guidance
- Timing requirements (e.g., Levothyroxine ±4-6 hours)

### Tab 4: Evidence & Sources
- Primary evidence sources
- Study citations
- Clinical guidelines
- CPhA recommendations
- NatMed Pro data

---

## 🎯 Clinical Features

### Smart Calcium Logic
```python
Recommend Calcium if:
✓ Female AND Age ≥ 50 (post-menopausal)
✓ Has bone health condition (Osteoporosis, Bone Loss, Menopause)
✓ Has malabsorption issue (Celiac, Crohn's, GERD, IBS)
✓ Pregnant or Lactating

DO NOT recommend for:
✗ Young males with just Hypertension
✗ Young women without bone conditions
✗ Men without bone health issues
```

### Evidence Grade Sorting
- **Grade A:** Strong evidence, well-established benefits
- **Grade B:** Moderate evidence, good clinical outcomes
- **Grade C:** Weaker evidence, supportive data

---

## 📝 Medical Conditions (40+)

**Autoimmune & Inflammatory:**
- Rheumatoid Arthritis, Osteoarthritis
- Autoimmune Conditions, Chronic Inflammation
- Eczema/Dermatitis

**Metabolic & Endocrine:**
- Type 2 Diabetes, Prediabetes, Metabolic Syndrome
- Hypothyroidism, Hashimoto's, Hyperthyroidism
- PCOS

**Bone & Joint:**
- Osteoporosis, Bone Loss (Osteopenia)
- Gout

**Cardiovascular:**
- Hypertension, Cardiovascular Disease
- High Cholesterol

**GI & Absorption:**
- IBS, GERD, Celiac Disease, Crohn's Disease

**Neurological & Mental Health:**
- Migraines, Neuropathy, Cognitive Decline
- Depression, Anxiety
- Insomnia/Sleep Issues

**Blood & Nutrition:**
- Anemia, Fatigue/Low Energy

**Reproductive & Life Stages:**
- PMS/PMDD, Menopause Symptoms
- Pregnancy (1st/2nd/3rd Trimester)

**Men's Health:**
- Prostate Health

**General:**
- Healthy Aging

---

## 🧪 Testing Checklist

- [ ] Test Case 1: 40M HTN + Diabetes (no Calcium)
- [ ] Test Case 2: 55F Pregnant + HTN + Hypothyroidism (Folic Acid visible)
- [ ] Test Case 3: 60F Osteoporosis (Calcium visible)
- [ ] Test Case 4: 30M Gout (includes Quercetin)
- [ ] Drug interactions displaying correctly
- [ ] Evidence grades sorting A→B→C
- [ ] All 4 tabs functioning
- [ ] No error messages

---

## 📊 Nutrients Database (18+)

- Folic Acid (A)
- Iron (A)
- Calcium (A)
- Vitamin D3 (A)
- Magnesium (A)
- Vitamin B12 (A)
- Selenium (A)
- Zinc (B)
- Omega-3 (EPA/DHA) (B)
- Vitamin C (B)
- Vitamin K2 (B)
- Vitamin B6 (B)
- Vitamin B2 (B)
- Probiotics (B)
- Chromium (B)
- CoQ10 (B)
- Alpha-Lipoic Acid (B)
- Quercetin (B)

---

## 🔄 Version History

### v4.2.2 (Current)
- Smart Calcium recommendations (F50+ only)
- Evidence grade sorting (A→B→C)
- Pregnancy + Folic Acid support
- NatMed Pro integration
- 40+ medical conditions
- 18+ nutrients
- 4-tab interface

### v4.1
- NatMed Pro drug-induced nutrient depletions added
- Expanded conditions
- Supplement interactions added

### v4.0
- Initial release with 4 basic conditions

---

## 💡 Feedback & Bug Reports

Found an issue? Have a suggestion?

Email: mostafa.shahin@example.com

Include:
- What you were testing
- What you expected
- What happened instead
- Screenshots if possible

---

## 📄 License

**For Choices Pharmacy Use Only**

Developed by: Mostafa Shahin (RPh, CDE, PhD)  
Date: July 2026

---

## 📞 Support

**For setup help:**
1. Check SETUP_INSTRUCTIONS.md
2. Try the online version first (no installation)
3. Email for technical support

**For clinical questions:**
Contact Mostafa Shahin (Lead Pharmacist)

---

## 🙏 Acknowledgments

- **Evidence Base:** Canadian Pharmacists Association (CPhA)
- **Drug Data:** NatMed Pro (May 2025 & March 2025)
- **Clinical Review:** Fabina Kara (Choices Pharmacy)

---

**Ready to test? Click below:**

👉 **[Try the App Now](https://smart-vitamin.streamlit.app)**

---

*Last Updated: July 31, 2026*  
*Version: 4.2.2*  
*Status: Production Ready for Choices Pharmacy Testing*
