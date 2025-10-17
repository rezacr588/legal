#!/usr/bin/env python3
"""
Add 5 new legal training samples to train.parquet
"""
import polars as pl
from pathlib import Path

PARQUET_PATH = Path("train.parquet")

# Define 5 new samples
new_samples = [
    {
        "id": "property_law_001",
        "question": "What are the essential requirements for acquiring title to land through adverse possession in England?",
        "answer": "To acquire title through adverse possession, the claimant must prove: 1) Actual possession - physical control of the land; 2) Exclusive possession - excluding the paper owner; 3) Adverse possession - without the owner's permission; 4) Continuous possession for the statutory period (10 years for registered land under Schedule 6 Land Registration Act 2002, 12 years for unregistered land under Limitation Act 1980). The claimant must also demonstrate factual possession and intention to possess (animus possidendi). For registered land, notice must be given to the registered proprietor who can object.",
        "topic": "Property Law - Adverse Possession",
        "difficulty": "advanced",
        "case_citation": "JA Pye (Oxford) Ltd v Graham [2002] UKHL 30; Schedule 6 Land Registration Act 2002",
        "reasoning": "Step 1: Identify the two types of land (registered vs unregistered) and applicable statutes. Step 2: List the elements of adverse possession - factual possession and intention to possess. Step 3: Explain the time requirements for each type. Step 4: Note the additional procedural requirements for registered land under LRA 2002."
    },
    {
        "id": "employment_law_042",
        "question": "When can an employee claim unfair dismissal and what remedies are available?",
        "answer": "Employees can claim unfair dismissal under Employment Rights Act 1996 s.94 if they have at least 2 years' continuous service (with exceptions for automatically unfair reasons like whistleblowing or pregnancy). The dismissal is unfair unless the employer shows: 1) A potentially fair reason (capability, conduct, redundancy, statutory restriction, or some other substantial reason); 2) The employer acted reasonably in treating it as sufficient reason. Remedies include: reinstatement (same job), re-engagement (similar job), or compensation (basic award + compensatory award capped at £115,115 or 52 weeks' pay, whichever is lower).",
        "topic": "Employment Law - Unfair Dismissal",
        "difficulty": "intermediate",
        "case_citation": "Employment Rights Act 1996 ss.94-134; British Home Stores v Burchell [1980] ICR 303",
        "reasoning": "Step 1: State the qualifying period for unfair dismissal claims. Step 2: List the potentially fair reasons for dismissal. Step 3: Apply the reasonableness test from Burchell. Step 4: Outline the three types of remedies and their limitations. Step 5: Note exceptions to the 2-year rule for automatically unfair dismissals."
    },
    {
        "id": "criminal_law_055",
        "question": "What are the elements of the offence of theft under the Theft Act 1968?",
        "answer": "Under s.1 Theft Act 1968, theft requires proof of five elements: 1) Dishonest appropriation - taking control of property belonging to another (s.3); 2) Property - must be property capable of being stolen (s.4); 3) Belonging to another - possession or control by another person (s.5); 4) Dishonesty - judged by the two-stage Ivey test: was the conduct dishonest by ordinary standards, and did the defendant know it would be regarded as dishonest? 5) Intention to permanently deprive - must intend to treat the property as their own (s.6). All five elements must be proven beyond reasonable doubt.",
        "topic": "Criminal Law - Theft",
        "difficulty": "basic",
        "case_citation": "Theft Act 1968 s.1; Ivey v Genting Casinos [2017] UKSC 67; R v Ghosh [1982] QB 1053 (overruled)",
        "reasoning": "Step 1: Break down s.1 Theft Act into its five constituent elements. Step 2: Define appropriation and explain s.3. Step 3: Clarify what constitutes property under s.4. Step 4: Explain 'belonging to another' under s.5. Step 5: Apply the modern Ivey test for dishonesty. Step 6: Define intention to permanently deprive under s.6."
    },
    {
        "id": "tort_law_028",
        "question": "What is the test for establishing a duty of care in negligence?",
        "answer": "The test for duty of care was established in Caparo Industries v Dickman [1990] and requires three elements: 1) Foreseeability - was the damage reasonably foreseeable? 2) Proximity - was there sufficient relationship of proximity between claimant and defendant? 3) Fair, just and reasonable - is it fair, just and reasonable to impose a duty in all the circumstances? Courts also consider policy factors and whether the situation falls within an established duty category. For novel situations, the incremental approach is used, developing the law step-by-step from established categories.",
        "topic": "Tort Law - Negligence - Duty of Care",
        "difficulty": "intermediate",
        "case_citation": "Caparo Industries plc v Dickman [1990] 2 AC 605; Donoghue v Stevenson [1932] AC 562",
        "reasoning": "Step 1: State the three-stage Caparo test. Step 2: Explain each element with examples. Step 3: Distinguish between established duty categories and novel situations. Step 4: Apply the incremental approach for new cases. Step 5: Consider policy factors that may negate a duty."
    },
    {
        "id": "trusts_law_015",
        "question": "What are the three certainties required to create a valid express trust?",
        "answer": "For a valid express trust, three certainties must be satisfied (Knight v Knight [1840]): 1) Certainty of intention - clear intention to create a trust, not merely a moral obligation or gift. Precatory words like 'hope' or 'wish' are insufficient unless context shows trust intended. 2) Certainty of subject matter - the trust property must be clearly identified. Both the trust assets and the beneficial interests must be certain. 3) Certainty of objects - the beneficiaries must be identifiable. For fixed trusts, the complete list test applies. For discretionary trusts, the is/is-not test applies (McPhail v Doulton [1971]). Failure of any certainty makes the trust void.",
        "topic": "Trusts Law - Three Certainties",
        "difficulty": "intermediate",
        "case_citation": "Knight v Knight (1840) 3 Beav 148; McPhail v Doulton [1971] AC 424; Palmer v Simmonds (1854) 2 Drew 221",
        "reasoning": "Step 1: Introduce the three certainties from Knight v Knight. Step 2: Explain certainty of intention with examples of sufficient and insufficient language. Step 3: Define certainty of subject matter for both property and beneficial interests. Step 4: Distinguish between the tests for certainty of objects in fixed vs discretionary trusts. Step 5: State the consequence of failing any certainty requirement."
    }
]

def main():
    print(f"Reading existing data from {PARQUET_PATH}...")
    df_existing = pl.read_parquet(PARQUET_PATH)

    print(f"Current row count: {len(df_existing)}")
    print(f"Current columns: {df_existing.columns}\n")

    # Create DataFrame from new samples
    df_new = pl.DataFrame(new_samples)

    print("New samples to add:")
    for i, sample in enumerate(new_samples, 1):
        print(f"{i}. ID: {sample['id']} | Topic: {sample['topic']} | Difficulty: {sample['difficulty']}")

    # Concatenate existing and new data
    df_combined = pl.concat([df_existing, df_new])

    print(f"\nNew total row count: {len(df_combined)}")

    # Save back to parquet
    df_combined.write_parquet(PARQUET_PATH, compression="zstd", statistics=True, use_pyarrow=False)

    print(f"✅ Successfully added {len(new_samples)} samples to {PARQUET_PATH}")

if __name__ == "__main__":
    main()
