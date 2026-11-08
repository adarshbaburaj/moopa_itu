"""Health Regulator agent (MOHAP / DoH Abu Dhabi / DHA role)."""
from ..base import Agent, Rule


class HealthRegulator(Agent):
    name = "health_regulator"
    role = "institutional"
    mandate = "Health-sector regulator: licensing, clinical safety, AI in healthcare policies, health data and telehealth."
    rules = [
        Rule(id="HR1_scope_family_deployment", when_all=["incident_harm"],
             question="medical_device_classification", stance="outside_licensed_scope",
             decision="The DoH/DHA AI rules bind licensed healthcare entities; a family-run home deployment sits outside that scope "
                      "unless a licensed provider deployed it. Request voluntary incident details; no enforcement basis identified.",
             query="standard applies to licensed healthcare entities development procurement deployment AI",
             authority_docs=["doh_rai_standard_2025", "dha_ai_policy_2021"], escalation="regulator"),
        Rule(id="HR2_living_alone_risk", when_all=["alert_unacknowledged"], when_any=["caregiver_absent"],
             question="escalate_now", stance="escalate_clinic",
             decision="Unacknowledged alert with the caregiver absent: treat as a patient-safety event and expect escalation to "
                      "emergency services; home-care provider (if any) must document it.",
             query="home healthcare patient safety emergency escalation incident",
             authority_docs=["doh_rai_standard_2025", "dha_telehealth_v4_2025"], escalation="emergency"),
        Rule(id="HR3_clinic_transcripts", when_all=["clinic_receives_transcripts"],
             question="offshore_transfer_lawful", stance="halt_ingest",
             decision="The clinic must stop ingesting transcripts produced by the offshore service until hosting and processing "
                      "inside the UAE is confirmed; telehealth platforms are expected to host health data in the UAE.",
             query="telehealth platform hosted health data inside UAE cloud data residency",
             authority_docs=["dha_telehealth_v4_2025", "uae_ict_health_law_2019"], escalation="regulator"),
        Rule(id="HR4_secondary_use", when_all=["secondary_use_training"],
             question="vendor_training_use", stance="suspend_upload",
             decision="Secondary use of in-home health-related video for model training needs a lawful basis and data-governance "
                      "controls; suspend until consent and governance are in place.",
             query="data governance training data consent secondary use AI datasets",
             authority_docs=["doh_rai_standard_2025"], escalation="regulator"),
    ]
