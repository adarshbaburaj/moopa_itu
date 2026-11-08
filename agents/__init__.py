"""CareGuard agents. REGISTRY maps the agent names used in scenario files to classes."""
from .care_agent import CareAgent
from .policy_adviser import PolicyAdviser
from .institutional.health import HealthRegulator
from .institutional.dpa import DataProtectionAuthority
from .institutional.telecom import TelecomRegulator
from .institutional.medprod import MedicalProductsRegulator
from .institutional.social import SocialCareAuthority

REGISTRY = {cls.name: cls for cls in (CareAgent, PolicyAdviser, HealthRegulator, DataProtectionAuthority,
                                      TelecomRegulator, MedicalProductsRegulator, SocialCareAuthority)}
