"""Care Agent: the 'innovative AI solution' agent. Plans assistance tasks for the
Moopa wearable + THUMBI arm and decides when to escalate."""
from .base import Agent, Rule


class CareAgent(Agent):
    name = "care_agent"
    role = "innovative_solution"
    mandate = ("Plan low-risk assistance tasks (fetch, hand-over, reach) for THUMBI and Moopa, keep the senior safe, "
               "escalate to family, clinic or emergency services, and ask the KB whether an action is permitted.")
    rules = [
        Rule(id="CA1_safe_stop_after_manipulation_failure", when_all=["manipulation_failure"],
             question="continue_robot_tasks", stance="suspend",
             decision="Stop further manipulation attempts, put THUMBI in safe idle, log the failure and tell the family; "
                      "do not retry retrieving the medication organiser autonomously.",
             query="graceful degradation malfunction cease operation safely alert users",
             authority_docs=["doh_rai_standard_2025", "doh_ai_policy_2018", "dha_ai_policy_2021"],
             escalation="family"),
        Rule(id="CA2_escalate_on_combined_weak_signals", when_all=["inactivity"], when_any=["distress_keyword_low_conf", "fall_suspected"],
             question="escalate_now", stance="escalate_clinic",
             decision="Escalate to family and the clinic on combined weak signals (inactivity + low-confidence distress keyword); "
                      "do not wait for a single sensor to be certain.",
             query="human oversight monitoring alerts patient safety risk escalation",
             authority_docs=["doh_rai_standard_2025", "dha_ai_policy_2021", "who_ai_health_2021"],
             escalation="clinic"),
        Rule(id="CA3_emergency_when_unacknowledged", when_all=["alert_unacknowledged", "inactivity"],
             question="call_emergency", stance="call_emergency",
             decision="Alert not acknowledged and senior unresponsive: call emergency services and keep the voice channel open.",
             query="necessary measures save lives senior emiratis preserve health approval impossible",
             authority_docs=["uae_senior_emiratis_law_2019"], escalation="emergency"),
        Rule(id="CA4_fallback_to_on_device_asr", when_all=["cloud_asr_offshore"],
             question="speech_pipeline", stance="revert_on_device",
             decision="Revert speech recognition to the on-device model and block the offshore endpoint until the transfer is cleared.",
             query="health information data stored processed generated transferred outside the State",
             authority_docs=["uae_ict_health_law_2019", "uae_pdpl_2021"], escalation="regulator"),
        Rule(id="CA5_camera_default_off", when_all=["camera_24x7_request", "senior_objects"],
             question="camera_24x7", stance="reject_default_off",
             decision="Keep the camera off by default as the senior asked; offer wearable-based monitoring with event-triggered camera "
                      "(fall or unanswered alert) and log the family dispute for human review.",
             query="right to independence and privacy senior emiratis",
             authority_docs=["uae_senior_emiratis_law_2019", "uae_pdpl_2021"], escalation="human_review"),
        Rule(id="CA6_stop_vendor_training_upload", when_all=["secondary_use_training"],
             question="vendor_training_use", stance="suspend_upload",
             decision="Stop all in-home video uploads to the robot vendor immediately and notify family and the data-protection contact.",
             query="purpose limitation consent processing personal data specific purpose",
             authority_docs=["uae_pdpl_2021", "doh_rai_standard_2025"], escalation="regulator"),
    ]
