"""Result aggregation component for the Coordinator Agent.

Consolidates risk levels, findings, and details from multiple specialized
sub-agents to compute a unified threat risk assessment and recommendation.
"""

import logging
from typing import Dict, List
from fraud_shield.interfaces import AgentResult, CoordinatorResponse
from fraud_shield.config import RISK_MAPPING, NUMERIC_TO_RISK
from fraud_shield.exceptions import AggregationError

logger = logging.getLogger(__name__)

class ResultAggregator:
    """Aggregates sub-agent results and calculates overall safety advisory parameters."""

    def aggregate(
        self,
        input_type: str,
        selected_agents: List[str],
        results: Dict[str, AgentResult],
        failures: List[str]
    ) -> CoordinatorResponse:
        """Merges results from invoked agents into a structured CoordinatorResponse.
        
        Args:
            input_type: The classified input type.
            selected_agents: List of agents originally selected for execution.
            results: Dictionary mapping agent name to its AgentResult.
            failures: List of agent names that failed execution.
            
        Returns:
            A CoordinatorResponse object.
            
        Raises:
            AggregationError: If no results are available and failures exist.
        """
        logger.info("Aggregating sub-agent results...")
        
        if not results and failures:
            raise AggregationError("All selected sub-agents failed execution. Cannot compile response.")
        elif not results and not failures:
            # Empty query or fallback
            return CoordinatorResponse(
                input_type=input_type,
                selected_agents=selected_agents,
                analysis_status="success",
                overall_risk="LOW",
                recommendation="No threat vectors were analyzed. Maintain general online safety practices.",
                next_steps=["Be cautious with unknown files, links, or contact requests."]
            )

        # 1. Determine Analysis Status
        if len(failures) == 0:
            analysis_status = "success"
        elif len(results) > 0:
            analysis_status = "partial_success"
        else:
            analysis_status = "failed"

        # 2. Compute Overall Risk Level (Highest risk level from results)
        highest_numeric_risk = 1  # Corresponds to LOW
        for result in results.values():
            numeric_val = RISK_MAPPING.get(result.risk_level.upper(), 1)
            if numeric_val > highest_numeric_risk:
                highest_numeric_risk = numeric_val
                
        overall_risk = NUMERIC_TO_RISK[highest_numeric_risk]
        logger.debug(f"Aggregated overall risk calculated as: {overall_risk}")

        # 3. Consolidate Findings & Recommendations
        all_findings = []
        for result in results.values():
            for finding in result.findings:
                if finding not in all_findings:
                    all_findings.append(finding)

        # 4. Generate Main Recommendation and Next Steps
        recommendation, next_steps = self._compile_advisory(input_type, overall_risk, all_findings)
        
        # Add a notification if there were failures in analysis
        if failures:
            next_steps.append(f"Note: Analysis was incomplete due to failures in: {', '.join(failures)}.")

        return CoordinatorResponse(
            input_type=input_type,
            selected_agents=selected_agents,
            analysis_status=analysis_status,
            overall_risk=overall_risk,
            recommendation=recommendation,
            next_steps=next_steps,
            agent_results=results
        )

    def _compile_advisory(self, input_type: str, overall_risk: str, findings: List[str]) -> tuple[str, List[str]]:
        """Compiles human-readable recommendations and next steps based on risk and findings."""
        next_steps = []
        
        # Base recommendations depending on overall threat level
        if overall_risk == "CRITICAL":
            recommendation = "CRITICAL THREAT DETECTED. Immediate protective action required. This shows high-probability fraud signatures."
            next_steps.extend([
                "DO NOT share any verification codes, passwords, or personal keys.",
                "Immediately disconnect, hang up, or close the page in question.",
                "Verify identity through independent official channels if you believe this might be legit."
            ])
        elif overall_risk == "HIGH":
            recommendation = "HIGH RISK ALERT. Strong indicators of scam/fraud are present. Proceeding is highly discouraged."
            next_steps.extend([
                "Do not click any links, open attachments, or send payments.",
                "Flag or report this contact as spam/phishing on your platform.",
                "Delete the message/email to avoid accidental interaction."
            ])
        elif overall_risk == "MEDIUM":
            recommendation = "MEDIUM RISK. Suspicious elements detected. Exercise caution and verify before proceeding."
            next_steps.extend([
                "Double-check the sender's email address or phone number for minor typos (typosquatting).",
                "Search the company name online with keywords like 'scam' or 'complaint'.",
                "Do not share sensitive files or credentials."
            ])
        else:
            recommendation = "LOW RISK. No explicit scam signatures found, but always maintain standard safety precautions."
            next_steps.extend([
                "Monitor for unexpected changes in security prompts.",
                "Keep your systems and apps updated with the latest security patches."
            ])

        # Customize recommendations based on input types if appropriate
        if input_type == "email":
            next_steps.append("Block the sender address if you do not recognize them.")
        elif input_type == "sms_whatsapp":
            next_steps.append("Never forward authentication SMS codes to anybody, including friends or family.")
        elif input_type == "url" or input_type == "shopping":
            next_steps.append("Check the domain registration age using a public WHOIS lookup tool.")
        elif input_type == "job_internship":
            next_steps.append("Verify the recruiter profile on LinkedIn and ensure their email matches the official company domain.")

        # If we have specific findings, we can inject a summary sentence
        if findings:
            summary_sentence = " ".join(findings[:2])
            recommendation = f"{recommendation} Key findings: {summary_sentence}"

        # De-duplicate next steps and return
        unique_next_steps = []
        for step in next_steps:
            if step not in unique_next_steps:
                unique_next_steps.append(step)
                
        return recommendation, unique_next_steps
