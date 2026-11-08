"""Social-Care Authority agent (Ministry of Family / Senior Emiratis protection role)."""
from ..base import Agent, Rule


class SocialCareAuthority(Agent):
    name = "social_care"
    role = "institutional"
    mandate = "Rights and protection of Senior Emiratis and People of Determination; family obligations; protection units."
    rules = [
        Rule(id="SC1_caregiver_absent", when_all=["caregiver_absent"],
             question="protection_referral", stance="refer_protection_unit",
             decision="A senior left without a present caregiver during an emergency should be referred to the Senior Emiratis "
                      "protection unit for follow-up on family and caregiver obligations.",
             query="senior emiratis protection unit family obligations caregiver",
             authority_docs=["uae_senior_emiratis_law_2019"], escalation="regulator"),
        Rule(id="SC2_privacy_independence", when_all=["consent_conflict"],
             question="whose_wish_prevails", stance="senior_wish_default",
             decision="The senior's right to independence and privacy applies; family preference does not override it without a "
                      "lawful representative. Support the least intrusive option.",
             query="right to independence and privacy senior emiratis",
             authority_docs=["uae_senior_emiratis_law_2019"], escalation="human_review"),
        Rule(id="SC3_no_guardian", when_all=["no_guardian"],
             question="legal_representative", stance="court_or_protection_unit",
             decision="No guardian is appointed: nobody may consent on the senior's behalf; refer to the protection unit and, if "
                      "capacity is in doubt, to the court process for appointing a representative.",
             query="guardian appointed by the court legal representative senior unable to take care of himself",
             authority_docs=["uae_senior_emiratis_law_2019", "uae_pod_law_2006"], escalation="human_review"),
    ]
