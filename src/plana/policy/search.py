"""
Policy search with keyword-based ranking.

Provides TF-IDF-like keyword matching to retrieve relevant
policy excerpts for planning applications.

When a ``council_id`` is supplied the search is scoped to only return
policies from the council's statutory development plan documents (plus
the NPPF which is always national).  The mapping is defined in
``plana.core.constants.PLANNING_AUTHORITY_SCOPE``.
"""

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import List, Optional

from plana.core.constants import PLANNING_AUTHORITY_SCOPE
from plana.policy.demo_policies import DEMO_POLICIES, get_all_policies


@dataclass
class PolicyExcerpt:
    """A matched policy excerpt with citation info."""

    doc_id: str  # NPPF, CSUCP, DAP
    doc_title: str  # Full document title
    policy_id: str  # e.g., "DM15", "NPPF-199"
    policy_title: str  # e.g., "Conservation of Heritage Assets"
    text: str  # Excerpt text
    page: int  # Page number
    score: float  # Relevance score (0-1)
    match_reason: str  # Why this policy was matched

    def citation(self) -> str:
        """Return a formatted citation string."""
        return f"{self.doc_id} {self.policy_id} (p.{self.page})"

    def full_citation(self) -> str:
        """Return a full citation with document title."""
        return f"{self.doc_title} - {self.policy_id}: {self.policy_title} (p.{self.page})"


class PolicySearch:
    """
    Keyword-based policy search with TF-IDF-like ranking.

    Retrieves relevant policies based on application context
    including proposal text, constraints, and application type.
    """

    # Keywords that trigger specific policy areas.
    #
    # Both Newcastle (CSUCP/DAP) and Broxtowe (ACS/BLP2) policy IDs
    # are listed.  When ``council_id`` is provided, the scope filter
    # removes policies outside the council's development plan *after*
    # scoring, so keyword boosts are harmless for other councils'
    # policies — they simply get filtered out.
    KEYWORD_MAPPINGS = {
        # Heritage keywords
        "conservation area": [
            "NPPF-199", "NPPF-200", "NPPF-206",
            "DM15", "DM16", "UC10", "UC11",       # Newcastle
            "ACS-11", "BLP2-23",                   # Broxtowe
        ],
        "listed building": [
            "NPPF-199", "NPPF-200",
            "DM15", "DM17", "UC11",                # Newcastle
            "ACS-11", "BLP2-23",                   # Broxtowe
        ],
        "heritage": [
            "NPPF-16", "NPPF-199", "NPPF-200",
            "DM15", "DM16", "DM17", "UC11",        # Newcastle
            "ACS-11", "BLP2-23",                   # Broxtowe
        ],
        "historic": [
            "NPPF-16", "NPPF-199",
            "DM15", "UC10", "UC11",                # Newcastle
            "ACS-11", "BLP2-23",                   # Broxtowe
        ],
        "grainger": ["UC10", "DM28", "CS1"],
        "character": [
            "NPPF-130", "NPPF-206",
            "DM6", "DM16", "CS15",                 # Newcastle
            "ACS-10", "BLP2-17",                   # Broxtowe
        ],

        # Design keywords
        "design": [
            "NPPF-12", "NPPF-130",
            "DM6", "CS15",                         # Newcastle
            "ACS-10", "BLP2-17",                   # Broxtowe
        ],
        "appearance": [
            "NPPF-130",
            "DM6", "DM16", "CS15",                 # Newcastle
            "ACS-10", "BLP2-17",                   # Broxtowe
        ],
        "scale": [
            "NPPF-130",
            "DM6", "CS15",                         # Newcastle
            "ACS-10", "BLP2-17",                   # Broxtowe
        ],
        "massing": [
            "DM6", "CS15",                         # Newcastle
            "BLP2-17",                             # Broxtowe
        ],

        # Residential keywords
        "residential": [
            "CS17", "DM21", "CS1",                 # Newcastle
            "ACS-8", "ACS-2", "BLP2-17",           # Broxtowe
        ],
        "housing": [
            "CS17", "NPPF-11",                     # Newcastle
            "ACS-8",                               # Broxtowe
        ],
        "conversion": [
            "CS17", "UC1", "DM21",                 # Newcastle
            "ACS-8", "BLP2-17",                    # Broxtowe
        ],
        "extension": [
            "DM6", "DM21", "CS15",                 # Newcastle
            "BLP2-17",                             # Broxtowe
        ],
        "amenity": [
            "DM21",                                # Newcastle
            "BLP2-17",                             # Broxtowe
        ],

        # Retail/commercial keywords
        "shop": ["DM20", "UC1", "CS1"],
        "retail": ["UC1", "CS1", "DM20"],
        "commercial": ["UC1", "CS1"],

        # Sustainability keywords
        "sustainable": [
            "NPPF-2",
            "DM1", "CS18",                         # Newcastle
            "ACS-A",                               # Broxtowe
        ],
        "brownfield": ["NPPF-11"],
        "environment": [
            "CS18", "NPPF-2",                      # Newcastle
            "BLP2-28",                             # Broxtowe
        ],
        "flood": [
            "BLP2-1",                              # Broxtowe
        ],
        "contamination": [
            "BLP2-19",                             # Broxtowe
        ],
        "transport": [
            "ACS-14", "BLP2-26",                   # Broxtowe
        ],
        "biodiversity": [
            "BLP2-28",                             # Broxtowe
        ],

        # Location keywords
        "urban core": ["UC1", "UC10", "UC11", "CS1"],
        "city centre": ["UC1", "CS1"],
        "town centre": [
            "CS1", "UC1",                          # Newcastle
            "ACS-2",                               # Broxtowe
        ],
        # Broxtowe-specific locations
        "beeston": ["ACS-2", "BLP2-17"],
        "stapleford": ["ACS-2", "BLP2-17"],
        "eastwood": ["ACS-2"],
        "kimberley": ["ACS-2"],
    }

    def __init__(self):
        """Initialize the policy search index."""
        self._all_policies = get_all_policies()
        self._build_index()

    def _build_index(self) -> None:
        """Build the search index with term frequencies."""
        self._policy_lookup = {p["id"]: p for p in self._all_policies}
        self._term_doc_freq: Counter = Counter()  # How many docs contain each term
        self._policy_terms: dict = {}  # Terms in each policy

        for policy in self._all_policies:
            terms = self._tokenize(policy["text"] + " " + policy["title"])
            self._policy_terms[policy["id"]] = Counter(terms)
            self._term_doc_freq.update(set(terms))

        self._total_docs = len(self._all_policies)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercase terms."""
        text = text.lower()
        # Keep hyphenated terms together
        text = re.sub(r"[^\w\s-]", " ", text)
        tokens = text.split()
        # Filter short tokens
        return [t for t in tokens if len(t) > 2]

    def _calculate_tfidf(self, query_terms: List[str], policy_id: str) -> float:
        """Calculate TF-IDF-like score for a query against a policy."""
        if policy_id not in self._policy_terms:
            return 0.0

        policy_term_freq = self._policy_terms[policy_id]
        score = 0.0

        for term in query_terms:
            tf = policy_term_freq.get(term, 0)
            if tf > 0:
                df = self._term_doc_freq.get(term, 1)
                idf = math.log(self._total_docs / df)
                score += (1 + math.log(tf)) * idf

        return score

    def retrieve_relevant_policies(
        self,
        proposal: str,
        constraints: List[str],
        application_type: str = "",
        address: str = "",
        max_results: int = 15,
        council_id: str = "",
    ) -> List[PolicyExcerpt]:
        """Retrieve policies relevant to an application.

        Args:
            proposal: The proposal description text
            constraints: List of site constraints (e.g., "Conservation Area")
            application_type: Type of application (e.g., "Full Planning")
            address: Site address
            max_results: Maximum number of policies to return
            council_id: When set, restricts local-plan results to the
                council's statutory development plan documents (NPPF is
                always included).  Mapping lives in
                ``PLANNING_AUTHORITY_SCOPE``.

        Returns:
            List of PolicyExcerpt objects sorted by relevance
        """
        # Resolve the set of allowed doc_ids for this council
        allowed_doc_ids: Optional[frozenset] = None
        if council_id:
            scope = PLANNING_AUTHORITY_SCOPE.get(council_id.lower())
            if scope:
                allowed_doc_ids = frozenset(scope["doc_ids"])

        # Build query context
        context = f"{proposal} {' '.join(constraints)} {application_type} {address}".lower()
        query_terms = self._tokenize(context)

        # First, get policies triggered by keyword mappings
        triggered_policies: dict = {}  # policy_id -> (score_boost, reason)

        for keyword, policy_ids in self.KEYWORD_MAPPINGS.items():
            if keyword in context:
                for pid in policy_ids:
                    current = triggered_policies.get(pid, (0, ""))
                    triggered_policies[pid] = (current[0] + 0.3, f"Keyword: '{keyword}'")

        # Calculate scores for all policies
        scored_policies = []
        for policy in self._all_policies:
            pid = policy["id"]

            # ---- Council scope filter ----
            # When a council_id is set, skip policies whose parent
            # document is NOT in the council's development plan.
            if allowed_doc_ids and policy["doc_short_name"] not in allowed_doc_ids:
                continue

            # Base TF-IDF score
            tfidf_score = self._calculate_tfidf(query_terms, pid)

            # Add keyword trigger boost
            boost, reason = triggered_policies.get(pid, (0, ""))
            if not reason:
                reason = "Content relevance"

            total_score = tfidf_score + boost

            if total_score > 0:
                scored_policies.append({
                    "policy": policy,
                    "score": total_score,
                    "reason": reason,
                })

        # Sort by score and take top results
        scored_policies.sort(key=lambda x: x["score"], reverse=True)
        top_policies = scored_policies[:max_results]

        # Normalize scores to 0-1 range
        if top_policies:
            max_score = top_policies[0]["score"]
            for p in top_policies:
                p["score"] = min(1.0, p["score"] / max_score) if max_score > 0 else 0

        # Convert to PolicyExcerpt objects
        results = []
        for item in top_policies:
            policy = item["policy"]
            results.append(PolicyExcerpt(
                doc_id=policy["doc_short_name"],
                doc_title=policy["doc_title"],
                policy_id=policy["id"],
                policy_title=policy["title"],
                text=policy["text"],
                page=policy["page"],
                score=round(item["score"], 3),
                match_reason=item["reason"],
            ))

        return results

    def get_policy_by_id(self, policy_id: str) -> Optional[PolicyExcerpt]:
        """Get a specific policy by its ID."""
        policy = self._policy_lookup.get(policy_id)
        if not policy:
            return None

        return PolicyExcerpt(
            doc_id=policy["doc_short_name"],
            doc_title=policy["doc_title"],
            policy_id=policy["id"],
            policy_title=policy["title"],
            text=policy["text"],
            page=policy["page"],
            score=1.0,
            match_reason="Direct lookup",
        )

    def get_policies_by_document(self, doc_id: str) -> List[PolicyExcerpt]:
        """Get all policies from a specific document."""
        results = []
        for policy in self._all_policies:
            if policy["doc_short_name"] == doc_id:
                results.append(PolicyExcerpt(
                    doc_id=policy["doc_short_name"],
                    doc_title=policy["doc_title"],
                    policy_id=policy["id"],
                    policy_title=policy["title"],
                    text=policy["text"],
                    page=policy["page"],
                    score=1.0,
                    match_reason="Document filter",
                ))
        return results
