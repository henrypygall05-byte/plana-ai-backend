"""
Policy management and storage.

Handles loading, storing, and updating planning policies.
"""

import json
import uuid
from datetime import date
from pathlib import Path
from typing import AsyncIterator

import structlog

from plana.config import get_settings
from plana.core.models import Policy, PolicyType

logger = structlog.get_logger(__name__)


class PolicyManager:
    """
    Manages planning policies storage and retrieval.

    Handles:
    - Loading policies from files
    - Storing policies in database/vector store
    - Policy versioning and updates
    """

    def __init__(self):
        """Initialize policy manager."""
        self.settings = get_settings()
        self._policies: dict[str, Policy] = {}
        self._loaded = False

    async def load_policies(self, source_dir: Path | None = None) -> int:
        """Load policies from source directory.

        Args:
            source_dir: Directory containing policy files

        Returns:
            Number of policies loaded
        """
        if source_dir is None:
            source_dir = self.settings.data_dir / "policies"

        if not source_dir.exists():
            logger.warning("Policy directory not found", path=str(source_dir))
            return 0

        count = 0
        for policy_file in source_dir.glob("**/*.json"):
            try:
                with open(policy_file) as f:
                    data = json.load(f)

                if isinstance(data, list):
                    for item in data:
                        policy = self._parse_policy(item)
                        self._policies[policy.id] = policy
                        count += 1
                else:
                    policy = self._parse_policy(data)
                    self._policies[policy.id] = policy
                    count += 1

            except Exception as e:
                logger.error("Failed to load policy file", file=str(policy_file), error=str(e))

        self._loaded = True
        logger.info("Loaded policies", count=count)
        return count

    def _parse_policy(self, data: dict) -> Policy:
        """Parse policy from dictionary."""
        return Policy(
            id=data.get("id", str(uuid.uuid4())),
            policy_type=PolicyType(data.get("policy_type", "other")),
            reference=data["reference"],
            title=data["title"],
            content=data["content"],
            summary=data.get("summary"),
            chapter=data.get("chapter"),
            council_id=data.get("council_id"),
            effective_date=self._parse_date(data.get("effective_date")),
            superseded_date=self._parse_date(data.get("superseded_date")),
            source_url=data.get("source_url"),
            metadata=data.get("metadata", {}),
        )

    def _parse_date(self, date_str: str | None) -> date | None:
        """Parse date string."""
        if not date_str:
            return None
        try:
            return date.fromisoformat(date_str)
        except ValueError:
            return None

    def get_policy(self, policy_id: str) -> Policy | None:
        """Get policy by ID."""
        return self._policies.get(policy_id)

    def get_policy_by_reference(
        self, reference: str, council_id: str | None = None
    ) -> Policy | None:
        """Get policy by reference code."""
        for policy in self._policies.values():
            if policy.reference.upper() == reference.upper():
                if council_id is None or policy.council_id == council_id:
                    return policy
        return None

    def list_policies(
        self,
        policy_type: PolicyType | None = None,
        council_id: str | None = None,
        current_only: bool = True,
    ) -> list[Policy]:
        """List policies with optional filters.

        Args:
            policy_type: Filter by policy type
            council_id: Filter by council (None for national)
            current_only: Only return current (not superseded) policies

        Returns:
            List of matching policies
        """
        policies = []
        for policy in self._policies.values():
            if policy_type and policy.policy_type != policy_type:
                continue
            if council_id is not None and policy.council_id != council_id:
                continue
            if current_only and not policy.is_current:
                continue
            policies.append(policy)
        return policies

    def get_nppf_policies(self) -> list[Policy]:
        """Get all NPPF policies."""
        return self.list_policies(policy_type=PolicyType.NPPF)

    def get_local_plan_policies(self, council_id: str) -> list[Policy]:
        """Get local plan policies for a council."""
        return self.list_policies(
            policy_type=PolicyType.LOCAL_PLAN,
            council_id=council_id,
        )

    async def add_policy(self, policy: Policy) -> Policy:
        """Add or update a policy.

        Args:
            policy: Policy to add

        Returns:
            Added policy
        """
        self._policies[policy.id] = policy
        logger.info("Added policy", policy_id=policy.id, reference=policy.reference)
        return policy

    async def remove_policy(self, policy_id: str) -> bool:
        """Remove a policy.

        Args:
            policy_id: ID of policy to remove

        Returns:
            True if removed, False if not found
        """
        if policy_id in self._policies:
            del self._policies[policy_id]
            return True
        return False

    async def save_policies(self, output_dir: Path | None = None) -> int:
        """Save all policies to files.

        Args:
            output_dir: Directory to save to

        Returns:
            Number of policies saved
        """
        if output_dir is None:
            output_dir = self.settings.data_dir / "policies"

        output_dir.mkdir(parents=True, exist_ok=True)

        # Group by type
        by_type: dict[str, list[dict]] = {}
        for policy in self._policies.values():
            type_key = policy.policy_type.value
            if type_key not in by_type:
                by_type[type_key] = []
            by_type[type_key].append(self._policy_to_dict(policy))

        count = 0
        for type_key, policies in by_type.items():
            output_file = output_dir / f"{type_key}.json"
            with open(output_file, "w") as f:
                json.dump(policies, f, indent=2, default=str)
            count += len(policies)

        logger.info("Saved policies", count=count, dir=str(output_dir))
        return count

    def _policy_to_dict(self, policy: Policy) -> dict:
        """Convert policy to dictionary for saving."""
        return {
            "id": policy.id,
            "policy_type": policy.policy_type.value,
            "reference": policy.reference,
            "title": policy.title,
            "content": policy.content,
            "summary": policy.summary,
            "chapter": policy.chapter,
            "council_id": policy.council_id,
            "effective_date": policy.effective_date.isoformat() if policy.effective_date else None,
            "superseded_date": (
                policy.superseded_date.isoformat() if policy.superseded_date else None
            ),
            "source_url": policy.source_url,
            "metadata": policy.metadata,
        }


# Default NPPF and Newcastle policies for pilot
DEFAULT_NPPF_POLICIES = [
    {
        "id": "nppf-chapter-2",
        "policy_type": "nppf",
        "reference": "NPPF-2",
        "title": "Achieving sustainable development",
        "chapter": "Chapter 2",
        "content": """The purpose of the planning system is to contribute to the achievement of sustainable development. At a very high level, the objective of sustainable development can be summarised as meeting the needs of the present without compromising the ability of future generations to meet their own needs.

Achieving sustainable development means that the planning system has three overarching objectives:

a) an economic objective – to help build a strong, responsive and competitive economy, by ensuring that sufficient land of the right types is available in the right places and at the right time to support growth, innovation and improved productivity; and by identifying and coordinating the provision of infrastructure;

b) a social objective – to support strong, vibrant and healthy communities, by ensuring that a sufficient number and range of homes can be provided to meet the needs of present and future generations; and by fostering well-designed, beautiful and safe places, with accessible services and open spaces that reflect current and future needs and support communities' health, social and cultural well-being; and

c) an environmental objective – to protect and enhance our natural, built and historic environment; including making effective use of land, improving biodiversity, using natural resources prudently, minimising waste and pollution, and mitigating and adapting to climate change, including moving to a low carbon economy.""",
        "summary": "Sets out the three pillars of sustainable development: economic, social, and environmental objectives.",
    },
    {
        "id": "nppf-chapter-12",
        "policy_type": "nppf",
        "reference": "NPPF-12",
        "title": "Achieving well-designed and beautiful places",
        "chapter": "Chapter 12",
        "content": """The Government attaches great importance to the design of the built environment. Good design is a key aspect of sustainable development, creates better places in which to live and work and helps make development acceptable to communities.

Planning policies and decisions should ensure that developments:
a) will function well and add to the overall quality of the area, not just for the short term but over the lifetime of the development;
b) are visually attractive as a result of good architecture, layout and appropriate and effective landscaping;
c) are sympathetic to local character and history, including the surrounding built environment and landscape setting, while not preventing or discouraging appropriate innovation or change (such as increased densities);
d) establish or maintain a strong sense of place, using the arrangement of streets, spaces, building types and materials to create attractive, welcoming and distinctive places to live, work and visit;
e) optimise the potential of the site to accommodate and sustain an appropriate amount and mix of development (including green and other public space) and support local facilities and transport networks; and
f) create places that are safe, inclusive and accessible and which promote health and well-being, with a high standard of amenity for existing and future users.""",
        "summary": "Requires development to be well-designed, visually attractive, and sympathetic to local character.",
    },
    {
        "id": "nppf-chapter-16",
        "policy_type": "nppf",
        "reference": "NPPF-16",
        "title": "Conserving and enhancing the historic environment",
        "chapter": "Chapter 16",
        "content": """Heritage assets range from sites and buildings of local historic value to those of the highest significance, such as World Heritage Sites which are internationally recognised to be of Outstanding Universal Value. These assets are an irreplaceable resource, and should be conserved in a manner appropriate to their significance, so that they can be enjoyed for their contribution to the quality of life of existing and future generations.

When considering the impact of a proposed development on the significance of a designated heritage asset, great weight should be given to the asset's conservation (and the more important the asset, the greater the weight should be). This is irrespective of whether any potential harm amounts to substantial harm, total loss or less than substantial harm to its significance.

Any harm to, or loss of, the significance of a designated heritage asset (from its alteration or destruction, or from development within its setting), should require clear and convincing justification.""",
        "summary": "Heritage assets should be conserved appropriately. Great weight given to conservation with clear justification needed for any harm.",
    },
]

NEWCASTLE_LOCAL_PLAN_POLICIES = [
    {
        "id": "ncl-cs-policy-1",
        "policy_type": "local_plan",
        "reference": "CS1",
        "title": "Spatial Strategy for Sustainable Growth",
        "council_id": "newcastle",
        "chapter": "Core Strategy",
        "content": """The Council will work with partners to deliver sustainable growth in Newcastle through a balanced approach to development that:

1. Focuses major development and investment in and around the Urban Core to enhance its role as the regional capital
2. Supports the regeneration of previously developed land, particularly along the River Tyne corridor
3. Protects and enhances the city's green infrastructure, including the Town Moor and green belt
4. Delivers new homes to meet identified housing needs across the city
5. Supports economic development and job creation
6. Improves connectivity and reduces the need to travel by private car

Development should contribute positively to the city's character and distinctiveness, respecting and enhancing the historic environment while meeting the challenges of climate change.""",
        "summary": "Focuses growth in Urban Core, supports regeneration, protects green infrastructure, delivers homes and jobs.",
    },
    {
        "id": "ncl-dm-policy-20",
        "policy_type": "local_plan",
        "reference": "DM20",
        "title": "Design Quality",
        "council_id": "newcastle",
        "chapter": "Development Management Policies",
        "content": """All development proposals will be required to demonstrate a high standard of design and sustainability. Proposals should:

1. Respond positively to the local context, creating a sense of place appropriate to the site and its surroundings
2. Provide high quality public realm and landscape design
3. Create safe and accessible environments that promote health and wellbeing
4. Incorporate sustainable design and construction principles
5. Achieve high standards of environmental performance
6. Consider the impact on views and vistas, particularly those of the city skyline
7. Respect the amenity of existing and future residents and occupiers

Major developments should submit a Design and Access Statement demonstrating how the proposal meets these requirements. Pre-application discussions and design review are strongly encouraged for significant proposals.""",
        "summary": "Requires high design standards, positive response to context, quality public realm, and sustainable construction.",
    },
    {
        "id": "ncl-dm-policy-21",
        "policy_type": "local_plan",
        "reference": "DM21",
        "title": "Conservation and Enhancement of Heritage Assets",
        "council_id": "newcastle",
        "chapter": "Development Management Policies",
        "content": """Development affecting heritage assets (including listed buildings, conservation areas, scheduled monuments, registered parks and gardens, and archaeology) will be required to:

1. Demonstrate a thorough understanding of the significance of the asset and its setting
2. Justify any harm to significance through clear public benefits
3. Preserve or enhance the character and appearance of conservation areas
4. Protect the setting of listed buildings and other designated assets
5. Ensure archaeological sites are properly assessed and mitigated

Proposals affecting designated heritage assets should be accompanied by a Heritage Statement proportionate to the significance of the asset and the potential impact. Where harm is identified, this should be minimised and mitigated.

Non-designated heritage assets of local importance will also be protected where their significance merits consideration in planning decisions.""",
        "summary": "Protects heritage assets. Requires Heritage Statements, justification for harm, and mitigation measures.",
    },
]
