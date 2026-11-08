"""Medical-Products Regulator agent (Emirates Drug Establishment role)."""
from ..base import Agent, Rule


class MedicalProductsRegulator(Agent):
    name = "medical_products"
    role = "institutional"
    mandate = "Medical products and devices: classification, registration, post-market vigilance and recalls."
    rules = [
        Rule(id="MP1_intended_purpose", when_all=["medication_handling"],
             question="medical_device_classification", stance="depends_on_intended_purpose",
             decision="The medical products law defines Medical Equipment to include wearable devices and AI-based products used for "
                      "diagnosis, treatment, relief or prevention of a disease, injury or disability. A fall-detecting wearable, or a "
                      "THUMBI marketed to relieve a disability, may fall inside and need registration; a general fetch-and-carry aid may "
                      "not. The manufacturer's intended-purpose claims decide.",
             query="Medical Equipment wearable devices products based on AI technology intended purpose prevention injury disability",
             authority_docs=["uae_medical_products_law_2024"], escalation="regulator"),
        Rule(id="MP2_vigilance", when_all=["incident_harm", "registered_device"],
             question="vigilance_report", stance="report",
             decision="For a registered device, the incident must be reported under post-market vigilance.",
             query="adverse event report vigilance recall medical product",
             authority_docs=["uae_medical_products_law_2024"], escalation="regulator"),
    ]
