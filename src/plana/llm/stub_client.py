"""
Stub LLM client for offline development.

Returns template-based responses without calling external APIs.
"""

import structlog

logger = structlog.get_logger(__name__)


class StubLLMClient:
    """
    Stub LLM client that returns template responses.

    Used for testing and development without API keys.
    Set PLANA_SKIP_LLM=true to enable.
    """

    def __init__(self):
        """Initialize stub client."""
        logger.info("Using stub LLM client (no API calls)")

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate a template response based on prompt content.

        Args:
            prompt: User prompt
            system_prompt: System prompt (ignored in stub)
            max_tokens: Max tokens (ignored in stub)
            temperature: Temperature (ignored in stub)

        Returns:
            Template response
        """
        logger.debug("Stub LLM generating response", prompt_length=len(prompt))

        # Detect section type from prompt and return appropriate template
        prompt_lower = prompt.lower()

        if "site and surroundings" in prompt_lower or "describe the site" in prompt_lower:
            return self._site_section(prompt)
        elif "proposal" in prompt_lower and "describe" in prompt_lower:
            return self._proposal_section(prompt)
        elif "planning history" in prompt_lower:
            return self._history_section(prompt)
        elif "policy" in prompt_lower:
            return self._policy_section(prompt)
        elif "design" in prompt_lower:
            return self._design_section(prompt)
        elif "heritage" in prompt_lower:
            return self._heritage_section(prompt)
        elif "amenity" in prompt_lower or "residential" in prompt_lower:
            return self._amenity_section(prompt)
        elif "transport" in prompt_lower or "parking" in prompt_lower:
            return self._transport_section(prompt)
        elif "planning balance" in prompt_lower:
            return self._balance_section(prompt)
        elif "recommendation" in prompt_lower:
            return self._recommendation_section(prompt)
        elif "condition" in prompt_lower:
            return self._conditions_section(prompt)
        else:
            return self._generic_section(prompt)

    def _site_section(self, prompt: str) -> str:
        return """The application site is located within the urban area of Newcastle upon Tyne. The surrounding area is characterised by a mix of commercial, retail, and residential uses typical of the city centre.

The site is situated on a principal shopping street with good pedestrian connectivity. The immediate context includes a range of building heights and architectural styles, with the predominant character being historic commercial buildings from the Victorian and Edwardian periods.

[STUB RESPONSE - Replace with actual LLM output in production]"""

    def _proposal_section(self, prompt: str) -> str:
        return """The application proposes development as described in the submitted documents. The scheme has been designed to respond to the site's urban context and planning constraints.

Key elements of the proposal include:
- The works described in the application form
- Associated external alterations
- Internal modifications where applicable

Full details are set out in the submitted plans and supporting documents.

[STUB RESPONSE - Replace with actual LLM output in production]"""

    def _history_section(self, prompt: str) -> str:
        return """A review of the planning history indicates that the site has been subject to previous planning applications. These applications provide relevant context for the current proposal.

Previous decisions on the site and surrounding area have established precedents for acceptable forms of development. The current application should be assessed having regard to this planning history.

[STUB RESPONSE - Replace with actual LLM output in production]"""

    def _policy_section(self, prompt: str) -> str:
        return """The development plan for the area comprises the Newcastle Local Plan and the National Planning Policy Framework (NPPF).

Key policies relevant to this application include:
- **CS1**: Spatial Strategy for Sustainable Growth
- **DM20**: Design Quality
- **NPPF Chapter 12**: Achieving well-designed and beautiful places

The application should be determined in accordance with the development plan unless material considerations indicate otherwise.

[STUB RESPONSE - Replace with actual LLM output in production]"""

    def _design_section(self, prompt: str) -> str:
        return """The design of the proposed development has been assessed against Policy DM20 (Design Quality) of the Local Plan and the design policies within the NPPF.

The submitted Design and Access Statement demonstrates how the proposal responds to its context. The scale, massing, and materials have been designed to complement the existing streetscape.

Subject to appropriate conditions, the design is considered acceptable and in accordance with relevant policies.

[STUB RESPONSE - Replace with actual LLM output in production]"""

    def _heritage_section(self, prompt: str) -> str:
        return """The site is located within/adjacent to a designated heritage asset. Section 66 of the Planning (Listed Buildings and Conservation Areas) Act 1990 requires special regard to the desirability of preserving listed buildings and their settings.

The submitted Heritage Statement assesses the significance of affected heritage assets and the impact of the proposed development. The proposals have been designed to minimise harm and, where harm is identified, it is considered to be less than substantial.

In accordance with NPPF paragraph 202, this harm should be weighed against the public benefits of the proposal.

[STUB RESPONSE - Replace with actual LLM output in production]"""

    def _amenity_section(self, prompt: str) -> str:
        return """The impact of the proposed development on residential amenity has been assessed in terms of:
- Privacy and overlooking
- Daylight and sunlight
- Noise and disturbance
- Visual impact

The proposal is not considered to result in unacceptable harm to the living conditions of neighbouring occupiers. The development complies with Policy DM20 in this respect.

[STUB RESPONSE - Replace with actual LLM output in production]"""

    def _transport_section(self, prompt: str) -> str:
        return """The site is located in a sustainable location with good access to public transport, including bus and Metro services. The proposal has been assessed against the council's parking standards.

The Highway Authority has been consulted and raises no objection subject to conditions. The development is considered acceptable in transport terms.

[STUB RESPONSE - Replace with actual LLM output in production]"""

    def _balance_section(self, prompt: str) -> str:
        return """**Planning Balance**

The proposal has been assessed against all relevant policies of the development plan and material considerations.

**Weighing in favour:**
- The proposal would contribute to economic activity
- The design responds appropriately to context
- Sustainable location with good transport links

**Weighing against:**
- [Any identified harm - to be completed based on assessment]

On balance, the benefits of the proposal are considered to outweigh any identified harm. The development is in accordance with the development plan when read as a whole.

[STUB RESPONSE - Replace with actual LLM output in production]"""

    def _recommendation_section(self, prompt: str) -> str:
        return """**RECOMMENDATION: APPROVE** subject to conditions.

The proposal is considered to accord with the policies of the development plan and is acceptable having regard to all material considerations. Planning permission should be granted subject to appropriate conditions.

Delegated authority is recommended for officers to finalise condition wording.

[STUB RESPONSE - Replace with actual LLM output in production]"""

    def _conditions_section(self, prompt: str) -> str:
        return """**Recommended Conditions:**

1. **Time Limit**: The development hereby permitted shall be begun before the expiration of three years from the date of this permission.

2. **Approved Plans**: The development shall be carried out in accordance with the approved plans.

3. **Materials**: Samples of all external materials shall be submitted to and approved in writing by the Local Planning Authority before the relevant works commence.

4. **Hours of Construction**: Construction works shall only take place between 08:00 and 18:00 Monday to Friday, and 08:00 and 13:00 on Saturdays, with no work on Sundays or Bank Holidays.

[STUB RESPONSE - Replace with actual LLM output in production]"""

    def _generic_section(self, prompt: str) -> str:
        return """This section provides an assessment of the relevant planning matters.

The proposal has been evaluated against the applicable policies and material considerations. On balance, the development is considered acceptable.

[STUB RESPONSE - Replace with actual LLM output in production]"""

    async def count_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
