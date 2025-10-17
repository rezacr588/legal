"""
Configuration module for Legal Training Dataset API.
Contains all application settings and constants.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple

# ============================================================================
# FILE PATHS
# ============================================================================

PARQUET_PATH = Path("train.parquet")

# ============================================================================
# PROVIDER CONFIGURATION
# ============================================================================

PROVIDERS = {
    'groq': {
        'api_key': os.getenv('GROQ_API_KEY', ''),  # Load from environment
        'enabled': bool(os.getenv('GROQ_API_KEY')),  # Auto-disable if no key
        'default_model': 'llama-3.3-70b-versatile',
        'requests_per_minute': 25,
        'tokens_per_minute': 5500
    },
    'cerebras': {
        'api_key': os.getenv('CEREBRAS_API_KEY', ''),  # Load from environment
        'enabled': bool(os.getenv('CEREBRAS_API_KEY')),  # Auto-disable if no key
        'default_model': 'gpt-oss-120b',  # Champion: 10/10 score, 681 words, 4 citations, 2.75s, best token efficiency
        'requests_per_minute': 600,  # 14400/day = 600/hour = 10/min conservative
        'tokens_per_minute': 48000  # 60k/min with buffer
    },
    'ollama': {
        'api_key': os.getenv('OLLAMA_API_KEY', ''),  # Load from environment
        'enabled': bool(os.getenv('OLLAMA_API_KEY')),  # Auto-disable if no key
        'default_model': 'gpt-oss:120b-cloud',  # Default to 120B cloud model
        'base_url': 'https://ollama.com/api',  # Ollama Cloud API endpoint
        'requests_per_minute': 60,  # Conservative estimate (exact limits undisclosed)
        'tokens_per_minute': 10000  # Conservative estimate
    }
}

# ============================================================================
# MODEL FALLBACK ORDERS
# ============================================================================

# Model fallback order for Groq (all available production models, prioritized by capability)
# Note: Whisper and Guard models excluded as they're not for text generation
MODEL_FALLBACK_ORDER = [
    "llama-3.3-70b-versatile",       # Primary: Best balance of speed & capability
    "llama-3.1-8b-instant",          # Fast fallback
    "openai/gpt-oss-120b",           # Large model option
    "openai/gpt-oss-20b",            # Medium model option
    # Legacy models (may be deprecated, but kept as final fallback)
    "llama-3.1-70b-versatile",
    "mixtral-8x7b-32768",
    "llama-3.2-90b-text-preview",
    "llama-3.2-11b-text-preview",
    "gemma2-9b-it"
]

# Model fallback order for Cerebras - OPTIMIZED BY SINGLE-QUESTION TEST
# Rate limits: 14.4K requests/day, 60K tokens/min (except qwen-3-coder-480b: 100/day)
# Updated 2025-10-11: Enhanced JSON extraction supports thinking models
# Updated 2025-10-11: Added Llama 4 models (Scout & Maverick)
# Updated 2025-10-11: Removed word count & citation thresholds - content quality over arbitrary limits
# Updated 2025-10-11: gpt-oss-120b proven champion (10/10 score, 681 words, 4 citations, 2.75s)
CEREBRAS_FALLBACK_ORDER = [
    "gpt-oss-120b",                       # 🏆 CHAMPION: 10/10 score, most comprehensive (681 words, 4 citations), best efficiency
    "llama-3.3-70b",                      # 🥈 FAST: 8/10 score, fastest generation (2.37s, 390 words, 4 citations)
    "qwen-3-235b-a22b-thinking-2507",    # 🥉 DEEP: 10/10 score, thinking model (588 words, 3 citations, excellent reasoning)
    "qwen-3-235b-a22b-instruct-2507",    # ✅ SOLID: 10/10 score (455 words, 3 citations, 3.47s)
    "llama-4-maverick-17b-128e-instruct", # ✅ NEW: 8/10 score, Llama 4 with 128 experts (252 words, 3 citations)
    "qwen-3-32b",                         # ✅ BUDGET: 8/10 score (417 words, 3 citations)
    "llama-4-scout-17b-16e-instruct",    # ⚠️  Llama 4 Scout - needs citation improvement
    "llama3.1-8b",                        # ⚠️  Last resort: Small model
    # Excluded:
    # "qwen-3-coder-480b",                # ❌ Coder model, not optimized for legal reasoning (100 req/day limit)
]

# All available Cerebras models (for API model selection and manual switching)
# Ordered by quality score from comprehensive testing
CEREBRAS_ALL_MODELS = [
    "gpt-oss-120b",                       # 🏆 Champion: 10/10 score (65k context)
    "llama-3.3-70b",                      # 🥈 Fast: 8/10 score (65k context)
    "qwen-3-235b-a22b-thinking-2507",    # 🥉 Thinking: 10/10 score (65k context)
    "qwen-3-235b-a22b-instruct-2507",    # ✅ Solid: 10/10 score (65k context)
    "llama-4-maverick-17b-128e-instruct", # ✅ Llama 4 Maverick: 8/10 score (8k context)
    "qwen-3-32b",                         # ✅ Budget: 8/10 score (65k context)
    "llama-4-scout-17b-16e-instruct",    # ⚠️  Llama 4 Scout (8k context)
    "llama3.1-8b",                        # ⚠️  Small model (8k context)
    "qwen-3-coder-480b"                   # ❌ Coder model (limited 100 req/day, 65k context)
]

# Model fallback order for Ollama Cloud
# All 5 cloud models prioritized by capability (largest first)
OLLAMA_FALLBACK_ORDER = [
    "kimi-k2:1t-cloud",                      # 🏆 MASSIVE: 1 trillion parameters
    "deepseek-v3.1:671b-cloud",             # 🥈 HUGE: 671B parameters
    "qwen3-coder:480b-cloud",                # 🥉 LARGE: 480B coder model
    "gpt-oss:120b-cloud",                    # ✅ SOLID: 120B default
    "gpt-oss:20b-cloud",                     # ✅ FAST: 20B fallback
]

# All available Ollama Cloud models (for API model selection)
OLLAMA_ALL_MODELS = [
    "kimi-k2:1t-cloud",
    "deepseek-v3.1:671b-cloud",
    "qwen3-coder:480b-cloud",
    "gpt-oss:120b-cloud",
    "gpt-oss:20b-cloud"
]

# Thinking models that output <thinking> tags (need special JSON extraction)
THINKING_MODELS = [
    'qwen-3-235b-a22b-thinking-2507',
    # Add future thinking models here
]

# ============================================================================
# GENERATION LIMITS
# ============================================================================

MAX_SAMPLE_RETRIES = 3  # Maximum retry attempts per sample
MAX_MODEL_SWITCHES = 25  # Maximum model switches per batch (allow trying most models)
MAX_BATCH_TIMEOUT = 7200  # 2 hours in seconds (realistic for large batches)

# ============================================================================
# CIRCUIT BREAKER CONFIGURATION
# ============================================================================

CIRCUIT_BREAKER_FAILURE_THRESHOLD = 3  # Open circuit after 3 consecutive failures
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 300  # Try again after 5 minutes (300 seconds)
CIRCUIT_BREAKER_SUCCESS_THRESHOLD = 2  # Close circuit after 2 consecutive successes

# ============================================================================
# QUALITY THRESHOLDS & DIFFICULTY SPECIFICATIONS
# ============================================================================

# Research-based quality specifications per difficulty level
# Based on 2024-2025 legal LLM training best practices
DIFFICULTY_SPECS: Dict[str, Dict] = {
    'basic': {
        'min_words': 250,
        'min_citations': 2,
        'reasoning_steps': '4-5',
        'min_reasoning_chars': 200,
        'complexity': 'foundational legal concepts, straightforward application',
        'description': 'Entry-level legal principles for general understanding'
    },
    'intermediate': {
        'min_words': 350,
        'min_citations': 2,
        'reasoning_steps': '5-6',
        'min_reasoning_chars': 300,
        'complexity': 'multi-factor analysis, moderate complexity',
        'description': 'Practical application requiring balanced legal analysis'
    },
    'advanced': {
        'min_words': 450,
        'min_citations': 3,
        'reasoning_steps': '6-7',
        'min_reasoning_chars': 400,
        'complexity': 'complex scenarios, multiple legal doctrines',
        'description': 'Sophisticated analysis with competing considerations'
    },
    'expert': {
        'min_words': 500,
        'min_citations': 3,
        'reasoning_steps': '7-8',
        'min_reasoning_chars': 500,
        'complexity': 'edge cases, conflicting authorities, nuanced analysis',
        'description': 'Expert-level reasoning with cutting-edge legal issues'
    },
    'foundational': {  # Alias for 'basic' for compatibility
        'min_words': 250,
        'min_citations': 2,
        'reasoning_steps': '4-5',
        'min_reasoning_chars': 200,
        'complexity': 'foundational legal concepts, straightforward application',
        'description': 'Entry-level legal principles for general understanding'
    }
}

# Scenario variation patterns for diversity
SCENARIO_PATTERNS: List[str] = [
    "client_consultation",      # Client initial consultation question
    "procedural_tactical",      # Specific procedural/tactical advice
    "risk_assessment",          # Risk assessment/commercial advice
    "dispute_resolution",       # Dispute resolution options
    "compliance_preventive"     # Compliance/preventive guidance
]

# Sample types for different training purposes
SAMPLE_TYPES: Dict[str, Dict] = {
    'case_analysis': {
        'name': 'Case Analysis',
        'description': 'Analyze legal problems using case law and statutes',
        'focus': 'Problem-solving with legal reasoning',
        'example': 'A client asks about liability in a specific scenario'
    },
    'educational': {
        'name': 'Educational/Law Teaching',
        'description': 'Explain legal principles, rules, and doctrines',
        'focus': 'Teaching foundational legal concepts',
        'example': 'What is the doctrine of consideration in contract law?'
    },
    'client_interaction': {
        'name': 'Client Interaction',
        'description': 'Practical client communication and advice',
        'focus': 'Real-world lawyer-client scenarios',
        'example': 'How to advise a client on next steps in litigation'
    },
    'statutory_interpretation': {
        'name': 'Statutory Interpretation',
        'description': 'Explain and apply statutory provisions',
        'focus': 'Understanding legislation',
        'example': 'Explain Section 172 of the Companies Act 2006'
    },
    'balance': {
        'name': 'Balanced Mix',
        'description': 'Cycle through all sample types for variety',
        'focus': 'Diverse training data with all sample type structures',
        'example': 'Generates equal distribution of all 4 sample types'
    }
}

# Sample type cycle order for balanced generation
SAMPLE_TYPE_CYCLE = ['case_analysis', 'educational', 'client_interaction', 'statutory_interpretation']

# ============================================================================
# JURISDICTION CONFIGURATION - GLOBAL LEGAL PLATFORM
# ============================================================================

JURISDICTIONS: Dict[str, Dict] = {
    'uk': {
        'name': 'United Kingdom',
        'legal_system': 'Common Law',
        'citation_format': 'UK case citations and statutes',
        'enabled': True
    },
    'us': {
        'name': 'United States',
        'legal_system': 'Common Law (Federal & State)',
        'citation_format': 'US case citations and statutes',
        'enabled': True
    },
    'eu': {
        'name': 'European Union',
        'legal_system': 'Mixed (Civil Law & EU Regulations)',
        'citation_format': 'EU regulations, directives, and case law',
        'enabled': True
    },
    'international': {
        'name': 'International Law',
        'legal_system': 'Public International Law & Treaties',
        'citation_format': 'Treaties, conventions, and international court decisions',
        'enabled': True
    }
}

DEFAULT_JURISDICTION = 'uk'  # Default for backward compatibility

# ============================================================================
# LEGAL TOPICS - MULTI-JURISDICTION
# ============================================================================

# Format: (Practice Area, Subtopic, Difficulty, Jurisdiction)
# For backward compatibility, topics without jurisdiction default to 'uk'

TOPICS: List[Tuple[str, str, str]] = [
    # UK Legal Topics (Original - maintain backward compatibility)
    ("Contract Law", "Formation of Contracts", "intermediate"),
    ("Contract Law", "Breach of Contract", "intermediate"),
    ("Contract Law", "Remedies for Breach", "advanced"),
    ("Contract Law", "Terms and Conditions", "basic"),
    ("Contract Law", "Misrepresentation", "advanced"),
    ("Tort Law", "Professional Negligence", "advanced"),
    ("Tort Law", "Occupiers Liability", "intermediate"),
    ("Tort Law", "Vicarious Liability", "intermediate"),
    ("Tort Law", "Defamation", "advanced"),
    ("Tort Law", "Nuisance", "intermediate"),
    ("Company Law", "Directors Duties", "advanced"),
    ("Company Law", "Shareholder Rights", "intermediate"),
    ("Company Law", "Corporate Governance", "advanced"),
    ("Company Law", "Insolvency", "expert"),
    ("Company Law", "Company Formation", "basic"),
    ("Employment Law", "Discrimination", "intermediate"),
    ("Employment Law", "Wrongful Dismissal", "advanced"),
    ("Employment Law", "Employment Contracts", "basic"),
    ("Employment Law", "TUPE", "advanced"),
    ("Employment Law", "Redundancy", "intermediate"),
    ("Property Law", "Leasehold vs Freehold", "basic"),
    ("Property Law", "Land Registration", "intermediate"),
    ("Property Law", "Easements and Covenants", "advanced"),
    ("Property Law", "Mortgages", "intermediate"),
    ("Criminal Law", "Actus Reus and Mens Rea", "basic"),
    ("Criminal Law", "Murder and Manslaughter", "intermediate"),
    ("Criminal Law", "Criminal Defenses", "advanced"),
    ("Criminal Law", "Fraud", "advanced"),
    ("Trusts Law", "Constructive Trusts", "advanced"),
    ("Trusts Law", "Charitable Trusts", "intermediate"),
    ("Trusts Law", "Breach of Trust", "advanced"),
    ("Family Law", "Divorce Proceedings", "intermediate"),
    ("Family Law", "Child Custody", "intermediate"),
    ("Family Law", "Financial Settlements", "advanced"),
    ("Tax Law", "Capital Gains Tax", "advanced"),
    ("Tax Law", "VAT", "intermediate"),
    ("Tax Law", "Income Tax", "intermediate"),
    ("Administrative Law", "Judicial Review", "advanced"),
    ("Administrative Law", "Public Law Remedies", "expert"),
    ("Legal Ethics", "Conflicts of Interest", "intermediate"),
    ("Legal Ethics", "Client Confidentiality", "basic"),
    ("Legal Ethics", "Money Laundering", "advanced"),
]

# Jurisdiction-specific topic extensions
# These will be merged with the main TOPICS list when jurisdiction filtering is enabled
JURISDICTION_TOPICS: Dict[str, List[Tuple[str, str, str]]] = {
    'us': [
        ("Constitutional Law", "First Amendment Rights", "advanced"),
        ("Constitutional Law", "Due Process", "advanced"),
        ("Constitutional Law", "Equal Protection", "advanced"),
        ("Federal Civil Procedure", "Personal Jurisdiction", "intermediate"),
        ("Federal Civil Procedure", "Subject Matter Jurisdiction", "intermediate"),
        ("Torts", "Products Liability", "advanced"),
        ("Torts", "Intentional Torts", "intermediate"),
        ("Contracts", "UCC Article 2", "intermediate"),
        ("Contracts", "Statute of Frauds", "intermediate"),
        ("Criminal Law", "Fourth Amendment Search and Seizure", "advanced"),
        ("Criminal Law", "Miranda Rights", "intermediate"),
        ("Corporate Law", "Delaware Corporate Law", "expert"),
        ("Securities Law", "SEC Regulations", "expert"),
        ("Intellectual Property", "Patent Law", "expert"),
        ("Intellectual Property", "Copyright Fair Use", "advanced"),
    ],
    'eu': [
        ("EU Competition Law", "Article 101 TFEU", "advanced"),
        ("EU Competition Law", "Article 102 TFEU", "advanced"),
        ("Data Protection", "GDPR Compliance", "intermediate"),
        ("Data Protection", "Right to be Forgotten", "intermediate"),
        ("EU Consumer Law", "Consumer Rights Directive", "intermediate"),
        ("Free Movement", "Freedom of Establishment", "advanced"),
        ("Free Movement", "Free Movement of Goods", "intermediate"),
        ("State Aid", "State Aid Rules", "expert"),
        ("EU Employment Law", "Working Time Directive", "intermediate"),
        ("EU Contract Law", "Unfair Terms Directive", "intermediate"),
    ],
    'international': [
        ("International Trade", "WTO Agreements", "expert"),
        ("International Trade", "Trade Remedies", "advanced"),
        ("Human Rights", "ECHR", "advanced"),
        ("Human Rights", "UN Human Rights Conventions", "advanced"),
        ("International Criminal Law", "ICC Jurisdiction", "expert"),
        ("International Arbitration", "UNCITRAL Rules", "expert"),
        ("Maritime Law", "UNCLOS", "advanced"),
        ("Investment Law", "BIT Arbitration", "expert"),
    ]
}

# ============================================================================
# DATABASE
# ============================================================================

DATABASE_URI = 'sqlite:///batches.db'
