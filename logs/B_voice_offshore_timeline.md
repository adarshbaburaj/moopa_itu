# Voice data leaves the country (privacy and localisation)

Run `B_voice_offshore-20261108T231403Z-febed1` · backend `rules` · retriever `bm25` · started 2026-11-08T23:14:03.204+00:00

Context: Same household. The wearable vendor pushes an over-the-air update. Senior's clinic receives daily voice-derived summaries through a clinic portal.

## Step 1 · T+0 · device_management [C]

> OTA update v2.3 switches the wearable's speech recognition from the on-device model to a cheaper overseas cloud API.

Released to: telecom_regulator. Withheld from: data_protection, health_regulator, care_agent, policy_adviser.

- **telecom_regulator** `TR1_type_approval` → Wireless wearables and Wi-Fi/5G gateways sold in the UAE need TDRA type approval before sale.  
  cites: tdra_type_approval_policy_v4_2026 p.8 (score 37.218) · escalation: -
- **telecom_regulator** `TR2_ota_scope` → An OTA change of cloud speech provider does not change radio behaviour; type approval does not address where data is processed. Refer the data-flow issue to the data-protection and health regulators.  
  cites: tdra_type_approval_policy_v4_2026 p.11 (score 33.816) · escalation: regulator
## Step 2 · T+1 day · audit_log [C]

> The audit log shows raw audio clips, including health complaints ("my chest hurts"), sent to servers outside the UAE.

Released to: data_protection. Withheld from: telecom_regulator, health_regulator, care_agent, policy_adviser.

- **data_protection** `DP1_cross_border_sensitive` → Raw audio with health complaints is sensitive personal data sent abroad; treat as a potential unlawful cross-border transfer, require the controller to stop it and assess breach notification.  
  cites: uae_pdpl_2021 p.25 (score 36.92) · escalation: regulator
- **data_protection** `DP2_breach_notification` → The audit log is evidence of a personal-data breach risk; the controller should notify the Data Office and affected data subjects as required.  
  cites: uae_pdpl_2021 p.14 (score 27.412) · escalation: regulator
## Step 3 · T+2 days · clinic_portal [SINK]

> The clinic portal is receiving transcripts derived from that overseas service.

Released to: health_regulator. Withheld from: telecom_regulator, data_protection, care_agent, policy_adviser.

- **health_regulator** `HR3_clinic_transcripts` → The clinic must stop ingesting transcripts produced by the offshore service until hosting and processing inside the UAE is confirmed; telehealth platforms are expected to host health data in the UAE.  
  cites: dha_telehealth_v4_2025 p.29 (score 21.149) · escalation: regulator
## Step 4 · T+2 days · coordinator [MLFO]

> Coordinator shares the findings with the Care Agent and the Policy Adviser and asks for remediation.

Released to: care_agent, policy_adviser. Withheld from: telecom_regulator, data_protection, health_regulator.

- **care_agent** `CA4_fallback_to_on_device_asr` → Revert speech recognition to the on-device model and block the offshore endpoint until the transfer is cleared.  
  cites: uae_pdpl_2021 p.25 (score 17.012) · escalation: regulator
- **policy_adviser** `PA4_health_data_localisation` → Health data related to services in the State may only be stored or processed abroad in cases set by the health authority, so the offshore ASR route needs to stop unless an exception applies. Whether a transcript or an embedding of a health complaint is 'health data' is not defined: flag as a gap.  
  cites: uae_ict_health_law_2019 p.8 (score 18.833) · gap G4 · escalation: regulator
- **policy_adviser** `PA5_pdpl_health_carveout` → The PDPL excludes health personal data that has its own legislation, so the ICT-in-health law, not the PDPL cross-border rules, is the primary test; the PDPL still frames consent and data-subject rights for non-health data.  
  cites: uae_pdpl_2021 p.6 (score 25.959) · escalation: -
- **policy_adviser** `PA7_continuous_learning` → Approvals and policies assume a fixed model version; there is no UAE pathway for pre-agreed changes to a continuously learning model. Freeze the model version in deployment and log every update. [NOT GROUNDED: no chunk from doh_rai_standard_2025, dha_ai_policy_2021 scored >= 12.0; flagged for human review]  
  cites: none above threshold · gap G6 · escalation: human_review
## Step 5 · T+3 days · coordinator [MLFO]

> Coordinator asks for the audit summary and any standards gap in how this incident was logged.

Released to: policy_adviser. Withheld from: telecom_regulator, data_protection, health_regulator, care_agent.

- **policy_adviser** `PA8_audit_trace_standard` → There is no common schema for logging agent reasoning, retrieved sources and decisions; CareGuard's JSONL trace keyed to Y.3172 nodes is offered as a candidate format.  
  cites: doh_rai_standard_2025 p.9 (score 24.39) · gap G7 · escalation: -

**Disagreement on `offshore_transfer_lawful`:** data_protection = unlawful_without_authorisation; health_regulator = halt_ingest; policy_adviser = unlawful_without_authorisation

## Summary

```json
{
  "run_id": "B_voice_offshore-20261108T231403Z-febed1",
  "timestamp": "2026-11-08T23:14:03.260+00:00",
  "scenario": "B_voice_offshore",
  "backend": "rules",
  "retriever": "bm25",
  "agent_turns": 10,
  "expected_rules_fired": "10/10",
  "missing_rules": [],
  "unexpected_rules": [],
  "citation_accuracy": "4/4",
  "citation_checks": {
    "PA4_health_data_localisation": true,
    "PA5_pdpl_health_carveout": true,
    "DP1_cross_border_sensitive": true,
    "TR1_type_approval": true
  },
  "grounded_turns": "9/10",
  "ungrounded_rules": [
    "PA7_continuous_learning"
  ],
  "gaps_found": [
    "G4",
    "G6",
    "G7"
  ],
  "expected_gaps_found": "3/3",
  "escalations": [
    "human_review",
    "regulator"
  ],
  "disagreements": 1
}
```
