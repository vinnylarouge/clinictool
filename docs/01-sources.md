# 01. Source registry

The licence column is the project's critical path. Statuses below were checked June 2026; re-verify any row before building its adapter. Legend for v0 status: **SPINE** (entity layer), **INGEST** (content stored locally), **LINK** (deep link-out per drug, no ingestion), **APPLY** (licence application in flight, ingest later), **OUT**.

| Source | What it holds | Access route | Licence reality | Machine-readable | Cadence | v0 |
|---|---|---|---|---|---|---|
| **dm+d** (Dictionary of Medicines and Devices) | The NHS drug entity model: VTM/VMP/VMPP/AMP/AMPP, ingredients, forms, routes, excipient-bearing AMP detail, prices | NHS England TRUD, free account | Free to use under TRUD licence terms; the standard spine for every UK meds system | XML releases | Weekly | SPINE |
| **SNOMED CT UK Drug Extension** | SNOMED alignment of dm+d | TRUD | UK licence via TRUD | RF2 | Periodic | OUT (v1) |
| **BNF / BNFC** | The core formulary: indications, doses, interactions, safety prose | Browse free at bnf.nice.org.uk. Programmatic: BNF has its own syndication API, separate from the NICE API, subject to its own criteria and technical specification | Application and licence required; NICE syndication generally requires cyber security certification (Cyber Essentials class, or DSPT for public sector). AI use on syndicated NICE content is permitted subject to approval of the stated use; training models on it is not permitted. Students can route access via a university signing the licence | XML via API once licensed | Monthly updates | APPLY |
| **NICE syndication API** (guidance, quality standards) | NICE guidance corpus; explicitly does not include BNF or CKS | Application form, licence, API key | Test licences (about 3 months) exist for evaluation; domestic use terms differ from international (international fees are substantial) | XML | Rolling | OUT (v1) |
| **NICE CKS** | Primary-care topic summaries | Separate syndication arrangement | As above, own contact route | XML | Rolling | LINK |
| **emc** (electronic Medicines Compendium, Datapharm) | SPCs and PILs for 9,000 plus UK products, published by the marketing-authorisation holders post regulator approval | Free to view at medicines.org.uk. Programmatic: Datapharm sells a RESTful API (emc med data / market intelligence) with SPC and PIL raw documents mapped to dm+d codes; emc content is structured in FHIR | Web terms do not permit bulk scraping; the commercial API is the clean route at scale. For a ten-drug spike, manual download of individual SPCs for local research use is the pragmatic path | HTML and PDF; FHIR via paid API | Continuous (MAH-driven) | INGEST (manual, ten drugs) |
| **MHRA Products portal** (products.mhra.gov.uk) | SPCs, PILs, Public Assessment Reports, served by the regulator | Public website | Government-hosted; SPC text itself remains MAH copyright. Treat as the public mirror for per-document retrieval | PDF mostly | Regulatory cadence | LINK (alt to emc) |
| **MHRA Drug Safety Update** | Monthly safety bulletins, the live signal layer | gov.uk, public | Open Government Licence applies to gov.uk content generally | HTML | Monthly | INGEST (index) |
| **Yellow Card iDAP / Drug Analysis Prints** | UK ADR report aggregates | Public interactive site | View and analyse; check terms before redistribution | Semi | Rolling | LINK |
| **SPS** (Specialist Pharmacy Service) | The working pharmacist's site: administration advice, switching, shortages (Medicine Supply Tool), lactation, Medicines Q&As | sps.nhs.uk, free | NHS-provided web content; ingestion terms to confirm before any bulk use. Q&A structure is also the seed for our eval set | HTML | Rolling | LINK |
| **UKTIS / bumps** | Teratology monographs and patient leaflets | Web; full UKTIS monographs require health-professional registration | Registration-gated | HTML | Rolling | LINK |
| **TOXBASE** | Poisons information | NHS organisational registration | Closed to us | n/a | n/a | OUT |
| **MedicinesComplete** (Pharmaceutical Press) | Stockley's Drug Interactions, Martindale, BNF mirror | Commercial subscription | The interactions gold standard sits here. Licensing Stockley's is a future commercial decision, not a tinkering one | Platform | Rolling | OUT |
| **FDB Multilex** | The interaction/contraindication dataset inside most GP systems | Commercial | Incumbent infrastructure, not a source for us | n/a | n/a | OUT |
| **Liverpool interaction checkers** (hiv-, hep-, covid19-druginteractions.org) | Best-in-class domain interaction tools | Free web tools | Free to use, not to redistribute | Web | Rolling | LINK |
| **STOPP/START v3** | About 190 explicit criteria for potentially inappropriate prescribing in older adults | Published in European Geriatric Medicine (2023), criteria reproduced in open literature | Encode as rules with citation to the paper; verify reproduction terms | Paper tables | Static | v1 INGEST |
| **Anticholinergic burden scales** (ACB, AEC) | Per-drug anticholinergic scores | Published literature and calculator sites | Scores are published data points; encode with citation | Tables | Static | v1 INGEST |
| **CredibleMeds QTdrugs** | Categorised QT risk lists | Free registration | Redistribution restricted; store category locally for personal research, render as link-out with category label | CSV on registration | Rolling | LINK |
| **NEWT guidelines** | Administration via enteral feeding tubes, crushing/dispersing | Subscription (modest) | Beloved niche resource; link-out | Web | Rolling | LINK |
| **Medusa** (Injectable Medicines Guide) | IV administration | NHS institutional login | Closed to us | n/a | n/a | OUT |
| **Renal Drug Database** | Renal dosing reference | Commercial | Link-out only | Platform | Rolling | LINK |
| **Maudsley Prescribing Guidelines** | Psychotropics | Book/commercial | Cite-and-link | n/a | Editions | LINK |
| **Palliative Care Formulary** | Palliative prescribing | Commercial | Link-out | Platform | Rolling | LINK |
| **OpenPrescribing** (Bennett Institute, Oxford) | English primary-care prescribing data, plus the best open dm+d browser | Open API | Open | JSON | Monthly | v1 (context: what is actually prescribed) |
| **openFDA** | US labels, FAERS adverse events | Open API | Open | JSON | Rolling | v1 (signal browsing, US caveats) |
| **DDInter 2.0 / TWOSIDES** | Open research drug-interaction datasets | Open downloads | Research licences; quality heterogeneous, never present as authoritative alongside SPC text without labelling | CSV | Static-ish | v1 candidate |
| **NAPOS drug database** (porphyria) | Per-drug porphyria safety classification | Free web | Link-out | Web | Rolling | LINK |

## Three structural observations

1. **The spine is free, the prose is gated.** dm+d gives identity, structure, excipient-bearing product detail, and prices at zero cost. The valuable prose (BNF, Stockley's) is licensed. Architecture must therefore make link-outs first-class citizens: a row that deep-links into the right page of a gated source, pre-resolved to the right drug, is most of the value of ingestion at none of the licensing cost.
2. **SPCs are the legally authoritative per-product text and are publicly viewable.** A workbench built on SPC sections 4.1 to 4.6 and 6.1, joined per case, is buildable today without any licence application. The BNF application (APPLY row) runs in parallel and upgrades the product when it lands.
3. **The emc commercial API mapping SPC/PIL to dm+d codes** is exactly the join we would otherwise build by hand. If this ever stops being a tinkering project, that API is the first cheque to consider writing.
