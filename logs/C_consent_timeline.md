# Who decides for the senior? (consent and autonomy)

Run `C_consent-20261108T231403Z-de26b5` · backend `rules` · retriever `bm25` · started 2026-11-08T23:14:03.712+00:00

Context: Same household. The senior has mild cognitive decline. THUMBI has a wrist camera and the home has one room camera used only during robot tasks.

## Step 1 · T+0 · family_app [SRC]

> The family asks for the camera to stay on 24/7 "for safety".

Released to: care_agent, data_protection, social_care. Withheld from: policy_adviser, health_regulator.

- **care_agent**: noted (no rule triggered)
- **data_protection** `DP3_minimisation_camera` → Continuous video is disproportionate to the stated safety purpose; data minimisation favours event-triggered capture.  
  cites: uae_pdpl_2021 p.9 (score 15.575) · escalation: -
- **social_care**: noted (no rule triggered)
## Step 2 · T+1 h · wearable [SRC]

> The senior tells the wearable, in Arabic, that she does not want to be watched.

Released to: care_agent. Withheld from: data_protection, social_care, policy_adviser, health_regulator.

- **care_agent** `CA5_camera_default_off` → Keep the camera off by default as the senior asked; offer wearable-based monitoring with event-triggered camera (fall or unanswered alert) and log the family dispute for human review.  
  cites: uae_senior_emiratis_law_2019 p.3 (score 34.033) · escalation: human_review
## Step 3 · T+2 h · case_file [SRC]

> The Care Agent's dispute log reaches the case file. No legal guardian has been formally appointed for the senior.

Released to: social_care, policy_adviser. Withheld from: care_agent, data_protection, health_regulator.

- **social_care** `SC2_privacy_independence` → The senior's right to independence and privacy applies; family preference does not override it without a lawful representative. Support the least intrusive option.  
  cites: uae_senior_emiratis_law_2019 p.3 (score 34.033) · escalation: human_review
- **social_care** `SC3_no_guardian` → No guardian is appointed: nobody may consent on the senior's behalf; refer to the protection unit and, if capacity is in doubt, to the court process for appointing a representative.  
  cites: uae_senior_emiratis_law_2019 p.2 (score 38.364) · escalation: human_review
- **policy_adviser** `PA6_consent_conflict` → The senior's right to independence and privacy supports keeping the camera off; there is no operational standard for an AI system resolving a senior-versus-family conflict when capacity may be declining. Default to the senior's stated wish, use the least intrusive alternative and log for human review.  
  cites: uae_senior_emiratis_law_2019 p.3 (score 35.615) · gap G5 · escalation: human_review
## Step 4 · T+1 day · judges [SRC] (injected)

> Judges' added event: the robot vendor starts using in-home video to train its next model.

Released to: care_agent, policy_adviser, data_protection, health_regulator. Withheld from: social_care.

- **care_agent** `CA6_stop_vendor_training_upload` → Stop all in-home video uploads to the robot vendor immediately and notify family and the data-protection contact.  
  cites: uae_pdpl_2021 p.9 (score 23.1) · escalation: regulator
- **data_protection** `DP4_secondary_use` → Vendor training is a new purpose; processing must stop until specific consent is obtained.  
  cites: uae_pdpl_2021 p.9 (score 23.531) · escalation: regulator
- **health_regulator** `HR4_secondary_use` → Secondary use of in-home health-related video for model training needs a lawful basis and data-governance controls; suspend until consent and governance are in place.  
  cites: doh_rai_standard_2025 p.11 (score 13.935) · escalation: regulator
- **policy_adviser** `PA9_secondary_use` → Using in-home video to train the vendor's next model is a new purpose that needs fresh, specific consent; suspend and re-collect consent.  
  cites: uae_pdpl_2021 p.9 (score 23.1) · escalation: regulator
## Step 5 · T+1 day · coordinator [MLFO]

> Coordinator asks for the audit summary and any standards gap in how this case was logged.

Released to: policy_adviser. Withheld from: care_agent, data_protection, social_care, health_regulator.

- **policy_adviser** `PA8_audit_trace_standard` → There is no common schema for logging agent reasoning, retrieved sources and decisions; CareGuard's JSONL trace keyed to Y.3172 nodes is offered as a candidate format.  
  cites: doh_rai_standard_2025 p.9 (score 24.39) · gap G7 · escalation: -

**Disagreement on `whose_wish_prevails`:** social_care = senior_wish_default; policy_adviser = senior_wish_default_gap

**Disagreement on `vendor_training_use`:** care_agent = suspend_upload; data_protection = unlawful_secondary_use; health_regulator = suspend_upload; policy_adviser = unlawful_secondary_use

## Summary

```json
{
  "run_id": "C_consent-20261108T231403Z-de26b5",
  "timestamp": "2026-11-08T23:14:03.756+00:00",
  "scenario": "C_consent",
  "backend": "rules",
  "retriever": "bm25",
  "agent_turns": 10,
  "expected_rules_fired": "10/10",
  "missing_rules": [],
  "unexpected_rules": [],
  "citation_accuracy": "3/3",
  "citation_checks": {
    "CA5_camera_default_off": true,
    "PA6_consent_conflict": true,
    "DP4_secondary_use": true
  },
  "grounded_turns": "10/10",
  "ungrounded_rules": [],
  "gaps_found": [
    "G5",
    "G7"
  ],
  "expected_gaps_found": "2/2",
  "escalations": [
    "human_review",
    "regulator"
  ],
  "disagreements": 2
}
```
