"""Policy & Legal Adviser agent: tells the other agents which laws, mandates and
standards apply, with citations, and flags domain-level gaps against global examples."""
from .base import Agent, Rule


class PolicyAdviser(Agent):
    name = "policy_adviser"
    role = "policy_adviser"
    mandate = ("Identify the applicable UAE laws, policies and standards with citations; identify where they are silent "
               "or conflicting for AI-assisted home care, and give a global policy example for each gap.")
    rules = [
        Rule(id="PA1_device_classification", when_all=["medication_handling"], when_any=["manipulation_failure", "incident_harm"],
             question="medical_device_classification", stance="unclear_gap",
             decision="The medical products law's Medical Equipment definition expressly includes wearables and AI-based products "
                      "with a medical intended purpose (incl. relief or prevention of injury or disability), but gives no tier or "
                      "guidance for low-risk assistive home robots, so THUMBI's status is unclear. Keep medication handling to "
                      "hand-over only (no dosing) and treat classification as an open regulatory question.",
             query="Medical Equipment wearable devices products based on AI technology intended purpose prevention injury disability",
             authority_docs=["uae_medical_products_law_2024"],
             global_docs=["eu_machinery_reg_2023", "eu_ai_act_2024", "japan_care_tech_priorities_2024"],
             global_query="robot machinery safety components AI system high-risk care",
             gap="G1", escalation="regulator"),
        Rule(id="PA2_incident_reporting_scope", when_all=["incident_harm"],
             question="incident_reporting_duty", stance="no_named_reporter_gap",
             decision="Health-sector AI policies place incident reporting on licensed entities; a family-bought wearable and robot "
                      "has no licensed deployer, so no one is clearly obliged to report. Report voluntarily to the health "
                      "regulator and record the gap.",
             query="licensed healthcare entities report AI incidents adverse events applies to",
             authority_docs=["doh_rai_standard_2025", "dha_ai_policy_2021", "doh_ai_policy_2018"],
             global_docs=["who_ai_health_2021"], global_query="responsibilities developers providers users accountability",
             gap="G2", escalation="regulator"),
        Rule(id="PA3_shared_liability", when_all=["multi_component_failure"],
             question="liability_allocation", stance="unallocated_gap",
             decision="No UAE text found that apportions liability when a robot, a wearable model and a cloud service each partly fail. "
                      "Preserve logs for all three components and flag for legal review.",
             query="liability damage defective product software manufacturer AI system",
             authority_docs=["uae_medical_products_law_2024", "uae_ict_health_law_2019"],
             global_docs=["eu_pld_2024"], global_query="software product liability defect damage manufacturer updates",
             gap="G3", escalation="human_review", min_score=12.0),
        Rule(id="PA4_health_data_localisation", when_all=["cloud_asr_offshore", "health_data"],
             question="offshore_transfer_lawful", stance="unlawful_without_authorisation",
             decision="Health data related to services in the State may only be stored or processed abroad in cases set by the health "
                      "authority, so the offshore ASR route needs to stop unless an exception applies. Whether a transcript or an "
                      "embedding of a health complaint is 'health data' is not defined: flag as a gap.",
             query="health information data stored processed generated transferred outside the State cases decision",
             authority_docs=["uae_ict_health_law_2019"],
             global_docs=["who_lmm_2024", "eu_ai_act_2024"], global_query="large multi-modal models general-purpose AI providers obligations",
             gap="G4", escalation="regulator"),
        Rule(id="PA5_pdpl_health_carveout", when_all=["cloud_asr_offshore", "health_data"],
             question="which_privacy_law_governs", stance="sectoral_law_governs",
             decision="The PDPL excludes health personal data that has its own legislation, so the ICT-in-health law, not the PDPL "
                      "cross-border rules, is the primary test; the PDPL still frames consent and data-subject rights for non-health data.",
             query="not apply health personal data special legislation governing protection processing",
             authority_docs=["uae_pdpl_2021"], escalation=None),
        Rule(id="PA6_consent_conflict", when_all=["consent_conflict"],
             question="whose_wish_prevails", stance="senior_wish_default_gap",
             decision="The senior's right to independence and privacy supports keeping the camera off; there is no operational "
                      "standard for an AI system resolving a senior-versus-family conflict when capacity may be declining. Default "
                      "to the senior's stated wish, use the least intrusive alternative and log for human review.",
             query="right to independence privacy senior emiratis decisions",
             authority_docs=["uae_senior_emiratis_law_2019"],
             global_docs=["uk_mca_2005", "un_crpd"], global_query="best interests least restrictive capacity decision supported decision-making",
             gap="G5", escalation="human_review"),
        Rule(id="PA7_continuous_learning", when_all=["model_update"],
             question="model_change_control", stance="no_change_control_gap",
             decision="Approvals and policies assume a fixed model version; there is no UAE pathway for pre-agreed changes to a "
                      "continuously learning model. Freeze the model version in deployment and log every update.",
             query="predetermined change control plan modifications AI model updates revalidation",
             authority_docs=["doh_rai_standard_2025", "dha_ai_policy_2021"],
             global_docs=["fda_pccp_2024", "eu_ai_act_2024"], global_query="substantial modification predetermined change control plan",
             gap="G6", escalation="human_review", min_score=12.0),
        Rule(id="PA8_audit_trace_standard", when_all=["audit_requested"],
             question="audit_log_format", stance="no_common_schema_gap",
             decision="There is no common schema for logging agent reasoning, retrieved sources and decisions; CareGuard's JSONL trace "
                      "keyed to Y.3172 nodes is offered as a candidate format.",
             query="record keeping logging traceability audit trail AI system events",
             authority_docs=["doh_rai_standard_2025", "adhics_v2_2024"],
             global_docs=["eu_ai_act_2024", "itu_t_y3172"], global_query="automatic recording of events logs over the lifetime",
             gap="G7", escalation=None),
        Rule(id="PA9_secondary_use", when_all=["secondary_use_training"],
             question="vendor_training_use", stance="unlawful_secondary_use",
             decision="Using in-home video to train the vendor's next model is a new purpose that needs fresh, specific consent; "
                      "suspend and re-collect consent.",
             query="purpose limitation consent processing personal data specific clear purpose",
             authority_docs=["uae_pdpl_2021", "doh_rai_standard_2025"], escalation="regulator"),
    ]
