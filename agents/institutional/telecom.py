"""Telecom Regulator agent (TDRA role)."""
from ..base import Agent, Rule


class TelecomRegulator(Agent):
    name = "telecom_regulator"
    role = "institutional"
    mandate = "Telecommunications: equipment type approval, network connectivity, spectrum; not data-protection substance."
    rules = [
        Rule(id="TR1_type_approval", when_all=["connected_device"],
             question="device_market_access", stance="type_approval_required",
             decision="Wireless wearables and Wi-Fi/5G gateways sold in the UAE need TDRA type approval before sale.",
             query="telecommunications equipment approval before displayed sold UAE registration wireless",
             authority_docs=["tdra_type_approval_policy_v4_2026"], escalation=None),
        Rule(id="TR2_ota_scope", when_all=["ota_update"],
             question="ota_software_change", stance="outside_tdra_scope_refer",
             decision="An OTA change of cloud speech provider does not change radio behaviour; type approval does not address where "
                      "data is processed. Refer the data-flow issue to the data-protection and health regulators.",
             query="type approval software update modification equipment re-approval",
             authority_docs=["tdra_type_approval_policy_v4_2026"], escalation="regulator"),
    ]
