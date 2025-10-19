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
            },
            'legal_dialogue': {
                'objective': 'Conduct multi-turn legal conversations demonstrating reasoning through dialogue',
                'question_format': 'Present a conversational exchange about a legal topic or scenario',
                'answer_approach': 'Use dialogue format (Q&A, discussion, debate) showing reasoning development',
                'focus': 'Conversational AI with dialectical legal reasoning',
                'example_context': 'A conversation between lawyer and client, or between opposing counsel discussing legal points'
            },
            'pure_conceptual': {
                'objective': 'Provide factual legal knowledge without analytical reasoning (textbook-style)',
                'question_format': 'Ask for definition, explanation, or description of legal concepts',
                'answer_approach': 'Present clear, encyclopedic knowledge without case analysis or reasoning',
                'focus': 'Knowledge retention and factual accuracy',
                'example_context': 'A reference question asking what a legal term means or how a law developed historically'
            },
            'comparative_analysis': {
                'objective': 'Compare different legal approaches, jurisdictions, or doctrines',
                'question_format': 'Ask for comparison between legal systems, approaches, or concepts',
                'answer_approach': 'Systematically compare and contrast with similarities and differences',
                'focus': 'Critical thinking and analytical reasoning across legal systems',
                'example_context': 'Someone wants to understand how different jurisdictions or doctrines differ'
            },
            'ethical_reasoning': {
                'objective': 'Analyze ethical dilemmas and professional responsibility issues',
                'question_format': 'Present an ethical scenario requiring moral and professional judgment',
                'answer_approach': 'Apply ethical frameworks and professional conduct rules to the dilemma',
                'focus': 'Moral reasoning within legal professional contexts',
                'example_context': 'A lawyer faces an ethical dilemma requiring professional judgment'
            },
            'procedural_guide': {
                'objective': 'Provide step-by-step procedural instructions for legal processes',
                'question_format': 'Ask how to complete a specific legal procedure or process',
                'answer_approach': 'Present sequential, actionable steps in chronological order',
                'focus': 'Practical procedural knowledge and execution',
                'example_context': 'Someone needs to know the exact steps to follow for a legal procedure'
            },
            'legal_news_analysis': {
                'objective': 'Analyze recent legal developments and their implications',
                'question_format': 'Present a recent court decision, legislation, or regulatory change',
                'answer_approach': 'Analyze the development, its legal basis, and practical implications',
                'focus': 'Current legal affairs and forward-looking analysis',
                'example_context': 'A recent Supreme Court ruling or new legislation has been announced'
            },
            'case_study': {
                'objective': 'Provide comprehensive analysis of landmark cases',
                'question_format': 'Ask for in-depth analysis of a significant legal case',
                'answer_approach': 'Thoroughly examine facts, legal issues, reasoning, and broader implications',
                'focus': 'Deep legal learning through case examination',
                'example_context': 'A landmark case needs detailed analysis for educational purposes'
            },
            'practical_application': {
                'objective': 'Address real-world legal scenarios in specific practice domains',
                'question_format': 'Present practical scenarios in immigration, criminal, family law, etc.',
                'answer_approach': 'Provide actionable legal guidance tailored to the specific domain',
                'focus': 'Domain-specific practical legal problem-solving',
                'example_context': 'A client needs practical guidance in immigration, criminal defense, or family matters'
            },
            'simple_qa': {
                'objective': 'Provide direct, concise answers to straightforward legal questions',
                'question_format': 'Ask a simple, direct question requiring a factual answer',
                'answer_approach': 'Give a clear, concise answer without complex structure',
                'focus': 'Quick factual knowledge and simple explanations',
                'example_context': 'Someone needs a quick factual answer or brief explanation'
            },
            'general_reasoning': {
                'objective': 'Explain legal principles and reasoning without rigid structure',
                'question_format': 'Ask about legal concepts, reasoning, or principles',
                'answer_approach': 'Provide flexible, thoughtful reasoning without mandatory format',
                'focus': 'Natural legal reasoning and explanation',
                'example_context': 'Someone wants to understand the reasoning behind a legal principle'
            },
            'hypothetical': {
                'objective': 'Analyze brief hypothetical scenarios concisely',
                'question_format': 'Present a short "what if" legal scenario',
                'answer_approach': 'Provide concise analysis without extensive structure',
                'focus': 'Quick scenario analysis and legal thinking',
                'example_context': 'Someone poses a hypothetical situation requiring quick legal analysis'
            },
            'conversational': {
                'objective': 'Respond like a professional lawyer in natural conversation',
                'question_format': 'Question requiring professional but conversational response',
                'answer_approach': 'Sound like an experienced lawyer speaking naturally - professional yet approachable',
                'focus': 'Professional legal voice in everyday conversation',
                'example_context': 'Client or colleague asks a question in conversation'
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
   │ APPLICATION: Demonstrate how the statute applies in practice""",

            'legal_dialogue': """Dialogue Format (MANDATORY)
   Your answer should follow this conversational structure:

   │ OPENING: Start the dialogue with initial question or statement
   │ EXCHANGE 1: First response with reasoning or clarification
   │ FOLLOW-UP: Build on previous point with deeper questioning
   │ EXCHANGE 2: Develop reasoning through discussion
   │ RESOLUTION: Conclude dialogue with synthesized understanding

   Format each turn as:
   [Speaker]: [Statement/Question]

   Example:
   Client: [question]
   Lawyer: [response with reasoning]
   Client: [follow-up]
   Lawyer: [deeper analysis]""",

            'pure_conceptual': """Encyclopedic Knowledge Format (MANDATORY)
   Your answer should follow this factual structure:

   │ CORE DEFINITION: Precise definition of the concept/term
   │ HISTORICAL CONTEXT: When and how this law/concept developed
   │ STATUTORY/DOCTRINAL BASIS: Legal foundation (acts, cases)
   │ KEY FEATURES: Essential characteristics and elements
   │ SCOPE AND LIMITS: What it covers and what it doesn't

   NOTE: NO reasoning steps needed - focus on factual knowledge only""",

            'comparative_analysis': """Comparative Structure (MANDATORY)
   Your answer should follow this comparative framework:

   │ INTRODUCTION: State what is being compared and why
   │ APPROACH A: Explain first jurisdiction/doctrine/approach
   │ APPROACH B: Explain second jurisdiction/doctrine/approach
   │ SIMILARITIES: Identify common elements and shared principles
   │ DIFFERENCES: Contrast key distinctions and divergences
   │ ANALYSIS: Evaluate strengths and weaknesses of each
   │ CONCLUSION: Synthesize insights from comparison""",

            'ethical_reasoning': """Ethical Analysis Structure (MANDATORY)
   Your answer should follow this ethical reasoning framework:

   │ ETHICAL DILEMMA: Identify the core ethical conflict
   │ PROFESSIONAL DUTIES: State relevant professional conduct rules
   │ COMPETING VALUES: Identify conflicting obligations or principles
   │ FRAMEWORKS: Apply ethical theories (deontology, consequentialism, virtue ethics)
   │ PRACTICAL CONSIDERATIONS: Assess real-world implications
   │ RESOLUTION: Recommend course of action with moral justification""",

            'procedural_guide': """Step-by-Step Procedural Format (MANDATORY)
   Your answer should follow this sequential structure:

   │ OVERVIEW: Brief summary of the procedure and its purpose
   │ PREREQUISITES: What must be in place before starting
   │ STEP 1: [First action with details]
   │ STEP 2: [Second action with details]
   │ STEP 3: [Third action with details]
   │ ... [Continue with all necessary steps]
   │ FINAL STEP: [Concluding action]
   │ IMPORTANT NOTES: Time limits, forms, fees, or special requirements

   Each step should be actionable and specific""",

            'legal_news_analysis': """Legal News Analysis Format (MANDATORY)
   Your answer should follow this current affairs structure:

   │ THE DEVELOPMENT: Describe the recent legal development (case, legislation, regulation)
   │ BACKGROUND: Provide context and previous legal position
   │ KEY CHANGES: Identify what has changed and why
   │ LEGAL REASONING: Explain the court's/legislature's reasoning
   │ IMPLICATIONS: Analyze practical impact on law and practice
   │ FUTURE OUTLOOK: Discuss potential future developments

   Focus on contemporary relevance and practical impact""",

            'case_study': """Case Study Format (MANDATORY)
   Your answer should follow this comprehensive analytical structure:

   │ CASE OVERVIEW: Name, citation, court, date, and significance
   │ FACTS: Detailed factual background
   │ LEGAL ISSUES: Central questions of law presented
   │ COURT'S REASONING: Detailed analysis of judicial reasoning
   │ JUDGMENT: The decision and its immediate legal effect
   │ BROADER IMPLICATIONS: Impact on legal doctrine and practice
   │ SUBSEQUENT TREATMENT: How later cases have applied/distinguished it

   Provide comprehensive educational analysis""",

            'practical_application': """Practical Application Format (MANDATORY)
   Your answer should follow this domain-specific structure:

   │ SCENARIO ASSESSMENT: Understand the specific domain context
   │ APPLICABLE LAW: State relevant law for this domain (immigration/criminal/family/etc.)
   │ PRACTICAL ANALYSIS: Apply law to the specific scenario
   │ AVAILABLE OPTIONS: Present domain-specific options and strategies
   │ RECOMMENDED APPROACH: Provide practical guidance
   │ PROCEDURAL STEPS: Outline immediate actions required
   │ RISKS AND CONSIDERATIONS: Highlight domain-specific challenges

   Tailor advice to the specific legal domain""",

            'simple_qa': """Simple Q&A Format (NO COMPLEX STRUCTURE REQUIRED)
   Your answer should be:

   │ Direct and concise (2-4 sentences maximum)
   │ Answer the question clearly without IRAC or formal structure
   │ Include key legal authority (case/statute) if relevant
   │ DO NOT use sections like ISSUE, RULE, APPLICATION, CONCLUSION
   │ Just state the answer plainly

   ⚠️  CRITICAL: This is a SIMPLE Q&A - do NOT write a complex legal analysis!
   Keep it straightforward like answering a quick question - no essays!""",

            'general_reasoning': """General Reasoning Format (FLEXIBLE STRUCTURE)
   Your answer should naturally explain the reasoning:

   │ Start with the core principle or concept
   │ Explain the reasoning or rationale
   │ Provide examples if helpful
   │ Reference relevant law naturally

   No rigid structure - write naturally and clearly""",

            'hypothetical': """Hypothetical Format (BRIEF AND CONCISE)
   Your answer should:

   │ Quickly identify the legal issue
   │ Apply relevant law concisely
   │ State the likely outcome
   │ Brief explanation (2-3 sentences)

   Keep it short and to the point - this is a quick analysis""",

            'conversational': """Professional Legal Conversation (LAWYER VOICE)
   Your answer should sound like a professional lawyer speaking naturally:

   │ Professional but approachable tone
   │ Use legal terminology naturally (as lawyers do in conversation)
   │ Confident and knowledgeable delivery
   │ Brief and conversational - no formal sections
   │ Reference law casually when relevant

   Write how an experienced lawyer would explain something in conversation - professional, clear, authoritative yet natural!"""
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
        valid_sample_types = [
            'case_analysis',
            'educational',
            'client_interaction',
            'statutory_interpretation',
            'legal_dialogue',
            'pure_conceptual',
            'comparative_analysis',
            'ethical_reasoning',
            'procedural_guide',
            'legal_news_analysis',
            'case_study',
            'practical_application',
            'simple_qa',
            'general_reasoning',
            'hypothetical',
            'conversational'
        ]
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

        # Build dynamic structure validation based on sample_type (MUST be before reasoning_section)
        structure_validations = {
            'case_analysis': (
                "☐ 2. IRAC structure: Answer follows Issue → Rule → Application → Conclusion",
                "Demonstrate IRAC progression through steps"
            ),
            'educational': (
                "☐ 2. Educational structure: Answer follows Definition → Legal Basis → Key Elements → Examples → Distinctions",
                "Show progression from definition to practical application"
            ),
            'client_interaction': (
                "☐ 2. Client communication structure: Answer follows Understanding → Legal Position → Options → Recommendation → Next Steps",
                "Show client-focused reasoning from understanding to action"
            ),
            'statutory_interpretation': (
                "☐ 2. Statutory analysis structure: Answer follows Statutory Text → Purpose → Interpretation → Case Law → Application",
                "Show progression from statutory text to practical application"
            ),
            'legal_dialogue': (
                "☐ 2. Dialogue structure: Answer uses conversational format with Opening → Exchange → Follow-up → Resolution",
                "Show reasoning development through multi-turn dialogue"
            ),
            'pure_conceptual': (
                "☐ 2. Encyclopedic structure: Answer follows Core Definition → Historical Context → Statutory Basis → Key Features → Scope",
                "Present factual knowledge systematically (NO reasoning steps needed)"
            ),
            'comparative_analysis': (
                "☐ 2. Comparative structure: Answer follows Introduction → Approach A → Approach B → Similarities → Differences → Analysis → Conclusion",
                "Show comparative reasoning across jurisdictions or doctrines"
            ),
            'ethical_reasoning': (
                "☐ 2. Ethical analysis structure: Answer follows Ethical Dilemma → Professional Duties → Competing Values → Frameworks → Resolution",
                "Show moral reasoning through ethical frameworks"
            ),
            'procedural_guide': (
                "☐ 2. Procedural structure: Answer follows Overview → Prerequisites → Step-by-step instructions → Important Notes",
                "Show sequential procedural progression"
            ),
            'legal_news_analysis': (
                "☐ 2. Legal news structure: Answer follows The Development → Background → Key Changes → Legal Reasoning → Implications → Future Outlook",
                "Show analysis of contemporary legal developments"
            ),
            'case_study': (
                "☐ 2. Case study structure: Answer follows Case Overview → Facts → Legal Issues → Court's Reasoning → Judgment → Broader Implications → Subsequent Treatment",
                "Show comprehensive case analysis for legal learning"
            ),
            'practical_application': (
                "☐ 2. Practical application structure: Answer follows Scenario Assessment → Applicable Law → Practical Analysis → Options → Recommended Approach → Procedural Steps → Risks",
                "Show domain-specific practical problem-solving"
            ),
            'simple_qa': (
                "☐ 2. Simple Q&A: Answer is direct and concise (no complex structure required)",
                "Provide clear, straightforward answer"
            ),
            'general_reasoning': (
                "☐ 2. General reasoning: Answer naturally explains the reasoning (flexible structure)",
                "Explain reasoning naturally without rigid format"
            ),
            'hypothetical': (
                "☐ 2. Hypothetical: Answer is brief and to the point (concise analysis)",
                "Provide quick, focused analysis"
            ),
            'conversational': (
                "☐ 2. Conversational: Answer sounds like a professional lawyer speaking naturally (no formal structure)",
                "Sound professional yet natural in conversation"
            )
        }

        structure_validation, reasoning_guidance = structure_validations.get(
            sample_type,
            ("☐ 2. Answer structure: Follow the specified format for this sample type",
             "Demonstrate logical progression through steps")
        )

        # Add special warning and adjust word count for simple types
        simple_warning = ""
        depth_guidance = f"Minimum {diff_spec['min_words']} words"
        simple_types_warning = ['simple_qa', 'hypothetical', 'conversational']

        if sample_type in simple_types_warning:
            simple_warning = f"""
⚠️  CRITICAL WARNING FOR {sample_type.upper()}:
   DO NOT generate a long, complex legal analysis!
   DO NOT use ISSUE, RULE, APPLICATION, CONCLUSION sections!
   DO NOT write an essay - keep your answer BRIEF and DIRECT!
   This is a {sample_type} sample - simplicity is required!
"""
            # Override word count for simple types
            if sample_type == 'simple_qa':
                depth_guidance = "Keep answer brief: 50-100 words (2-4 sentences)"
            elif sample_type == 'hypothetical':
                depth_guidance = "Keep answer concise: 100-150 words maximum"
            elif sample_type == 'conversational':
                depth_guidance = "Keep response natural: 100-200 words (conversational length)"

        # Build examples section based on sample type
        if sample_type == 'simple_qa':
            examples_section = """
╔══════════════════════════════════════════════════════════════╗
║ SIMPLE Q&A EXAMPLES (Keep it this brief!)                   ║
╚══════════════════════════════════════════════════════════════╝

EXAMPLE (Simple Q&A):
{
    "question": "What is the limitation period for breach of contract claims in England?",
    "answer": "Under the Limitation Act 1980, the limitation period for breach of contract claims is six years from the date of the breach. This applies to simple contracts. For contracts made by deed, the period is 12 years.",
    "reasoning": "The Limitation Act 1980 sets statutory time limits for bringing claims. For contract breaches, the six-year period starts when the breach occurs, giving claimants a reasonable window to pursue remedies while ensuring defendants aren't exposed to indefinite liability."
}"""
        elif sample_type in ['hypothetical', 'conversational']:
            examples_section = f"""
╔══════════════════════════════════════════════════════════════╗
║ {sample_type.upper()} EXAMPLE (Keep it brief!)              ║
╚══════════════════════════════════════════════════════════════╝

⚠️  Remember: This is {sample_type} - NO long IRAC analysis needed!
Keep your answer SHORT and DIRECT."""
        else:
            examples_section = """
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
}}"""

        # Build reasoning section based on sample type (MUST be after reasoning_guidance is defined)
        # Simple types don't need complex reasoning structure
        simple_types = ['pure_conceptual', 'simple_qa', 'hypothetical', 'conversational']

        if sample_type in simple_types:
            if sample_type == 'pure_conceptual':
                reasoning_section = f"""4. FACTUAL KNOWLEDGE PRESENTATION
   - Focus on encyclopedic accuracy and clarity
   - Present information systematically without analytical reasoning
   - The 'reasoning' field should briefly explain how the concept developed or its logical structure
   - No "Step 1, Step 2" format needed{reasoning_req}"""
            elif sample_type == 'simple_qa':
                reasoning_section = f"""4. BRIEF EXPLANATION (OPTIONAL)
   - The 'reasoning' field can contain a brief explanation of your answer
   - No complex step-by-step analysis needed
   - Keep it simple and direct{reasoning_req}"""
            elif sample_type == 'hypothetical':
                reasoning_section = f"""4. QUICK REASONING (CONCISE)
   - Briefly explain the legal reasoning (2-3 steps maximum)
   - Keep it concise and focused
   - No extensive chain-of-thought needed{reasoning_req}"""
            elif sample_type == 'conversational':
                reasoning_section = f"""4. INFORMAL REASONING (NATURAL)
   - The 'reasoning' field should explain your thinking informally
   - Write how a lawyer would explain their reasoning in conversation
   - No step format needed - just natural explanation{reasoning_req}"""
        elif sample_type == 'general_reasoning':
            reasoning_section = f"""4. FLEXIBLE REASONING
   - Explain the reasoning naturally without rigid step format
   - Can use informal steps or flowing explanation
   - Focus on clarity over format
   - {reasoning_guidance}{reasoning_req}"""
        else:
            reasoning_section = f"""4. REASONING - Chain-of-Thought Analysis
   - Minimum {diff_spec['reasoning_steps']} steps
   - Each step format: "Step X: [legal principle] → [application to facts] → [intermediate conclusion]"
   - Connect steps logically (each builds on previous)
   - Reference specific cases/statutes within reasoning steps
   - {reasoning_guidance}{reasoning_req}"""

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
{simple_warning}
1. ANSWER STRUCTURE
   {self._get_answer_structure_guidance(sample_type)}

2. ANSWER DEPTH - {depth_guidance}
   - Legal content appropriate for {difficulty} level
   - Complexity: {diff_spec['complexity']}
   - Balance depth with clarity (avoid excessive verbosity)

3. CITATIONS - Minimum {diff_spec['min_citations']} distinct authorities
   - Format: [Case Name] [Year] [Court] [Reporter] [Page]
   - Example: "Carlill v Carbolic Smoke Ball [1893] 1 QB 256"
   - Mix: Include BOTH cases AND statutes where relevant
   - PROHIBITED: Fabricated cases, outdated law, non-UK authorities
   - ONLY use real, verifiable UK legal authorities

{reasoning_section}
{examples_section}

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
        # Exception: Simple types don't need formal reasoning steps
        sample_type = sample.get('sample_type', 'case_analysis')
        simple_types_no_reasoning = ['pure_conceptual', 'simple_qa', 'hypothetical', 'conversational']

        if sample_type not in simple_types_no_reasoning:
            step_count = len(re.findall(r'Step \d+:', reasoning))
            min_steps = int(diff_spec['reasoning_steps'].split('-')[0])

            # General reasoning can be flexible - allow lower threshold
            if sample_type == 'general_reasoning':
                min_steps = max(2, min_steps - 2)  # Reduce requirement by 2 steps

            if step_count < min_steps:
                return f"Insufficient reasoning steps: {step_count} found (minimum {min_steps} required for {sample_type})"

        # 4. Check for empty fields (critical content must exist)
        # Exception: pure_conceptual can have minimal/no reasoning field
        if not answer:
            return "Answer is empty"
        if sample_type != 'pure_conceptual' and not reasoning:
            return "Reasoning is empty"

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
            },
            'legal_dialogue': {
                # More flexible - check for dialogue indicators
                'keywords': ['LAWYER:', 'CLIENT:', 'COUNSEL:', 'JUDGE:', 'Q:', 'A:'],
                'min_required': 2  # Must have at least 2 speakers/turns
            },
            'pure_conceptual': {
                # Factual knowledge structure
                'keywords': ['DEFINITION', 'HISTORICAL', 'BASIS', 'FEATURES', 'SCOPE'],
                'min_required': 3  # More lenient for factual content
            },
            'comparative_analysis': {
                # Comparison structure
                'keywords': ['INTRODUCTION', 'APPROACH', 'SIMILARITIES', 'DIFFERENCES', 'ANALYSIS'],
                'min_required': 3
            },
            'ethical_reasoning': {
                # Ethical analysis structure
                'keywords': ['DILEMMA', 'DUTIES', 'VALUES', 'FRAMEWORK', 'RESOLUTION'],
                'min_required': 3
            },
            'procedural_guide': {
                # Step-by-step procedural structure
                'keywords': ['OVERVIEW', 'STEP', 'PREREQUISITES', 'PROCEDURE', 'NOTES'],
                'min_required': 2  # Must have overview and steps
            },
            'legal_news_analysis': {
                # Legal news and developments structure
                'keywords': ['DEVELOPMENT', 'BACKGROUND', 'CHANGES', 'REASONING', 'IMPLICATIONS', 'OUTLOOK'],
                'min_required': 3
            },
            'case_study': {
                # Case study structure
                'keywords': ['OVERVIEW', 'FACTS', 'ISSUES', 'REASONING', 'JUDGMENT', 'IMPLICATIONS'],
                'min_required': 4  # More comprehensive analysis required
            },
            'practical_application': {
                # Practical domain-specific structure
                'keywords': ['ASSESSMENT', 'APPLICABLE', 'ANALYSIS', 'OPTIONS', 'APPROACH', 'STEPS', 'RISKS'],
                'min_required': 3
            },
            'simple_qa': {
                # Simple Q&A - no structure required
                'keywords': [],  # No mandatory keywords
                'min_required': 0
            },
            'general_reasoning': {
                # General reasoning - flexible
                'keywords': [],
                'min_required': 0
            },
            'hypothetical': {
                # Hypothetical - flexible
                'keywords': [],
                'min_required': 0
            },
            'conversational': {
                # Conversational - no structure required
                'keywords': [],
                'min_required': 0
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
