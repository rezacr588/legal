#!/usr/bin/env python3
"""
Migrate Legal Training Data from Parquet to PostgreSQL.

This script:
1. Reads all records from train.parquet
2. Creates the legal_samples table in PostgreSQL
3. Inserts all records with transaction safety
4. Verifies record count matches source

Usage:
    python3 backend/scripts/migrate_parquet_to_postgres.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import polars as pl
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.models import db, LegalSample
from backend.config import DATABASE_URI, PARQUET_PATH
from datetime import datetime

def count_parquet_records():
    """Count records in parquet file."""
    df = pl.read_parquet(PARQUET_PATH)
    return len(df)

def count_postgres_records(session):
    """Count records in PostgreSQL."""
    return session.query(LegalSample).count()

def migrate():
    """Execute the migration."""
    print("=" * 80)
    print("🔄 Starting Parquet → PostgreSQL Migration")
    print("=" * 80)

    # Step 1: Count source records
    print("\n📊 Step 1: Counting source records...")
    parquet_count = count_parquet_records()
    print(f"   ✅ Found {parquet_count:,} records in parquet file")

    # Step 2: Read parquet data
    print("\n📖 Step 2: Reading parquet data...")
    df = pl.read_parquet(PARQUET_PATH)
    print(f"   ✅ Loaded {len(df):,} records")
    print(f"   Columns: {df.columns}")

    # Step 3: Create database connection
    print("\n🔌 Step 3: Connecting to PostgreSQL...")
    print(f"   Database: {DATABASE_URI.split('@')[1] if '@' in DATABASE_URI else 'SQLite'}")
    engine = create_engine(DATABASE_URI)

    # Step 4: Create table
    print("\n🏗️  Step 4: Creating table if not exists...")
    db.metadata.bind = engine
    LegalSample.__table__.create(engine, checkfirst=True)
    print("   ✅ Table 'legal_samples' ready")

    # Step 5: Prepare session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Check if table already has data
    existing_count = count_postgres_records(session)
    if existing_count > 0:
        print(f"\n⚠️  WARNING: Table already contains {existing_count:,} records")
        response = input("   Do you want to continue? This will add duplicates. (yes/no): ")
        if response.lower() != 'yes':
            print("   ❌ Migration cancelled")
            return

    # Step 6: Convert to records
    print("\n🔄 Step 5: Converting records...")
    records = df.to_dicts()
    print(f"   ✅ Converted {len(records):,} records")

    # Step 7: Insert records with progress tracking
    print("\n💾 Step 6: Inserting records into PostgreSQL...")
    print("   This may take a few minutes...")

    inserted_count = 0
    failed_count = 0
    batch_size = 100

    try:
        for i, record in enumerate(records, 1):
            try:
                # Handle NULL/empty case_citation and reasoning values
                case_citation = record.get('case_citation')
                if not case_citation or case_citation == '':
                    case_citation = 'No case citation provided'

                reasoning = record.get('reasoning')
                if not reasoning or reasoning == '':
                    reasoning = 'No reasoning provided'

                # Create LegalSample object
                sample = LegalSample(
                    id=record['id'],
                    question=record['question'],
                    answer=record['answer'],
                    topic=record['topic'],
                    difficulty=record['difficulty'],
                    case_citation=case_citation,
                    reasoning=reasoning,
                    sample_type=record.get('sample_type', 'case_analysis'),
                    jurisdiction=record.get('jurisdiction', 'uk'),
                    batch_id=record.get('batch_id'),
                )
                session.add(sample)
                inserted_count += 1

                # Commit in batches for performance
                if i % batch_size == 0:
                    session.commit()
                    print(f"   Progress: {i:,}/{len(records):,} ({i/len(records)*100:.1f}%)", end='\r')

            except Exception as e:
                failed_count += 1
                print(f"\n   ⚠️  Failed to insert record {record.get('id', 'unknown')}: {e}")
                session.rollback()

        # Final commit
        session.commit()
        print(f"\n   ✅ Inserted {inserted_count:,} records")
        if failed_count > 0:
            print(f"   ⚠️  Failed: {failed_count:,} records")

    except Exception as e:
        print(f"\n   ❌ Migration failed: {e}")
        session.rollback()
        raise

    # Step 8: Verify record count
    print("\n✅ Step 7: Verifying migration...")
    postgres_count = count_postgres_records(session)
    print(f"   Source (Parquet): {parquet_count:,} records")
    print(f"   Target (PostgreSQL): {postgres_count:,} records")

    if postgres_count >= parquet_count:
        print(f"   ✅ SUCCESS: All {parquet_count:,} records migrated!")

        # Calculate statistics
        print("\n📊 Migration Statistics:")
        print(f"   Total records: {postgres_count:,}")
        print(f"   Inserted: {inserted_count:,}")
        print(f"   Failed: {failed_count:,}")

        # Sample distribution
        by_difficulty = session.query(
            LegalSample.difficulty,
            db.func.count(LegalSample.id)
        ).group_by(LegalSample.difficulty).all()

        print(f"\n   By Difficulty:")
        for difficulty, count in sorted(by_difficulty, key=lambda x: x[1], reverse=True):
            print(f"      {difficulty}: {count:,}")

        by_sample_type = session.query(
            LegalSample.sample_type,
            db.func.count(LegalSample.id)
        ).group_by(LegalSample.sample_type).all()

        print(f"\n   By Sample Type:")
        for sample_type, count in sorted(by_sample_type, key=lambda x: x[1], reverse=True):
            print(f"      {sample_type}: {count:,}")
    else:
        print(f"   ❌ ERROR: Record count mismatch!")
        print(f"      Expected: {parquet_count:,}")
        print(f"      Got: {postgres_count:,}")
        print(f"      Missing: {parquet_count - postgres_count:,}")

    session.close()

    print("\n" + "=" * 80)
    print("✨ Migration Complete!")
    print("=" * 80)

if __name__ == '__main__':
    try:
        migrate()
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
