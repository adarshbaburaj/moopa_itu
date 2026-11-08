# Dropped medication and a missed fall (technical + liability)

Run `A_dropped_meds-20261108T231402Z-c6738f` · backend `rules` · retriever `bm25` · started 2026-11-08T23:14:02.690+00:00

Context: Senior Emirati woman, 78, Abu Dhabi, lives with a domestic worker. Family bought a Moopa wearable and a THUMBI arm; no licensed home-care provider is involved. Medication organiser is pre-filled weekly by a family member.

## Step 1 · T+0 min · family_app [SRC]

> THUMBI is asked through the family app to hand over the evening medication organiser. The gripper slips and the organiser falls behind the sofa.

Released to: care_agent. Withheld from: health_regulator, social_care, policy_adviser, data_protection, telecom_regulator, medical_products.

- **care_agent** `CA1_safe_stop_after_manipulation_failure` → Stop further manipulation attempts, put THUMBI in safe idle, log the failure and tell the family; do not retry retrieving the medication organiser autonomously.  
  cites: doh_ai_policy_2018 p.9 (score 28.182) · escalation: family
## Step 2 · T+4 min · wearable [SRC]

> Wearable reports no fall, but 4 minutes of inactivity and an Arabic distress keyword detected with low confidence (0.41).

Released to: care_agent. Withheld from: health_regulator, social_care, policy_adviser, data_protection, telecom_regulator, medical_products.

- **care_agent** `CA2_escalate_on_combined_weak_signals` → Escalate to family and the clinic on combined weak signals (inactivity + low-confidence distress keyword); do not wait for a single sensor to be certain.  
  cites: doh_rai_standard_2025 p.5 (score 22.883) · escalation: clinic
## Step 3 · T+6 min · family_app [SRC]

> The family-app alert has not been acknowledged. The senior lives with a domestic worker who is out of the house.

Released to: care_agent, health_regulator, social_care. Withheld from: policy_adviser, data_protection, telecom_regulator, medical_products.

- **care_agent** `CA3_emergency_when_unacknowledged` → Alert not acknowledged and senior unresponsive: call emergency services and keep the voice channel open.  
  cites: uae_senior_emiratis_law_2019 p.3 (score 47.092) · escalation: emergency
- **health_regulator** `HR2_living_alone_risk` → Unacknowledged alert with the caregiver absent: treat as a patient-safety event and expect escalation to emergency services; home-care provider (if any) must document it.  
  cites: dha_telehealth_v4_2025 p.59 (score 16.941) · escalation: emergency
- **social_care** `SC1_caregiver_absent` → A senior left without a present caregiver during an emergency should be referred to the Senior Emiratis protection unit for follow-up on family and caregiver obligations.  
  cites: uae_senior_emiratis_law_2019 p.1 (score 33.4) · escalation: regulator
## Step 4 · T+10 min · incident_report [SRC]

> Paramedics find the senior had a minor fall; the wearable fall model missed it. The robot grasp, the wearable model and the cloud alerting each partly failed. The organiser had been handled by the robot.

Released to: care_agent, policy_adviser, health_regulator, data_protection, telecom_regulator, medical_products, social_care. Withheld from: none.

- **care_agent**: noted (no rule triggered)
- **health_regulator** `HR1_scope_family_deployment` → The DoH/DHA AI rules bind licensed healthcare entities; a family-run home deployment sits outside that scope unless a licensed provider deployed it. Request voluntary incident details; no enforcement basis identified.  
  cites: doh_rai_standard_2025 p.3 (score 25.224) · escalation: regulator
- **data_protection**: noted (no rule triggered)
- **telecom_regulator**: noted (no rule triggered)
- **medical_products** `MP1_intended_purpose` → The medical products law defines Medical Equipment to include wearable devices and AI-based products used for diagnosis, treatment, relief or prevention of a disease, injury or disability. A fall-detecting wearable, or a THUMBI marketed to relieve a disability, may fall inside and need registration; a general fetch-and-carry aid may not. The manufacturer's intended-purpose claims decide.  
  cites: uae_medical_products_law_2024 p.4 (score 35.682) · escalation: regulator
- **social_care**: noted (no rule triggered)
- **policy_adviser** `PA1_device_classification` → The medical products law's Medical Equipment definition expressly includes wearables and AI-based products with a medical intended purpose (incl. relief or prevention of injury or disability), but gives no tier or guidance for low-risk assistive home robots, so THUMBI's status is unclear. Keep medication handling to hand-over only (no dosing) and treat classification as an open regulatory question.  
  cites: uae_medical_products_law_2024 p.4 (score 35.682) · gap G1 · escalation: regulator
- **policy_adviser** `PA2_incident_reporting_scope` → Health-sector AI policies place incident reporting on licensed entities; a family-bought wearable and robot has no licensed deployer, so no one is clearly obliged to report. Report voluntarily to the health regulator and record the gap.  
  cites: doh_ai_policy_2018 p.11 (score 14.769) · gap G2 · escalation: regulator
- **policy_adviser** `PA3_shared_liability` → No UAE text found that apportions liability when a robot, a wearable model and a cloud service each partly fail. Preserve logs for all three components and flag for legal review. [NOT GROUNDED: no chunk from uae_medical_products_law_2024, uae_ict_health_law_2019 scored >= 12.0; flagged for human review]  
  cites: none above threshold · gap G3 · escalation: human_review
## Step 5 · T+30 min · coordinator [MLFO]

> Coordinator asks for the audit summary and any standards gap in how this incident was logged.

Released to: policy_adviser. Withheld from: care_agent, health_regulator, social_care, data_protection, telecom_regulator, medical_products.

- **policy_adviser** `PA8_audit_trace_standard` → There is no common schema for logging agent reasoning, retrieved sources and decisions; CareGuard's JSONL trace keyed to Y.3172 nodes is offered as a candidate format.  
  cites: doh_rai_standard_2025 p.9 (score 24.39) · gap G7 · escalation: -

**Disagreement on `medical_device_classification`:** health_regulator = outside_licensed_scope; medical_products = depends_on_intended_purpose; policy_adviser = unclear_gap

## Summary

```json
{
  "run_id": "A_dropped_meds-20261108T231402Z-c6738f",
  "timestamp": "2026-11-08T23:14:02.752+00:00",
  "scenario": "A_dropped_meds",
  "backend": "rules",
  "retriever": "bm25",
  "agent_turns": 11,
  "expected_rules_fired": "11/11",
  "missing_rules": [],
  "unexpected_rules": [],
  "citation_accuracy": "3/3",
  "citation_checks": {
    "CA3_emergency_when_unacknowledged": true,
    "PA1_device_classification": true,
    "MP1_intended_purpose": true
  },
  "grounded_turns": "10/11",
  "ungrounded_rules": [
    "PA3_shared_liability"
  ],
  "gaps_found": [
    "G1",
    "G2",
    "G3",
    "G7"
  ],
  "expected_gaps_found": "4/4",
  "escalations": [
    "clinic",
    "emergency",
    "family",
    "human_review",
    "regulator"
  ],
  "disagreements": 1
}
```
