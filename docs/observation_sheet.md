# Analyst session observation sheet

Created 2026-09-06 for B09.3. One sheet per participant. This records what an observer saw during a single session; it is not a usability study, a measurement of time saved, or evidence of scientific validity.

## Before the session

- Confirm the participant agreed to be observed and to anonymous summary in team documents. Stop if they have not.
- Record no names, employers, contact details or raw quotes that identify anyone. Use "participant" and "recipient" throughout.
- Note the build: commit, whether the packaged kit or a development checkout was used, and whether the machine was offline.
- Do not coach. Answer a direct question only after recording that the participant needed to ask.

| Field | Entry |
|---|---|
| Session date | |
| Observer | |
| Participant role (no name) | |
| Build commit / package | |
| Offline? | |
| Prior exposure to BASIN | none / demo seen / used before |

## The task given to the participant

Read this aloud, unchanged:

> Using the bundled rainfall observations, choose three rainfall stress scenarios you would send to a hydrologist for deeper analysis. Explain why you chose each one. Challenge at least one assumption the tool is making. Then produce a packet you would actually be willing to send.

## Timing

| Milestone | Clock time | Notes |
|---|---|---|
| Started | | |
| First scenario generated | | |
| Shortlist settled | | |
| First assumption challenged or disagreement recorded | | |
| Packet built | | |
| Finished or gave up | | |

Total elapsed: ____ minutes. Elapsed time is descriptive. Without a recorded baseline of the participant's current method (B09.5), it does not support any claim about time saved.

## Assistance needed

Log every intervention, including "I pointed at the screen".

| # | Clock | What the participant was trying to do | What the observer did or said | Would the participant have proceeded unaided? |
|---|---|---|---|---|
| 1 | | | | yes / no / unclear |
| 2 | | | | |
| 3 | | | | |

## Terms and screens the participant misread

| Term, control or screen | What they said or assumed it meant | What it actually means | Where they encountered it |
|---|---|---|---|
| | | | |

Watch particularly for: retention percentage versus drought severity; concurrence versus single-station stress frequency; reference percentile versus probability of occurrence; "Accept" versus professional sign-off; the reservoir experiment versus a prediction; group or profile names versus catchment types.

## Assumptions the participant rejected or questioned

| Assumption | Their objection, in their framing | Recorded in the tool? | Where it should have been visible |
|---|---|---|---|
| | | evidence record / conflict / note / nowhere | |

## Evidence they wanted and could not find

| What they looked for | Why they wanted it | Where they looked first |
|---|---|---|
| | | |

## Can they explain the result?

Ask at the end, without prompting from the screen:

1. Why is this scenario on your shortlist and that one not? → recorded answer, in their words:
2. What is this rainfall number actually measuring, and over what area? →
3. What in this packet is uncertain or disputed? →
4. What would the hydrologist do with it next? →

| Judgement | Observer's rating | Basis |
|---|---|---|
| Could explain the selection unaided | yes / partly / no | |
| Could state the geographic limitation | yes / partly / no | |
| Could locate the unresolved issues | yes / partly / no | |
| Would send this packet to a colleague as-is | yes / with changes / no | |

## Recipient handoff (B09.6, if a recipient participated)

| Question | Entry |
|---|---|
| Opened the CSV and brief without help? | |
| Format changes their workflow requires | |
| What they would ask the sender for next | |
| Would they accept this as a request for analysis? | |

## Observer's close-out

- Three problems worth turning into board tasks, most disruptive first:
  1.
  2.
  3.
- Anything the participant liked enough to say unprompted:
- Anything the observer did that likely changed the outcome:
- Session order and learning effects (first session of the day, participant had watched a previous run, etc.):

## After the session

- Convert the three problems into owned subtasks under the relevant board ID and link this sheet.
- Summarize in `docs/validation_notes.md` under the pending-validation items. Record what was observed, not what was hoped for.
- If no external participant was available, label the session an internal rehearsal in every document that cites it.
