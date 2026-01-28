"""
Similarity search for historic planning cases.

Uses keyword matching and constraint overlap to find
similar planning applications for precedent analysis.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SimilarCase:
    """A similar historic planning case."""

    reference: str  # Application reference
    address: str  # Site address
    proposal: str  # Proposal description
    decision: str  # APPROVED / REFUSED
    decision_date: str  # Date of decision
    similarity_score: float  # 0-1 similarity score
    similarity_reason: str  # Why this case is similar
    constraints: List[str]  # Site constraints
    key_issues: List[str]  # Key planning issues addressed
    officer_comments: Optional[str] = None  # Key officer comments


# Demo historic cases for offline mode
DEMO_HISTORIC_CASES = [
    {
        "reference": "2019/0485/01/DET",
        "address": "Former Co-op Building, 67-77 Newgate Street, Newcastle Upon Tyne, NE1 5RQ",
        "proposal": "Conversion of upper floors to 45 residential apartments with associated external alterations",
        "decision": "APPROVED",
        "decision_date": "2019-08-15",
        "constraints": ["Grainger Town Conservation Area", "Adjacent to listed buildings"],
        "key_issues": ["Heritage impact", "Residential amenity", "Design quality"],
        "officer_comments": "The proposed conversion will bring back into use vacant upper floors while preserving the historic character of the building. The external alterations are sensitively designed and will not harm the Conservation Area.",
    },
    {
        "reference": "2020/1234/01/DET",
        "address": "45-51 Grey Street, Newcastle Upon Tyne, NE1 6EE",
        "proposal": "Change of use from retail to restaurant with external alterations to shop front",
        "decision": "APPROVED",
        "decision_date": "2020-06-22",
        "constraints": ["Grainger Town Conservation Area", "Grade II Listed Building"],
        "key_issues": ["Listed building impact", "Shop front design", "Conservation Area character"],
        "officer_comments": "Subject to conditions regarding materials and detailed design, the proposal will preserve the special interest of the listed building and enhance the Conservation Area.",
    },
    {
        "reference": "2018/0876/01/DET",
        "address": "Central Arcade, 33 Grainger Street, Newcastle Upon Tyne, NE1 5JE",
        "proposal": "Extension at rear roof level and internal alterations to create additional office space",
        "decision": "APPROVED",
        "decision_date": "2018-11-30",
        "constraints": ["Grainger Town Conservation Area", "Grade II* Listed Building"],
        "key_issues": ["Heritage significance", "Roof extension design", "Visual impact"],
        "officer_comments": "The roof extension is designed to be subservient and is set back from the principal elevation. It will not be visible from street level and will not harm the significance of the heritage assets.",
    },
    {
        "reference": "2021/0567/01/DET",
        "address": "55-59 Pilgrim Street, Newcastle Upon Tyne, NE1 6QG",
        "proposal": "Demolition of rear additions and erection of 4-storey rear extension for mixed use",
        "decision": "REFUSED",
        "decision_date": "2021-03-18",
        "constraints": ["Grainger Town Conservation Area", "Adjacent to Grade II listed buildings"],
        "key_issues": ["Scale and massing", "Heritage impact", "Loss of historic fabric"],
        "officer_comments": "The proposed extension by reason of its scale, height and massing would cause less than substantial harm to the significance of the adjacent listed buildings and the character of the Conservation Area. The public benefits do not outweigh this harm.",
    },
    {
        "reference": "2022/0298/01/DET",
        "address": "112-116 Grainger Street, Newcastle Upon Tyne, NE1 5JQ",
        "proposal": "Installation of new shop front and signage with internal alterations",
        "decision": "APPROVED",
        "decision_date": "2022-07-08",
        "constraints": ["Grainger Town Conservation Area"],
        "key_issues": ["Shop front design", "Conservation Area character", "Signage"],
        "officer_comments": "The replacement shop front follows the traditional pattern for the area and uses appropriate materials. The signage is proportionate and will not detract from the character of the streetscape.",
    },
    {
        "reference": "2017/0943/01/DET",
        "address": "Fenwick Department Store, Northumberland Street, Newcastle Upon Tyne, NE1 7AS",
        "proposal": "Alterations to existing building including new roof plant enclosure and facade improvements",
        "decision": "APPROVED",
        "decision_date": "2017-12-05",
        "constraints": ["City Centre", "Prominent location"],
        "key_issues": ["Design quality", "Visual impact", "City centre character"],
        "officer_comments": "The proposals will improve the appearance of this prominent city centre building. The new plant enclosure is well-designed and will not be unduly prominent.",
    },
]


class SimilaritySearch:
    """
    Finds similar historic planning cases.

    Uses constraint matching, proposal keyword similarity,
    and location proximity to identify relevant precedents.
    """

    def __init__(self):
        """Initialize with demo historic cases."""
        self._historic_cases = DEMO_HISTORIC_CASES

    def _calculate_constraint_overlap(
        self, constraints1: List[str], constraints2: List[str]
    ) -> float:
        """Calculate Jaccard similarity of constraints."""
        if not constraints1 and not constraints2:
            return 0.5  # Neutral if both empty

        set1 = set(c.lower() for c in constraints1)
        set2 = set(c.lower() for c in constraints2)

        if not set1 or not set2:
            return 0.2

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0

    def _calculate_proposal_similarity(self, proposal1: str, proposal2: str) -> float:
        """Calculate keyword-based proposal similarity."""
        # Key planning terms
        planning_terms = [
            "extension", "conversion", "residential", "retail", "office",
            "shop", "front", "rear", "roof", "demolition", "alteration",
            "change of use", "listed", "heritage", "conservation",
        ]

        words1 = set(proposal1.lower().split())
        words2 = set(proposal2.lower().split())

        # Find matching planning terms
        terms1 = set(t for t in planning_terms if t in proposal1.lower())
        terms2 = set(t for t in planning_terms if t in proposal2.lower())

        term_overlap = len(terms1 & terms2) / max(len(terms1 | terms2), 1)

        # General word overlap
        common_words = words1 & words2
        word_overlap = len(common_words) / max(len(words1 | words2), 1)

        return 0.6 * term_overlap + 0.4 * word_overlap

    def _calculate_similarity(
        self,
        proposal: str,
        constraints: List[str],
        historic_case: dict,
    ) -> tuple:
        """Calculate overall similarity score and reason."""
        constraint_sim = self._calculate_constraint_overlap(
            constraints, historic_case["constraints"]
        )
        proposal_sim = self._calculate_proposal_similarity(
            proposal, historic_case["proposal"]
        )

        # Weighted combination
        total_score = 0.5 * constraint_sim + 0.5 * proposal_sim

        # Generate reason
        reasons = []
        if constraint_sim > 0.3:
            matching = [c for c in constraints if any(
                c.lower() in hc.lower() or hc.lower() in c.lower()
                for hc in historic_case["constraints"]
            )]
            if matching:
                reasons.append(f"Similar constraints: {', '.join(matching[:2])}")

        if proposal_sim > 0.3:
            reasons.append("Similar proposal type")

        if historic_case["decision"] == "APPROVED":
            reasons.append("Approved precedent")
        else:
            reasons.append("Refusal precedent - review reasons")

        reason = "; ".join(reasons) if reasons else "General similarity"

        return total_score, reason

    def find_similar_cases(
        self,
        proposal: str,
        constraints: List[str],
        address: str = "",
        application_type: str = "",
        max_results: int = 5,
        min_score: float = 0.2,
    ) -> List[SimilarCase]:
        """Find similar historic planning cases.

        Args:
            proposal: Proposal description
            constraints: Site constraints
            address: Site address (for location matching)
            application_type: Type of application
            max_results: Maximum cases to return
            min_score: Minimum similarity score

        Returns:
            List of SimilarCase objects sorted by similarity
        """
        scored_cases = []

        for case in self._historic_cases:
            score, reason = self._calculate_similarity(proposal, constraints, case)

            if score >= min_score:
                scored_cases.append({
                    "case": case,
                    "score": score,
                    "reason": reason,
                })

        # Sort by score descending
        scored_cases.sort(key=lambda x: x["score"], reverse=True)

        # Convert to SimilarCase objects
        results = []
        for item in scored_cases[:max_results]:
            case = item["case"]
            results.append(SimilarCase(
                reference=case["reference"],
                address=case["address"],
                proposal=case["proposal"],
                decision=case["decision"],
                decision_date=case["decision_date"],
                similarity_score=round(item["score"], 3),
                similarity_reason=item["reason"],
                constraints=case["constraints"],
                key_issues=case["key_issues"],
                officer_comments=case.get("officer_comments"),
            ))

        return results

    def get_approved_precedents(
        self,
        proposal: str,
        constraints: List[str],
        max_results: int = 3,
    ) -> List[SimilarCase]:
        """Get only approved similar cases for precedent support."""
        all_similar = self.find_similar_cases(
            proposal, constraints, max_results=max_results * 2
        )
        approved = [c for c in all_similar if c.decision == "APPROVED"]
        return approved[:max_results]

    def get_refused_cases(
        self,
        proposal: str,
        constraints: List[str],
        max_results: int = 2,
    ) -> List[SimilarCase]:
        """Get refused similar cases to understand potential issues."""
        all_similar = self.find_similar_cases(
            proposal, constraints, max_results=max_results * 2
        )
        refused = [c for c in all_similar if c.decision == "REFUSED"]
        return refused[:max_results]
