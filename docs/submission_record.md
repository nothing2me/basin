# BASIN: Official Competition Submission & Finalist Q&A Record

**Competition:** *From the Ground Up 2026 AI Hackathon*  
**Organizer:** Zoho Corporation — Corporate Communications (Contact: Garrett White, Customer Advocacy Manager)  
**Team Name:** BASIN (Texas A&M University-Corpus Christi)  
**Team Members:** Noah Wilborn, Mohammed Asad Khan, Misha Stegall  
**Key Dates:**
- **Tie-Breaker Submission Deadline:** September 2, 2026, at 5:00 PM CT
- **Finalist Showcase Event:** September 22, 2026 (Pleasanton, CA)

---

## Part 1: Official Stage 1 Submission Answers

### 1. What problem are you solving?
> **Prompt:** *Describe the specific challenge your project addresses and who it affects. Be as concrete as possible about the community or region you have in mind.*

**Team Response:**  
Region N is an 11-county regional water-planning area covering Corpus Christi and surrounding rural-serving communities that depend on the regional water supply system. Its 2026 plan recognizes that the Corpus Christi Water Supply Model includes hydrology only through 2015, so it does not include newer drought conditions that may be worse than the historical drought-of-record conditions used in the model. The plan also notes that there was insufficient funding to update the model through current conditions before the planning deadline. As a result, regional planners, consulting hydrologists, Water Control and Improvement Districts, and rural-serving water providers have limited ways to organize and compare plausible conditions worse than the pre-2015 drought-of-record hydrology represented in the current model before commissioning specialized hydrologic analysis.

---

### 2. What is your proposed AI solution?
> **Prompt:** *Describe the tool, system, or approach you want to build. What does it do, how does it work, and what makes it appropriate for the community it serves?*

**Team Response:**  
We propose **BASIN: Basin Analysis and Scenario Intelligence Navigator**. BASIN is a small, locally run AI decision-support tool that generates transparent rainfall-based "what if" drought scenarios for the key source areas feeding Corpus Christi's multi-basin regional water supply system. Using public NOAA precipitation records, including post-2015 observations where available, BASIN lets users adjust drought severity, duration, seasonal timing, and whether drought hits several source areas at once. It then documents every modification so each scenario can be reviewed and challenged.

BASIN does not predict reservoir levels, water deliveries, safe yield, or restriction dates. Instead, it produces rainfall-stress scenarios, not hydrologic yield estimates, for professional hydrologic review. The tool examines hundreds of candidate scenarios, uses unsupervised learning to group similar drought patterns, and applies an explainable ranking layer to export a small, diverse shortlist. That shortlist helps planners and providers decide which drought conditions are worth deeper modeling by a hydrologist.

BASIN is designed for modest local deployment. It runs on a laptop-class machine with no cloud inference calls, using lightweight statistical learning and clustering sized to the scenario-generation task rather than a large general-purpose model. Because it processes decades of daily precipitation records rather than continuous sensor streams, a full run should complete in minutes on consumer hardware. In Stage 2, we would estimate energy use per run and treat on-device, on-demand operation as a hard design constraint.

BASIN's export format is intentionally interoperable, so hydrologists and planners can move scenario assumptions into existing reports, spreadsheets, or future water-planning models rather than locking results inside a single tool.

---

### 3. Who are the intended users, and how would they be involved?
> **Prompt:** *Explain who would use or benefit from your solution — farmers, tribal land managers, rural water districts, or others.*

**Team Response:**  
The primary users are Region N technical participants, consulting hydrologists, and rural-serving wholesale water providers who need to reason about drought risk before formal model-update funding is available. Additional users include Water Control and Improvement Districts and smaller communities that depend on the regional supply system but may not have staff, software, or funding to commission exploratory scenario analysis on their own.

These users would shape BASIN's scenario priorities, terminology, and report format. For example, one provider may care most about long concurrent multi-basin droughts, while another may care about short extreme deficits during high-demand seasons. BASIN would let those users set the ranking weights before the shortlist is generated. Our first Stage 2 milestone would be 2-3 short validation conversations with a mix of Region N participants, WCIDs or rural-serving wholesale providers, and consulting hydrologists before finalizing BASIN's ranking priorities.

---

### 4. How would you ensure the community has meaningful input or control over the tool?
> **Prompt:** *Describe how the community exercises governance, input, and operational oversight over the tool.*

**Team Response:**  
BASIN is structured so participating providers and community representatives control the scenario limits, ranking priorities, and final shortlist. Users can decide which drought features matter most, including duration, severity, seasonal timing, and whether multiple source catchments are stressed at the same time. They can reject, edit, or replace any AI-selected scenario before exporting results.

BASIN will not declare a water plan safe or inadequate. Its output format contains no verdict field: only ranked, editable scenarios with visible assumptions, measurements, and selection rules. Every input, transformation, score, and selection reason will be exportable so a hydrologist or provider can audit the result.

Provider-specific information will remain on the user's device unless the user chooses to share it. BASIN will use public precipitation and planning data by default, and any local provider notes or priorities will be stored locally. In Stage 2, user feedback would directly shape the labels, ranking controls, and report templates so the tool reflects the language and decision workflows of the people using it.

---

### 5. Why does this matter? What would change for the better?
> **Prompt:** *What would change for the better if your solution worked as intended? What is the real-world impact you're aiming for?*

**Team Response:**  
Right now, Region N planners and rural-serving water providers face a practical gap: the plan acknowledges that drought conditions after 2015 may be worse than the historical drought conditions used in the model, but a full hydrologic model update requires specialized funding and time. BASIN would not replace that expert modeling. It would make the step before modeling more organized, transparent, and community-directed.

If BASIN works as intended, planners and providers would no longer have to start from a blank page when deciding which drought conditions deserve analysis. They could begin with a ranked set of clear, auditable scenarios and take those scenarios to a hydrologist, regional planning meeting, or provider discussion. Smaller providers would gain a concrete way to say, "model this kind of concurrent drought first," instead of relying only on assumptions chosen by larger institutions or funded consultants.

The real-world impact we are aiming for is faster, fairer drought planning. Success is not BASIN predicting the exact date of a water emergency. Success is a Region N participant, WCID, or rural-serving provider using BASIN's shortlist to focus scarce modeling time on the drought patterns that matter most to their communities. Because BASIN is local, low-cost, and built around public data plus user-controlled priorities, the same approach could later transfer to other rural regions by swapping in their own source-catchment data and planning benchmarks.

---

## Part 2: Finalist Round Tie-Breaker Correspondence

### Email 1: Invitation & Tie-Breaker Questions
**From:** Garrett White (`garrett.w@zohocorp.com`)  
**Date:** September 1, 2026  
**To:** Noah Wilborn, Mohammed Asad Khan, Misha Stegall  
**Subject:** From the Ground Up - Finalist Round Questions

> *Hello Noah Wilborn, Mohammed Asad Khan, and Misha Stegall!*  
> *We are reaching out because your submission for From the Ground Up was among a select group that tied for our finalist round. Congratulations! That alone is a huge victory.*  
> *We are now trying to determine which of these select few will go on to become finalists and which will go on to become alternates. In order to do that, we have two more questions for your team to answer. We would like responses as soon as possible, but the hard deadline will be tomorrow, September 2nd at 5:00 PM CT.*  
> *Please hit "Reply All" to this email and answer the questions in your own words.*  
> *AI should not be used to draft these responses—we want to hear your unique voice!*  
> *Please follow the length requirements set for each question.*  
> *Only one team member should reply.*  
> 
> ***Question 1 (2-3 sentences):***  
> *Our finalist event will be September 22nd. By then, you will be expected to have a pitch deck and prototype to demonstrate for our judges. Looking at your submission answers, how feasible is it that you will be able to deliver a working prototype? What changes, if any, would you make to the scope of your project in order to ensure this?*  
> 
> ***Question 2 (3-4 sentences):***  
> *Community is at the heart of this competition. In your opinion, what is the unique selling point of your solution in terms of BOTH community impact and community involvement? What pitfalls would there be to overcome?*

---

### Email 2: Organizer Reminder
**From:** Garrett White (`garrett.w@zohocorp.com`)  
**Date:** September 2, 2026  
**To:** Noah Wilborn, Mohammed Asad Khan, Misha Stegall  

> *Hello there!*  
> *I am just reaching out with a reminder about those tie-breaker questions I sent over yesterday. You still have until 5:00 PM CT today in order to send your team's response over so we can place you as either a finalist or alternate.*  
> *Please let me know if you have any questions or concerns. We are looking forward to reading your answers!*

---

### Email 3: Official Team Response
**From:** Noah Wilborn  
**Date:** September 2, 2026  
**To:** Garrett White, Mohammed Asad Khan, Misha Stegall  

> *Hello,*  
> *We greatly appreciate the opportunity; here are our responses!*  
> 
> **Question 1 Response:**  
> *"We’re confident that we can deliver a pitchable prototype by September 22nd. Two of our team members have already shipped demo ready software under tight deadlines, even placing in a similarly themed hackathon with a disaster-preparedness prototype. To stay on schedule, we’re keeping BASIN scoped to its core functionality: turning public documentation and historical data into transparent drought scenarios for analyst review, leaning away from more active cases that could involve live utility data and automation techniques, until the core workflow of BASIN is built and reviewed by professionals in our community."*  
> 
> **Question 2 Response:**  
> *"BASIN’s unique selling point is that it transforms scattered documentation, starting assumptions, and public data into clear scenarios that Region N water professionals can verifiably reference in their judgments and planning processes. We seek to aid management officials with their greatest pains, something we verified by sending out a discovery survey to professionals across Region N; many of whom stated their biggest frustration isn’t a lack of data, but instead conflicting data with no easy way to tell what's trustworthy. Community involvement is a foundation and local officials will help define what assumptive policy is acceptable and what outputs are actually useful; so that the tool is continuously shaped by the people who understand the real budgets, trust issues, and operational risks of the industry. The main pitfalls we face are deciding how to handle possibly sensitive data as we scale, earning professional trust, and keeping every AI-generated output verifiable before it is handed off and possibly used to affect a real decision; if accepted, we’ll work directly with TAMUCC and local officials to work towards appropriately managing all of the above, and to accomplish our project goals."*  
> 
> *Many thanks,*  
> *Noah Wilborn*

---

## Part 3: Strategic Guardrails & Commitments for Agents & Developers

Any agent or contributor modifying BASIN must honor the formal commitments made in these answers:

1. **Pre-Engineering Scoping, Not Engineering Certification (§ 1001):**
   - BASIN produces **rainfall-stress scenarios**, not statutory safe-yield declarations or restriction dates.
   - Outputs must never contain a binding "verdict" field.
2. **Deterministic Scoping & Lightweight Architecture:**
   - On-device execution on consumer hardware with **0 cloud inference calls**.
   - Use deterministic clustering (K-Means) and explainable scoring rather than opaque LLM hallucinations.
3. **Local Privacy by Default:**
   - Private analyst notes, local custom gauge uploads, and provider priorities must remain strictly on-device.
4. **Interoperable Handoff:**
   - Scenarios must be exportable in open, auditable formats (`rainfall.csv`, `shortlist.csv`, `Hydrologist_Handoff_Brief.md`) directly compatible with Texas WAM Run 3 and HEC-ResSim.
5. **Community-Driven Ranking & Transparent Conflict Handling:**
   - Enable rural-serving providers and WCIDs to set their own weighting profiles (e.g. summer crop timing vs. multi-basin concurrence).
   - Address the #1 practitioner pain point discovered in the regional survey: **conflicting data and lack of provenance**, by enforcing SHA-256 snapshots and public evidence conflict logs.
