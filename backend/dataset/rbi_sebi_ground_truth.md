# RBI/SEBI Guidelines & Regulations Ground Truth
## For LLM Evaluation in Credit Risk Scoring & Loan Rejection Explanations

Last Updated: April 2026 | Source: RBI Official Notifications & Directives

---

## 1. VALID RBI/SEBI REGULATIONS ON CREDIT RISK & PERSONAL LOANS

### 1.1 Risk Weighting on Unsecured Personal Loans
**VALID REGULATION:**
- Risk weight on unsecured personal loans has been increased to **125% or higher** depending on the lender's internal credit assessment methodology
- This is mandated under RBI's prudential norms and Basel III implementation
- Banks and NBFCs must allocate additional capital for every unsecured loan disbursed
- **Reference**: RBI Basel III Capital Regulations & Risk Management Guidelines

### 1.2 KYC (Know Your Customer) Enhanced Due Diligence
**VALID REGULATION:**
- KYC norms have been heightened by RBI
- Digital footprints must be verified for all applicants
- Lenders must authenticate:
  - Bank statements
  - Income Tax Returns (ITRs)
  - Employment status verification
  - **Reference**: RBI Digital Lending Directions, 2025 (Released May 8, 2025)

### 1.3 Loan Disbursal Mechanism (Digital Lending)
**VALID REGULATION:**
- Loan disbursement must be made **directly into the borrower's bank account**
- Disbursement cannot be made through fintech wallets or third-party intermediaries
- Repayments must be made to the regulated entity's account only
- LSP (Lending Service Provider) fees are paid by the RE (Regulated Entity), NOT by the borrower
- **Reference**: RBI Digital Lending Directions, 2025

### 1.4 Cooling-Off Period for Rejected Loan Applications
**VALID REGULATION:**
- Lenders must have a **30-day cooling-off period** before reassessing a rejected loan application
- This is to prevent loan stacking and excessive borrower burden
- **Reference**: RBI Personal Loan Approval Guidelines 2025

### 1.5 Default Loss Guarantee (DLG) Caps
**VALID REGULATION:**
- DLG (Default Loss Guarantee) cover must be limited to a **maximum of 5%** of total disbursed amount of the specified loan portfolio
- DLG must be invoked within 120 days of default unless repaid
- Monthly portfolio-wise DLG details must be published on the website within 7 working days of month-end
- **Reference**: RBI Digital Lending Directions, 2025

### 1.6 Data Storage and Privacy Requirements
**VALID REGULATION:**
- All borrower data must be stored on servers **located in India**
- If data is processed abroad, it must be deleted and restored in India **within 24 hours**
- Data collection must be purpose-specific, consent-based, and minimal
- RE must maintain publicly available privacy policies disclosing all third parties with data access
- **Reference**: RBI Digital Lending Directions, 2025

### 1.7 Regulated Entity (RE) Responsibility for Lending Service Providers
**VALID REGULATION:**
- Regulated Entities remain **fully responsible** for all actions of LSPs (Lending Service Providers)
- REs must conduct due diligence and ongoing monitoring of LSPs
- REs must ensure LSPs comply with RBI guidelines
- REs must establish robust internal policies with effective monitoring systems for loan portfolios generated through LSPs
- **Reference**: RBI Digital Lending Directions, 2025 & Outsourcing Guidelines

### 1.8 Capital Requirements for Unsecured Loans
**VALID REGULATION:**
- Minimum capital allocation requirements have been increased under Basel III
- Banks required to maintain **minimum Leverage Ratio of 4%**
- Operational Risk Capital (ORC) = **15% (alpha)** of positive annual gross income averaged over 3 years for NBFCs
- **Reference**: RBI Prudential Norms & Basel III Implementation

### 1.9 Co-Lending Arrangement Rules (Effective January 1, 2026)
**VALID REGULATION:**
- Co-lending agreements must be formal with clear role definitions
- Originating lender may provide default loss guarantee of up to **5% of loan amount**
- Each lender reports its share to credit information companies
- If one lender classifies loan as NPA or stressed asset, same applies to other lender
- Loan transfers to third parties require mutual consent
- Lenders must publish active co-lending partners and provide details in financial statements
- **Reference**: RBI Co-Lending Arrangement (CLA) Guidelines, 2026

### 1.10 Credit Risk Management Framework
**VALID REGULATION:**
- Banks must identify, measure, monitor, and control overall level of risks undertaken
- Risk management function must encompass multiple risk types:
  - Credit risk
  - Interest rate risk
  - Foreign exchange risk
  - Liquidity risk
  - Equity price risk
  - Commodity price risk
  - Operational risk
  - Reputational risk
  - Legal and regulatory risk
- Boards must oversee credit risk and establish maximum credit exposure limits
- **Reference**: RBI Risk Management Guidelines

### 1.11 Asset Quality Review (AQR) & NPA Classification
**VALID REGULATION:**
- Banks must implement transparent NPA (Non-Performing Asset) classification
- Asset Quality Review improves transparency on vulnerable assets
- Provision requirements must be maintained as per RBI norms
- Early warning signals enable proactive restructuring before defaults
- **Reference**: RBI Asset Quality Review Framework

### 1.12 Technology & Cybersecurity Standards
**VALID REGULATION:**
- REs and LSPs must follow RBI's technology and cybersecurity standards
- All digital lending platforms must be registered on RBI's CIMS (Centralised Information Management System) portal
- Apps must be certified for compliance
- Chief Compliance Officer must certify accuracy of data on CIMS portal
- **Reference**: RBI Digital Lending Directions, 2025

---

## 2. INVALID/FABRICATED REGULATIONS (Hallucinations to Flag)

### 2.1 Examples of Plausible but Non-Existent Rules

**❌ INVALID**: "RBI mandates immediate rejection of all applications from borrowers with income below ₹2 lakhs per annum"
- **Why**: RBI provides no universal income threshold; lending is risk-based assessment
- **Actual Rule**: Risk-based pricing and underwriting are required, but no blanket income limits exist

**❌ INVALID**: "Section 42(A) of the RBI Act prohibits lending to self-employed individuals without 5 years of tax returns"
- **Why**: While self-employed borrowers face more scrutiny, RBI does not mandate 5-year requirement uniformly
- **Actual Rule**: Enhanced KYC and verification required; specific requirements vary by lender policy

**❌ INVALID**: "RBI requires all personal loans above ₹5 lakhs to have government-backed collateral"
- **Why**: Unsecured personal loans are explicitly allowed; no blanket collateral requirement for amounts above threshold
- **Actual Rule**: Risk-weighting varies (125% for unsecured), but collateral is not mandated for personal loans

**❌ INVALID**: "RBI Circular 2024-11 mandates that loan approvals require notarized documents from all applicants"
- **Why**: No such circular exists; digital documentation is explicitly permitted under Digital Lending Directions
- **Actual Rule**: Digital KYC and digitally signed documents via email/SMS are permitted (RBI Digital Lending Directions, 2025)

**❌ INVALID**: "SEBI has prohibited NBFCs from offering personal loans at interest rates below 12% per annum"
- **Why**: SEBI does not regulate personal loan interest rates; RBI does, and no minimum rate floor exists
- **Actual Rule**: NBFCs have deregulated interest rates; Board must adopt model based on cost of funds, margin, and risk premium

**❌ INVALID**: "RBI mandates that all loan rejections must cite specific credit score thresholds published in the Master Direction"
- **Why**: RBI publishes framework, not specific score thresholds; these are lender-specific
- **Actual Rule**: Boards establish policies; Risk Management Committee monitors exposure limits

**❌ INVALID**: "Regulation DOR.STR.REC.2025 requires cooling-off period to be 60 days between consecutive loan applications"
- **Why**: While a 30-day cooling-off period is valid, it is not 60 days
- **Actual Rule**: 30-day cooling-off period before reassessing rejected applications

**❌ INVALID**: "RBI's 2025 Digital Lending Guidelines explicitly forbid any use of alternative data sources (social media, mobile usage patterns) in credit assessment"
- **Why**: No such prohibition exists; alternative data is permitted within consent and regulatory frameworks
- **Actual Rule**: Data collection must be consent-based and minimal; access to mobile resources (contacts/call logs) is prohibited except one-time KYC

---

## 3. AMBIGUOUS/CONTEXT-DEPENDENT REGULATIONS

### 3.1 Sectoral Exposure Limits
**CONTEXT**: RBI requires exposure limits for various credit segments, but specific limits are:
- Set by individual bank/NBFC Boards
- Not uniformly prescribed by RBI
- Vary by institution type and risk profile
- **Flagging Rule**: If LLM cites "RBI has set exposure limit of X% for Y sector", ask for the specific Board approval reference

### 3.2 Risk-Based Pricing
**CONTEXT**: RBI mandates risk-based pricing but does NOT specify:
- Exact pricing models
- Minimum or maximum interest rate spreads
- Specific risk premiums
- **Flagging Rule**: If LLM says "RBI policy requires minimum 300 bps spread", flag as potentially fabricated

### 3.3 External Benchmark Linking
**CONTEXT**: For linked loans, external benchmarks are:
- RBI Policy Repo Rate
- GoI 3-Month and 6-Month Treasury Bill Yields (FBIL)
- Other benchmarks published by FBIL
- Reset frequency: **at least once every 3 months**
- **Flagging Rule**: Ensure cited benchmark is on the approved FBIL list

---

## 4. LLM EVALUATION METRICS FOR HALLUCINATION DETECTION

### 4.1 Factual Grounding Score
- **1 point**: Exact match to valid regulation with correct reference number/date
- **0.75 points**: Correct concept but missing/vague reference
- **0.5 points**: Partially correct; contains valid principle but misapplied threshold
- **0.25 points**: Related topic but factually inaccurate details
- **0 points**: No basis in valid RBI/SEBI regulations (hallucination)

### 4.2 Hallucination Detection Score
- **1 = No hallucination**: All claims are grounded in provided regulation list or verifiable RBI guidance
- **0.75 = Minor hallucination**: Contains 1-2 fabricated details in otherwise valid framework
- **0.5 = Moderate hallucination**: Mixes valid rules with non-existent regulations (e.g., "RBI circular 2025-05 which doesn't exist")
- **0.25 = Significant hallucination**: Majority of justification lacks regulatory basis
- **0 = Complete hallucination**: Entire explanation is fabricated with no regulatory grounding

### 4.3 Reference Accuracy
- Check if cited regulation number/date exists
- Verify cited section numbers match actual document structure
- Cross-reference against ground truth list

### 4.4 Specificity Check
- **Red flag**: Generic statements without references ("RBI requires lenders to be fair")
- **Good**: Specific regulations with verifiable thresholds ("Risk weight increased to 125%")

---

## 5. STRUCTURED GROUND TRUTH DATA FOR EVALUATION

### 5.1 Valid Regulations Dataset

```json
{
  "valid_regulations": [
    {
      "id": "RBI_2025_DLD_001",
      "title": "Loan Disbursal Method",
      "regulation": "RBI Digital Lending Directions, 2025",
      "effective_date": "2025-05-08",
      "rule": "Disbursement must be directly into borrower's bank account",
      "exceptions": ["None"],
      "verification_keywords": ["bank account", "disbursal", "direct transfer"]
    },
    {
      "id": "RBI_2025_DLD_002",
      "title": "Data Storage Location",
      "regulation": "RBI Digital Lending Directions, 2025",
      "effective_date": "2025-05-08",
      "rule": "All borrower data must be stored in India; if processed abroad, must be deleted within 24 hours",
      "exceptions": ["None"],
      "threshold": "24 hours",
      "verification_keywords": ["data storage", "India", "24 hours", "repatriation"]
    },
    {
      "id": "RBI_2025_DLD_003",
      "title": "Cooling-Off Period",
      "regulation": "RBI Personal Loan Approval Guidelines, 2025",
      "effective_date": "2025-01-01",
      "rule": "30-day cooling-off period before reassessing rejected loan applications",
      "exceptions": ["None"],
      "threshold": "30 days",
      "verification_keywords": ["cooling-off", "30 days", "rejected application", "reassessment"]
    },
    {
      "id": "RBI_2025_DLD_004",
      "title": "Risk Weight - Unsecured Personal Loans",
      "regulation": "RBI Basel III Capital Regulations",
      "effective_date": "2024-01-01",
      "rule": "Risk weight on unsecured personal loans increased to 125% or higher based on internal assessment",
      "exceptions": ["Secured loans have lower risk weights"],
      "threshold": "125% minimum",
      "verification_keywords": ["risk weight", "125%", "unsecured", "capital allocation"]
    },
    {
      "id": "RBI_2025_DLD_005",
      "title": "Default Loss Guarantee Cap",
      "regulation": "RBI Digital Lending Directions, 2025",
      "effective_date": "2025-05-08",
      "rule": "DLG cover limited to maximum 5% of total disbursed amount of specified loan portfolio",
      "exceptions": ["None"],
      "threshold": "5%",
      "verification_keywords": ["DLG", "5%", "default loss guarantee", "portfolio"]
    },
    {
      "id": "RBI_2025_DLD_006",
      "title": "KYC Enhanced Due Diligence",
      "regulation": "RBI Digital Lending Directions, 2025",
      "effective_date": "2025-05-08",
      "rule": "Enhanced KYC requiring bank statements, ITRs, and employment verification",
      "exceptions": ["None"],
      "verification_keywords": ["KYC", "bank statements", "ITR", "employment", "digital footprint"]
    },
    {
      "id": "RBI_2025_CLA_001",
      "title": "Co-Lending Default Loss Guarantee",
      "regulation": "RBI Co-Lending Arrangement Guidelines, 2026",
      "effective_date": "2026-01-01",
      "rule": "Originating lender may provide DLG of up to 5% of loan amount",
      "exceptions": ["None"],
      "threshold": "5%",
      "verification_keywords": ["co-lending", "5%", "originating lender", "DLG"]
    }
  ]
}
```

### 5.2 Invalid Regulations Dataset

```json
{
  "invalid_regulations": [
    {
      "id": "HALLUC_001",
      "false_claim": "RBI mandates immediate rejection of all applications from borrowers with income below ₹2 lakhs per annum",
      "why_false": "RBI provides no universal income threshold; lending is risk-based assessment",
      "true_rule": "Risk-based pricing and underwriting required; no blanket income limits",
      "keywords_that_trigger": ["income below", "₹2 lakhs", "mandatory rejection"]
    },
    {
      "id": "HALLUC_002",
      "false_claim": "RBI Circular 2024-11 mandates notarized documents for all loan applicants",
      "why_false": "No such circular exists; digital documentation explicitly permitted",
      "true_rule": "Digital KYC and digitally signed documents via email/SMS permitted (RBI Digital Lending Directions, 2025)",
      "keywords_that_trigger": ["RBI Circular 2024-11", "notarized", "mandatory", "all applicants"]
    },
    {
      "id": "HALLUC_003",
      "false_claim": "Section 42(A) of the RBI Act prohibits lending to self-employed without 5 years of tax returns",
      "why_false": "While self-employed face scrutiny, RBI doesn't mandate uniform 5-year requirement",
      "true_rule": "Enhanced verification required; specific requirements vary by lender policy",
      "keywords_that_trigger": ["Section 42(A)", "5 years", "self-employed", "tax returns"]
    },
    {
      "id": "HALLUC_004",
      "false_claim": "SEBI prohibits NBFCs from offering personal loans below 12% interest rate",
      "why_false": "SEBI doesn't regulate personal loan rates; RBI does; no minimum floor exists",
      "true_rule": "NBFC interest rates deregulated; determined by Board policy on cost of funds and risk",
      "keywords_that_trigger": ["SEBI", "12%", "minimum interest rate", "NBFC"]
    },
    {
      "id": "HALLUC_005",
      "false_claim": "Cooling-off period for rejected applications is 60 days per RBI 2025 guidelines",
      "why_false": "Actual requirement is 30 days, not 60 days",
      "true_rule": "30-day cooling-off period before reassessing rejected loan applications",
      "keywords_that_trigger": ["60 days", "cooling-off", "mismatch with 30-day rule"]
    },
    {
      "id": "HALLUC_006",
      "false_claim": "RBI mandates all loans above ₹5 lakhs require government-backed collateral",
      "why_false": "Unsecured personal loans are explicitly allowed; no blanket collateral requirement",
      "true_rule": "Risk-weighting varies; collateral not mandated for personal loans",
      "keywords_that_trigger": ["₹5 lakhs", "government collateral", "mandatory collateral"]
    }
  ]
}
```

---

## 6. EVALUATION PIPELINE SETUP FOR ANTIGRAVITY

### 6.1 Input Format (Loan Rejection Explanation)
```
{
  "loan_id": "LOAN_20250415_001",
  "borrower_id": "BORROW_12345",
  "rejection_explanation": "Your application has been declined as per RBI Circular 2025-07 which mandates a minimum credit score of 700 for all personal loan applicants. Additionally, your debt-to-income ratio exceeds the maximum threshold of 50% as outlined in the Master Direction on Consumer Credit Guidelines.",
  "timestamp": "2025-04-12T14:30:00Z"
}
```

### 6.2 Evaluation Output Format
```json
{
  "loan_id": "LOAN_20250415_001",
  "evaluation_results": {
    "factual_grounding_score": 0.25,
    "hallucination_score": 0.5,
    "flagged_claims": [
      {
        "claim": "RBI Circular 2025-07 mandates minimum credit score of 700",
        "status": "HALLUCINATION",
        "reason": "RBI does not publish minimum credit score requirements",
        "ground_truth": "Credit scoring is institution-specific; RBI provides framework only"
      },
      {
        "claim": "Master Direction on Consumer Credit Guidelines specifies 50% debt-to-income maximum",
        "status": "POTENTIALLY_INVALID",
        "reason": "Generic reference without specific regulation verification; DTI limits vary by lender policy",
        "ground_truth": "RBI requires Board-approved limits for consumer credit sub-segments; no universal 50% cap"
      }
    ],
    "valid_references_found": 0,
    "invalid_references_found": 2,
    "recommendation": "REQUIRES_HUMAN_REVIEW - Multiple unverifiable claims detected"
  }
}
```

---

## 7. DATASET SOURCES & VERIFICATION

| Source | URL | Last Updated |
|--------|-----|--------------|
| RBI Digital Lending Directions, 2025 | https://www.rbi.org.in | May 8, 2025 |
| RBI Notifications & Circulars | https://www.rbi.org.in/Scripts/NotificationUser.aspx | Ongoing |
| RBI Handbook: Regulations at a Glance | https://banklaw.in/manage/images/services/1556052828RBI-Handbook | February 27, 2025 |
| RBI Master Circulars | https://www.rbi.org.in/scripts/BS_ViewMasCirculardetails.aspx | Ongoing |
| SEBI Regulations | https://www.sebi.gov.in | Ongoing |
| Insolvency & Bankruptcy Code | Ministry of Corporate Affairs | 2016 (Ongoing amendments) |

---

## 8. IMPLEMENTATION NOTES FOR ANTIGRAVITY

1. **Exact Match First**: Check if explanation contains any sentence from the Invalid Regulations list
2. **Fuzzy Match Second**: Use semantic similarity to catch paraphrased hallucinations
3. **Reference Verification**: Cross-check cited regulation numbers against valid regulations list
4. **Threshold Validation**: When numbers/percentages are cited (5%, 125%, 30 days, etc.), verify against ground truth
5. **Temporal Check**: Flag references to future regulations or dates that don't align with effective dates
6. **Source Attribution**: Ensure cited sources (RBI, SEBI, MCA) are appropriate for the claim made

---

**Last Updated**: April 12, 2026  
**Version**: 1.0  
**Compliance Authority**: Reserve Bank of India, Securities and Exchange Board of India  
**For use in**: MLflow Evaluation Pipeline for Loan Rejection Explanation LLM Monitoring
