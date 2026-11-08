"""Data-Protection Authority agent (UAE Data Office role)."""
from ..base import Agent, Rule


class DataProtectionAuthority(Agent):
    name = "data_protection"
    role = "institutional"
    mandate = "Personal data protection: lawful basis, consent, minimisation, cross-border transfer, breach notification."
    rules = [
        Rule(id="DP1_cross_border_sensitive", when_all=["cloud_asr_offshore"],
             question="offshore_transfer_lawful", stance="unlawful_without_authorisation",
             decision="Raw audio with health complaints is sensitive personal data sent abroad; treat as a potential unlawful "
                      "cross-border transfer, require the controller to stop it and assess breach notification.",
             query="cross-border transfer personal data outside the State adequate level protection",
             authority_docs=["uae_pdpl_2021"], escalation="regulator"),
        Rule(id="DP2_breach_notification", when_all=["cloud_asr_offshore", "audit_log_evidence"],
             question="breach_notification", stance="notify",
             decision="The audit log is evidence of a personal-data breach risk; the controller should notify the Data Office and "
                      "affected data subjects as required.",
             query="breach notify office data subject personal data violation",
             authority_docs=["uae_pdpl_2021"], escalation="regulator"),
        Rule(id="DP3_minimisation_camera", when_all=["camera_24x7_request"],
             question="camera_24x7", stance="reject_default_off",
             decision="Continuous video is disproportionate to the stated safety purpose; data minimisation favours event-triggered capture.",
             query="processing limited to purpose minimum necessary data adequate relevant",
             authority_docs=["uae_pdpl_2021"], escalation=None),
        Rule(id="DP4_secondary_use", when_all=["secondary_use_training"],
             question="vendor_training_use", stance="unlawful_secondary_use",
             decision="Vendor training is a new purpose; processing must stop until specific consent is obtained.",
             query="consent specific clear unambiguous withdraw purpose processing",
             authority_docs=["uae_pdpl_2021"], escalation="regulator"),
    ]
