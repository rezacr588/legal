"""
Generation Service - Handles sample generation logic with intelligent failover.
Coordinates between providers, models, and error handling.
"""

import json
import time
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from services.llm_service import LLMProviderFactory, BaseLLMProvider
from utils.error_handler import categorize_error
from config import PROVIDERS, DIFFICULTY_SPECS, SCENARIO_PATTERNS, SAMPLE_TYPES, THINKING_MODELS
import random
import re


class GenerationService:
    """
    Service for generating legal training samples.
    Handles provider coordination, model fallback, and error recovery.
    """

    def __init__(self):
        """Initialize generation service with provider factory."""
        self.factory = LLMProviderFactory()

    def _get_sample_type_guidance(self, sample_type: str) -> Dict[str, str]:
        """
        Get specific guidance for different sample types.

        Args:
            sample_type: Type of sample to generate

        Returns:
            Dictionary with type-specific guidance
        """
        sample_config = SAMPLE_TYPES.get(sample_type, SAMPLE_TYPES['case_analysis'])

        type_guidance = {
            'case_analysis': {
                'objective': 'Analyze a practical legal problem using case law and statutes',
                'question_format': 'Present a realistic client scenario requiring legal analysis and advice',
                'answer_approach': 'Apply IRAC methodology to analyze the legal issue and provide clear guidance',
                'focus': 'Problem-solving with comprehensive legal reasoning',
                'example_context': 'A client comes to you with a factual situation requiring legal assessment'
            },
            'educational': {
                'objective': 'Explain legal principles, doctrines, and rules to teach foundational concepts',
                'question_format': 'Ask a question about a legal concept, doctrine, or principle',
                'answer_approach': 'Provide a clear, structured explanation with examples and case law support',
                'focus': 'Teaching legal concepts with clarity and accuracy',
                'example_context': 'A student or junior lawyer wants to understand a legal doctrine'
            },
            'client_interaction': {
                'objective': 'Demonstrate effective lawyer-client communication and practical advice',
                'question_format': 'Present a client communication scenario requiring professional guidance',
                'answer_approach': 'Balance legal accuracy with client-friendly explanations and next steps',
                'focus': 'Real-world client communication and relationship management',
                'example_context': 'A client asks for practical guidance on how to proceed with a matter'
            },
            'statutory_interpretation': {
                'objective': 'Explain and apply specific statutory provisions',
                'question_format': 'Ask about the meaning, application, or implications of a statute',
                'answer_approach': 'Systematically explain the statute with case law showing its interpretation',
                'focus': 'Understanding and applying legislation',
                'example_context': 'Someone needs to understand what a statutory provision means and how it applies'
            }
        }

        return type_guidance.get(sample_type, type_guidance['case_analysis'])

    def _get_answer_structure_guidance(self, sample_type: str) -> str:
        """
        Get answer structure guidance based on sample type.

        Args:
            sample_type: Type of sample

        Returns:
            Formatted string with structure guidance
        """
        structures = {
            'case_analysis': """IRAC Methodology (MANDATORY)
   Your answer MUST follow this exact structure:

   │ ISSUE: Identify the core legal question/problem
   │ RULE: State the applicable UK law (statutes + case law)
   │ APPLICATION: Apply legal rules to the facts with step-by-step analysis
   │ CONCLUSION: Provide clear answer with legal justification""",

            'educational': """Structured Explanation (MANDATORY)
   Your answer should follow this teaching structure:

   │ DEFINITION: Clearly define the legal concept or doctrine
   │ LEGAL BASIS: Explain the statutory/case law foundation
   │ KEY ELEMENTS: Break down the essential components or requirements
   │ EXAMPLES: Provide practical examples showing how it works
   │ DISTINCTIONS: Clarify common misconceptions or similar concepts""",

            'client_interaction': """Client Communication Structure (MANDATORY)
   Your answer should follow this practical structure:

   │ UNDERSTANDING: Acknowledge and clarify the client's situation
   │ LEGAL POSITION: Explain the relevant law in client-friendly terms
   │ OPTIONS: Present available courses of action with pros/cons
   │ RECOMMENDATION: Advise on best approach with reasoning
   │ NEXT STEPS: Provide clear, actionable next steps""",

            'statutory_interpretation': """Statutory Analysis Structure (MANDATORY)
   Your answer should follow this interpretive structure:

   │ STATUTORY TEXT: Quote the relevant statutory provision(s)
   │ PURPOSE: Explain the legislation's objective and policy rationale
   │ INTERPRETATION: Break down key terms and their legal meaning
   │ CASE LAW: Show how courts have interpreted and applied the statute
   │ APPLICATION: Demonstrate how the statute applies in practice"""
        }

        return structures.get(sample_type, structures['case_analysis'])

    def generate_single_sample(
        self,
        practice_area: str,
        topic: str,
        difficulty: str,
        counter: int,
        provider: str = 'groq',
        model: Optional[str] = None,
        reasoning_instruction: Optional[str] = None,
        batch_id: Optional[str] = None,
        sample_type: str = 'case_analysis'
    ) -> Tuple[Optional[Dict], int, float, Optional[str]]:
        """
        Generate a single legal Q&A sample using specified LLM provider.

        Args:
            practice_area: Legal practice area (e.g., "Contract Law")
            topic: Specific topic within practice area
            difficulty: Difficulty level (basic/intermediate/advanced/expert)
            counter: Sample counter for ID generation
            provider: Provider name ('groq' or 'cerebras')
            model: Optional specific model, uses provider default if None
            reasoning_instruction: Optional custom reasoning requirements
            batch_id: Optional batch identifier
            sample_type: Type of sample (case_analysis, educational, client_interaction, statutory_interpretation)

        Returns:
            Tuple of (sample_dict, tokens_used, elapsed_time, error_message)
        """
        if provider not in PROVIDERS:
            return None, 0, 0, f"Unknown provider: {provider}"

        # Validate sample_type (exclude 'balance' - it should be converted before reaching here)
        valid_sample_types = ['case_analysis', 'educational', 'client_interaction', 'statutory_interpretation']
        if sample_type not in valid_sample_types:
            return None, 0, 0, f"Invalid sample_type: {sample_type}. Valid types: {', '.join(valid_sample_types)} (Note: 'balance' should be converted to a specific type before generation)"

        if model is None:
            model = PROVIDERS[provider]['default_model']

        # Get difficulty specifications
        diff_spec = DIFFICULTY_SPECS.get(difficulty, DIFFICULTY_SPECS['intermediate'])

        # Get sample type guidance
        type_guide = self._get_sample_type_guidance(sample_type)
        sample_type_config = SAMPLE_TYPES.get(sample_type, SAMPLE_TYPES['case_analysis'])

        # Select random scenario pattern for diversity (only for case_analysis)
        if sample_type == 'case_analysis':
            scenario_pattern = random.choice(SCENARIO_PATTERNS)
            scenario_guidance = {
                "client_consultation": "Frame as a client's initial consultation question seeking legal guidance",
                "procedural_tactical": "Frame as a question about specific procedural steps or tactical considerations",
                "risk_assessment": "Frame as a request for risk assessment or commercial legal advice",
                "dispute_resolution": "Frame as a question about dispute resolution options and strategies",
                "compliance_preventive": "Frame as a compliance or preventive legal guidance question"
            }
            scenario_text = scenario_guidance[scenario_pattern]
        else:
            scenario_text = type_guide['example_context']

        # Build custom reasoning instruction if provided
        reasoning_req = ""
        if reasoning_instruction:
            reasoning_req = f"\n- ADDITIONAL REQUIREMENT: {reasoning_instruction}"

        # Build dynamic structure validation based on sample_type
        if sample_type == 'case_analysis':
            structure_validation = "☐ 2. IRAC structure: Answer follows Issue → Rule → Application → Conclusion"
            reasoning_guidance = "Demonstrate IRAC progression through steps"
        elif sample_type == 'educational':
            structure_validation = "☐ 2. Educational structure: Answer follows Definition → Legal Basis → Key Elements → Examples → Distinctions"
            reasoning_guidance = "Show progression from definition to practical application"
        elif sample_type == 'client_interaction':
            structure_validation = "☐ 2. Client communication structure: Answer follows Understanding → Legal Position → Options → Recommendation → Next Steps"
            reasoning_guidance = "Show client-focused reasoning from understanding to action"
        elif sample_type == 'statutory_interpretation':
            structure_validation = "☐ 2. Statutory analysis structure: Answer follows Statutory Text → Purpose → Interpretation → Case Law → Application"
            reasoning_guidance = "Show progression from statutory text to practical application"
        else:
            structure_validation = "☐ 2. Answer structure: Follow the specified format for this sample type"
            reasoning_guidance = "Demonstrate logical progression through steps"

        prompt = f"""You are a UK legal expert creating high-quality training data for an AI legal assistant. Your samples will train LLMs to provide accurate legal guidance to UK lawyers and clients.

╔══════════════════════════════════════════════════════════════╗
║ GENERATION TASK                                              ║
╚══════════════════════════════════════════════════════════════╝

Practice Area: {practice_area}
Specific Topic: {topic}
Difficulty Level: {difficulty} ({diff_spec['description']})
Sample Type: {sample_type_config['name']}
Type Objective: {type_guide['objective']}
Question Format: {type_guide['question_format']}
Context: {scenario_text}

╔══════════════════════════════════════════════════════════════╗
║ QUALITY STANDARDS (Research-Based 2024-2025)                ║
╚══════════════════════════════════════════════════════════════╝

1. ANSWER STRUCTURE
   {self._get_answer_structure_guidance(sample_type)}

2. ANSWER DEPTH - Minimum {diff_spec['min_words']} words
   - Comprehensive legal analysis appropriate for {difficulty} level
   - Complexity: {diff_spec['complexity']}
   - Balance depth with clarity (avoid excessive verbosity)

3. CITATIONS - Minimum {diff_spec['min_citations']} distinct authorities
   - Format: [Case Name] [Year] [Court] [Reporter] [Page]
   - Example: "Carlill v Carbolic Smoke Ball [1893] 1 QB 256"
   - Mix: Include BOTH cases AND statutes where relevant
   - PROHIBITED: Fabricated cases, outdated law, non-UK authorities
   - ONLY use real, verifiable UK legal authorities

4. REASONING - Chain-of-Thought Analysis
   - Minimum {diff_spec['reasoning_steps']} steps
   - Each step format: "Step X: [legal principle] → [application to facts] → [intermediate conclusion]"
   - Connect steps logically (each builds on previous)
   - Reference specific cases/statutes within reasoning steps
   - {reasoning_guidance}{reasoning_req}

╔══════════════════════════════════════════════════════════════╗
║ FEW-SHOT EXAMPLES (Learn from these)                        ║
╚══════════════════════════════════════════════════════════════╝

⚠️  CRITICAL: These examples show case_analysis type. YOU MUST use the sample_type
specified above ("{sample_type}") and follow its required answer structure. Do NOT
default to IRAC if a different sample_type is requested!

EXAMPLE 1 (Basic Difficulty):
{{
    "id": "example_001",
    "question": "A homeowner agreed verbally to sell their property to a buyer for £300,000. The buyer paid a £5,000 deposit. Is this contract enforceable under UK law?",
    "answer": "**ISSUE**: Whether a verbal agreement for the sale of land is enforceable under UK law. **RULE**: Under Section 2 of the Law of Property (Miscellaneous Provisions) Act 1989, contracts for the sale of land must be in writing and signed by both parties. A verbal agreement, regardless of deposit payment, cannot satisfy the statutory formality requirements. The seminal case *McCausland v Duncan Lawrie Ltd* [1997] 1 WLR 38 confirms that Section 2 renders oral land contracts void, not merely unenforceable. **APPLICATION**: In this scenario, the homeowner and buyer entered a verbal agreement for property sale at £300,000. Despite the buyer paying a £5,000 deposit (demonstrating intention and part performance), the absence of a written contract signed by both parties means the agreement fails to meet Section 2 requirements. The court in *McCausland* held that no doctrine of part performance can overcome the statutory writing requirement. The deposit payment, while evidencing serious intent, cannot cure the fundamental defect. **CONCLUSION**: The verbal contract is void and unenforceable. The buyer may be entitled to recover the £5,000 deposit under principles of unjust enrichment, but cannot compel the sale. The homeowner is not bound to complete the transaction. To create an enforceable contract, the parties must execute a written agreement signed by both, incorporating all agreed terms.",
    "topic": "Property Law - Contract Formation",
    "difficulty": "basic",
    "case_citation": "Law of Property (Miscellaneous Provisions) Act 1989, Section 2; McCausland v Duncan Lawrie Ltd [1997] 1 WLR 38",
    "reasoning": "Step 1: Identify the governing statute - Section 2 of the Law of Property (Miscellaneous Provisions) Act 1989 requires written contracts for land sales → verbal agreements are insufficient. Step 2: Apply *McCausland v Duncan Lawrie Ltd* [1997] 1 WLR 38 - court held Section 2 renders oral contracts void, not voidable → formality requirement is absolute. Step 3: Assess deposit payment significance - while showing intent, deposit cannot satisfy writing requirement → part performance doctrine abolished by Section 2. Step 4: Determine enforceability - absence of written signed contract means agreement is void → neither party can enforce specific performance. Step 5: Consider buyer's remedies - buyer may recover deposit under unjust enrichment principles → restitution available but not contract enforcement.",
    "sample_type": "case_analysis"
}}

EXAMPLE 2 (Advanced Difficulty):
{{
    "id": "example_002",
    "question": "A director of a technology company personally guaranteed a loan to the company. The company later entered administration. Can the director argue that the guarantee was given under undue influence from the company's CEO, who is also her spouse?",
    "answer": "**ISSUE**: Whether a personal guarantee can be set aside on grounds of undue influence where the guarantor-director is the spouse of the CEO who requested the guarantee. **RULE**: The doctrine of undue influence, governed by *Royal Bank of Scotland v Etridge (No 2)* [2001] UKHL 44, recognizes two categories: actual undue influence (proven coercion) and presumed undue influence (arising from relationships of trust). When a guarantee is given for another's debt in a relationship where influence may be exercised (spousal relationship), the court presumes undue influence unless rebutted. However, *Pesticcio v Huet* [2004] EWCA Civ 372 establishes that directors are expected to understand commercial transactions given their fiduciary position. The Insolvency Act 1986 also permits administrators to challenge transactions at undervalue or preferences. **APPLICATION**: Here, the director-wife gave a personal guarantee for the company's loan at the request of her CEO-husband. While *Etridge* would normally raise a presumption of undue influence in a spousal transaction, *Pesticcio* complicates this. As a director, she owed fiduciary duties to the company and is presumed to understand the commercial implications of guarantees. The court in *Pesticcio* held that directors cannot easily claim undue influence in commercial dealings given their sophistication. However, if she can demonstrate she received no independent legal advice, and the CEO-husband actively concealed risks or pressured her, actual undue influence under *Etridge* may be established. The burden shifts to the lender to show reasonable steps were taken to ensure she understood the guarantee (e.g., requiring independent advice). **CONCLUSION**: The director faces significant hurdles due to her fiduciary status under *Pesticcio*, which presumes commercial sophistication. However, if she proves actual undue influence (coercion, lack of independent advice, concealment of material facts) under *Etridge*, the guarantee may be voidable. The outcome depends on evidence of pressure and whether the lender ensured she had independent legal advice. In administration, the administrator may also examine whether the guarantee constituted a transaction at undervalue under the Insolvency Act 1986.",
    "topic": "Company Law - Directors' Duties and Undue Influence",
    "difficulty": "advanced",
    "case_citation": "Royal Bank of Scotland v Etridge (No 2) [2001] UKHL 44; Pesticcio v Huet [2004] EWCA Civ 372; Insolvency Act 1986",
    "reasoning": "Step 1: Establish undue influence framework - *Royal Bank of Scotland v Etridge (No 2)* [2001] UKHL 44 sets out two categories: actual undue influence (proven coercion) and presumed undue influence (from relationships of trust) → spousal relationships create presumption. Step 2: Consider director's fiduciary position - *Pesticcio v Huet* [2004] EWCA Civ 372 held directors are sophisticated parties who understand commercial transactions → presumption of undue influence harder to establish for directors. Step 3: Assess evidence requirements - must prove actual pressure, lack of independent advice, concealment of risks → burden on director to demonstrate CEO-husband's improper influence. Step 4: Evaluate lender's duties - under *Etridge*, lender must take reasonable steps to ensure guarantor understood obligation (e.g., require independent legal advice) → failure may render guarantee voidable. Step 5: Apply insolvency law considerations - Insolvency Act 1986 allows administrator to challenge transactions at undervalue or preferences → additional avenue for challenging guarantee. Step 6: Balance competing doctrines - tension between *Etridge* (protecting vulnerable parties) and *Pesticcio* (holding directors to higher standard) → outcome depends on evidence of actual coercion versus commercial sophistication. Step 7: Determine likely outcome - director must prove actual undue influence given her fiduciary status → if successful and lender failed to ensure independent advice, guarantee may be set aside.",
    "sample_type": "case_analysis"
}}

╔══════════════════════════════════════════════════════════════╗
║ DIVERSITY REQUIREMENTS                                       ║
╚══════════════════════════════════════════════════════════════╝

Vary your sample to increase dataset uniqueness:
- Scenario perspective: client, lawyer, third party, or multi-party
- Temporal context: pre-litigation, during proceedings, post-judgment, preventive
- Question complexity: balance straightforward with nuanced within {difficulty} level
- Legal sub-issues: incorporate related doctrines where appropriate

╔══════════════════════════════════════════════════════════════╗
║ SELF-VALIDATION CHECKLIST (Complete before returning JSON)  ║
╚══════════════════════════════════════════════════════════════╝

Before generating JSON, verify:
☐ 1. Word count: Answer contains ≥ {diff_spec['min_words']} words
{structure_validation}
☐ 3. Citations: Includes ≥ {diff_spec['min_citations']} distinct real UK authorities
☐ 4. Reasoning depth: Contains {diff_spec['reasoning_steps']} complete analytical steps
☐ 5. UK jurisdiction: No US or other jurisdiction references
☐ 6. Realistic scenario: Question reflects actual practitioner scenarios
☐ 7. Professional tone: Clear, precise legal language throughout
☐ 8. Citation format: All citations follow [Case Name] [Year] [Court] [Reporter] [Page]

If ANY check fails, regenerate with corrections before returning JSON.

╔══════════════════════════════════════════════════════════════╗
║ OUTPUT FORMAT (JSON ONLY - NO MARKDOWN, NO EXTRA TEXT)      ║
╚══════════════════════════════════════════════════════════════╝

⚠️  CRITICAL REQUIREMENT: The "sample_type" field MUST be "{sample_type}" (NOT "case_analysis")
and your answer MUST follow the structure specified for "{sample_type}" above!

Return ONLY a valid JSON object:
{{
    "id": "temporary_id",
    "question": "your generated question here",
    "answer": "your comprehensive answer following the {sample_type} structure (minimum {diff_spec['min_words']} words)",
    "topic": "{practice_area} - {topic}",
    "difficulty": "{difficulty}",
    "case_citation": "Real UK cases/statutes (minimum {diff_spec['min_citations']})",
    "reasoning": "Step 1: ... Step 2: ... [minimum {diff_spec['reasoning_steps']} steps]",
    "sample_type": "{sample_type}"
}}

Generate NOW:"""

        try:
            start_time = time.time()

            # Get provider instance
            provider_instance = self.factory.get_provider(provider)

            # Adjust max_tokens for thinking models (they need more tokens for reasoning)
            # Check against THINKING_MODELS constant for robust detection
            is_thinking_model = model in THINKING_MODELS
            max_tokens = 8000 if is_thinking_model else 4000

            # Generate using provider
            result = provider_instance.generate(
                model=model,
                prompt=prompt,
                temperature=0.9 if provider == 'groq' else 0.6,
                max_tokens=max_tokens,
                top_p=1 if provider == 'groq' else 0.95
            )

            response_text = result['text']
            tokens_used = result['tokens_used']

            # Extract JSON from response (handle various formats)
            response_text = self._extract_json(response_text)

            if not response_text:
                raise ValueError("Empty response after JSON extraction")

            sample = json.loads(response_text)

            # Validate required fields
            required_fields = ["id", "question", "answer", "topic", "difficulty", "case_citation", "reasoning"]
            if not all(field in sample for field in required_fields):
                raise ValueError(f"Missing required fields in generated sample")

            # Generate truly unique UUID for the sample
            unique_id = f"{provider}_{str(uuid.uuid4())}"
            sample['id'] = unique_id

            # ALWAYS override sample_type to prevent LLM from changing it
            # Validation will check if structure matches the requested type
            sample['sample_type'] = sample_type

            # Add metadata (timestamps, provider, model, batch_id)
            now = datetime.now().isoformat()
            sample['created_at'] = now
            sample['updated_at'] = now
            sample['provider'] = provider
            sample['model'] = model

            if batch_id:
                sample['batch_id'] = batch_id

            elapsed = time.time() - start_time

            # POST-GENERATION QUALITY VALIDATION
            validation_error = self._validate_sample_quality(sample, difficulty)
            if validation_error:
                return None, 0, 0, f"[quality_error] {validation_error}"

            return sample, tokens_used, elapsed, None

        except json.JSONDecodeError as e:
            return None, 0, 0, f"[json_error] JSON parsing error: {str(e)}"
        except Exception as e:
            # Use comprehensive error categorization function
            error_type = categorize_error(str(e), provider)
            return None, 0, 0, f"[{error_type}] {str(e)}"

    def _validate_sample_quality(self, sample: Dict, difficulty: str) -> Optional[str]:
        """
        Validate generated sample quality against research-based standards.
        Focus on content correctness and reasoning over arbitrary thresholds.

        Args:
            sample: Generated sample dictionary
            difficulty: Difficulty level

        Returns:
            Error message if validation fails, None if passes
        """
        diff_spec = DIFFICULTY_SPECS.get(difficulty, DIFFICULTY_SPECS['intermediate'])

        answer = sample.get('answer', '')
        reasoning = sample.get('reasoning', '')
        case_citation = sample.get('case_citation', '')

        # 1. REMOVED: Word count validation - content quality matters more than length
        # 2. REMOVED: Citation count validation - not all questions require case citations

        # 3. Validate reasoning steps - CORE QUALITY INDICATOR
        step_count = len(re.findall(r'Step \d+:', reasoning))
        min_steps = int(diff_spec['reasoning_steps'].split('-')[0])
        if step_count < min_steps:
            return f"Insufficient reasoning steps: {step_count} found (minimum {min_steps} required)"

        # 4. Check for empty fields (critical content must exist)
        if not answer or not reasoning:
            return "Answer or reasoning is empty"

        # Note: case_citation can be empty for questions that don't require case law

        # 5. Basic content quality check - ensure answer has minimum substance
        word_count = len(answer.split())
        if word_count < 100:  # Very low threshold - just ensures it's not trivial
            return f"Answer lacks substance: {word_count} words (minimum 100 for meaningful legal analysis)"

        # 6. Validate answer structure matches sample_type
        sample_type = sample.get('sample_type', 'case_analysis')
        structure_error = self._validate_answer_structure(answer, sample_type)
        if structure_error:
            return structure_error

        # All validations passed
        return None

    def _validate_answer_structure(self, answer: str, sample_type: str) -> Optional[str]:
        """
        Validate answer structure matches sample type requirements.

        Ensures samples have the correct structure for their designated type:
        - case_analysis: IRAC (Issue, Rule, Application, Conclusion)
        - educational: Teaching structure (Definition, Legal Basis, Key Elements, Examples)
        - client_interaction: Client communication (Understanding, Legal Position, Options, Recommendation)
        - statutory_interpretation: Legislative analysis (Statutory Text, Purpose, Interpretation, Application)

        Args:
            answer: Generated answer text
            sample_type: Type of sample (case_analysis, educational, client_interaction, statutory_interpretation)

        Returns:
            Error message if structure validation fails, None if passes
        """
        # Define required structure keywords for each sample type
        structure_requirements = {
            'case_analysis': {
                'keywords': ['ISSUE', 'RULE', 'APPLICATION', 'CONCLUSION'],
                'min_required': 3  # Must have at least 3 of 4 sections (some flexibility)
            },
            'educational': {
                'keywords': ['DEFINITION', 'LEGAL BASIS', 'KEY ELEMENTS', 'EXAMPLES'],
                'min_required': 3
            },
            'client_interaction': {
                'keywords': ['UNDERSTANDING', 'LEGAL POSITION', 'OPTIONS', 'RECOMMENDATION'],
                'min_required': 3
            },
            'statutory_interpretation': {
                'keywords': ['STATUTORY TEXT', 'PURPOSE', 'INTERPRETATION', 'APPLICATION'],
                'min_required': 3
            }
        }

        # Default to case_analysis if type not recognized
        if sample_type not in structure_requirements:
            sample_type = 'case_analysis'

        requirements = structure_requirements[sample_type]
        required_keywords = requirements['keywords']
        min_required = requirements['min_required']

        # Case-insensitive check
        answer_upper = answer.upper()

        # Count how many required keywords are present
        found_keywords = [kw for kw in required_keywords if kw in answer_upper]

        if len(found_keywords) < min_required:
            missing_keywords = [kw for kw in required_keywords if kw not in answer_upper]
            return (f"Answer structure does not match sample_type '{sample_type}'. "
                    f"Found {len(found_keywords)}/{len(required_keywords)} required sections. "
                    f"Missing: {', '.join(missing_keywords[:2])}")  # Show first 2 missing

        # Validation passed
        return None

    def _extract_json(self, response_text: str) -> str:
        """
        Extract JSON from LLM response handling various formats including thinking models.

        Args:
            response_text: Raw response from LLM

        Returns:
            Extracted JSON string
        """
        # STEP 1: Remove ALL thinking tags (Cerebras thinking models can have multiple)
        # Add iteration limit to prevent infinite loops on malformed tags
        max_thinking_removals = 10
        thinking_removal_count = 0

        while ('<thinking>' in response_text or '</thinking>' in response_text) and thinking_removal_count < max_thinking_removals:
            thinking_removal_count += 1

            # Find and remove thinking sections
            start_think = response_text.find('<thinking>')
            end_think = response_text.find('</thinking>')

            if start_think != -1 and end_think != -1:
                # Remove the entire thinking section including tags
                response_text = response_text[:start_think] + response_text[end_think + len('</thinking>'):]
            elif start_think != -1:
                # Unclosed thinking tag - remove everything from there
                response_text = response_text[:start_think]
                break
            elif end_think != -1:
                # Orphaned closing tag - remove it and everything before
                response_text = response_text[end_think + len('</thinking>'):]
            else:
                break

        # STEP 2: Extract JSON from markdown code blocks
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
            else:
                # Incomplete code block, take everything after ```json
                response_text = response_text[start:].strip()
        elif "```" in response_text:
            # Generic code block
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text

        # STEP 3: Find the JSON object (most robust method)
        # Look for the first complete JSON object
        if not response_text.strip().startswith('{'):
            start_json = response_text.find('{')
            if start_json != -1:
                # Find the matching closing brace by counting braces
                brace_count = 0
                end_json = -1
                for i in range(start_json, len(response_text)):
                    if response_text[i] == '{':
                        brace_count += 1
                    elif response_text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_json = i
                            break

                if end_json != -1:
                    response_text = response_text[start_json:end_json+1]
                else:
                    # Fallback to rfind if counting fails
                    end_json = response_text.rfind('}')
                    if end_json != -1:
                        response_text = response_text[start_json:end_json+1]

        # STEP 4: Clean up any remaining whitespace or artifacts
        response_text = response_text.strip()

        # Remove any trailing incomplete strings or commas (common in truncated responses)
        if response_text.endswith(','):
            response_text = response_text[:-1]

        return response_text

    def get_next_provider_and_model(
        self,
        current_provider: str,
        current_model: str,
        failed_models_by_provider: Dict[str, List[str]]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Get next provider/model combination with cross-provider fallback.

        Args:
            current_provider: Provider that just failed
            current_model: Model that just failed
            failed_models_by_provider: Dict mapping provider -> list of failed models

        Returns:
            Tuple of (next_provider, next_model) or (None, None) if all exhausted
        """
        # Try next model in same provider first
        failed_models = failed_models_by_provider.get(current_provider, [])
        provider_instance = self.factory.get_provider(current_provider)
        next_model = self.factory.get_next_model(current_model, failed_models, provider_instance)

        if next_model:
            return current_provider, next_model

        # All models in current provider failed, try switching provider
        print(f"⚠️  All {current_provider} models exhausted, attempting cross-provider fallback")

        # Determine alternative provider
        alternative_provider = 'cerebras' if current_provider == 'groq' else 'groq'

        # Check if alternative provider is available and has unfailed models
        if PROVIDERS.get(alternative_provider, {}).get('enabled'):
            alt_failed = failed_models_by_provider.get(alternative_provider, [])
            alt_provider_instance = self.factory.get_provider(alternative_provider)
            fallback_order = alt_provider_instance.get_fallback_order()

            # Try to find an unfailed model in alternative provider
            for model in fallback_order:
                if model not in alt_failed:
                    print(f"🔄 Switching to {alternative_provider} provider with model {model}")
                    return alternative_provider, model

        # All providers and models exhausted
        return None, None
