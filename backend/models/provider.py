"""
Database models for LLM provider management.
Enables dynamic provider configuration without hardcoded values.
"""

from models.batch import db
from datetime import datetime
from cryptography.fernet import Fernet
import os
import json


class Provider(db.Model):
    """
    LLM Provider configuration model.
    Stores provider metadata, rate limits, and default settings.
    """
    __tablename__ = 'providers'

    # Primary identification
    id = db.Column(db.String(50), primary_key=True)  # groq, cerebras, ollama, google, mistral
    name = db.Column(db.String(100), nullable=False)  # Display name
    base_url = db.Column(db.String(500), nullable=False)  # API endpoint

    # Status
    enabled = db.Column(db.Boolean, default=True, nullable=False)

    # Rate limits
    requests_per_minute = db.Column(db.Integer, nullable=False)
    tokens_per_minute = db.Column(db.Integer, nullable=False)

    # Model references
    default_model_id = db.Column(db.String(100), nullable=False)
    champion_model_id = db.Column(db.String(100), nullable=False)

    # Provider-specific settings (JSON)
    extra_config = db.Column(db.Text, nullable=True)  # JSON string for provider-specific configs

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    models = db.relationship('Model', back_populates='provider', lazy='dynamic', cascade='all, delete-orphan')
    config = db.relationship('ProviderConfig', back_populates='provider', uselist=False, cascade='all, delete-orphan')

    # Indexes
    __table_args__ = (
        db.Index('idx_provider_enabled', 'enabled'),
    )

    def to_dict(self, include_models=False, include_config=False):
        """Convert provider to dictionary for API responses."""
        result = {
            'id': self.id,
            'name': self.name,
            'base_url': self.base_url,
            'enabled': self.enabled,
            'requests_per_minute': self.requests_per_minute,
            'tokens_per_minute': self.tokens_per_minute,
            'default_model': self.default_model_id,
            'champion_model': self.champion_model_id,
            'extra_config': json.loads(self.extra_config) if self.extra_config else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_models:
            result['models'] = [model.to_dict() for model in self.models.all()]

        if include_config and self.config:
            result['api_key_configured'] = self.config.has_api_key()

        return result

    def __repr__(self):
        return f"<Provider(id='{self.id}', name='{self.name}', enabled={self.enabled})>"


class Model(db.Model):
    """
    LLM Model configuration model.
    Stores model metadata and fallback order per provider.
    """
    __tablename__ = 'models'

    # Primary identification
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    display_name = db.Column(db.String(200), nullable=False)

    # Provider relationship
    provider_id = db.Column(db.String(50), db.ForeignKey('providers.id'), nullable=False)
    provider = db.relationship('Provider', back_populates='models')

    # Configuration
    fallback_priority = db.Column(db.Integer, nullable=False)  # Lower = higher priority (0 is champion)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    max_tokens = db.Column(db.Integer, default=4000, nullable=False)
    supports_json_schema = db.Column(db.Boolean, default=False, nullable=False)
    is_thinking_model = db.Column(db.Boolean, default=False, nullable=False)

    # Model-specific settings (JSON)
    extra_config = db.Column(db.Text, nullable=True)  # JSON string for model-specific configs

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        db.Index('idx_model_provider', 'provider_id'),
        db.Index('idx_model_enabled', 'enabled'),
        db.Index('idx_model_priority', 'fallback_priority'),
    )

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            'id': self.model_id,
            'display_name': self.display_name,
            'provider': self.provider_id,
            'fallback_priority': self.fallback_priority,
            'enabled': self.enabled,
            'max_tokens': self.max_tokens,
            'supports_json_schema': self.supports_json_schema,
            'is_thinking_model': self.is_thinking_model,
            'extra_config': json.loads(self.extra_config) if self.extra_config else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<Model(id='{self.model_id}', provider='{self.provider_id}', priority={self.fallback_priority})>"


class ProviderConfig(db.Model):
    """
    Secure storage for provider API keys and sensitive configuration.
    Uses Fernet symmetric encryption for API key storage.
    """
    __tablename__ = 'provider_configs'

    # Primary identification
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    provider_id = db.Column(db.String(50), db.ForeignKey('providers.id'), nullable=False, unique=True)
    provider = db.relationship('Provider', back_populates='config')

    # Encrypted API key
    api_key_encrypted = db.Column(db.Text, nullable=True)  # Fernet-encrypted API key

    # Additional sensitive config (encrypted JSON)
    config_encrypted = db.Column(db.Text, nullable=True)  # Fernet-encrypted config JSON

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Class-level encryption key (loaded from environment)
    _encryption_key = None

    @classmethod
    def get_encryption_key(cls):
        """Get or generate encryption key for Fernet."""
        if cls._encryption_key is None:
            # Try to load from environment
            key = os.getenv('ENCRYPTION_KEY')
            if not key:
                # Generate new key if not exists (DEVELOPMENT ONLY - use proper key management in production)
                key = Fernet.generate_key().decode()
                print(f"⚠️  Generated new encryption key. Set ENCRYPTION_KEY={key} in .env for persistence")
            cls._encryption_key = key.encode() if isinstance(key, str) else key
        return cls._encryption_key

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """Encrypt plaintext string using Fernet."""
        if not plaintext:
            return None
        f = Fernet(cls.get_encryption_key())
        return f.encrypt(plaintext.encode()).decode()

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """Decrypt ciphertext string using Fernet."""
        if not ciphertext:
            return None
        f = Fernet(cls.get_encryption_key())
        return f.decrypt(ciphertext.encode()).decode()

    def set_api_key(self, api_key: str):
        """Encrypt and store API key."""
        if api_key:
            self.api_key_encrypted = self.encrypt(api_key)

    def get_api_key(self) -> str:
        """Decrypt and return API key."""
        if self.api_key_encrypted:
            return self.decrypt(self.api_key_encrypted)
        return None

    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key_encrypted)

    def set_config(self, config: dict):
        """Encrypt and store config dictionary."""
        if config:
            config_json = json.dumps(config)
            self.config_encrypted = self.encrypt(config_json)

    def get_config(self) -> dict:
        """Decrypt and return config dictionary."""
        if self.config_encrypted:
            config_json = self.decrypt(self.config_encrypted)
            return json.loads(config_json) if config_json else {}
        return {}

    def to_dict(self, include_secrets=False):
        """Convert config to dictionary for API responses."""
        result = {
            'provider_id': self.provider_id,
            'has_api_key': self.has_api_key(),
            'has_config': bool(self.config_encrypted),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_secrets:
            result['api_key'] = self.get_api_key()
            result['config'] = self.get_config()

        return result

    def __repr__(self):
        return f"<ProviderConfig(provider='{self.provider_id}', has_key={self.has_api_key()})>"
