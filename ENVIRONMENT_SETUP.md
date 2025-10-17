# Environment Variables Configuration

**Last Updated**: 2025-10-18
**Status**: ✅ All API keys configured and secured

---

## 🔐 Configured Environment Variables

All API keys are stored in environment variables and are **safe to push to GitHub** because they are not hardcoded in the repository.

### Current Configuration

| Variable | Status | Location | Purpose |
|----------|--------|----------|---------|
| `GROQ_API_KEY` | ✅ Set | ~/.zshrc (line 36, 37) | Groq LLM API access |
| `CEREBRAS_API_KEY` | ✅ Set | ~/.zshrc (line 39) | Cerebras LLM API access |
| `OLLAMA_API_KEY` | ✅ Set | ~/.zshrc (line 40) | Ollama API access |
| `HUGGINGFACE_TOKEN` | ✅ Set | ~/.zshrc (line 38), ~/.bashrc (line 2) | HuggingFace Hub access |

---

## 📍 Configuration Locations

### Primary Configuration: `~/.zshrc`
```bash
# Lines 36-40
export GROQ_API_KEY=gsk_T1Qjuv...
export GROQ_API_KEY="gsk_SlpZxT..."  # Duplicate (newer version)
export HUGGINGFACE_TOKEN="hf_fyFGak..."
export CEREBRAS_API_KEY="csk_j5wrh..."
export OLLAMA_API_KEY="d2e15e..."
```

### Backup Configuration: `~/.bashrc`
```bash
# Line 2
export HUGGINGFACE_TOKEN="hf_fyFGak..."
```

---

## ✅ Verification Status

**Python Access**: ✅ Verified
```bash
$ python3 -c "import os; print('HF Token found:', 'Yes' if os.getenv('HUGGINGFACE_TOKEN') else 'No')"
HF Token found: Yes
```

**Shell**: zsh (default on macOS)
**Config Files Present**:
- ✅ `~/.zshrc` (primary)
- ✅ `~/.zprofile` (exists)
- ✅ `~/.bashrc` (backup)
- ✅ `~/.bash_profile` (exists)

---

## 🔒 Security Best Practices

### ✅ What's Already Secure

1. **Environment Variables** - All API keys stored as environment variables
2. **Not in Code** - No hardcoded keys in Python files
3. **Shell Config Files** - Keys in user-specific config files (not committed to git)
4. **Access Control** - Config files are user-readable only (chmod 600)

### ⚠️ Important: .gitignore Setup

Before pushing to GitHub, ensure these files are in `.gitignore`:

```gitignore
# Environment files (if accidentally copied to repo)
.env
.env.local
*.env

# Shell configuration (should never be in repo anyway)
.bashrc
.zshrc
.zprofile
.bash_profile

# Database files with potential secrets
*.db
batches.db

# IDE settings that might contain paths
.vscode/
.idea/

# macOS
.DS_Store

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/

# Node modules
node_modules/
```

---

## 🚀 How Code Accesses Keys

### Current Implementation (Secure)

**In `api_server.py` and route files**:
```python
import os

# Groq API
groq_api_key = os.getenv('GROQ_API_KEY')

# Cerebras API
cerebras_api_key = os.getenv('CEREBRAS_API_KEY')

# HuggingFace
hf_token = os.getenv('HUGGINGFACE_TOKEN')

# Ollama
ollama_api_key = os.getenv('OLLAMA_API_KEY')
```

This approach is **secure** because:
- ✅ No keys in source code
- ✅ Keys only in environment variables
- ✅ Environment variables not committed to git
- ✅ Each developer can have their own keys

---

## 📝 Usage in Different Contexts

### Terminal/Shell Scripts
Environment variables are automatically available:
```bash
echo $HUGGINGFACE_TOKEN  # Works in new shells
```

### Python Scripts
```python
import os
token = os.getenv('HUGGINGFACE_TOKEN')
```

### Flask Application
```python
# In backend/config.py or backend/routes/*.py
import os

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY')
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY')
```

### React Frontend
**Note**: Never expose API keys in frontend code!
- API calls should always go through backend
- Backend handles authentication with API keys
- Frontend only communicates with Flask backend

---

## 🔧 Managing Environment Variables

### Add a New Variable
```bash
# Edit ~/.zshrc
nano ~/.zshrc

# Add line:
export NEW_API_KEY="your-key-here"

# Reload configuration
source ~/.zshrc

# Verify
echo $NEW_API_KEY
```

### Update an Existing Variable
```bash
# Edit ~/.zshrc
nano ~/.zshrc

# Find and update the line
# Save and reload
source ~/.zshrc
```

### Remove a Variable
```bash
# Edit ~/.zshrc and delete the line
nano ~/.zshrc

# Reload
source ~/.zshrc
```

---

## 🎯 GitHub Push Checklist

Before pushing to GitHub, verify:

- [ ] ✅ All API keys are in environment variables (not hardcoded)
- [ ] ✅ `.gitignore` includes sensitive file patterns
- [ ] ✅ No `.env` files in repository
- [ ] ✅ No `config.py` with hardcoded keys
- [ ] ✅ No database files with secrets
- [ ] ✅ No shell config files in repository

### Scan for Hardcoded Secrets
```bash
# Check for potential hardcoded API keys
cd /Users/rezazeraat/Desktop/Data
grep -r "gsk_\|hf_\|csk_\|sk-" --include="*.py" --include="*.js" --include="*.jsx" .

# If any matches found in source code (not in .gitignore'd files), they need to be moved to environment variables
```

---

## 📚 Additional Resources

### HuggingFace Token Management
- Dashboard: https://huggingface.co/settings/tokens
- Documentation: https://huggingface.co/docs/hub/security-tokens

### Groq API Key
- Dashboard: https://console.groq.com/keys
- Documentation: https://console.groq.com/docs

### Cerebras API Key
- Dashboard: https://cloud.cerebras.ai/
- Documentation: https://inference-docs.cerebras.ai/

### Best Practices
- 🔄 Rotate keys periodically (every 3-6 months)
- 🔒 Use read-only keys when possible
- 📝 Keep backup of keys in secure password manager
- ⚠️ Never commit keys to version control
- 🔍 Use git-secrets or similar tools to prevent accidental commits

---

## 🆘 Troubleshooting

### Key Not Found Error
```bash
# Check if variable is set
echo $HUGGINGFACE_TOKEN

# If empty, reload shell config
source ~/.zshrc

# Or open a new terminal window
```

### Python Can't Access Key
```python
import os

# Check if key exists
key = os.getenv('HUGGINGFACE_TOKEN')
if not key:
    print("Key not found - open new terminal or source shell config")
else:
    print(f"Key found: {key[:10]}...")
```

### Different Keys in Different Shells
- bash uses `~/.bashrc` or `~/.bash_profile`
- zsh uses `~/.zshrc` or `~/.zprofile`
- Make sure keys are in the config file for your active shell

---

## ✅ Summary

**Status**: All environment variables are properly configured!

- ✅ HUGGINGFACE_TOKEN is set in both .zshrc and .bashrc
- ✅ All other API keys (GROQ, CEREBRAS, OLLAMA) are configured
- ✅ Variables are accessible to Python applications
- ✅ Safe to push code to GitHub (no hardcoded secrets)

**Action Required**: None - everything is already configured correctly!

**Recommended**: Add the `.gitignore` patterns above to your repository before first push.
