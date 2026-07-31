"""
Smart Vitamin Assessment Tool v4.2.2 - Enhanced with NatMed Pro Resources
For: Choices Pharmacy | Lead: Mostafa Shahin (RPh, CDE, PhD)
Evidence Base: CPhA Guidelines + NatMed Pro (May 2025 & March 2025)
GitHub: mostafashahin-sketch/smart-vitamin

VERSION 4.2.2: 
- Smart Calcium recommendations (only for: Female 50+, bone conditions, or malabsorption issues)
- Sorted nutrients by Evidence Grade (Grade A at top, B middle, C bottom)
- Pregnancy conditions with Folic Acid
- Color-coded evidence grade sections
"""

import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Smart Vitamin Assessment Tool",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem;}
    .warning-box {background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 1rem; border-radius: 4px; margin: 1rem 0;}
    .critical-box {background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 1rem; border-radius: 4px; margin: 1rem 0;}
    .success-box {background-color: #d4edda; border-left: 4px solid #28a745; padding: 1rem; border-radius: 4px; margin: 1rem 0;}
    .major-interaction {background-color: #f8d7da; color: #721c24; padding: 0.75rem; border-left: 4px solid #dc3545; margin: 0.5rem 0;}
    .moderate-interaction {background-color: #fff3cd; color: #856404; padding: 0.75rem; border-left: 4px solid #ffc107; margin: 0.5rem 0;}
    .minor-interaction {background-color: #d4edda; color: #155724; padding: 0.75rem; border-left: 4px solid #28a745; margin: 0.5rem 0;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# NATMED PRO: DRUG-SUPPLEMENT INTERACTIONS (May 2025)
# ============================================================================

NATMED_SUPPLEMENT_INTERACTIONS = {
    'Ashwagandha': {
        'supplements': ['Ashwagandha'],
        'interactions': [
            {'drug': 'Thyroid hormones', 'severity': 'Moderate', 'detail': 'Ashwagandha might increase thyroid hormone levels causing additive effects'}
        ]
    },
    'Garlic': {
        'supplements': ['Garlic'],
        'interactions': [
            {'drug': 'Over 50% of prescription medications', 'severity': 'Moderate', 'detail': 'Might alter CYP 3A4 and CYP2E1 function; allicin is the active compound'}
        ]
    },
    'Glucosamine': {
        'supplements': ['Glucosamine', 'Glucosamine + Chondroitin'],
        'interactions': [
            {'drug': 'Warfarin (Coumadin)', 'severity': 'MAJOR', 'detail': 'AVOID: Might increase INR and bleeding risk'}
        ]
    },
    'Green Tea Extract': {
        'supplements': ['Green Tea (Extract)'],
        'interactions': [
            {'drug': 'Hepatotoxic medications', 'severity': 'Moderate', 'detail': 'Extracts linked to liver damage; beverage form is safer'}
        ]
    },
    'Fruit Juices': {
        'supplements': ['Orange Juice', 'Grape Juice', 'Grapefruit Juice', 'Apple Juice', 'Cranberry Juice'],
        'interactions': [
            {'drug': 'Over 50% of prescription medications', 'severity': 'Moderate to MAJOR', 'detail': 'Alters medication absorption/metabolism via CYP and OATP enzymes'}
        ]
    },
    'Probiotics': {
        'supplements': ['Probiotics'],
        'interactions': [
            {'drug': 'Antibiotic drugs', 'severity': 'Moderate', 'detail': 'Separate by at least 2 hours; antibiotics reduce probiotic effectiveness'}
        ]
    },
    'Red Yeast Rice': {
        'supplements': ['Red Yeast Rice'],
        'interactions': [
            {'drug': 'Statins (HMG-CoA reductase inhibitors)', 'severity': 'Moderate', 'detail': 'Contains lovastatin; increases risk of muscle damage and liver problems'}
        ]
    },
    'Sedative Supplements': {
        'supplements': ['Valerian', 'Passionflower', 'Chamomile (concentrated)', 'Kava'],
        'interactions': [
            {'drug': 'CNS Depressants, Sedatives', 'severity': 'Moderate to MAJOR', 'detail': 'Additive sedation and drowsiness; avoid combining'}
        ]
    },
    'Serotonergic Supplements': {
        'supplements': ["St. John's Wort", '5-HTP', 'SAM-e'],
        'interactions': [
            {'drug': 'SSRIs, SNRIs, Tricyclic antidepressants', 'severity': 'Moderate to MAJOR', 'detail': 'Risk of serotonin syndrome; serious side effects possible'}
        ]
    },
    "St. John's Wort": {
        'supplements': ["St. John's Wort"],
        'interactions': [
            {'drug': 'Over 50% of prescription medications', 'severity': 'Moderate to MAJOR', 'detail': 'Induces CYP enzymes; reduces effectiveness of many drugs'}
        ]
    }
}

# ============================================================================
# NATMED PRO: DRUG-INDUCED NUTRIENT DEPLETIONS (March 2025)
# ============================================================================

NATMED_NUTRIENT_DEPLETIONS = {
    'Anticonvulsants': {
        'drugs': ['Carbamazepine', 'Phenytoin', 'Phenobarbital'],
        'depletions': [
            {'nutrient': 'Calcium', 'severity': 'Moderate', 'detail': 'Inactivates vitamin D; monitor if used more than 6 months'},
            {'nutrient': 'Vitamin D', 'severity': 'Moderate', 'detail': 'Slow calcium absorption; consider supplementation'},
            {'nutrient': 'Folic Acid', 'severity': 'Moderate', 'detail': 'Monitor for depletion; consult physician before supplementing'}
        ]
    },
    'Biguanides': {
        'drugs': ['Metformin'],
        'depletions': [
            {'nutrient': 'Vitamin B12', 'severity': 'Moderate', 'detail': 'Reduces B12 absorption 10-30 percent; monitor annually'}
        ]
    },
    'PPIs': {
        'drugs': ['Omeprazole', 'Pantoprazole', 'Lansoprazole'],
        'depletions': [
            {'nutrient': 'Magnesium', 'severity': 'MAJOR', 'detail': 'Especially if used more than 1 year; supplement needed for most patients'},
            {'nutrient': 'Vitamin B12', 'severity': 'Moderate', 'detail': 'Reduces intrinsic factor; monitor if used chronically'}
        ]
    },
    'Diuretics': {
        'drugs': ['Loop Diuretics', 'Thiazide Diuretics'],
        'depletions': [
            {'nutrient': 'Potassium', 'severity': 'MAJOR', 'detail': 'Supplement needed for most patients; increases urinary excretion'},
            {'nutrient': 'Magnesium', 'severity': 'Moderate', 'detail': 'Loop diuretics especially; monitor for depletion'},
            {'nutrient': 'Calcium', 'severity': 'Moderate', 'detail': 'Loop diuretics increase excretion'}
        ]
    },
    'Corticosteroids': {
        'drugs': ['Prednisone', 'Hydrocortisone', 'Dexamethasone'],
        'depletions': [
            {'nutrient': 'Calcium', 'severity': 'Moderate', 'detail': 'Decreases absorption and increases excretion; supplement needed'},
            {'nutrient': 'Vitamin D', 'severity': 'Moderate', 'detail': 'Given to improve calcium absorption'},
            {'nutrient': 'Magnesium', 'severity': 'Moderate', 'detail': 'Long-term use increases excretion'}
        ]
    },
    'Statins': {
        'drugs': ['Atorvastatin', 'Simvastatin', 'Rosuvastatin'],
        'depletions': [
            {'nutrient': 'Coenzyme Q10', 'severity': 'Insufficient Evidence', 'detail': 'Reduces CoQ10 levels; may contribute to muscle pain'}
        ]
    }
}

# ============================================================================
# EXPANDED CONDITION-NUTRIENT MAPPING (40+ CONDITIONS)
# ============================================================================

CONDITION_NUTRIENT_MAP = {
    'Gout': ['Magnesium', 'Vitamin C', 'Quercetin', 'Omega-3 (EPA/DHA)'],
    'Osteoporosis': ['Calcium', 'Vitamin D3', 'Vitamin K2', 'Magnesium'],
    'Hypertension': ['Magnesium', 'Omega-3 (EPA/DHA)'],  # Removed Calcium - recommend based on sex/age
    'Type 2 Diabetes': ['Magnesium', 'Vitamin B12', 'Omega-3 (EPA/DHA)'],
    'Rheumatoid Arthritis': ['Omega-3 (EPA/DHA)', 'Vitamin D3', 'Magnesium'],
    'Osteoarthritis': ['Omega-3 (EPA/DHA)', 'Magnesium', 'Vitamin C'],
    'Bone Loss (Osteopenia)': ['Calcium', 'Vitamin D3', 'Vitamin K2', 'Magnesium'],
    'Cardiovascular Disease': ['Omega-3 (EPA/DHA)', 'Magnesium', 'Vitamin D3'],
    'High Cholesterol': ['Omega-3 (EPA/DHA)'],
    'Prediabetes': ['Magnesium', 'Chromium'],
    'Metabolic Syndrome': ['Magnesium', 'Omega-3 (EPA/DHA)', 'Vitamin D3'],
    'IBS (Irritable Bowel Syndrome)': ['Magnesium', 'Probiotics', 'Vitamin B12'],
    'GERD (Acid Reflux)': ['Magnesium', 'Calcium', 'Vitamin B12'],
    'Celiac Disease': ['Iron', 'Vitamin B12', 'Folic Acid', 'Calcium'],
    'Crohns Disease': ['Iron', 'Vitamin B12', 'Folic Acid', 'Vitamin D3'],
    'Migraines': ['Magnesium', 'Vitamin B2', 'Coenzyme Q10'],
    'Neuropathy': ['Vitamin B12', 'Alpha-Lipoic Acid', 'Omega-3 (EPA/DHA)'],
    'Cognitive Decline': ['Omega-3 (EPA/DHA)', 'Vitamin D3'],
    'Hypothyroidism': ['Selenium', 'Iron', 'Zinc', 'Vitamin D3'],
    'Hashimotos Thyroiditis': ['Selenium', 'Iron', 'Zinc', 'Vitamin D3'],
    'Hyperthyroidism': ['Selenium', 'Vitamin D3'],
    'Depression': ['Omega-3 (EPA/DHA)', 'Vitamin D3', 'Magnesium'],
    'Anxiety': ['Magnesium', 'Omega-3 (EPA/DHA)'],
    'Autoimmune Conditions': ['Vitamin D3', 'Omega-3 (EPA/DHA)', 'Magnesium'],
    'Chronic Inflammation': ['Omega-3 (EPA/DHA)', 'Magnesium', 'Vitamin D3'],
    'Anemia': ['Iron', 'Vitamin B12', 'Folic Acid'],
    'Fatigue/Low Energy': ['Iron', 'Vitamin B12', 'Magnesium', 'Vitamin D3'],
    'Eczema/Dermatitis': ['Omega-3 (EPA/DHA)', 'Vitamin D3', 'Probiotics'],
    'Acne': ['Zinc', 'Vitamin A', 'Omega-3 (EPA/DHA)'],
    'PMS/PMDD': ['Magnesium', 'Calcium', 'Vitamin B6'],
    'Menopause Symptoms': ['Calcium', 'Vitamin D3', 'Magnesium', 'Omega-3 (EPA/DHA)'],
    'PCOS': ['Magnesium', 'Chromium', 'Omega-3 (EPA/DHA)'],
    'Prostate Health': ['Selenium', 'Zinc', 'Omega-3 (EPA/DHA)'],
    'Insomnia/Sleep Issues': ['Magnesium', 'Vitamin B6'],
    'Healthy Aging': ['Vitamin D3', 'Magnesium', 'Omega-3 (EPA/DHA)', 'Calcium'],
    'Pregnancy (First Trimester)': ['Folic Acid', 'Iron', 'Calcium', 'Vitamin D3', 'Omega-3 (EPA/DHA)'],
    'Pregnancy (Second Trimester)': ['Folic Acid', 'Iron', 'Calcium', 'Vitamin D3', 'Omega-3 (EPA/DHA)'],
    'Pregnancy (Third Trimester)': ['Folic Acid', 'Iron', 'Calcium', 'Vitamin D3', 'Omega-3 (EPA/DHA)'],
}

# ============================================================================
# NUTRIENT DATABASE (EXPANDED)
# ============================================================================

NUTRIENT_DATABASE = {
    'Magnesium': {
        'name': 'Magnesium (Glycinate)',
        'dri_female': '310-320 mg/day',
        'dri_male': '400-420 mg/day',
        'recommended_dose': '300-400 mg/day',
        'forms': ['Glycinate (preferred)', 'Citrate', 'Malate'],
        'evidence_grade': 'B',
        'monitoring': 'Symptom improvement, GI tolerance',
        'side_effects': ['Loose stools (especially oxide)', 'Mild GI upset'],
        'conditions': ['Gout', 'Osteoporosis', 'Hypertension', 'Type 2 Diabetes'],
        'mechanism': 'Supports uric acid metabolism, bone mineral density'
    },
    'Calcium': {
        'name': 'Calcium (Citrate)',
        'dri_female': '1000-1200 mg/day',
        'dri_male': '1000-1200 mg/day',
        'recommended_dose': '800-1000 mg/day (split doses)',
        'forms': ['Citrate (30-35 percent)', 'Malate', 'Glycinate'],
        'evidence_grade': 'A',
        'monitoring': 'Serum calcium, 25-OH Vitamin D, PTH every 12 weeks',
        'side_effects': ['Constipation', 'Hypercalcemia if excessive'],
        'conditions': ['Osteoporosis'],
        'mechanism': 'Essential for bone mineralization'
    },
    'Vitamin D3': {
        'name': 'Vitamin D3 (Cholecalciferol)',
        'dri_female': '600-800 IU/day',
        'dri_male': '600-800 IU/day',
        'recommended_dose': '1000-2000 IU/day',
        'forms': ['D3 (preferred)', 'D2 (less effective)'],
        'evidence_grade': 'A',
        'target_level': '75-125 nmol/L',
        'monitoring': 'Serum 25-OH Vitamin D every 8-12 weeks',
        'side_effects': ['Hypercalcemia if greater than 4000 IU/day long-term'],
        'conditions': ['Osteoporosis'],
        'mechanism': 'Essential for calcium absorption and bone metabolism'
    },
    'Vitamin K2': {
        'name': 'Vitamin K2 (Menaquinone-7/MK-7)',
        'dri_female': '90 mcg/day',
        'dri_male': '120 mcg/day',
        'recommended_dose': '45-120 mcg/day',
        'forms': ['MK-7 (preferred)', 'MK-4'],
        'evidence_grade': 'B',
        'monitoring': 'Bone turnover markers',
        'side_effects': ['Very rare'],
        'conditions': ['Osteoporosis'],
        'mechanism': 'Activates bone matrix proteins'
    },
    'Vitamin C': {
        'name': 'Vitamin C (Ascorbic Acid)',
        'dri_female': '75-90 mg/day',
        'dri_male': '90 mg/day',
        'recommended_dose': '500-1000 mg/day',
        'forms': ['Ascorbic acid', 'Sodium ascorbate', 'Buffered'],
        'evidence_grade': 'B',
        'monitoring': 'Uric acid levels in 6-8 weeks',
        'side_effects': ['GI upset', 'Kidney stone risk at high doses'],
        'conditions': ['Gout'],
        'mechanism': 'Supports uric acid excretion'
    },
    'Omega-3 (EPA/DHA)': {
        'name': 'Omega-3 Fatty Acids',
        'dri_female': '1.1 g ALA/day',
        'dri_male': '1.6 g ALA/day',
        'recommended_dose': '1000-2000 mg/day',
        'forms': ['Fish oil', 'Algae-based (vegan)'],
        'evidence_grade': 'B',
        'monitoring': 'Triglyceride levels',
        'conditions': ['Gout', 'Osteoporosis'],
        'mechanism': 'Potent anti-inflammatory'
    },
    'Vitamin B12': {
        'name': 'Vitamin B12 (Cyanocobalamin)',
        'dri_female': '2.4 mcg/day',
        'dri_male': '2.4 mcg/day',
        'recommended_dose': '1000 mcg/day (oral)',
        'forms': ['Cyanocobalamin', 'Methylcobalamin'],
        'evidence_grade': 'A',
        'monitoring': 'Serum B12, homocysteine annually',
        'conditions': ['Diabetes', 'Hypertension'],
        'mechanism': 'Essential for methylation and neurological function'
    },
    'Probiotics': {
        'name': 'Probiotics (Multi-strain)',
        'recommended_dose': '10-50 billion CFU/day',
        'forms': ['Lactobacillus', 'Bifidobacterium', 'Multi-strain blends'],
        'evidence_grade': 'B',
        'timing': 'With or between meals; 2+ hours from antibiotics',
        'monitoring': 'Digestive symptoms, bloating, tolerance',
        'conditions': ['IBS', 'GERD', 'Eczema'],
        'mechanism': 'Supports gut microbiome and immune function'
    },
    'Folic Acid': {
        'name': 'Folic Acid (Methylfolate)',
        'dri_female': '400 mcg/day',
        'dri_male': '400 mcg/day',
        'recommended_dose': '400-800 mcg/day',
        'forms': ['Folic acid', 'Methylfolate (preferred)', 'Folinic acid'],
        'evidence_grade': 'A',
        'monitoring': 'Homocysteine levels, symptom improvement',
        'conditions': ['Anemia', 'Depression', 'Celiac Disease'],
        'mechanism': 'Essential for DNA synthesis and methylation'
    },
    'Iron': {
        'name': 'Iron (Heme or Chelated)',
        'dri_female': '18 mg/day',
        'dri_male': '8 mg/day',
        'recommended_dose': '18-25 mg/day (elemental)',
        'forms': ['Heme iron (better absorbed)', 'Ferrous sulfate', 'Iron chelate'],
        'evidence_grade': 'B',
        'monitoring': 'Serum ferritin, hemoglobin, hematocrit',
        'conditions': ['Anemia', 'Fatigue'],
        'mechanism': 'Essential for oxygen transport and energy'
    },
    'Selenium': {
        'name': 'Selenium',
        'dri_female': '55 mcg/day',
        'dri_male': '55 mcg/day',
        'recommended_dose': '100-200 mcg/day',
        'forms': ['Selenomethionine (preferred)', 'Sodium selenite'],
        'evidence_grade': 'B',
        'monitoring': 'Thyroid antibodies, TSH levels',
        'conditions': ['Hypothyroidism', 'Hashimotos', 'Autoimmune'],
        'mechanism': 'Essential cofactor for thyroid peroxidase'
    },
    'Zinc': {
        'name': 'Zinc (Glycinate or Picolinate)',
        'dri_female': '8 mg/day',
        'dri_male': '11 mg/day',
        'recommended_dose': '15-30 mg/day (elemental)',
        'forms': ['Zinc glycinate (preferred)', 'Zinc picolinate', 'Zinc citrate'],
        'evidence_grade': 'B',
        'monitoring': 'Copper status monitor ratio; Immune function',
        'conditions': ['Hypothyroidism', 'Acne', 'Immune support'],
        'mechanism': 'Essential for immune function and wound healing'
    },
    'Chromium': {
        'name': 'Chromium (Picolinate)',
        'dri_female': '25 mcg/day',
        'dri_male': '35 mcg/day',
        'recommended_dose': '200-400 mcg/day',
        'forms': ['Chromium picolinate (preferred)', 'Chromium polynicotinate'],
        'evidence_grade': 'B',
        'monitoring': 'Blood glucose levels, metabolism',
        'conditions': ['Prediabetes', 'PCOS'],
        'mechanism': 'Supports glucose metabolism and insulin sensitivity'
    },
    'Coenzyme Q10 (CoQ10)': {
        'name': 'Coenzyme Q10 (Ubiquinone)',
        'recommended_dose': '100-300 mg/day',
        'forms': ['Ubiquinone (standard)', 'Ubiquinol (reduced, better absorbed)'],
        'evidence_grade': 'B',
        'timing': 'With fat-containing meal',
        'monitoring': 'Energy levels, muscle pain resolution',
        'conditions': ['Migraines', 'Heart Health'],
        'mechanism': 'Energy production in cells; powerful antioxidant'
    },
    'Alpha-Lipoic Acid': {
        'name': 'Alpha-Lipoic Acid (ALA)',
        'recommended_dose': '300-600 mg/day',
        'forms': ['R-alpha-lipoic acid (preferred)', 'Racemic ALA'],
        'evidence_grade': 'B',
        'timing': 'Best on empty stomach',
        'monitoring': 'Neuropathy symptoms, blood glucose',
        'conditions': ['Neuropathy', 'Diabetes'],
        'mechanism': 'Powerful antioxidant; supports glucose metabolism'
    },
    'Vitamin B6': {
        'name': 'Vitamin B6 (Pyridoxal-5-Phosphate)',
        'dri_female': '1.3-1.5 mg/day',
        'dri_male': '1.3-1.7 mg/day',
        'recommended_dose': '25-100 mg/day',
        'forms': ['Pyridoxal-5-phosphate (preferred)', 'Pyridoxine'],
        'evidence_grade': 'B',
        'monitoring': 'Symptom improvement, homocysteine',
        'conditions': ['PMS/PMDD', 'Cognitive Decline'],
        'mechanism': 'Essential for neurotransmitter and hormone synthesis'
    },
    'Quercetin': {
        'name': 'Quercetin (Flavonoid)',
        'recommended_dose': '500-1000 mg/day',
        'forms': ['Quercetin dihydrate', 'Quercetin glycoside'],
        'timing': 'With meals',
        'evidence_grade': 'B',
        'monitoring': 'Uric acid levels, gout symptom improvement',
        'conditions': ['Gout'],
        'mechanism': 'Natural xanthine oxidase inhibitor'
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_relevant_nutrients(conditions, pregnancy_status, patient_age=None, patient_sex=None):
    nutrients = set()
    
    # Add pregnancy-specific nutrients based on Pregnancy Status
    if pregnancy_status == "Pregnant (1st)":
        nutrients.update(['Folic Acid', 'Iron', 'Calcium', 'Vitamin D3', 'Omega-3 (EPA/DHA)'])
    elif pregnancy_status == "Pregnant (2nd)":
        nutrients.update(['Folic Acid', 'Iron', 'Calcium', 'Vitamin D3', 'Omega-3 (EPA/DHA)'])
    elif pregnancy_status == "Pregnant (3rd)":
        nutrients.update(['Folic Acid', 'Iron', 'Calcium', 'Vitamin D3', 'Omega-3 (EPA/DHA)'])
    elif pregnancy_status == "Lactating":
        nutrients.update(['Folic Acid', 'Iron', 'Calcium', 'Vitamin D3', 'Omega-3 (EPA/DHA)'])
    
    # Add nutrients from medical conditions
    for condition in conditions:
        if condition in CONDITION_NUTRIENT_MAP:
            nutrients.update(CONDITION_NUTRIENT_MAP[condition])
    
    # Add Calcium conditionally based on sex and age
    # Recommend for: post-menopausal women (50+) OR bone health conditions
    has_bone_condition = any(c in conditions for c in ['Osteoporosis', 'Bone Loss (Osteopenia)', 'Menopause Symptoms', 'Healthy Aging', 'PMS/PMDD', 'PCOS'])
    has_absorption_issue = any(c in conditions for c in ['Celiac Disease', 'Crohns Disease', 'GERD (Acid Reflux)', 'IBS (Irritable Bowel Syndrome)'])
    
    if has_bone_condition or has_absorption_issue:
        nutrients.add('Calcium')
    elif patient_sex == "Female" and patient_age and patient_age >= 50:
        nutrients.add('Calcium')
    
    return nutrients

def get_supplement_interactions(medications):
    interactions = []
    for med in medications:
        med_lower = med.lower()
        for supp_name, supp_data in NATMED_SUPPLEMENT_INTERACTIONS.items():
            for interaction in supp_data['interactions']:
                if med_lower in interaction['drug'].lower() or interaction['drug'].lower() in med_lower:
                    interactions.append({
                        'supplement': supp_name,
                        'medication': med,
                        'data': interaction
                    })
    return interactions

def get_nutrient_depletions(medications):
    depletions = []
    for med in medications:
        med_lower = med.lower()
        for drug_class, depl_data in NATMED_NUTRIENT_DEPLETIONS.items():
            for drug in depl_data['drugs']:
                if med_lower in drug.lower() or drug.lower() in med_lower:
                    for depl in depl_data['depletions']:
                        depletions.append({
                            'medication': med,
                            'drug_class': drug_class,
                            'nutrient': depl['nutrient'],
                            'severity': depl['severity'],
                            'detail': depl['detail']
                        })
    return depletions

def calculate_bmi(height_cm, weight_kg):
    return round(weight_kg / ((height_cm / 100) ** 2), 1)

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.title("💊 Smart Vitamin Assessment Tool v4.2.2")
    st.markdown("*Evidence-based personalized nutrient recommendations for pharmacy patients*")
    st.markdown("**Evidence Base:** Canadian Pharmacists Association (CPhA) + **NatMed Pro (May 2025 & March 2025)**")
    st.markdown("**✅ Version 4.2.2: Smart Calcium | Evidence Grade Sorting | Pregnancy + Folic Acid**")
    
    with st.sidebar:
        st.header("Assessment Configuration")
        st.info("💊 **New Patient Assessment Mode**")
        
        st.divider()
        st.subheader("Display Options")
        show_depletions = st.checkbox("Show Drug-Induced Nutrient Depletions", value=True)
        show_supplement_int = st.checkbox("Show Supplement Interactions", value=True)
        show_pharmacist_notes = st.checkbox("Show Pharmacist Notes", value=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Assessment", "Recommendations", "Drug Interactions", "Evidence & Sources"])
    
    with tab1:
        st.header("Patient Assessment")
        
        st.subheader("Patient Information")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            age = st.number_input("Age (years)", min_value=1, max_value=120, value=55)
        with col2:
            sex = st.selectbox("Sex", ["Female", "Male", "Other"], index=0)
        with col3:
            height = st.number_input("Height (cm)", min_value=100, max_value=250, value=170)
        with col4:
            weight = st.number_input("Weight (kg)", min_value=30, max_value=300, value=75)
        
        bmi = calculate_bmi(height, weight)
        pregnancy = st.selectbox("Pregnancy Status", 
            ["Not applicable", "Pregnant (1st)", "Pregnant (2nd)", "Pregnant (3rd)", "Lactating"], index=0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("BMI", f"{bmi}")
        
        st.subheader("Current Medications")
        medications_input = st.text_area(
            "Enter medications (one per line or comma-separated)",
            value="Allopurinol",
            height=100
        )
        medications = [m.strip() for m in medications_input.split('\n') if m.strip()]
        medications = [item.strip() for med in medications for item in med.split(',') if item.strip()]
        
        st.caption(f"✓ {len(medications)} medication(s) entered")
        
        st.subheader("Medical Conditions")
        
        condition_options = [
            "Gout", "Rheumatoid Arthritis", "Osteoarthritis",
            "Osteoporosis", "Bone Loss (Osteopenia)",
            "Hypertension", "Cardiovascular Disease", "High Cholesterol",
            "Type 2 Diabetes", "Prediabetes", "Metabolic Syndrome",
            "IBS (Irritable Bowel Syndrome)", "GERD (Acid Reflux)", "Celiac Disease", "Crohns Disease",
            "Migraines", "Neuropathy", "Cognitive Decline",
            "Hypothyroidism", "Hashimotos Thyroiditis", "Hyperthyroidism",
            "Depression", "Anxiety",
            "Autoimmune Conditions", "Chronic Inflammation",
            "Anemia", "Fatigue/Low Energy",
            "Eczema/Dermatitis", "Acne",
            "PMS/PMDD", "Menopause Symptoms", "PCOS",
            "Prostate Health",
            "Insomnia/Sleep Issues",
            "Healthy Aging",
            "Pregnancy (First Trimester)",
            "Pregnancy (Second Trimester)",
            "Pregnancy (Third Trimester)"
        ]
        
        selected_conditions = st.multiselect(
            "Select relevant conditions (40+ available)",
            condition_options,
            default=["Gout", "Osteoporosis"]
        )
        
        st.write("**Or add a custom condition:**")
        col1, col2 = st.columns([3, 1])
        with col1:
            custom_condition = st.text_input(
                "Enter custom condition",
                placeholder="e.g., Fibromyalgia, Lupus, etc.",
                label_visibility="collapsed"
            )
        with col2:
            add_custom = st.button("Add Custom", use_container_width=True)
        
        if add_custom and custom_condition.strip():
            if custom_condition not in selected_conditions:
                selected_conditions = list(selected_conditions) + [custom_condition.strip()]
                st.success(f"✓ Added: {custom_condition}")
        
        st.caption(f"✓ {len(selected_conditions)} condition(s) selected")
        
        if st.button("Generate Recommendations", use_container_width=True):
            st.session_state.show_results = True
            st.session_state.patient_data = {
                'age': age, 'sex': sex, 'height': height, 'weight': weight, 'bmi': bmi,
                'pregnancy': pregnancy
            }
            st.session_state.medications = medications
            st.session_state.conditions = selected_conditions
            st.session_state.pregnancy_status = pregnancy
    
    with tab2:
        if 'show_results' in st.session_state and st.session_state.show_results:
            medications = st.session_state.medications
            conditions = st.session_state.conditions
            pregnancy_status = st.session_state.pregnancy_status
            patient_age = st.session_state.patient_data['age']
            patient_sex = st.session_state.patient_data['sex']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Conditions", len(conditions))
            with col2:
                relevant_nuts = get_relevant_nutrients(conditions, pregnancy_status, patient_age, patient_sex)
                st.metric("Nutrients", len(relevant_nuts))
            with col3:
                st.metric("Medications", len(medications))
            
            st.divider()
            st.subheader("Targeted Nutrient Recommendations")
            
            relevant_nutrients = get_relevant_nutrients(conditions, pregnancy_status, patient_age, patient_sex)
            
            # Sort nutrients by evidence grade (A, B, C, etc.)
            grade_order = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
            sorted_nutrients = sorted(relevant_nutrients, 
                key=lambda x: (grade_order.get(NUTRIENT_DATABASE.get(x, {}).get('evidence_grade', 'Z')[0], 999), x))
            
            # Display by evidence grade
            current_grade = None
            for nut_name in sorted_nutrients:
                if nut_name in NUTRIENT_DATABASE:
                    nut = NUTRIENT_DATABASE[nut_name]
                    grade = nut.get('evidence_grade', 'N/A')
                    
                    # Add section header when grade changes
                    if grade != current_grade:
                        current_grade = grade
                        if grade == 'A':
                            st.markdown("### 🟢 **Grade A Evidence** (Strong - Recommended)")
                        elif grade == 'B':
                            st.markdown("### 🟡 **Grade B Evidence** (Moderate - Consider)")
                        elif grade == 'C':
                            st.markdown("### 🟠 **Grade C Evidence** (Weak - Monitor)")
                        else:
                            st.markdown(f"### **Grade {grade} Evidence**")
                    
                    with st.expander(f"💊 {nut['name']}", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Evidence Grade", f"Grade {grade}")
                        with col2:
                            dri = nut.get('dri_female' if st.session_state.patient_data['sex'] == 'Female' else 'dri_male', 'N/A')
                            st.metric("DRI", dri)
                        with col3:
                            st.metric("Recommended", nut['recommended_dose'])
                        
                        st.write(f"**Mechanism:** {nut['mechanism']}")
                        if 'forms' in nut:
                            st.write(f"**Forms:** {', '.join(nut['forms'])}")
                        if 'monitoring' in nut:
                            st.write(f"**Monitoring:** {nut['monitoring']}")
                        
                        if nut.get('side_effects'):
                            st.warning(f"**Side Effects:** {', '.join(nut['side_effects'])}")
        else:
            st.info("👈 Complete the assessment form and click 'Generate Recommendations'")
    
    with tab3:
        if 'show_results' in st.session_state and st.session_state.show_results:
            medications = st.session_state.medications
            
            if show_depletions:
                st.subheader("Drug-Induced Nutrient Depletions (NatMed Pro)")
                depletions = get_nutrient_depletions(medications)
                
                if depletions:
                    for depl in depletions:
                        if depl['severity'] == 'MAJOR':
                            st.markdown(f"""<div class="major-interaction">
                                <strong>🚨 {depl['medication']} → {depl['nutrient']} (MAJOR)</strong><br/>
                                {depl['detail']}
                            </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown(f"""<div class="moderate-interaction">
                                <strong>⚠️ {depl['medication']} → {depl['nutrient']} ({depl['severity']})</strong><br/>
                                {depl['detail']}
                            </div>""", unsafe_allow_html=True)
                else:
                    st.success("✓ No significant drug-induced nutrient depletions identified")
            
            st.divider()
            
            if show_supplement_int:
                st.subheader("Supplement-Drug Interactions (NatMed Pro)")
                supp_interactions = get_supplement_interactions(medications)
                
                if supp_interactions:
                    for si in supp_interactions:
                        severity = si['data']['severity']
                        if 'MAJOR' in severity:
                            st.markdown(f"""<div class="major-interaction">
                                <strong>🚨 {si['supplement']} + {si['medication']} (MAJOR)</strong><br/>
                                {si['data']['detail']}
                            </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown(f"""<div class="moderate-interaction">
                                <strong>⚠️ {si['supplement']} + {si['medication']} ({severity})</strong><br/>
                                {si['data']['detail']}
                            </div>""", unsafe_allow_html=True)
                else:
                    st.success("✓ No supplement-drug interactions identified")
        else:
            st.info("👈 Complete the assessment form first")
    
    with tab4:
        st.subheader("Evidence Sources and References")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            ### Primary Evidence Sources
            
            **Canadian Pharmacists Association (CPhA)**
            - CPhA Nutritional Supplements Guide (2021)
            - Evidence-based nutrient recommendations
            - Grade A/B clinical evidence
            
            **NatMed Pro (May 2025)**
            - Drug-Supplement Interactions Chart
            - 12+ major supplement interactions
            - Severity ratings (Major/Moderate/Minor)
            
            **NatMed Pro (March 2025)**
            - Drug-Induced Nutrient Depletions
            - 10+ medication classes
            - Severity and monitoring recommendations
            """)
        
        with col2:
            st.markdown("""
            ### Additional Guidelines
            
            - ADA Standards of Care 2024
            - AHA/ACC Guidelines 2017-2019
            - Endocrine Society Clinical Practice
            - National Osteoporosis Foundation
            - ASPEN Nutrition Guidelines
            - Academy of Nutrition and Dietetics
            
            ### Important Disclaimer
            This tool is educational and does not replace professional medical advice. Always consult with a healthcare provider before starting supplements.
            """)
        
        st.divider()
        st.info("""
        **Evidence Quality Grading (CPhA):**
        - **Grade A:** Strong Evidence (RCTs, meta-analyses)
        - **Grade B:** Moderate Evidence (observational studies, some RCTs)
        - **Grade C:** Weak Evidence
        - **Grade D:** Insufficient Evidence
        """)

if __name__ == "__main__":
    main()
