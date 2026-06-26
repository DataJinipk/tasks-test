# Project Report: FinAI-Lens
**Course:** AI-101: AI Prompting in 2026  
**Task:** Lecture 3 – Open-Ended App or Game Development  
**Project Title:** FinAI-Lens // Autonomous IFRS 9 ECL & Ratio Analytics Dashboard  
**Target Repository:** https://github.com/datajinipk/tasks-test.git  

---

## 1. The Idea Behind the Project
FinAI-Lens is an autonomous, single-page financial analysis dashboard built to solve a critical, real-world business challenge: the automation of repetitive financial statement analysis and compliance calculations under the **IFRS 9 (Expected Credit Loss - ECL)** framework. 

Manual spreadsheets are highly prone to calculation errors and are time-consuming for corporate finance and risk teams. FinAI-Lens provides an immediate, zero-installation portal tailored to the Pakistani financial ecosystem (**PKR currency** standards), enabling microfinance institutes, corporate analysts, and SME lenders to:
1. Instantly simulate impairment provisioning pools across multi-stage risk portfolios.
2. Monitor core corporate liquidity and profitability thresholds seamlessly.

## 2. Real-World Problem Solved
In corporate banking and risk compliance, calculating financial health metrics and determining asset provisioning under IFRS 9 guidelines typically requires complex accounting software or massive, error-prone Excel workbooks. This tool automates the calculations by tracking:
* **Credit Provision Risk Tiers:** Dynamically warning if Non-Performing Loans (NPLs) push the portfolio into elevated or critical stress boundaries.
* **Liquidity Deficits:** Spotting immediate solvency issues by parsing balance sheet inputs into color-coded performance badges (*Strong*, *Marginal*, *Illiquid Alert*).

## 3. Final Working Features
* **IFRS 9 Compliance Calculator:** Allocates asset portfolios across Stage 1 (Performing), Stage 2 (Underperforming), and Stage 3 (Non-performing) loan pools to evaluate the ultimate blended impairment allowance.
* **Corporate Statement Ratio Suite:** Processes real-time balance sheet items to compute the **Current Ratio** and **Net Profit Margin**.
* **Dynamic UX Indicators:** Uses Tailwind CSS visual badges that flag high-risk credit scenarios dynamically as input values shift.
* **Data Export Pipeline:** Includes a localized script execution block allowing users to export full summaries into a portable `.txt` layout instantly.

## 4. AI-Assisted Development & Prompt Engineering Techniques
The application was written entirely inside a single-file `index.html` structure by engineering specific foundational prompts to an advanced LLM agent, utilizing several key techniques:

### A. Role & Expert Persona Prompting
The AI was locked into a high-level technical domain:
> *"Act as an expert senior financial software engineer and UI/UX designer with deep expertise in corporate finance and advanced risk analytics."*
This prevented generic code suggestions and forced the AI to build realistic asset-allocation math natively in vanilla JavaScript.

### B. Structural and Negative Constraints
To guarantee a modular, zero-dependency architecture that runs instantly out of the box, strict boundaries were injected:
> *"Build everything self-contained within a single `index.html` file using Tailwind CSS via CDN. Do not rely on external node modules or build steps. Exclude conversational pleasantries or explanations and begin directly with the code payload."*

### C. Sequential Iterative Refinement
The workflow progressed through multiple systematic prompt generations:
* **Iteration 1 (Base Core):** Generated the default HTML structure and basic script processing formulas using standard USD indicators.
* **Iteration 2 (Localization Shift):** Refined formatting, numerical masks, and localized output strings exclusively to map onto the **PKR (Rs.)** financial currency model.

## 5. Problems Faced & Solutions Applied
* **The Issue:** Initial generation scripts triggered default formatting anomalies when outputting mixed localized numbers without standard fractional rules.
* **The Solution:** Prompted the model to replace standard string concatenation with strict `.toLocaleString('en-PK')` configurations, guaranteeing pristine comma separations matching Pakistani banking metrics.
* **The Git Push Defect:** Attempting to upload code triggered an upstream error (`src refspec main does not match any`).
* **The Resolution:** Diagnosed that the local branch default environment was tracked under `master`, matching it up appropriately to push to the GitHub remote repository cleanly.
