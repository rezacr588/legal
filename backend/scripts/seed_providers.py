"""
Migration script to seed provider and model configurations from config.py to database.
Run this once to migrate from hardcoded config to database-driven configuration.

Usage:
    python -m scripts.seed_providers
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from models import db, Provider, Model, ProviderConfig
from config import (
    PROVIDERS,
    MODEL_FALLBACK_ORDER,
    CEREBRAS_FALLBACK_ORDER,
    OLLAMA_FALLBACK_ORDER,
    GOOGLE_FALLBACK_ORDER,
    MISTRAL_FALLBACK_ORDER,
    THINKING_MODELS
)
from app import app
import os


def get_fallback_order(provider_id: str) -> list:
    """Get fallback order for a provider."""
    fallback_orders = {
        'groq': MODEL_FALLBACK_ORDER,
        'cerebras': CEREBRAS_FALLBACK_ORDER,
        'ollama': OLLAMA_FALLBACK_ORDER,
        'google': GOOGLE_FALLBACK_ORDER,
        'mistral': MISTRAL_FALLBACK_ORDER
    }
    return fallback_orders.get(provider_id, [])


def get_model_display_name(model_id: str, provider_id: str) -> str:
    """Generate display name for model."""
    # Clean up model ID for display
    name = model_id.replace('-', ' ').replace('_', ' ').title()

    # Add emoji based on characteristics
    if 'thinking' in model_id.lower():
        name = f"🧠 {name}"
    elif 'large' in model_id.lower() or '70b' in model_id or '120b' in model_id:
        name = f"🏆 {name}"
    elif 'medium' in model_id.lower():
        name = f"🥈 {name}"
    elif 'small' in model_id.lower() or '8b' in model_id:
        name = f"⚡ {name}"
    elif 'code' in model_id.lower():
        name = f"💻 {name}"
    else:
        name = f"🔮 {name}"

    return name


def seed_providers():
    """Seed provider and model data from config.py."""
    with app.app_context():
        print("=" * 80)
        print("🌱 Seeding Provider and Model Database")
        print("=" * 80)

        # Check if already seeded
        existing_count = Provider.query.count()
        if existing_count > 0:
            print(f"⚠️  Database already contains {existing_count} providers.")
            response = input("Do you want to clear and re-seed? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("❌ Aborted.")
                return

            # Clear existing data
            print("🗑️  Clearing existing data...")
            ProviderConfig.query.delete()
            Model.query.delete()
            Provider.query.delete()
            db.session.commit()
            print("✅ Existing data cleared")

        print("\n📝 Creating providers and models from config.py...\n")

        total_providers = 0
        total_models = 0

        for provider_id, provider_config in PROVIDERS.items():
            # Skip if not enabled in config
            if not provider_config.get('enabled', False):
                print(f"⏭️  Skipping disabled provider: {provider_id}")
                continue

            print(f"🔧 Creating provider: {provider_id}")

            # Create Provider record
            provider = Provider(
                id=provider_id,
                name=provider_config.get('name', provider_id.title()),
                base_url=provider_config.get('base_url', ''),
                enabled=provider_config.get('enabled', True),
                requests_per_minute=provider_config.get('requests_per_minute', 60),
                tokens_per_minute=provider_config.get('tokens_per_minute', 10000),
                default_model_id=provider_config.get('default_model', ''),
                champion_model_id=provider_config.get('champion_model', ''),
                extra_config=None  # Can add provider-specific config here
            )
            db.session.add(provider)
            total_providers += 1

            # Create ProviderConfig with encrypted API key
            api_key = provider_config.get('api_key', '')
            if api_key:
                provider_config_record = ProviderConfig(
                    provider_id=provider_id
                )
                provider_config_record.set_api_key(api_key)
                db.session.add(provider_config_record)
                print(f"  🔐 API key encrypted and stored")
            else:
                print(f"  ⚠️  No API key found in config")

            # Create Model records
            fallback_order = get_fallback_order(provider_id)
            if not fallback_order:
                print(f"  ⚠️  No fallback order found for {provider_id}")
                continue

            print(f"  📋 Creating {len(fallback_order)} models:")
            for priority, model_id in enumerate(fallback_order):
                is_thinking = model_id in THINKING_MODELS
                is_champion = (priority == 0)

                model = Model(
                    model_id=model_id,
                    display_name=get_model_display_name(model_id, provider_id),
                    provider_id=provider_id,
                    fallback_priority=priority,
                    enabled=True,
                    max_tokens=4000,
                    supports_json_schema=(provider_id in ['cerebras', 'google']),
                    is_thinking_model=is_thinking,
                    extra_config=None
                )
                db.session.add(model)
                total_models += 1

                # Show priority indicator
                priority_emoji = "🏆" if is_champion else f"  {priority+1}."
                thinking_tag = " [THINKING]" if is_thinking else ""
                print(f"    {priority_emoji} {model_id}{thinking_tag}")

            print()  # Blank line between providers

        # Commit all changes
        db.session.commit()

        print("=" * 80)
        print(f"✅ Migration completed successfully!")
        print(f"   Providers created: {total_providers}")
        print(f"   Models created: {total_models}")
        print("=" * 80)

        # Verification
        print("\n🔍 Verification:")
        for provider in Provider.query.all():
            model_count = Model.query.filter_by(provider_id=provider.id).count()
            has_key = ProviderConfig.query.filter_by(provider_id=provider.id).first() is not None
            print(f"  ✓ {provider.id}: {model_count} models, API key: {'✅' if has_key else '❌'}")

        print("\n💡 Next steps:")
        print("  1. Update config.py to load from database (ConfigLoader)")
        print("  2. Update LLMProviderFactory to use database configs")
        print("  3. Test all providers with database-driven configuration")
        print()


if __name__ == '__main__':
    try:
        seed_providers()
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
