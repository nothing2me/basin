# September 22 demo runbook

## Three-minute product demonstration

1. Sidebar / New run: keep three provisional station proxies; 90, 180, 270 days; Jan/Apr/Jul/Oct; 35–85% retained rainfall; 300 candidates; six shortlisted; seed 22. Explain provisional geography and rainfall-only scope. Generate.
2. Workspace / Ranking weights: increase concurrent stress or duration weight. Scores change immediately. Rebuild the shortlist and show coverage beside score-only and seeded random. Do not claim clustering always maximizes distance or gives a scientifically better choice.
3. Review: show a source window and same-duration rainfall reference. Accept a scenario, add a note, then reduce rainfall. Show that acceptance clears and revision increments. Accept the new revision.
4. Accept or reject remaining scenarios. Rejection needs a reason. Show candidate swap or the custom CSV replacement if time permits.
5. Export: leave private notes unchecked. Build verified export, then download. Rainfall CSV, audit and snapshot form a request for expert analysis, not a water-planning verdict.
6. Explain measured compute and assumption-based energy. Water impact is unquantified. Name remaining practitioner validation.

## Before travel

- Use the actual presentation laptop. The kit requires 64-bit Windows and Python 3.12 installed beforehand. Setup BASIN.cmd uses bundled wheels offline. Start BASIN.cmd opens the local app. Other OS scripts need their own installation test.
- Run `.venv\Scripts\python.exe -m pytest -q` and `.venv\Scripts\python.exe scripts/demo_smoke.py`. The rehearsal blocks network sockets, generates 500 candidates, edits, approves and replays six exports. Automated approvals are not practitioner validation.
- Rehearse with Wi-Fi off and the actual projector. Test downloads and sidebar session restoration after a refresh.
- Copy the kit to USB. Distribution excludes private notes and sessions; back up the local workspace separately if needed.
- Record a backup video using the final demo build. No video has been recorded by this build.
- Team review of AI-assisted code, dependencies, disclosure, final pitch and new organizer instructions remains necessary.

## Recovery

Keep the console open. On browser refresh use Saved runs / Open run. If port 8501 is occupied, close the old BASIN console or specify another Streamlit port. On checksum failure restore observations.csv and manifest.json together. Saved sessions require their original snapshot.

## Judge questions

- AI is local KMeans; generation, ranking and explanations are deterministic/statistical. No LLM in the product.
- Three discovery responses informed traceability and user control. No field validation or demonstrated improvement in water outcomes is claimed.
- Privacy is a single-operator loopback server with local notes and export opt-in, not encrypted multiuser storage.
- Scientific limitations include unvalidated regional proxies, rainfall-only transformations, a short empirical reference, and no occurrence probabilities.
