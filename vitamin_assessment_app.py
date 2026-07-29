import streamlit as st
import pandas as pd
import json
from datetime import datetime
from collections import defaultdict
import base64
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ============================================================================
# PAGE CONFIGURATION (MUST BE FIRST)
# ============================================================================

st.set_page_config(
    page_title="Smart Vitamin Assessment",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# IMPORT EVIDENCE-BASED NUTRIENT DATABASE
# ============================================================================

try:
    from evidence_based_nutrient_db import (
        DRUG_NUTRIENT_INTERACTIONS,
        CONDITION_NUTRIENT_NEEDS,
        SUPPLEMENT_SUPPLEMENT_INTERACTIONS,
        CONTRAINDICATIONS
    )
    EVIDENCE_DB_LOADED = True
except ImportError:
    EVIDENCE_DB_LOADED = False  
    st.warning("⚠️ Evidence database not found. Running with basic recommendations.")

# Try to import API integration
try:
    from evidence_api_integration import evidence_api
    API_INTEGRATION_AVAILABLE = True
except ImportError:
    API_INTEGRATION_AVAILABLE = False
    st.info("💡 API integration not available. Using cached evidence database.")

# ============================================================================
# NUTRIENT NAME MAPPING (Handle variations in naming)
# ============================================================================

NUTRIENT_NAME_MAPPING = {
    # Vitamin B12 variations
    "b12": "Vitamin B12",
    "cobalamin": "Vitamin B12",
    "cyanocobalamin": "Vitamin B12",
    "methylcobalamin": "Vitamin B12",
    
    # B vitamins
    "b6": "Vitamin B6",
    "pyridoxine": "Vitamin B6",
    "folate": "Folate",
    "folic acid": "Folate",
    "5-mthf": "Folate",
    "methylfolate": "Folate",
    
    # Vitamin D variations
    "vitamin d": "Vitamin D3",
    "vitamin d3": "Vitamin D3",
    "cholecalciferol": "Vitamin D3",
    "vitamin d2": "Vitamin D3",
    
    # Minerals
    "iron": "Iron",
    "ferrous": "Iron",
    "ferric": "Iron",
    "calcium": "Calcium",
    "magnesium": "Magnesium",
    "potassium": "Potassium",
    "zinc": "Zinc",
    "selenium": "Selenium",
    "chromium": "Chromium",
    
    # Other nutrients
    "coq10": "CoQ10",
    "ubiquinone": "CoQ10",
    "ubiquinol": "CoQ10",
    "omega-3": "Omega-3 Fatty Acids (EPA/DHA)",
    "omega3": "Omega-3 Fatty Acids (EPA/DHA)",
    "fish oil": "Omega-3 Fatty Acids (EPA/DHA)",
    "epa dha": "Omega-3 Fatty Acids (EPA/DHA)",
    "alpha-lipoic acid": "Alpha-Lipoic Acid",
    "ala": "Alpha-Lipoic Acid",
    "inositol": "Inositol (myo-inositol)",
    "myo-inositol": "Inositol (myo-inositol)",
    "plant sterols": "Plant Sterols (Phytosterols)",
    "phytosterols": "Plant Sterols (Phytosterols)",
}

# ============================================================================
# CONDITION NAME MAPPING (Handle common variations)
# ============================================================================

CONDITION_NAME_MAPPING = {
    # Heart/Cardiovascular
    "heart disease": "Coronary Artery Disease / Post-MI",
    "coronary artery disease": "Coronary Artery Disease / Post-MI",
    "cad": "Coronary Artery Disease / Post-MI",
    "myocardial infarction": "Coronary Artery Disease / Post-MI",
    "mi": "Coronary Artery Disease / Post-MI",
    "post-mi": "Coronary Artery Disease / Post-MI",
    "heart failure": "Coronary Artery Disease / Post-MI",
    "angina": "Coronary Artery Disease / Post-MI",
    
    # Diabetes
    "diabetes": "Type 2 Diabetes",
    "type 2 diabetes": "Type 2 Diabetes",
    "type 1 diabetes": "Type 2 Diabetes",
    
    # Blood Pressure
    "hypertension": "Hypertension",
    "high blood pressure": "Hypertension",
    "elevated bp": "Hypertension",
    
    # Cholesterol
    "dyslipidemia": "Dyslipidemia (High Cholesterol/Triglycerides)",
    "high cholesterol": "Dyslipidemia (High Cholesterol/Triglycerides)",
    "high triglycerides": "Dyslipidemia (High Cholesterol/Triglycerides)",
    
    # Bone Health
    "osteoporosis": "Osteoporosis",
    "osteopenia": "Osteopenia (Low Bone Density)",
    "low bone density": "Osteopenia (Low Bone Density)",
    
    # Cognitive
    "cognitive decline": "Cognitive Decline / Mild Cognitive Impairment",
    "mci": "Cognitive Decline / Mild Cognitive Impairment",
    "memory loss": "Cognitive Decline / Mild Cognitive Impairment",
    
    # Aging
    "aging": "Frailty / Aging (Polypharmacy)",
    "frailty": "Frailty / Aging (Polypharmacy)",
    "elderly": "Frailty / Aging (Polypharmacy)",
    
    # Thyroid (Note: Limited database support - will use general recommendations)
    # "thyroid disorder" - Not in database, will be skipped for condition-based needs
}

def get_canonical_condition_name(condition):
    """
    Convert condition name to canonical form used in database
    """
    norm = condition.lower().strip()
    
    # Check mapping first
    if norm in CONDITION_NAME_MAPPING:
        return CONDITION_NAME_MAPPING[norm]
    
    # Check for close matches in mapping
    for key, value in CONDITION_NAME_MAPPING.items():
        if key in norm or norm in key:
            return value
    
    # Return original if no mapping found
    return condition

def get_canonical_nutrient_name(nutrient):
    """
    Convert nutrient name to canonical form used in database
    """
    norm = nutrient.lower().strip()
    
    # Check mapping first
    if norm in NUTRIENT_NAME_MAPPING:
        return NUTRIENT_NAME_MAPPING[norm]
    
    # Check for close matches in mapping
    for key, value in NUTRIENT_NAME_MAPPING.items():
        if key in norm or norm in key:
            return value
    
    # Return original if no mapping found
    return nutrient
def get_evidence_for_nutrient(nutrient, medications, conditions):
    """
    Look up evidence data from multiple sources:
    1. Try API integration (Health Canada LNHPD, NIH ODS, NCCIH, PubMed)
    2. Fall back to hardcoded evidence database
    """
    # Get canonical nutrient name for lookup
    canonical_nutrient = get_canonical_nutrient_name(nutrient)
    
    evidence_data = {
        "nutrient": nutrient,
        "grade": "Unknown",
        "mechanism": "",
        "clinical_evidence": "",
        "dose": "",
        "monitoring": "",
        "guideline": "",
        "doi": "",
        "sources": [],
        "api_sources": []  # Track API sources
    }
    
    # Try API first (if available)
    if API_INTEGRATION_AVAILABLE:
        try:
            # Get first medication and condition for context
            first_med = medications[0] if medications else None
            first_condition = conditions[0] if conditions else None
            
            # Query APIs (this may take a moment)
            api_evidence = evidence_api.get_comprehensive_evidence(
                nutrient, 
                drug_name=first_med,
                condition=first_condition
            )
            
            if api_evidence and api_evidence.get('sources'):
                # Extract and grade evidence from API results
                api_evidence = evidence_api.grade_evidence_quality(api_evidence)
                evidence_data["grade"] = api_evidence.get('evidence_grade', 'Unknown')
                evidence_data["api_sources"] = list(api_evidence['sources'].keys())
                
                # Prioritize PubMed systematic reviews
                if 'PubMed' in api_evidence['sources']:
                    pubmed_data = api_evidence['sources']['PubMed']
                    if pubmed_data.get('systematic_reviews'):
                        sr = pubmed_data['systematic_reviews'][0]
                        evidence_data["clinical_evidence"] = f"Systematic Review: {sr.get('title')}"
                        evidence_data["doi"] = sr.get('url')
                        evidence_data["guideline"] = "PubMed (Peer-Reviewed)"
                
                # Add NIH ODS info
                if 'NIH ODS' in api_evidence['sources']:
                    nih_data = api_evidence['sources']['NIH ODS']
                    if nih_data.get('results'):
                        evidence_data["mechanism"] = nih_data['results'][0].get('summary', '')
                        evidence_data["guideline"] = "NIH ODS (U.S. Government)"
                
                # Add NCCIH research
                if 'NCCIH' in api_evidence['sources']:
                    nccih_data = api_evidence['sources']['NCCIH']
                    if nccih_data.get('research'):
                        evidence_data["clinical_evidence"] = nccih_data['research'][0].get('research_summary', '')
                
                return evidence_data
                
        except Exception as e:
            # Silently fall back to database
            pass
    
    # Fall back to hardcoded evidence database
    if not EVIDENCE_DB_LOADED:
        return evidence_data
    
    # Check drug-nutrient interactions first (highest priority)
    for drug_class, interactions in DRUG_NUTRIENT_INTERACTIONS.items():
        for med in medications:
            # Check if medication matches this drug class
            med_lower = med.lower().strip()
            drug_class_lower = drug_class.lower().strip()
            
            if med_lower in drug_class_lower or drug_class_lower in med_lower:
                # Find matching nutrient in this drug's interactions
                for nutrient_key, details in interactions.items():
                    # Try exact match first
                    if canonical_nutrient.lower() == nutrient_key.lower():
                        evidence_data["grade"] = details.get("evidence_grade", "Unknown")
                        evidence_data["mechanism"] = details.get("mechanism", "")
                        evidence_data["clinical_evidence"] = details.get("clinical_impact", "")
                        evidence_data["dose"] = details.get("dose", "")
                        evidence_data["monitoring"] = details.get("monitoring", "")
                        evidence_data["guideline"] = details.get("source", "")
                        evidence_data["doi"] = details.get("doi", "")
                        evidence_data["sources"].append(f"Drug: {med}")
                        return evidence_data
    
    # Check condition-based needs
    for condition in conditions:
        # Convert to canonical condition name for database lookup
        canonical_condition = get_canonical_condition_name(condition)
        
        if canonical_condition in CONDITION_NUTRIENT_NEEDS:
            for nutrient_key, details in CONDITION_NUTRIENT_NEEDS[canonical_condition].items():
                # Try exact match first
                if canonical_nutrient.lower() == nutrient_key.lower():
                    evidence_data["grade"] = details.get("evidence_grade", "Unknown")
                    evidence_data["mechanism"] = details.get("mechanism", "")
                    evidence_data["clinical_evidence"] = details.get("clinical_evidence", "")
                    evidence_data["dose"] = details.get("dose", "")
                    evidence_data["monitoring"] = details.get("monitoring", "")
                    evidence_data["guideline"] = details.get("source", "")
                    evidence_data["doi"] = details.get("doi", "")
                    evidence_data["sources"].append(f"Condition: {condition}")
                    return evidence_data
    
    return evidence_data

# ============================================================================
# FUNCTION: DISPLAY NUTRIENT WITH EVIDENCE
# ============================================================================

def display_nutrient_with_evidence(nutrient, sources, reasons, evidence_data):
    """
    Display a nutrient recommendation with full evidence details
    """
    # Evidence grade colors
    grade_colors = {
        "A": "🟢",
        "B": "🟡",
        "C": "🟠",
        "D": "🔴"
    }
    
    grade_icon = grade_colors.get(evidence_data.get("grade", "Unknown"), "❓")
    
    st.markdown(f"""
    <div style='border-left: 4px solid #1f77b4; padding: 15px; background-color: #f0f8ff; margin: 10px 0;'>
    <h4>{nutrient.upper()}</h4>
    """, unsafe_allow_html=True)
    
    # Evidence Grade
    grade = evidence_data.get("grade", "Unknown")
    st.markdown(f"**Evidence Grade:** {grade_icon} **{grade}**")
    
    # Show API sources if available
    if evidence_data.get("api_sources"):
        api_sources_str = ", ".join(evidence_data['api_sources'])
        st.markdown(f"📊 **Sources:** {api_sources_str}")
    
    # Mechanism
    if evidence_data.get("mechanism"):
        st.markdown(f"**How It Works:** {evidence_data['mechanism']}")
    
    # Clinical Evidence
    if evidence_data.get("clinical_evidence"):
        st.markdown(f"**Clinical Evidence:** {evidence_data['clinical_evidence']}")
    
    # Recommended Dose
    if evidence_data.get("dose"):
        st.markdown(f"**Evidence-Based Dose:** {evidence_data['dose']}")
    
    # Monitoring
    if evidence_data.get("monitoring"):
        st.markdown(f"**Monitoring Parameters:** {evidence_data['monitoring']}")
    
    # Guideline Source
    if evidence_data.get("guideline"):
        st.markdown(f"**Guideline Source:** {evidence_data['guideline']}")
    
    # DOI/Citation
    if evidence_data.get("doi"):
        st.markdown(f"**Reference:** [`View Study`]({evidence_data['doi']})")
    
    # Reasons from assessment
    if reasons:
        st.markdown("**Why Recommended for This Patient:**")
        for reason in reasons:
            st.markdown(f"- {reason}")
    
    st.markdown("</div>", unsafe_allow_html=True)

@st.cache_data
def load_pharmacy_formulary():
    """Load drug names from pharmacy formulary CSV"""
    try:
        # Try to load from common locations
        df = pd.read_csv('Pharmacy_Formulary_-_Mar_2026_Full_Formulary_.csv')
        drug_names = sorted(df['Drug Name'].unique().tolist())
        return drug_names
    except:
        # If file not found, return empty list (will use fallback)
        return []

# Load formulary at startup
formulary_drugs = load_pharmacy_formulary()

# If formulary loads, use it; otherwise fall back to manual list
if formulary_drugs:
    AVAILABLE_MEDICATIONS = formulary_drugs
else:
    # Fallback: All 683 medications from pharmacy formulary (if CSV not loaded)
    AVAILABLE_MEDICATIONS = [
        "5-ASA", "Abacavir", "Abacavir / lamivudine", "Abiraterone", "Acarbose", "Acebutolol", "Acetazolamide", "Acetylcysteine Solution", "Acetylsalicylic/butalbital/caffeine (Tecnal)", "Acitretin", "Acyclovir", "Acyclovir Oint", "Adapalene / Benzoyl Peroxide", "Adefovir", "Afatinib", "Alendronate", "Alendronate/Vitamin D3", "Alfacalcidol", "Alfuzosin", "Allopurinol", "Almotriptan", "Alprazolam", "Ambrisentan", "Amcinonide", "Amiloride", "Amiloride/HCTZ", "Amiodarone", "Amiodarone Injection", "Amitriptyline", "Amlodipine", "Amlodipine/Atorvastatin", "Amoxicillin", "Amoxicillin / Clavulanate", "Amoxicillin / Clavulanate Susp", "Amoxicillin Suspension", "Amphetamine XR", "Ampicillin", "Ampicillin Sodium Injection", "Anagrelide", "Anastrozole", "Anusol HC (Anodan HC, Jampzinc HC)", "Apixaban", "Aripiprazole", "Ascorbic Acid Injection", "Atazanavir", "Atenolol", "Atenolol/Chlorthalidone", "Atomoxetine", "Atorvastatin", "Atovaquone/Proguanil", "Atropine Injection", "Azathioprine", "Azelastine/Fluticasone nasal", "Azilsartan", "Azithromycin", "Azithromycin Susp", "Baclofen", "Beclomethasone Nasal", "Benazepril", "Benzoyl peroxide/clindamycin", "Benzydamine", "Betahistine", "Betamethasone (Crm, Oint, Lot)", "Betamethasone / Calcipotriol Ointment", "Bezafibrate", "Bicalutamide", "Bilastine", "Bimatoprost", "Bisoprolol", "Bortezomib Inj", "Bosentan", "Brimonidine / Timolol", "Brimonidine Oph Solution", "Brivaracetam", "Bromazepam", "Bromfenac Oph", "Bromocriptine", "Budesonide Inh", "Budesonide Nasal", "Buprenorphine/Naloxone", "Bupropion SR", "Bupropion XL", "Buspirone", "Butorphanol", "Cabergoline", "Calcitriol", "Canagliflozin", "Candesartan", "Candesartan/HCT", "Capecitabine", "Captopril", "Carbamazepine", "Carbamazepine CR", "Carbamazepine Chewtabs", "Carvedilol", "Cefadroxil", "Cefazolin Sodium Injection", "Cefixime", "Cefixime Suspension", "Cefprozil", "Cefprozil Suspension", "Ceftriaxone Sodium Inj", "Cefuroxime", "Celecoxib", "Cephalexin", "Cephalexin Suspension", "Cetirizine (rx)", "Chloral Hydrate", "Chlordiazepoxide", "Chlorhexidine Rinse", "Chlorpromazine", "Chlorthalidone", "Cholestyramine", "Ciclopirox", "Cilazapril", "Cilazapril HCT", "Cimetidine", "Cinacalcet", "Ciprofloxacin", "Ciprofloxacin / Dexamethasone ear drops", "Ciprofloxacin Opth Solution", "Ciprofloxacin XL", "Citalopram", "Cladribine", "Clarithromycin", "Clarithromycin Suspension", "Clarithromycin XL", "Clindamycin", "Clindamycin Topical solution", "Clobazam", "Clobetasol Crm/Oint/Lotion", "Clobetasol Shampoo", "Clobetasol Spray", "Clomipramine", "Clonazepam", "Clonidine", "Clopidogrel", "Clorazepate", "Clotrimazole", "Clotrimazole / Betamethasone", "Cloxacillin", "Clozapine", "Codeine", "Codeine / acetaminophen", "Codeine / acetaminophen / caffeine (Lenoltec)", "Colchicine", "Colesevelam", "Colistimethate Inj", "Cotridin (Co-Actifed)", "Cyclobenzaprine", "Cyclosporine", "Cyclosporine Oph", "Cyproheptadine", "Cyproterone", "Cyproterone/Ethinyl Estradiol (Diane 35)", "Dabigatran", "Dapagliflozin", "Dapagliflozin / Metformin", "Dapsone", "Darunavir", "Dasatinib", "Deferasirox", "Desipramine", "Desmopressin", "Desvenlafaxine", "Dexamethasone", "Dexamethasone Injection", "Dexlansoprazole", "Dextroamphetamine", "Diazepam", "Diazepam Injection", "Diclofenac 1.5% (Pennsaid)", "Diclofenac EC", "Diclofenac Opth", "Diclofenac Rapide / K", "Diclofenac SR", "Diclofenac Sachet", "Diclofenac Sup", "Diclofenac/Misoprostol", "Dicyclomine", "Dienogest", "Digoxin", "Digoxin Injection", "Diltiazem", "Diltiazem CD", "Diltiazem Injection", "Diltiazem T", "Diltiazem XC", "Dimenhydrinate Injection", "Diphenhydramine HCl Injection", "Divalproex", "Dobutamine Injection", "Dolutegravir", "Domperidone", "Donepezil", "Dorzolamide", "Dorzolamide/Timolol", "Doxazosin", "Doxepin", "Doxycycline", "Doxycycline MR", "Doxylamine / pyridoxine", "Drospirenone / ethinyl estradiol (YAZ, Mya-APO)", "Drospirenone / ethinyl estradiol (Yasmin, Zamine-Apo)", "Duloxetine", "Dutasteride", "Edoxaban", "Efavirenz", "Efavirenz / emtricitabine / tenofovir", "Eletriptan", "Eltrombopag", "Emtricitabine / tenofovir", "Enalapril", "Enalapril HCT", "Entacapone", "Entecavir", "Enzalutamide", "Ephedrine Injection", "Eplerenone", "Erlotinib", "Escitalopram", "Escitalopram ODT", "Eslicarbazepine", "Esomeprazole", "Esomeprazole / Naproxen", "Estradiol Derm Patch", "Estradiol tab", "Eszopiclone", "Ethosuximide", "Everolimus", "Exemestane", "Ezetimibe", "Famciclovir", "Famotidine", "Fampridine", "Febuxostat", "Felodipine", "Fenofibrate E", "Fenofibrate Micro", "Fenofibrate S", "Fentanyl Cit Injection", "Fentanyl Patch", "Fesoterodine", "Finasteride", "Flecainide", "Fluconazole", "Fludrocortisone", "Flumazenil Injection", "Flunarizine", "Fluocinonide", "Fluoromethalone Opth", "Fluoxetine", "Fluoxetine Soln", "Fluphenazine", "Flurazepam", "Flurbiprofen", "Flutamide", "Fluticasone / Salmeterol Inh (Myl-Wixela)", "Fluticasone Inh", "Fluticasone Nasal Spray", "Fluvastatin", "Fluvoxamine", "Folic Acid", "Fosfomycin", "Fosinopril", "Frovatriptan", "Fulvestrant Inj", "Furosemide", "Furosemide Injection", "Gabapentin", "Galantamine", "Gatifloxacin Oph", "Gemfibrozil", "Gentamicin Injection", "Gliclazide", "Gliclazide MR", "Glimepiride", "Glyburide", "Glycopyrrolate Injection", "Granisetron", "Guanfacine", "Haloperidol", "Haloperidol Injection", "Haloperidol LA Injection", "Heparin Injection", "Hydralazine", "Hydrochlorothiazide", "Hydrocortisone Crm/Oint", "Hydrocortisone Tab", "Hydromorphone", "Hydromorphone HCl Injection", "Hydromorphone Syrup", "Hydroxychloroquine", "Hydroxyurea", "Hydroxyzine", "Hyoscine Injection", "Ibuprofen", "Imatinib", "Imipramine", "Imiquimod", "Indapamide", "Indomethacin", "Ipratropium / Salbutamol", "Ipratropium Inh Soln", "Ipratropium Nasal", "Ipratropium Puffer", "Irbesartan", "Irbesartan HCT", "Iron Sucrose Injection", "Isosorbide Dinitrate (ISDN)", "Isosorbide Mononitrate (ISMN)", "Isotretinoin (Myl-Clarus)", "Itraconazole", "Itraconazole Soln", "Ketamine Injection", "Ketoconazole", "Ketoconazole cream", "Ketoprofen", "Ketorolac", "Ketorolac Injection", "Ketorolac Opth", "Ketotifen Oph", "Labetalol", "Labetalol Injection", "Lacosamide", "Lamivudine", "Lamivudine / Zidovudine", "Lamotrigine", "Lansoprazole", "Lansoprazole / Amoxicillin / Clarithromycin", "Latanoprost", "Latanoprost/Timolol", "Leflunomide", "Letrozole", "Leucovorin", "Levetiracetam", "Levetiracetam Oral Solution", "Levocarb CR", "Levocarbidopa", "Levofloxacin", "Levonorgestrel (Plan B, Apo - Backup Plan, Mylan - Contingency One, Jamp - Mystep)", "Levonorgestrel / Ethinyl Estradiol (Alesse; Apo - Alysena, Teva - Aviane)", "Levothyroxine", "Linezolid", "Liothyronine", "Lisdexamfetamine", "Lisinopril", "Lisinopril HCT", "Lithium Carbonate", "Lorazepam", "Lorazepam Injection", "Losartan", "Losartan HCT", "Lovastatin", "Loxapine Inj", "Lurasidone", "Marvelon or Ortho Cept Generic (Apo - Mirvala, Teva - Apri, Myl-Freya)", "Medroxyprogesterone", "Mefenamic Acid", "Mefloquine", "Megestrol", "Meloxicam", "Memantine", "Meperidine Injection", "Meropenem Injection", "Metformin", "Metformin ER / XR", "Methadone Liquid (only brand Methadose/Metadol-D covered for OAT)", "Methadone Tabs", "Methazolamide", "Methimazole", "Methoprazine", "Methotrexate", "Methotrexate Injection", "Methyldopa", "Methylphenidate", "Methylphenidate CR (Biphentin)", "Methylphenidate ER (Concerta)", "Metoclopramide", "Metoclopramide Injection", "Metoclopramide Solution", "Metoprolol", "Metoprolol Injection", "Metoprolol SR", "Metronidazole", "Mexiletine", "Midazolam Injection", "Midodrine", "Min-Ovral Generic (Apo-Ovima, Teva-Portia)", "Minocycline", "Mirabegron", "Mirtazapine", "Mirtazapine OD", "Misoprostol", "Moclobemide", "Modafinil", "Mometasone Crm/Lot/Oint", "Mometasone Nasal Spray", "Montelukast", "Morphine", "Morphine Injection", "Morphine SR", "Moxifloxacin", "Moxifloxacin Oph", "Mupirocin", "Mycophenolate", "Mycophenolate Susp", "Mycophenolic Acid", "Nabilone", "Nabumetone", "Nadolol", "Naloxone Injection", "Naltrexone", "Naproxen", "Naproxen EC", "Naproxen Sodium", "Naratriptan", "Nebivolol", "Nevirapine", "Nifedipine", "Nifedipine XL", "Nintedanib", "Nitrofurantoin", "Nitrofurantoin Macrocrystals", "Nitrofurantoin Monohydrate/Macrocrystals", "Nitroglycerin Patch", "Nitroglycerin Pumpspray", "Norepinephrine Injection", "Norethidrone (Brand-Micronor, Myl-Movisse)", "Norethidrone / Ethinyl Estradiol (Brand-Lolo, Apo-Elfy)", "Norfloxacin", "Nortriptyline", "Nystatin", "OTC-Acetaminophen", "OTC-Acetylsalicylic Acid (Pms-Praxis)", "OTC-Bisacodyl", "OTC-Bisacodyl Supp", "OTC-Calcium + Vit D", "OTC-Calcium Carbonate", "OTC-Cetirizine", "OTC-Dimenhydrinate", "OTC-Diphenhydramine", "OTC-Docusate", "OTC-Ferrous Fumarate (PRZ-Ferofit, Jamp-Wamp Ferrous Fumarate, Sdz-Euro Ferrous Fumarate)", "OTC-Ferrous Gluconate", "OTC-Ferrous Polysaccharide", "OTC-Ferrous Sulfate", "OTC-Ferrous Sulfate Soln", "OTC-Folic Acid 1mg", "OTC-Glucose", "OTC-Iron Polypeptide", "OTC-Lactase Enzyme", "OTC-Lactulose", "OTC-Loperamide", "OTC-Loratadine", "OTC-Magnesium", "OTC-Niacin", "OTC-Peglyte (Jamp-Lyte)", "OTC-Polyethylene Glycol (Jamp-Emolax, Pms-Lax-A-Day)", "OTC-Pyrantel Pamoate", "OTC-Sennosides", "OTC-Sennosides / Docusate", "OTC-Sodium Bicarbonate", "OTC-Vitamin B12", "OTC-Vitamin B6", "Octreotide Injection", "Olanzapine", "Olanzapine ODT", "Olmesartan", "Olmesartan / HCT", "Olopatadine", "Omeprazole", "Ondansetron", "Ondansetron Injection", "Ondansetron ODT", "Ondansetron Oral Solution", "Orphenadrine", "Oseltamivir", "Oxazepam", "Oxcarbazepine", "Oxybutynin", "Oxycodone (Sdz-Supeudol)", "Oxycodone / ASA (Teva-Oxycodan, Percodan)", "Oxycodone / Acetaminophen (Oxycocet)", "Oxycodone CR", "Oxycodone Supp (Sdz-Supeudol)", "Pantoprazole Magnesium", "Pantoprazole Sodium", "Papaverine Injection", "Paroxetine", "Pazopanib", "Pen Needles", "Penicillin", "Pentoxifylline", "Perampanel", "Perindopril", "Perindopril / Amlodipine", "Perindopril / Indapamide", "Perphenazine", "Phenobarbital Injection", "Phentolamine Injection", "Phenylephrine Injection", "Phenytoin", "Phenytoin Injection", "Phenytoin Suspension", "Pilocarpine", "Pimozide", "Pindolol", "Pioglitazone", "Piperacillin/Tazobactam Injection", "Piroxicam", "Posaconazole", "Potassium", "Pramipexole", "Pravastatin", "Prazosin", "Prednisolone Oph Suspension", "Prednisolone Oral Soln", "Prednisone", "Pregabalin", "Primidone", "Procainamide Injection", "Prochlorperazine", "Progesterone", "Progesterone Inj", "Propafenone", "Propranolol", "Propranolol Injection", "Protamine Injection", "Prucalopride", "Pyridostigmine", "Quetiapine", "Quetiapine XR", "Quinapril", "Quinapril / HCTZ", "Quinine", "Rabeprazole", "Raloxifene", "Ramipril", "Ramipril/HCTZ", "Ranitidine", "Rasagiline", "Repaglinide", "Riluzole", "Risedronate", "Risperidone", "Risperidone Liquid", "Ritonavir", "Rivaroxaban", "Rivastigmine", "Rivastigmine Patch", "Rizatriptan", "Rizatriptan ODT", "Rocuronium Injection", "Ropinirole", "Rosiglitazone", "Rosuvastatin", "Rufinamide", "Rupatadine", "SPECIALTY - Apremilast", "SPECIALTY - Dimethyl Fumarate", "SPECIALTY - Fingolimod", "SPECIALTY - Pirfenidone", "SPECIALTY - Teriflunomide", "SPECIALTY - Tofacitinib", "SPECIALTY - Tofacitinib XR", "Sacubitril/Valsartan", "Salbutamol Nebules", "Salbutamol Puffer", "Saxagliptin", "Seasonale (Myl-Indayo)", "Selegiline", "Semaglutide Inj", "Sertraline", "Sildenafil", "Silodosin", "Simvastatin", "Sitagliptin", "Sitagliptin / Metformin", "Sitagliptin / Metformin XR", "Sodium Bicarbonate Inj", "Sodium Phosphate", "Sodium Polystyrene Sulfonate", "Solifenacin", "Sotalol", "Spironolactone", "Spironolactone HCT", "Sucralfate", "Sufentanil Injection", "Sulfasalazine", "Sulfatrim", "Sulindac", "Sumatriptan", "Sumatriptan DF", "Sumatriptan Inj", "Sunitinib", "Tacrolimus", "Tacrolimus XR", "Tadalafil", "Tamoxifen", "Tamsulosin CR", "Tamsulosin SR", "Telmisartan", "Telmisartan HCT", "Temazepam", "Temozolomide", "Tenofovir", "Terazosin", "Terbinafine", "Terconazole Vag crm", "Teriparatide Inj", "Testosterone Cap", "Testosterone Cyp Injection", "Testosterone gel", "Tetrabenazine", "Tetracycline", "Theophylline", "Tiaprofenic", "Ticagrelor", "Timolol", "Timolol Oph Sol", "Tiotropium", "Tizanidine", "Tobramycin Inh", "Tobramycin Injection", "Tobramycin Oph Sol", "Tolterodine", "Tolterodine ER", "Topiramate", "Tramadol", "Tramadol ER", "Tramadol/Acetaminophen", "Trandolapril", "Tranexamic Acid", "Tranexamic Acid Injection", "Travoprost", "Travoprost / Timolol", "Trazodone", "TriCyclen Lo (Apo-Tricira Lo)", "Triamcinolone / Nystatin / Neomycin / Gramicidin (Viaderm KC, Teva-Triacomb)", "Triamcinolone Nasal", "Triamcinolone crm/oint", "Triamterene HCTZ", "Triazolam", "Trifluoperazine", "Trihexyphenidyl", "Trimebutine", "Trimethoprim", "Trimipramine", "Trospium", "Tryptophan", "Ursodiol", "Valacyclovir", "Valganciclovir", "Valganciclovir Susp", "Valproic Acid", "Valproic Acid Oral Soln", "Valsartan", "Valsartan HCT", "Vancomycin", "Vancomycin Injection", "Vardenafil", "Vardenafil ODT", "Varenicline", "Vasopressin Inj", "Venlafaxine XR", "Verapamil", "Verapamil Injection", "Verapamil SR", "Vilazodone", "Vitamin B12 Injection", "Vitamin D 10,000", "Voriconazole", "Vortioxetine", "Warfarin", "Zidovudine", "Ziprasidone", "Zoledronic Injection 4mg", "Zoledronic Injection 5mg", "Zolmitriptan", "Zolmitriptan ODT", "Zolpidem ODT", "Zopiclone"
    ]

# Custom CSS
st.markdown("""
<style>
    .recommendation-box {
        background-color: #f0f8ff;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #0066cc;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #ff9800;
        margin: 10px 0;
    }
    .interaction-alert {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #dc3545;
        margin: 10px 0;
    }
    .header-title {
        color: #1f77b4;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CLINICAL KNOWLEDGE BASE
# ============================================================================

DRUG_NUTRIENT_INTERACTIONS = {
    # Diabetes medications
    "metformin": {
        "deficiencies": ["Vitamin B12", "Folate", "Calcium"],
        "severity": "moderate",
        "notes": "Reduces B12 absorption; increases risk of neuropathy if untreated"
    },
    "glp-1 agonist": {
        "deficiencies": ["Vitamin B12", "Calcium", "Iron"],
        "severity": "moderate",
        "notes": "GI effects may reduce nutrient absorption"
    },
    "sulfonylurea": {
        "deficiencies": ["Folate"],
        "severity": "mild",
        "notes": "May increase folate requirements"
    },
    
    # Cardiovascular
    "ace inhibitor": {
        "deficiencies": ["Zinc"],
        "severity": "mild",
        "notes": "May cause zinc loss; taste changes possible"
    },
    "diuretic": {
        "deficiencies": ["Potassium", "Magnesium", "Calcium", "Zinc"],
        "severity": "moderate",
        "notes": "Loop/thiazide diuretics increase electrolyte excretion"
    },
    "beta blocker": {
        "deficiencies": ["CoQ10"],
        "severity": "mild",
        "notes": "May reduce CoQ10; consider for heart failure patients"
    },
    "statin": {
        "deficiencies": ["CoQ10"],
        "severity": "mild",
        "notes": "Depletes CoQ10; may cause muscle symptoms"
    },
    
    # Thyroid
    "levothyroxine": {
        "deficiencies": ["Iron", "Calcium", "Selenium"],
        "severity": "moderate",
        "notes": "Absorption impaired by Ca, Fe, Mg; require 4-hour spacing"
    },
    
    # Gastrointestinal
    "ppi": {
        "deficiencies": ["Vitamin B12", "Calcium", "Iron", "Magnesium"],
        "severity": "moderate",
        "notes": "Chronic use increases risk of deficiency; >1 year = screen B12"
    },
    "h2 blocker": {
        "deficiencies": ["Vitamin B12", "Iron", "Calcium"],
        "severity": "mild",
        "notes": "Less severe than PPIs but still affects absorption"
    },
    
    # Bone health
    "bisphosphonate": {
        "deficiencies": ["Calcium", "Vitamin D"],
        "severity": "moderate",
        "notes": "Requires adequate Ca/D for efficacy and safety"
    },
    
    # Immunosuppressants
    "corticosteroid": {
        "deficiencies": ["Vitamin D", "Calcium", "Potassium"],
        "severity": "moderate",
        "notes": "Impairs D metabolism; increases osteoporosis risk"
    },
    
    # Antibiotics
    "fluoroquinolone": {
        "deficiencies": ["Magnesium"],
        "severity": "mild",
        "notes": "May chelate minerals"
    },
    
    # Psychiatric
    "lithium": {
        "deficiencies": ["Iodine"],
        "severity": "mild",
        "notes": "Monitor thyroid function"
    },
}

CONDITION_NUTRIENT_NEEDS = {
    "Type 2 Diabetes": {
        "nutrients": ["Chromium", "Vitamin B-Complex", "Alpha-Lipoic Acid", "Cinnamon"],
        "priority": "high",
        "notes": "Chromium improves insulin sensitivity; B vitamins for neuropathy prevention"
    },
    "Hypertension": {
        "nutrients": ["Potassium", "Magnesium", "Calcium", "CoQ10"],
        "priority": "high",
        "notes": "DASH diet alignment; CoQ10 for those on statins"
    },
    "Osteoporosis": {
        "nutrients": ["Calcium", "Vitamin D3", "Vitamin K2", "Magnesium"],
        "priority": "high",
        "notes": "Requires adequate D3 (1000-2000 IU daily); K2 for bone quality"
    },
    "Heart Disease": {
        "nutrients": ["Omega-3", "CoQ10", "Magnesium", "Folate"],
        "priority": "high",
        "notes": "CoQ10 especially important if on statins"
    },
    "Anemia": {
        "nutrients": ["Iron", "Vitamin B12", "Folate"],
        "priority": "high",
        "notes": "Determine type before supplementing iron; intrinsic factor?"
    },
    "Thyroid Disorder": {
        "nutrients": ["Selenium", "Iron", "Zinc", "Iodine"],
        "priority": "high",
        "notes": "Selenium for autoimmune thyroiditis; space iron 4h from levothyroxine"
    },
    "Depression": {
        "nutrients": ["Vitamin D", "B-Complex", "Omega-3", "Magnesium"],
        "priority": "moderate",
        "notes": "Vitamin D deficiency linked to depression; seasonal assessment"
    },
    "Cognitive Decline": {
        "nutrients": ["Vitamin B12", "Folate", "Vitamin D", "Omega-3"],
        "priority": "moderate",
        "notes": "B12 deficiency can mimic dementia; assess before assuming decline"
    },
}

LIFESTYLE_NUTRIENT_NEEDS = {
    "Vegan/Vegetarian": {
        "nutrients": ["Vitamin B12", "Iron", "Zinc", "Omega-3"],
        "notes": "Plant-based iron less bioavailable; consider supplementation"
    },
    "Heavy Alcohol Use": {
        "nutrients": ["Thiamine (B1)", "Folate", "B12", "Magnesium"],
        "notes": "Alcohol impairs absorption and metabolism"
    },
    "Smoker": {
        "nutrients": ["Vitamin C", "Vitamin E", "Selenium"],
        "notes": "Increased oxidative stress; avoid high-dose beta-carotene"
    },
    "Limited Sun Exposure": {
        "nutrients": ["Vitamin D3"],
        "notes": "Consider 1000-2000 IU daily year-round"
    },
    "High Stress": {
        "nutrients": ["B-Complex", "Magnesium", "Vitamin C"],
        "notes": "Stress increases cortisol and nutrient depletion"
    },
    "Athlete/High Exercise": {
        "nutrients": ["Magnesium", "Iron", "Zinc", "Electrolytes"],
        "notes": "Increased loss through sweat; monitor hydration status"
    },
}

NUTRIENT_INFO = {
    "Vitamin D3": {
        "daily_value": "1000-2000 IU",
        "max_safe": "4000 IU",
        "form": "D3 preferred over D2",
        "timing": "With fat-containing meal",
        "warning": "Monitor PTH if >2000 IU; check calcium"
    },
    "Vitamin B12": {
        "daily_value": "1-2 mcg",
        "max_safe": "No known toxicity",
        "form": "Sublingual or IM for absorption issues",
        "timing": "Any time",
        "warning": "Check intrinsic factor if pernicious anemia suspected"
    },
    "Folate": {
        "daily_value": "400 mcg",
        "max_safe": "5000 mcg (Lozalzapam limit)",
        "form": "Methylfolate better if MTHFR mutation",
        "timing": "Any time",
        "warning": "Don't mask B12 deficiency; check both"
    },
    "Calcium": {
        "daily_value": "800-1200 mg",
        "max_safe": "2500 mg/day",
        "form": "Citrate better than carbonate for absorption",
        "timing": "With food, split doses",
        "warning": "Space 4h from levothyroxine, PPI use affects absorption"
    },
    "Magnesium": {
        "daily_value": "300-400 mg",
        "max_safe": "400 mg/day",
        "form": "Glycinate or citrate; avoid oxide (laxative)",
        "timing": "Evening preferred",
        "warning": "May cause loose stools; take with meals"
    },
    "Iron": {
        "daily_value": "8-18 mg",
        "max_safe": "No known upper limit",
        "form": "Ferrous over ferric; ascorbic acid enhances",
        "timing": "On empty stomach, separate from PPI",
        "warning": "Causes constipation; don't supplement without diagnosis"
    },
    "Zinc": {
        "daily_value": "8-11 mg",
        "max_safe": "40 mg/day",
        "form": "Picolinate, citrate, glycinate preferred",
        "timing": "With food",
        "warning": "Can impair copper absorption; balance needed"
    },
    "CoQ10": {
        "daily_value": "100-200 mg",
        "max_safe": "1200 mg",
        "form": "Ubiquinol more bioavailable than ubiquinone",
        "timing": "With fat-containing meal",
        "warning": "May reduce warfarin efficacy; monitor INR"
    },
    "Omega-3": {
        "daily_value": "1000-2000 mg",
        "max_safe": "3000 mg/day",
        "form": "Fish oil or algae-based (vegan)",
        "timing": "With meals",
        "warning": "May increase bleeding risk if on anticoagulants"
    },
    "Vitamin C": {
        "daily_value": "75-90 mg",
        "max_safe": "2000 mg/day",
        "form": "Any form; buffered for sensitive GI",
        "timing": "Any time",
        "warning": "High doses may increase kidney stone risk if predisposed"
    },
}

# ============================================================================
# PDF GENERATION FUNCTION
# ============================================================================

def generate_pdf(patient_id, age, sex, bmi, medications, conditions, 
                 diet_type, symptoms, nutrient_recommendations, nutrient_reasons, 
                 NUTRIENT_INFO, sorted_nutrients):
    """Generate professional PDF assessment report"""
    
    # Create PDF in memory
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter,
                          rightMargin=0.5*inch, leftMargin=0.5*inch,
                          topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0066cc'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#0066cc'),
        spaceAfter=8,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Title
    story.append(Paragraph("SMART VITAMIN ASSESSMENT", title_style))
    story.append(Paragraph("Personalized Nutrient Recommendations", styles['Normal']))
    story.append(Spacer(1, 0.15*inch))
    
    # Patient Info
    story.append(Paragraph("Patient Information", heading_style))
    patient_data = [
        ['Patient ID:', patient_id if patient_id else 'Not recorded'],
        ['Age:', f'{age} years'],
        ['Sex:', sex],
        ['BMI:', f'{bmi:.1f}'],
        ['Assessment Date:', datetime.now().strftime('%Y-%m-%d')]
    ]
    
    t_patient = Table(patient_data, colWidths=[1.5*inch, 3*inch])
    t_patient.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f8ff')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(t_patient)
    story.append(Spacer(1, 0.2*inch))
    
    # Medical Profile
    story.append(Paragraph("Medical Profile", heading_style))
    med_text = f"<b>Medications:</b> {', '.join(medications) if medications else 'None recorded'}<br/>"
    med_text += f"<b>Conditions:</b> {', '.join(conditions) if conditions else 'None recorded'}<br/>"
    med_text += f"<b>Diet:</b> {', '.join(diet_type) if diet_type else 'Omnivore'}<br/>"
    med_text += f"<b>Symptoms:</b> {', '.join(symptoms) if symptoms else 'None reported'}"
    story.append(Paragraph(med_text, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Recommendations
    story.append(Paragraph("Evidence-Based Nutrient Recommendations", heading_style))
    
    # Add note about evidence grading
    evidence_note = """
    <b>Evidence Grading:</b> 🟢 Grade A (Strong RCT evidence) • 🟡 Grade B (Moderate evidence) • 
    🟠 Grade C (Weak evidence) • 🔴 Grade D (Insufficient evidence)<br/>
    <br/>
    Each recommendation includes mechanism, clinical evidence, dosing based on trials, 
    monitoring parameters, and guideline sources from ADA, AHA, Endocrine Society, and other 
    peer-reviewed clinical guidelines.
    """
    story.append(Paragraph(evidence_note, ParagraphStyle('Note', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#666666'))))
    story.append(Spacer(1, 0.15*inch))
    
    if not nutrient_recommendations:
        story.append(Paragraph("No specific nutrient needs identified. Maintain general health with balanced diet.", body_style))
    else:
        rec_num = 1
        for nutrient, sources in sorted_nutrients:
            if nutrient in NUTRIENT_INFO:
                info = NUTRIENT_INFO[nutrient]
                
                # Get evidence data
                evidence_data = get_evidence_for_nutrient(nutrient, medications, conditions)
                
                # DEBUG: Check if evidence was found
                if evidence_data.get("grade") == "Unknown":
                    import sys
                    print(f"DEBUG: No evidence found for {nutrient}", file=sys.stderr)
                    print(f"  Medications: {medications}", file=sys.stderr)
                    print(f"  Conditions: {conditions}", file=sys.stderr)
                else:
                    import sys
                    print(f"DEBUG: Found evidence for {nutrient}: Grade {evidence_data.get('grade')}", file=sys.stderr)
                
                # Nutrient heading with evidence grade
                grade_icon = {
                    "A": "🟢",
                    "B": "🟡",
                    "C": "🟠",
                    "D": "🔴"
                }.get(evidence_data.get("grade", "?"), "❓")
                
                rec_heading = f"{rec_num}. {nutrient.upper()} [{grade_icon} Grade {evidence_data.get('grade', 'Unknown')}]"
                story.append(Paragraph(rec_heading, ParagraphStyle('RecHeading', parent=styles['Heading3'], fontSize=11, textColor=colors.HexColor('#0066cc'), spaceAfter=6)))
                
                # Evidence-based dose (if available)
                if evidence_data.get("dose"):
                    rec_text = f"<b>Evidence-Based Dose:</b> {evidence_data['dose']}<br/>"
                else:
                    rec_text = f"<b>Dose:</b> {info['daily_value']}<br/>"
                
                rec_text += f"<b>Form:</b> {info['form']}<br/>"
                rec_text += f"<b>Timing:</b> {info['timing']}<br/>"
                rec_text += f"<b>Important Note:</b> {info['warning']}"
                story.append(Paragraph(rec_text, body_style))
                
                # Mechanism of action
                if evidence_data.get("mechanism"):
                    story.append(Paragraph(f"<b>Mechanism:</b> {evidence_data['mechanism']}", body_style))
                
                # Clinical evidence
                if evidence_data.get("clinical_evidence"):
                    story.append(Paragraph(f"<b>Clinical Evidence:</b> {evidence_data['clinical_evidence']}", body_style))
                
                # Monitoring
                if evidence_data.get("monitoring"):
                    story.append(Paragraph(f"<b>Monitoring:</b> {evidence_data['monitoring']}", body_style))
                
                # Guideline source
                if evidence_data.get("guideline"):
                    story.append(Paragraph(f"<b>Guideline:</b> {evidence_data['guideline']}", body_style))
                
                # DOI
                if evidence_data.get("doi"):
                    story.append(Paragraph(f"<b>DOI:</b> {evidence_data['doi']}", body_style))
                
                # Reasons
                story.append(Paragraph("<b>Why this nutrient for this patient:</b>", body_style))
                for reason in nutrient_reasons[nutrient]:
                    story.append(Paragraph(f"• {reason}", body_style))
                
                story.append(Spacer(1, 0.15*inch))
            
            rec_num += 1
    
    story.append(Spacer(1, 0.15*inch))
    
    # Next Steps
    story.append(Paragraph("Next Steps", heading_style))
    next_steps = """
    1. Review recommendations with your pharmacist
    2. Discuss any concerns or known allergies
    3. Start with recommended supplements as directed
    4. Report any side effects to your pharmacist
    5. Schedule follow-up assessment in 8-12 weeks
    """
    story.append(Paragraph(next_steps, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Disclaimer
    story.append(Paragraph("Important Disclaimer", heading_style))
    disclaimer = """
    <i>This assessment is for educational purposes only. It is not a medical diagnosis. 
    Please consult with your healthcare provider before starting any new supplement, 
    especially if you are pregnant, breastfeeding, or taking medications with potential interactions.</i>
    """
    story.append(Paragraph(disclaimer, body_style))
    
    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

# ============================================================================
# INITIALIZATION
# ============================================================================

if 'assessment_data' not in st.session_state:
    st.session_state.assessment_data = {}
if 'custom_medications' not in st.session_state:
    st.session_state.custom_medications = []
if 'custom_conditions' not in st.session_state:
    st.session_state.custom_conditions = []

# ============================================================================
# MAIN APP
# ============================================================================

st.markdown("<div class='header-title'>💊 Smart Vitamin Assessment Tool</div>", unsafe_allow_html=True)
st.markdown("*Evidence-based personalized nutrient recommendations for pharmacy patients*")

st.divider()

# Sidebar configuration
with st.sidebar:
    st.header("Assessment Config")
    assessment_type = st.radio(
        "Select Assessment Type",
        ["New Patient", "Follow-up Assessment", "Data Analysis"],
        help="New Patient = full workup; Follow-up = focused on changes"
    )
    
    show_clinical_notes = st.checkbox("Show Pharmacist Notes", value=True)
    show_interactions = st.checkbox("Show Drug-Nutrient Interactions", value=True)

# ============================================================================
# PATIENT INFORMATION
# ============================================================================

st.header("👤 Patient Information")
col1, col2, col3 = st.columns(3)

with col1:
    patient_id = st.text_input("Patient ID (optional)", value="")
    age = st.number_input("Age", min_value=18, max_value=120, value=55)

with col2:
    sex = st.selectbox("Sex", ["Female", "Male", "Non-binary", "Prefer not to say"])
    pregnancy_status = st.selectbox(
        "Pregnancy Status (if applicable)",
        ["Not applicable", "Planning pregnancy", "Pregnant", "Breastfeeding"]
    )

with col3:
    height_cm = st.number_input("Height (cm)", min_value=100, max_value=250, value=170)
    weight_kg = st.number_input("Weight (kg)", min_value=30, max_value=250, value=75)

bmi = weight_kg / ((height_cm/100) ** 2)

st.divider()

# ============================================================================
# MEDICATIONS
# ============================================================================

st.header("💊 Current Medications")
st.markdown("*Search and select medications from pharmacy formulary*")

# Show info about formulary
if formulary_drugs:
    st.info(f"✓ Loaded {len(AVAILABLE_MEDICATIONS)} medications from pharmacy formulary")

# Combine available medications with custom ones
all_medication_options = list(set(AVAILABLE_MEDICATIONS + st.session_state.custom_medications))

# Add common brand names that might not be in formulary
brand_name_aliases = {
    "Ozempic": "Semaglutide Inj",
    "Trulicity": "Dulaglutide",
    "Humalog": "Insulin Lispro",
    "Lantus": "Insulin Glargine",
    "Metformin ER": "Metformin ER / XR",
}

# Add aliases to the list if the generic version exists
for brand, generic in brand_name_aliases.items():
    if generic in all_medication_options and brand not in all_medication_options:
        all_medication_options.append(brand)

all_medication_options.sort()

# Helpful hint about common medications
with st.expander("🔍 **Can't find your medication?** (Click to see common ones)", expanded=False):
    st.markdown("""
    **Medications we support:**
    - Ozempic (search "Ozempic" or "Semaglutide")
    - Metformin (search "Metformin")
    - Levothyroxine (search "Levothyroxine")
    - Metoprolol (search "Metoprolol")
    - Atorvastatin, Simvastatin (search "statin")
    - Amlodipine (search "Amlodipine")
    - Omeprazole (search "Omeprazole")
    
    💡 **Pro tip:** Start typing to search! Don't see it? Scroll down to "Add medication not in list"
    """)

# Searchable medication multiselect
medications = st.multiselect(
    "Search and select medications",
    all_medication_options,
    help="Type to search for medication name. Select all that apply.",
    key="meds_select"
)

# Add custom medication if not in list
st.markdown("**Add medication not in list (optional):**")
col_custom1, col_custom2 = st.columns([4, 1])
with col_custom1:
    custom_med = st.text_input(
        "Type medication name",
        placeholder="e.g., Jardiance",
        label_visibility="collapsed",
        key="custom_med_input"
    )
with col_custom2:
    st.write("")  # Spacing
    if st.button("➕ Add", use_container_width=True, key="add_med_btn"):
        if custom_med and custom_med.strip():
            if custom_med.strip() not in st.session_state.custom_medications:
                st.session_state.custom_medications.append(custom_med.strip())
                # Clear the input field
                st.session_state.custom_med_input = ""
                st.success(f"✅ Added: {custom_med}")
                # Don't rerun - let the script continue and update on next interaction
    
    # Show count of custom medications
    if st.session_state.custom_medications:
        st.caption(f"✓ {len(st.session_state.custom_medications)} custom")

st.divider()

# ============================================================================
# MEDICAL CONDITIONS
# ============================================================================

st.header("🏥 Medical Conditions")

# Combine available conditions with custom ones
all_condition_options = list(set(list(CONDITION_NUTRIENT_NEEDS.keys()) + st.session_state.custom_conditions))
all_condition_options.sort()

# Helpful hint about common conditions
with st.expander("🔍 **Which conditions do we support?** (Click to see)", expanded=False):
    st.markdown("""
    **Conditions with evidence-based nutrient protocols:**
    - Type 2 Diabetes (search "Type 2 Diabetes")
    - Hypertension (search "Hypertension" or "High Blood Pressure")
    - Heart Disease (search "Heart Disease" or "Coronary Artery")
    - Dyslipidemia (search "Dyslipidemia" or "High Cholesterol")
    - Osteoporosis (search "Osteoporosis")
    - Cognitive Decline (search "Cognitive Decline")
    - Frailty / Aging (search "Frailty" or "Aging")
    
    💡 **Pro tip:** Start typing to search! Don't see yours? You can add custom conditions below
    """)

conditions = st.multiselect(
    "Select Relevant Conditions",
    all_condition_options,
    help="Conditions that increase nutrient requirements",
    key="conditions_select"
)

# Add custom conditions
st.markdown("**Add custom conditions (comma-separated):**")
col_cond1, col_cond2 = st.columns([4, 1])
with col_cond1:
    custom_cond_input = st.text_input(
        "Type condition name",
        placeholder="e.g., Arthritis, Autoimmune disease",
        label_visibility="collapsed",
        key="custom_cond_input"
    )
with col_cond2:
    st.write("")  # Spacing
    if st.button("➕ Add", use_container_width=True, key="add_condition_btn"):
        if custom_cond_input and custom_cond_input.strip():
            # Parse comma-separated conditions
            new_conditions = [c.strip() for c in custom_cond_input.split(',') if c.strip()]
            for cond in new_conditions:
                if cond not in st.session_state.custom_conditions:
                    st.session_state.custom_conditions.append(cond)
            # Clear the input field
            st.session_state.custom_cond_input = ""
            st.success(f"✅ Added: {', '.join(new_conditions)}")
            # Don't rerun - let the script continue and update on next interaction
    
    # Show count of custom conditions
    if st.session_state.custom_conditions:
        st.caption(f"✓ {len(st.session_state.custom_conditions)} custom")

st.divider()

# ============================================================================
# LIFESTYLE & DIET
# ============================================================================

st.header("🍽️ Lifestyle & Diet")

col1, col2 = st.columns(2)

with col1:
    diet_type = st.multiselect(
        "Diet Type",
        ["Omnivore", "Vegan", "Vegetarian", "Pescatarian", "Keto", "Mediterranean"],
        default=["Omnivore"],
        key="diet_select"
    )
    
    exercise = st.selectbox(
        "Exercise Level",
        ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Athlete"]
    )

with col2:
    alcohol = st.selectbox(
        "Alcohol Consumption",
        ["None", "Occasional (< 1x/week)", "Moderate (1-2x/week)", "Regular (3-7x/week)", "Heavy (daily)"]
    )
    
    smoking = st.selectbox(
        "Smoking Status",
        ["Non-smoker", "Former smoker", "Occasional", "Daily smoker"]
    )

sun_exposure = st.selectbox(
    "Sun Exposure",
    ["High (>30 min/day)", "Moderate (15-30 min/day)", "Low (<15 min/day)", "Very Low (indoor)"]
)

st.divider()

# ============================================================================
# SYMPTOMS / CONCERNS
# ============================================================================

st.header("⚠️ Current Symptoms or Concerns")
symptoms = st.multiselect(
    "Select any current symptoms",
    [
        "Fatigue/Low Energy",
        "Poor Memory/Brain Fog",
        "Muscle Weakness/Cramping",
        "Bone Pain/Weakness",
        "Numbness/Tingling in Extremities",
        "Hair Loss",
        "Poor Wound Healing",
        "Mood Issues",
        "Brittle Nails",
        "Dry Skin",
        "Frequent Infections",
        "Irregular Heartbeat",
        "None"
    ],
    key="symptoms_select"
)

# ============================================================================
# SMART DRUG MATCHING
# ============================================================================

def match_drug_to_interactions(selected_medications, drug_db):
    """
    Match selected medications to drug-nutrient interactions database.
    Handles partial matches and variations in drug names.
    """
    # Map brand names to database keys
    brand_to_generic = {
        "ozempic": "glp-1 agonists (semaglutide, liraglutide)",
        "semaglutide": "glp-1 agonists (semaglutide, liraglutide)",
        "trulicity": "glp-1 agonists (semaglutide, liraglutide)",
        "dulaglutide": "glp-1 agonists (semaglutide, liraglutide)",
        "liraglutide": "glp-1 agonists (semaglutide, liraglutide)",
    }
    
    matched_interactions = []
    
    # Create lowercase version of drug_db keys for matching
    drug_db_lower = {key.lower(): (key, value) for key, value in drug_db.items()}
    
    for med in selected_medications:
        med_lower = med.lower()
        
        # Check if this is a brand name - if so, convert to generic
        canonical_med = brand_to_generic.get(med_lower, med_lower)
        
        # Exact match (case-insensitive)
        if canonical_med in drug_db_lower:
            db_key, interaction_data = drug_db_lower[canonical_med]
            matched_interactions.append((med, interaction_data))
            continue
        
        # Partial match - check if any database drug is substring of selected drug
        # E.g., "Metformin 500mg" contains "metformin"
        for db_drug_lower, (db_drug_original, interaction_data) in drug_db_lower.items():
            if db_drug_lower in canonical_med:
                matched_interactions.append((med, interaction_data))
                break
        else:
            # If no match found, check for common drug class keywords
            keywords = {
                'metformin': 'metformin',
                'insulin': 'glp-1 agonist',
                'ozempic': 'glp-1 agonist',
                'semaglutide': 'glp-1 agonist',
                'liraglutide': 'glp-1 agonist',
                'trulicity': 'glp-1 agonist',
                'dulaglutide': 'glp-1 agonist',
                'omeprazole': 'ppi',
                'ppi': 'ppi',
                'proton pump': 'ppi',
                'statin': 'statin',
                'atorvastatin': 'statin',
                'simvastatin': 'statin',
                'diuretic': 'diuretic',
                'furosemide': 'diuretic',
                'hctz': 'diuretic',
                'bisphosphonate': 'bisphosphonate',
                'alendronate': 'bisphosphonate',
                'thyroid': 'levothyroxine',
                'levothyroxine': 'levothyroxine',
                'metoprolol': 'beta-blockers',
                'atenolol': 'beta-blockers',
                'corticosteroid': 'corticosteroid',
                'prednisone': 'corticosteroid',
            }
            
            for keyword, db_drug in keywords.items():
                if keyword in canonical_med:
                    # Find the matching database key (case-insensitive)
                    for db_key_lower, (db_key_original, db_data) in drug_db_lower.items():
                        if db_drug.lower() in db_key_lower:
                            matched_interactions.append((med, db_data))
                            break
                    break
    
    return matched_interactions

st.divider()
st.header("📊 Nutrient Assessment Results")

# Collect all nutrient needs
nutrient_recommendations = defaultdict(dict)
nutrient_reasons = defaultdict(list)

# ============================================================================
# DIRECT DRUG MATCHING (Simplified & Bulletproof)
# ============================================================================

# 1. Drug-nutrient interactions
if show_interactions and medications:
    st.subheader("🚨 Drug-Nutrient Interactions")
    
    interaction_found = False
    
    # DIRECT approach: Iterate through selected medications
    for med_selected in medications:
        med_lower = med_selected.lower().strip()
        
        # Try to find this medication in the database
        matched_interaction_data = None
        
        # 1. Try exact case-insensitive match
        for db_drug, interaction_data in DRUG_NUTRIENT_INTERACTIONS.items():
            if db_drug.lower() == med_lower:
                matched_interaction_data = interaction_data
                break
        
        # 2. If not found, try keyword matching
        if not matched_interaction_data:
            keyword_map = {
                'metformin': 'Metformin',
                'ozempic': 'GLP-1 Agonists (Semaglutide, Liraglutide)',
                'semaglutide': 'GLP-1 Agonists (Semaglutide, Liraglutide)',
                'trulicity': 'GLP-1 Agonists (Semaglutide, Liraglutide)',
                'levothyroxine': 'Levothyroxine',
                'metoprolol': 'Beta-Blockers (Metoprolol, Atenolol)',
                'atenolol': 'Beta-Blockers (Metoprolol, Atenolol)',
                'jardiance': 'GLP-1 Agonists (Semaglutide, Liraglutide)',  # SGLT2i, but treat as GLP-1 for now
            }
            
            if med_lower in keyword_map:
                db_key = keyword_map[med_lower]
                if db_key in DRUG_NUTRIENT_INTERACTIONS:
                    matched_interaction_data = DRUG_NUTRIENT_INTERACTIONS[db_key]
        
        # 3. If found, extract nutrients
        if matched_interaction_data:
            interaction_found = True
            
            st.markdown(f"""
            <div class='interaction-alert'>
            <b>{med_selected.upper()}</b> - Drug-Nutrient Interactions Detected<br>
            <small>See recommendations below for evidence-based supplementation</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Process each nutrient in this drug's interactions
            for nutrient, nutrient_details in matched_interaction_data.items():
                if isinstance(nutrient_details, dict) and "evidence_grade" in nutrient_details:
                    # Add to recommendations
                    nutrient_recommendations[nutrient][med_selected] = "high"
                    
                    # Add reason
                    mechanism = nutrient_details.get("mechanism", "")
                    reason = nutrient_details.get("recommendation", mechanism)
                    nutrient_reasons[nutrient].append(f"⚠️ {med_selected}: {reason}")
    
    if not interaction_found and medications:
        st.info("✓ No major drug-nutrient interactions found for selected medications")
    
    st.divider()


# 2. Condition-based needs
st.subheader("🏥 Condition-Based Nutrient Needs")

for condition in conditions:
    # Convert to canonical condition name for database lookup
    canonical_condition = get_canonical_condition_name(condition)
    
    if canonical_condition in CONDITION_NUTRIENT_NEEDS:
        cond_data = CONDITION_NUTRIENT_NEEDS[canonical_condition]
        # cond_data is now {"Nutrient1": {...}, "Nutrient2": {...}}
        for nutrient, nutrient_details in cond_data.items():
            if isinstance(nutrient_details, dict) and "evidence_grade" in nutrient_details:
                if nutrient not in nutrient_recommendations:
                    nutrient_recommendations[nutrient] = {}
                nutrient_recommendations[nutrient][canonical_condition] = "high"
                reason = nutrient_details.get("recommendation", nutrient_details.get("mechanism", ""))
                nutrient_reasons[nutrient].append(f"📌 {condition}: {reason}")

condition_nutrients = set()
for condition in conditions:
    # Convert to canonical condition name for database lookup
    canonical_condition = get_canonical_condition_name(condition)
    
    if canonical_condition in CONDITION_NUTRIENT_NEEDS:
        cond_data = CONDITION_NUTRIENT_NEEDS[canonical_condition]
        for nutrient, nutrient_details in cond_data.items():
            if isinstance(nutrient_details, dict) and "evidence_grade" in nutrient_details:
                condition_nutrients.add(nutrient)

if condition_nutrients:
    for nutrient in sorted(condition_nutrients):
        st.markdown(f"• **{nutrient}**")
else:
    st.info("No conditions selected")

st.divider()

# 3. Lifestyle-based needs
st.subheader("🍽️ Lifestyle-Based Nutrient Needs")

lifestyle_nutrients = set()
for diet in diet_type:
    if diet in LIFESTYLE_NUTRIENT_NEEDS:
        for nutrient in LIFESTYLE_NUTRIENT_NEEDS[diet]["nutrients"]:
            nutrient_recommendations[nutrient][diet] = "moderate"
            nutrient_reasons[nutrient].append(
                f"🥗 {diet}: {LIFESTYLE_NUTRIENT_NEEDS[diet]['notes']}"
            )
            lifestyle_nutrients.add(nutrient)

# Exercise level
if exercise in ["Very Active", "Athlete"]:
    for nutrient in ["Magnesium", "Iron", "Zinc", "Electrolytes"]:
        nutrient_recommendations[nutrient]["Exercise"] = "moderate"
        nutrient_reasons[nutrient].append(f"🏃 {exercise}: Increased loss through sweat")
        lifestyle_nutrients.add(nutrient)

# Smoking
if smoking != "Non-smoker":
    for nutrient in ["Vitamin C", "Vitamin E", "Selenium"]:
        nutrient_recommendations[nutrient]["Smoking"] = "moderate"
        nutrient_reasons[nutrient].append(f"🚬 {smoking}: Increased oxidative stress")
        lifestyle_nutrients.add(nutrient)

# Alcohol
if alcohol != "None":
    for nutrient in ["Thiamine (B1)", "Folate", "B12", "Magnesium"]:
        nutrient_recommendations[nutrient]["Alcohol"] = "moderate"
        nutrient_reasons[nutrient].append(f"🍷 {alcohol} alcohol: Impairs absorption/metabolism")
        lifestyle_nutrients.add(nutrient)

# Sun exposure
if sun_exposure in ["Low (<15 min/day)", "Very Low (indoor)"]:
    nutrient_recommendations["Vitamin D3"]["Sun Exposure"] = "high"
    nutrient_reasons["Vitamin D3"].append(f"☀️ {sun_exposure}: Reduced endogenous synthesis")
    lifestyle_nutrients.add("Vitamin D3")

if lifestyle_nutrients:
    for nutrient in sorted(lifestyle_nutrients):
        st.markdown(f"• **{nutrient}**")
else:
    st.info("No lifestyle factors identified requiring additional nutrients")

st.divider()

# ============================================================================
# PERSONALIZED RECOMMENDATIONS
# ============================================================================

st.subheader("💡 Personalized Nutrient Recommendations")

# Initialize sorted_nutrients as empty
sorted_nutrients = []

if not nutrient_recommendations:
    st.info("No specific nutrient needs identified. Maintain general health with balanced diet.")
else:
    # Sort by priority (drug interactions > high severity > moderate)
    sorted_nutrients = sorted(
        nutrient_recommendations.items(),
        key=lambda x: (
            any(sev == "high" for sev in x[1].values()),
            any("⚠️" in reason for reason in nutrient_reasons[x[0]]),
        ),
        reverse=True
    )
    
    recommendation_count = 0
    for nutrient, sources in sorted_nutrients:
        recommendation_count += 1
        
        # Get severity
        severities = list(sources.values())
        is_high_priority = "high" in severities or any("⚠️" in r for r in nutrient_reasons[nutrient])
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if nutrient in NUTRIENT_INFO:
                info = NUTRIENT_INFO[nutrient]
                
                st.markdown(f"""
                <div class='recommendation-box'>
                <b>{recommendation_count}. {nutrient.upper()}</b><br>
                <b>Recommended Dose:</b> {info['daily_value']}<br>
                <b>Form:</b> {info['form']}<br>
                <b>Timing:</b> {info['timing']}<br>
                <b>⚠️ Important:</b> {info['warning']}<br>
                """, unsafe_allow_html=True)
                
                # Reasons
                st.markdown("**Reasons for this recommendation:**")
                for reason in nutrient_reasons[nutrient]:
                    st.markdown(f"- {reason}")
                
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                # Get evidence data for this nutrient
                evidence_data = get_evidence_for_nutrient(nutrient, medications, conditions)
                
                # Display nutrient with evidence
                display_nutrient_with_evidence(nutrient, sources, nutrient_reasons.get(nutrient, []), evidence_data)
                
                recommendation_count += 1

st.divider()

# ============================================================================
# PHARMACIST NOTES & CONSULTATION POINTS
# ============================================================================

if show_clinical_notes:
    st.subheader("📋 Pharmacist Consultation Notes")
    
    consultation_points = []
    
    # Drug interactions check
    if medications:
        consultation_points.append(
            f"**Medication Review:** Patient on {len(medications)} medication(s). Monitor for nutrient depletion, especially with long-term PPI or metformin use."
        )
    
    # Absorption considerations
    if "levothyroxine" in [m.lower() for m in medications]:
        consultation_points.append(
            "**Thyroid Management:** Ensure 4-hour spacing between levothyroxine and calcium/iron/magnesium supplements."
        )
    
    if "ppi" in [m.lower() for m in medications]:
        consultation_points.append(
            "**PPI Note:** Patient on long-term PPI. Consider B12 screening (serum + methylmalonic acid) annually."
        )
    
    # Condition-specific
    if "Type 2 Diabetes" in conditions:
        consultation_points.append(
            "**Diabetes Management:** Chromium and B-complex support glucose control. Assess for neuropathy (B12/B6 risk)."
        )
    
    if "Osteoporosis" in conditions:
        consultation_points.append(
            "**Bone Health:** Ensure adequate Vitamin D3 (target 1000-2000 IU daily + Calcium 1000-1200 mg). Check PTH/25-OH Vitamin D in 8-12 weeks."
        )
    
    # Pregnancy/breastfeeding
    if pregnancy_status != "Not applicable":
        consultation_points.append(
            f"**{pregnancy_status.upper()}:** Adjust recommendations for pregnancy/lactation requirements. Refer to obstetrician if high-dose supplementation needed."
        )
    
    # Vegan/vegetarian
    if any(diet in diet_type for diet in ["Vegan", "Vegetarian"]):
        consultation_points.append(
            "**Plant-Based Diet:** Patient at risk for B12, iron, zinc deficiency. Consider supplementation + dietary counseling."
        )
    
    # Heavy exercise
    if exercise in ["Very Active", "Athlete"]:
        consultation_points.append(
            "**Athletic Performance:** Monitor electrolyte balance, especially magnesium and iron. Hydration status impacts absorption."
        )
    
    # Symptoms
    if "Fatigue/Low Energy" in symptoms:
        consultation_points.append(
            "**Fatigue Assessment:** Check for B12/iron deficiency (CBC), vitamin D (25-OH), thyroid (TSH). Prioritize B12, iron, D3."
        )
    
    if "Numbness/Tingling in Extremities" in symptoms:
        consultation_points.append(
            "**Neuropathy Concern:** Assess for B12 deficiency (methylmalonic acid test). Check glucose control if diabetic."
        )
    
    if "Poor Memory/Brain Fog" in symptoms:
        consultation_points.append(
            "**Cognitive Symptoms:** Screen for B12, folate, vitamin D deficiency. Consider omega-3 supplementation."
        )
    
    # Add follow-up
    consultation_points.append(
        "**Follow-up:** Reassess nutrient status in 8-12 weeks. Document patient education on timing, food interactions, expected benefits."
    )
    
    for point in consultation_points:
        st.markdown(f"• {point}")

st.divider()

# ============================================================================
# EVIDENCE-BASED INFORMATION SECTION
# ============================================================================

st.header("📚 Evidence-Based Information")

# Show evidence grading explanation
with st.expander("📖 How to Read Evidence Grades"):
    st.markdown("""
    **Evidence Grade System:**
    
    - 🟢 **Grade A:** Strong evidence (RCTs, meta-analyses, consistent results)
      → Highly recommended based on clinical trials
    
    - 🟡 **Grade B:** Moderate evidence (observational studies, some RCTs)
      → Consider if condition or drug interaction present
    
    - 🟠 **Grade C:** Weak evidence (small studies, mixed results)
      → Discuss with healthcare provider
    
    - 🔴 **Grade D:** Insufficient evidence
      → Inform only, not strongly recommended
    """)

# Show database stats if loaded
if EVIDENCE_DB_LOADED:
    col_stats1, col_stats2, col_stats3 = st.columns(3)
    with col_stats1:
        st.metric("Drug-Nutrient Interactions", len(DRUG_NUTRIENT_INTERACTIONS))
    with col_stats2:
        st.metric("Condition Protocols", len(CONDITION_NUTRIENT_NEEDS))
    with col_stats3:
        st.metric("Clinical Guidelines", "7")
    
    st.info("""
    ✅ **This tool uses evidence-based guidelines:**
    
    - **ADA Standards of Care 2024** — Diabetes management & micronutrient deficiency screening
    - **AHA/ACC Guidelines 2017-2019** — Cardiovascular & hypertension management
    - **Endocrine Society Clinical Practice Guidelines** — Thyroid, bone health, vitamin D
    - **American Geriatrics Society Beers Criteria 2023** — Medication & nutrient interactions in aging
    - **National Osteoporosis Foundation Guidelines** — Calcium, vitamin D, bone health
    - **ASPEN (Parenteral/Enteral Nutrition) Guidelines** — Micronutrient deficiency assessment
    - **Academy of Nutrition & Dietetics** — Drug-nutrient interactions evidence tables
    
    📋 **Each recommendation includes:**
    - Mechanism of action (HOW it works)
    - Clinical evidence (WHAT studies show)
    - Evidence grade (A/B/C/D)
    - Recommended dosing (BASED on clinical trials)
    - Monitoring parameters (WHEN to recheck)
    - DOI/citations (WHERE to verify)
    """)
else:
    st.warning("⚠️ Evidence database not loaded. Showing basic recommendations only.")

st.divider()

# ============================================================================
# PATIENT EDUCATION & EXPORT
# ============================================================================

st.subheader("📥 Export Assessment")

col1, col2, col3 = st.columns(3)

with col1:
    # Generate PDF
    if st.button("📄 Download as PDF", use_container_width=True):
        pdf_buffer = generate_pdf(
            patient_id, age, sex, bmi, medications, conditions,
            diet_type, symptoms, nutrient_recommendations, nutrient_reasons,
            NUTRIENT_INFO, sorted_nutrients
        )
        
        st.download_button(
            label="📥 Download PDF File",
            data=pdf_buffer.getvalue(),
            file_name=f"vitamin_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

with col2:
    # Generate text summary
    if st.button("📝 Generate Text Summary", use_container_width=True):
        summary = f"""
SMART VITAMIN ASSESSMENT - PATIENT SUMMARY
{'='*50}

Patient ID: {patient_id if patient_id else 'Not recorded'}
Age: {age} | Sex: {sex} | BMI: {bmi:.1f}
Assessment Date: {datetime.now().strftime('%Y-%m-%d')}

MEDICATIONS ON FILE:
{', '.join(medications) if medications else 'None recorded'}

MEDICAL CONDITIONS:
{', '.join(conditions) if conditions else 'None recorded'}

RECOMMENDED NUTRIENT SUPPLEMENTS:
{'-'*50}
"""
        
        rec_num = 1
        for nutrient, sources in sorted_nutrients:
            if nutrient in NUTRIENT_INFO:
                info = NUTRIENT_INFO[nutrient]
                summary += f"""
{rec_num}. {nutrient}
   Dose: {info['daily_value']}
   Form: {info['form']}
   Timing: {info['timing']}
   Important: {info['warning']}
"""
            rec_num += 1
        
        summary += f"""

NEXT STEPS:
1. Review recommendations with pharmacy staff
2. Discuss any concerns or allergies
3. Schedule follow-up in 8-12 weeks
4. Report any side effects or interactions

DISCLAIMER:
This assessment is educational. Consult with your healthcare provider
before starting any new supplement, especially if pregnant, breastfeeding,
or taking medications with potential interactions.
"""
        
        st.text_area("Patient Summary", value=summary, height=400, disabled=True)
        
        # Download button
        b64 = base64.b64encode(summary.encode()).decode()
        href = f'<a href="data:text/plain;base64,{b64}" download="vitamin_assessment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt">📥 Download as Text</a>'
        st.markdown(href, unsafe_allow_html=True)

with col3:
    # Export as JSON for database
    if st.button("📊 Export as JSON", use_container_width=True):
        export_data = {
            "patient_id": patient_id,
            "assessment_date": datetime.now().isoformat(),
            "demographics": {
                "age": age,
                "sex": sex,
                "bmi": round(bmi, 2),
                "pregnancy_status": pregnancy_status
            },
            "medications": medications,
            "conditions": conditions,
            "lifestyle": {
                "diet": diet_type,
                "exercise": exercise,
                "alcohol": alcohol,
                "smoking": smoking,
                "sun_exposure": sun_exposure
            },
            "symptoms": symptoms,
            "recommendations": {
                nutrient: {
                    "reasons": nutrient_reasons[nutrient],
                    "info": NUTRIENT_INFO.get(nutrient, {})
                }
                for nutrient in nutrient_recommendations.keys()
            }
        }
        
        json_str = json.dumps(export_data, indent=2)
        st.text_area("JSON Export", value=json_str, height=400, disabled=True)
        
        b64 = base64.b64encode(json_str.encode()).decode()
        href = f'<a href="data:application/json;base64,{b64}" download="vitamin_assessment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json">📥 Download as JSON</a>'
        st.markdown(href, unsafe_allow_html=True)

st.divider()

st.markdown("""
---
### ℹ️ About This Tool

**Smart Vitamin Assessment** is an educational pharmacist decision-support tool designed to:
- Identify potential nutrient deficiencies based on medications, conditions, and lifestyle
- Assess drug-nutrient interactions
- Provide evidence-based supplementation guidance
- Support patient education in community pharmacy

**Limitations:**
- Not a diagnosis tool
- Does not replace clinical judgment
- Recommendations should be reviewed by a pharmacist
- Patient history (labs, previous testing) not captured in this version

**For Pharmacy Implementation:**
- Use as patient intake questionnaire
- Supplement clinical interview and patient record review
- Document consultation notes in patient record
- Follow up in 8-12 weeks to assess outcomes

---
*Version 1.0 | Built for evidence-based pharmacy practice*
""")
