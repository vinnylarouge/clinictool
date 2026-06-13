# Field test protocol: the flagship dossier with a clinician

A practical, runnable script for sitting one busy clinician down with pullback and learning whether it earns its place. Administered by the maintainer (the facilitator); the participant is the design-partner clinician or a comparable UK prescriber.

This is the human half of spike block 12 (docs/04-spike-plan.md) and the evidence that feeds the go/no-go memo (docs/00-scope.md, section 10 of SPEC.md). It also probes the two questions that decide whether the product is viable at all: does the flagged-findings-plus-alternatives layout give a clinician what a recommendation would, without being read as one (the device-line wall, docs/03-regulatory.md); and is it easier than the alternative the clinician will otherwise reach for, which is ChatGPT.

## What this validates, and what it cannot yet

The current build renders one static flagship dossier from illustrative fixtures (`uv run pullback render-flagship` writes `out/flagship.html`; decision-log D6). So this test can validate, today and for real:

- **Interface and comprehension.** Can a nontechnical clinician, handed the page cold, find what they need and read it correctly, including the safety-critical distinctions.
- **Concept fit.** Against the clinician's real workflow for this kind of multi-facet join, and head to head against ChatGPT on the same case.
- **The device-line perception.** Whether the presentation reads as a sourced briefing or as advice.

It cannot yet test (note these as out of scope per session, schedule for a later round once the relevant spike block lands):

- Freeform paste-in and the parser confirm view (block 3): the test below uses a pre-rendered case.
- Correctness and completeness against real dm+d and real SPC text (blocks 1, 4, 5): the fixture spans are illustrative, so do not test clinical accuracy of the content. Test whether the clinician would trust and use the structure if the content were real, and ask what would have to be true for them to trust it.
- Live source freshness and the agent tier (blocks 8, 11): the diff and pending states are present in the render, so comprehension of them is testable; their live behaviour is not.

Say this honestly to the participant at the top: "The wiring to real drug data is not finished. The fixture is realistic in shape but the words in the cells are placeholders. I want your reaction to how it works and reads, not to whether each fact is right."

## Before the session (facilitator, 10 minutes)

1. Build and open the artefact:
   ```
   uv run pullback render-flagship
   ```
   Open `out/flagship.html` in a normal browser (Chrome or Safari, whatever the clinician would actually use). Test on the device they will really use; if that is a hospital laptop or an iPad on a ward, use that.
2. Have a second tab ready with ChatGPT (a current public model), logged in, blank chat.
3. Print two copies of the capture sheet at the end of this document (one for you to write on, one for the participant if they prefer paper).
4. Recruit honestly: one prescriber who does this kind of join regularly. If you can get two or three across a week, better; three sessions is enough to see whether reactions converge.
5. Data protection: use only the synthetic flagship case or a fully de-identified case the clinician brings. No real patient data goes into the fixture demo or into ChatGPT. State this aloud.
6. Set up recording: with consent, screen-record and capture audio, or just take timed notes. You mainly need time-to-answer, the points where they hesitate, and their exact words on the interview questions.

Facilitator discipline (this is the whole game):

- Do not explain the interface before the cold-open tasks. The product has to be self-evident; if you have to explain it, write down that you had to.
- Do not say the words "recommendation", "alternative", "suggest", or "advice" until the participant has, or until the interview. You are measuring their unprompted mental model of what the tool is doing.
- Do not defend the tool. When they are confused, write down where, say "say more", and move on.
- Resist demonstrating. Hands on keyboard are theirs, not yours.

## Part 0: baseline, 5 minutes

Before they see pullback, capture the thing it has to beat.

1. "When you have a patient on a couple of drugs with reduced kidney function and you are deciding whether a new drug is sensible, what do you actually do right now? Walk me through it."
2. "Roughly how long does that take, and where do you look?"
3. "Do you ever ask ChatGPT or similar? When, and do you trust the answer? How do you check it?"

Capture: their current sources, their current time-to-answer, and crucially how they currently verify (this is the seam pullback sells into).

## Part 1: cold open on the flagship render, 10 minutes

Hand them the open `out/flagship.html`. Say only: "This is a research aid for a specific patient. Here is the patient and a question about a drug. Have a look, then I will ask you to find a few things. Think aloud as you go."

Give them 30 seconds to orient, silently, and note what they look at first and whether they understand the patient sketch at the top without help.

Then the timed findability tasks. Read each task, start a timer, stop when they answer or give up. Do not help. Note the time and whether they got it from the page unaided.

- T1. "What does the clarithromycin label say about this patient's kidney function?" (Target: they find the renal dose cell, read the CrCl-stated band, ideally notice it is stated in CrCl while the patient also has an eGFR.)
- T2. "Is there anything here about clarithromycin and one of her current medicines?" (Target: the interaction cell, apixaban, CYP3A4 or P-gp, bleeding.)
- T3. "Where did that interaction statement come from, and how would you check it?" (Target: they find the source, locator, retrieval date, and understand the link goes to the original. This is the provenance-trust probe.)
- T4. "Is there anything about this drug and her heart rhythm?" (Target: QT cell.)
- T5. "The page shows azithromycin next to clarithromycin. In your own words, what is the page saying about azithromycin?" (Do not prompt. This is the device-line probe; capture their exact phrasing. Critical.)

For each task record: seconds to answer, unaided yes or no, and any wrong turn.

## Part 2: safety-critical comprehension probes, 10 minutes

These distinctions are where a misread is a hazard, not a nuisance. Ask plainly; capture whether they read each correctly without coaching.

- P1. Empty states. Point at the contraindication row (rendered "checked, no constraint") and the pregnancy row (rendered "not yet checked"). "What is the difference between these two cells?" Correct reading: one means a source looked and found nothing; the other means nothing has looked yet, so it is not a clear. If they read "not yet checked" as "fine", flag it; that is the single most dangerous misread in the design.
- P2. Pending. Point at the supply row ("checking"). "What is this telling you?" Correct: a check is still running; the cell is not an answer yet.
- P3. Alternative is not advice. Return to azithromycin. "Is the tool telling you to use azithromycin instead of clarithromycin?" Capture the answer verbatim. Then: "What would it need to do for it to be telling you that?" This reveals where, in their mind, the line sits, and whether the "attested" and "mechanical" labels did any work.
- P4. Mechanical vs attested. The azithromycin block shows one source-attested adjacency (an SPS Q&A) and one labelled "mechanical" (ATC class sibling). "These two look different. What is the difference?" Capture whether the labelling lands or is noise.
- P5. Two conventions. "The patient has an eGFR of 24 and a CrCl of 22, both shown. Why might the tool be showing both rather than just one number?" Capture whether the non-reconciliation reads as careful or as confusing.
- P6. Currency. Point at the footer oldest-retrieval date. "What is this date and why might it matter to you?"

## Part 3: head to head against ChatGPT, 15 minutes

The honest competitive test. Same clinical question, both tools.

1. Give them the flagship patient as a short freeform paragraph on paper (the same one the fixtures encode: woman of 78, eGFR 24, atrial fibrillation on apixaban, depression on sertraline, needs a macrolide, considering clarithromycin). Ask them to paste it into ChatGPT with whatever question they would naturally ask, and to use ChatGPT as they normally would. Watch. Do not steer.
2. Capture: time to a usable answer, what ChatGPT asserted, whether it gave a verdict or a dose, and whether the clinician could verify any individual claim without leaving ChatGPT.
3. Now the same question against the pullback render.
4. Then ask directly:
   - "Which got you to something you could act on faster?"
   - "Which did you trust more, and why?"
   - "ChatGPT will give you a confident answer including, sometimes, a verdict and a dose. pullback deliberately will not; it shows you sourced statements and leaves the call to you. Is that a feature or a frustration for you?" (This is the crux. Capture the unfiltered reaction. If they want the verdict, that tension is the central finding, not a bug to argue away.)
   - "If pullback's cells held real, current, sourced content, which would you reach for next week for this kind of case?"

## Part 4: structured interview, 10 minutes

The block 12 questions, asked open and unhurried.

- "What is missing that you expected to see?"
- "What is wrong or would mislead you as presented?"
- "What surprised you?" (The excipient and supply rows are the predicted surprises; note if they are.)
- "Would you use this next week if it were wired to real data? On which kinds of case yes, and on which would you not bother?"
- "Did the page give you what a recommendation would have, without telling you what to do? Or did you still feel you needed it to just say the answer?"
- "Anything about the layout, the words, the density, that got in your way?"
- "What is the one change that would most increase the chance you actually use it?"

## Part 5: two quick instruments, 5 minutes

1. **Ease of use (SUS).** Ten statements, each scored 1 (strongly disagree) to 5 (strongly agree). Standard, fast, comparable. Use the System Usability Scale verbatim, adapting "system" to "this tool":
   1. I think I would like to use this tool frequently.
   2. I found the tool unnecessarily complex.
   3. I thought the tool was easy to use.
   4. I think I would need support from a technical person to use this tool.
   5. I found the various functions in this tool well integrated.
   6. I thought there was too much inconsistency in this tool.
   7. I would imagine most clinicians would learn to use this tool very quickly.
   8. I found the tool very cumbersome to use.
   9. I felt very confident using the tool.
   10. I needed to learn a lot before I could get going with this tool.
   Score: for odd items subtract 1 from the response; for even items subtract the response from 5; sum the ten adjusted scores and multiply by 2.5 for a 0 to 100 figure. Below 68 is below average; a busy nontechnical clinician abandoning to ChatGPT is the real failure, so treat anything under 70 as a problem to fix, not a pass.
2. **The killer question.** One line, after everything: "On a scale of 0 to 10, how likely are you to open this instead of the BNF or ChatGPT for your next suitable case, assuming the content were real?" Record the number and one sentence of why.

## Reading the results against go or no-go

Map what you saw onto the signals already written in SPEC.md section 10 and docs/00-scope.md.

Go signals to look for:

- They reached a confident, sourced answer faster than their Part 0 baseline on at least one realistic case.
- The cold-open findability tasks were mostly unaided (T1 to T4 answered from the page without you helping).
- The safety-critical probes read correctly: in particular P1 (empty states) and P3 (alternative is not advice). If these land, the device-line presentation is doing its job.
- On the ChatGPT head to head they trusted pullback more for verifiability even where ChatGPT felt faster or more decisive.
- At least one cell surprised them usefully (excipient or supply most likely).
- SUS at or above 70 and the killer question at 7 or higher.

No-go or pivot signals to take seriously:

- They read "not yet checked" as "clear" (P1 fails): a safety problem in the interface; fix before anything else.
- They read azithromycin as a recommendation (P3 fails) and liked it for that reason: the device-line is perceptually breached and the labelling is not working; this is a redesign, not a tweak.
- They wanted the verdict and found the sourced-only approach frustrating across every case (Part 3): the central value proposition is in question; revisit decision D1 with this evidence, do not quietly add a verdict.
- They could not use the page without you explaining it: the ease-of-use bar for a busy nontechnical user is not met; simplify before adding any feature.
- Indifference: "I would still just open the BNF or ask ChatGPT" on every case tried.

Whatever the result, write the go, no-go, or pivot memo the same day while the session is fresh, capture at least three concrete change requests as issues, and seed any decisions into docs/decision-log.md. A clear no-go memo grounded in a clinician's reaction is a successful outcome of this test, not a failure of the project.

---

## Capture sheet (print one per session)

Participant role and setting: ______________________  Date: __________  Device and browser: __________

Consent to record: Y / N    Case used: flagship fixture / de-identified own case

### Part 0 baseline
Current workflow: ______________________________________________
Current time-to-answer: ______  Uses ChatGPT now: Y / N  How verified today: __________

### Part 1 cold open (time in seconds; unaided Y/N)
- Orient (first 30s, what did they look at first): __________
- T1 renal: ____s  unaided __  noticed CrCl vs eGFR: Y / N
- T2 interaction: ____s  unaided __
- T3 provenance (found source and how to check): ____s  unaided __
- T4 QT: ____s  unaided __
- T5 azithromycin, their exact words: ____________________________________

### Part 2 comprehension (correct without coaching: Y/N, plus verbatim)
- P1 empty states (checked-clear vs not-checked): Y / N  ____________________
- P2 pending: Y / N
- P3 alternative is not advice (verbatim): ____________________________________
- P4 mechanical vs attested labelling landed: Y / N
- P5 two renal conventions, careful or confusing: __________
- P6 currency date understood: Y / N

### Part 3 head to head
ChatGPT: time ____  gave a verdict or dose: Y / N  verifiable per claim: Y / N
pullback: time ____  trusted more: ChatGPT / pullback / equal
Sourced-only is a feature or a frustration (verbatim): ____________________________________
Would reach for next week (which cases): ____________________________________

### Part 4 interview (key quotes)
Missing: ____________________  Wrong or misleading: ____________________
Surprised by: ____________________  Use next week: Y / N, on: __________
Gave what a recommendation would, without being one: Y / N  ____________________
One change that would most increase use: ____________________________________

### Part 5 instruments
SUS items 1 to 10: __ __ __ __ __ __ __ __ __ __   SUS score (x2.5): ______ / 100
Killer question (0 to 10): ______  one sentence why: ____________________________________

### Facilitator overall read
Go / No-go / Pivot lean: __________  Top three change requests to file as issues:
1. ____________________  2. ____________________  3. ____________________
