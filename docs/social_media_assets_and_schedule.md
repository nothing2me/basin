# BASIN Social Media Campaign & Promotion Schedule

> **Unconfirmed planning draft.** The number of required posts, deadline, tags, coordinator details and publication copy have not been substantiated by repository source material. The team must verify requirements and approve claims before anything is published. No post has been sent by this project work.

**Competition:** Zoho "From The Ground Up" AI Hackathon (2026)  
**Coordinator Lead:** Mira (Zoho Corporate Communications / Social Media Lead)  
**Hard Completion Deadline:** **Friday, September 18, 2026 (End of Day)**  
**Mandatory Tags & Handles:**
- **LinkedIn:** Tag `Zoho` / `Zoho USA` (`https://www.linkedin.com/company/zoho/`)
- **Instagram:** Tag `@zoho` / `@zohousa`
- **Mandatory Hashtag:** `#fromthegroundup`
- **Supporting Hashtags:** `#AIForGood #WaterSecurity #OpenSource #CivicTech #HackathonFinalist #TexasTech`

---

## Campaign Rules & Best Practices (From Zoho Coordinators)

1. **Spread Across Multiple Days:** Do *not* post all three on September 18. Post across separate days so the Zoho social media team can monitor, like, and repost each one to their global audience.
2. **Screenshot Every Post:** Take a clear screenshot immediately after publishing each post (showing timestamp, tags, and content). Store in `docs/social_proof/` or keep on your phone to show coordinators if an algorithm hides it.
3. **Collaboration & Reposting:** One team member publishes the primary post; teammates collaborate (on Instagram) and repost/comment (on LinkedIn).
4. **School / Club Amplification:** Tag your university departments, engineering clubs, and student government accounts to boost reach.
5. **Bilingual / Multilingual Option:** As confirmed by Mira, posting in both English and your native language increases visibility and is explicitly welcomed by the judges.

---

## Post 1: The Finalist Announcement

- **Target Publication Date:** **Monday, September 15, 2026 (Morning, ~9:00 AM CDT)**
- **Primary Platform:** LinkedIn & Instagram (Collaborative Post)
- **Visual Asset:** Official Zoho Finalist Badge Graphic (from Zoho Toolkit) customized with team photo or BASIN logo banner.

### Post 1 Copy:

> 🚀 **Exciting News: We’re heading to California as National Finalists in Zoho’s inaugural "From The Ground Up" AI Hackathon!**
> 
> Out of hundreds of nationwide submissions, our team—Noah Wilborn, Mohammed Asad Khan, and Misha Stegall—has been selected as one of the **Top 5 Finalists** to present our project at Zoho’s North American Headquarters in Pleasanton on September 22!
> 
> We built **BASIN** (Basin Analysis & Scenario Intelligence Navigator) in response to a challenge we saw in Texas: rainfall evidence, scenario assumptions, and review decisions can become scattered across downloads, spreadsheets, screenshots, and meeting notes.
> 
> BASIN provides an open, on-device workflow that turns public rainfall observations and explicit assumptions into a transparent scenario shortlist for technical review. Its replayable handoff preserves the data, calculations, limitations, and human screening decisions.
> 
> A huge thank you to Ariel, Garrett, Mira, and the entire @Zoho USA team for creating a competition centered around real community impact.
> 
> Stay tuned as we pull back the curtain on the technology and the human stories driving BASIN over the next week! 🌊
> 
> #fromthegroundup #Zoho #AIForGood #WaterSecurity #CivicTech #OpenSource #DataSovereignty #TexasTech

---

## Post 2: The Faces Behind the Idea

- **Target Publication Date:** **Wednesday, September 17, 2026 (~11:00 AM CDT)**
- **Primary Platform:** Instagram (Carousel) & LinkedIn
- **Visual Asset:** 3–4 candid photos:
  - Slide 1: Team photo around laptops analyzing code/data.
  - Slide 2: Whiteboard diagram of the reservoir mass-balance and K-Means clustering.
  - Slide 3: Close-up of the `BASIN.exe` interface running on an unplugged laptop.

### Post 2 Copy:

> 👋 **Meet the team behind BASIN.**
> 
> Why would three college students spend their summer nights obsessed with reservoir evaporation, municipal water codes, and offline AI?
> 
> Because living in Texas, drought isn't an abstract concept—it’s our everyday reality. We watched our regional reservoirs plunge to a record low of 7.8% combined storage in April 2026 (per the City's water-supply update), while neighbors faced 20 months under lawn-watering bans and steep water surcharges.
> 
> When we dug deeper, we realized the biggest problem wasn't just a lack of rain; it was a lack of **data democracy**:
> - Billion-dollar corporations have teams of hydrologists running proprietary river basin models.
> - Rural county commissioners and small water supply corporations have… Microsoft Excel.
> 
> We wanted to change that equation.
> 
> - **Noah** focused on the rainfall-screening workflow, the illustrative storage accounting experiment, and transparent assumptions.
> - **Mohammed** built the optional on-device assistant, connecting a pinned local language model to deterministic BASIN tools so calculations remain inspectable.
> - **Misha** focused on plain-language review, evidence provenance, and the human handoff workflow.
> 
> On September 22, we’re taking our prototype to Pleasanton to pitch to Zoho’s judges. We can't wait to share what we've built!
> 
> #fromthegroundup @Zoho USA #Teamwork #MeetTheTeam #AIForSocialGood #Hydrology #StudentBuilders #TechForGood

---

## Post 3: The 5 Ws Deep Dive (In-Depth Long-Form)

- **Target Publication Date:** **Friday, September 18, 2026 (Early Afternoon, ~1:00 PM CDT)**
- **Primary Platform:** LinkedIn Article / Long-Form Post
- **Visual Asset:** High-resolution UI screenshots showing the 4-stage workflow and the Multi-Sector Delivery breakdown.

### Post 3 Copy:

> 💧 **What does "AI for Social Good" actually mean when a city is running out of water?**
> 
> As we finalize our presentation deck for the @Zoho USA #fromthegroundup finals next week, here is the complete 5 Ws breakdown of what BASIN is and why it matters:
> 
> 📍 **WHERE:**
> South Texas and the 11-county Coastal Bend (Region N). In April 2026, reservoir levels dropped to 7.8% combined storage, sparking national headlines that Corpus Christi was on track to become "the first city in America to run out of water."
> 
> 👥 **WHO:**
> Municipal and rural water providers, community planners, and technical reviewers who need to organize rainfall evidence and shortlist questions before commissioning formal analysis.
> 
> ❓ **WHAT:**
> BASIN (Basin Analysis & Scenario Intelligence Navigator) is an on-device, pre-model rainfall-scenario screening and expert-handoff tool. It turns a pinned NOAA rainfall snapshot and explicit assumptions into a reviewable shortlist and a SHA-256 hash-checked, replayable ZIP. The checks establish internal consistency within the ZIP's declared scope, not hydrologic validation or professional approval.
> 
> ⚙️ **HOW (THE AI ARCHITECTURE):**
> Many AI projects fail in municipal government because language models hallucinate. In water planning, an invented reservoir elevation could trigger a false emergency or delay critical conservation.
> BASIN solves this with a **dual-AI architecture**:
> 1. **Unsupervised K-Means clustering:** Groups 300 rainfall candidates using five shared features plus one normalized station-deficit feature per selected station, then selects one high-scoring representative from each cluster for human review.
> 2. **Optional local assistant:** A pinned Qwen model can route plain-language questions to deterministic BASIN tools. The rainfall workflow remains usable without the model, and no AI system is presented as incapable of error.
> 3. **Illustrative storage accounting:** A secondary, uncalibrated experiment checks numerical mass balance under visible capacity, demand, evaporation, pipeline, and rainfall-to-inflow assumptions. It is not a reservoir forecast or reliability model.
> 
> 🎯 **WHY:**
> Transparent tools can help communities and technical reviewers inspect where data came from, how scenarios were transformed, why a scenario was shortlisted, and which questions still require formal water-supply modeling and professional review.
> 
> We are deeply grateful to Zoho for championing grassroots civic tech. See you in Pleasanton on Tuesday! 🚀
> 
> #fromthegroundup @Zoho USA #AI #MachineLearning #WaterEquity #EnvironmentalJustice #CivicTech #DataSovereignty #Sustainability

---

## Social Media Tracking & Verification Checklist

| Deliverable | Target Date | Owner | Status | Screenshot Captured | Zoho Handle Tagged |
|---|---|---|---|---|---|
| **Post 1 (Announcement)** | Sept 15 | Noah | Ready to Post | [ ] | `@ZohoUSA` / `#fromthegroundup` |
| **Post 2 (Team Faces)** | Sept 17 | Misha | Ready to Post | [ ] | `@ZohoUSA` / `#fromthegroundup` |
| **Post 3 (The 5 Ws)** | Sept 18 | Mohammed | Ready to Post | [ ] | `@ZohoUSA` / `#fromthegroundup` |
| **Outreach Confirmation** | Sept 18 | Team | Ready | [ ] | Email screenshots to Garrett & Mira |
