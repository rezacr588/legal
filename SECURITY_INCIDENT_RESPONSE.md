# 🚨 Security Incident Response - API Key Exposure

**Date**: October 18, 2025
**Severity**: CRITICAL
**Status**: Response in progress

---

## Summary

GitGuardian detected **real API keys** committed to GitHub in `.env.template`:

- **Google AI API Key**: `AIzaSyD6PBuUjlsIuguRqrzw-oFrJEFO4d7-bZk`
- **Mistral AI API Key**: `HO34S6unwF0N9oscFi925jKzwCt1KlPY`

**Affected Commit**: `60e7902fa4951eca60bd29bdfb08f0024d0032e7`
**Push Date**: October 18, 2025, 16:17:19 UTC
**Repository**: rezacr588/legal

---

## Immediate Actions (URGENT - Do in Order)

### 1. ✅ INVALIDATE EXPOSED API KEYS (DO THIS FIRST!)

**Google API Key** (URGENT):
1. Go to: https://console.cloud.google.com/apis/credentials
2. Project: `pac` (Project #: 885976075589)
3. Find key: `AIzaSyD6PBuUjlsIuguRqrzw-oFrJEFO4d7-bZk`
4. Click **"Delete"** or **"Regenerate"**
5. Create a new API key
6. Update the encrypted database with the new key via Provider Manager UI

**Mistral API Key** (URGENT):
1. Go to: https://console.mistral.ai/api-keys/
2. Find key: `HO34S6unwF0N9oscFi925jKzwCt1KlPY`
3. Click **"Revoke"**
4. Generate a new API key
5. Update the encrypted database with the new key via Provider Manager UI

**⏰ DO THIS WITHIN 1 HOUR OF RECEIVING THIS ALERT**

---

### 2. ✅ Fixed Template File (COMPLETED)

The `.env.template` file has been updated to remove real keys and replace them with placeholders.

**Commit**: `47d8c88` - "Security: Remove exposed API keys from .env.template"

**Changes**:
```diff
- GOOGLE_AI_API_KEY=AIzaSyD6PBuUjlsIuguRqrzw-oFrJEFO4d7-bZk
+ GOOGLE_AI_API_KEY=your_google_api_key_here

- MISTRAL_API_KEY=HO34S6unwF0N9oscFi925jKzwCt1KlPY
+ MISTRAL_API_KEY=your_mistral_api_key_here
```

---

### 3. ⏳ Remove Keys from Git History (REQUIRED)

The keys are still accessible in git history. You **MUST** remove them completely.

#### Option A: Using git-filter-branch (Recommended)

A cleanup script has been created at `/tmp/git_security_cleanup.sh`

**Run it**:
```bash
cd /Users/rezazeraat/Desktop/Data
bash /tmp/git_security_cleanup.sh
```

**What it does**:
1. Creates a backup branch
2. Removes `.env.template` from all commits in git history
3. Cleans up refs and garbage collection
4. Prepares for force push

#### Option B: Using BFG Repo-Cleaner (Alternative)

```bash
# Install BFG
brew install bfg

# Remove the file from history
bfg --delete-files .env.template

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

---

### 4. ⏳ Force Push to GitHub (REQUIRED)

**⚠️  WARNING**: This rewrites history. Anyone who has cloned the repo must re-clone!

```bash
# Review changes first
git log --oneline --all

# Force push to remote
git push origin --force --all
git push origin --force --tags
```

---

### 5. ⏳ Verify Cleanup

**Check GitHub**:
1. Go to: https://github.com/rezacr588/legal/commits/main
2. Verify commit `60e7902` no longer appears
3. Check `.env.template` in old commits - should be gone

**Search GitHub history**:
```bash
git log --all --full-history --source --pretty=format:"%H" | \
  xargs -I {} git show {}:.env.template 2>/dev/null | \
  grep -E "AIza|HO34S6"
```

Should return **no results** after cleanup.

---

## Why This Happened

**Root Cause**: Real API keys were accidentally placed in `.env.template` instead of `.env`

**Template files** (`.env.template`, `.env.example`) are **meant to be committed** to show structure, but should contain **only placeholders**, never real values.

**Correct pattern**:
```
✅ .env.template (committed) → Contains: your_api_key_here
✅ .env (gitignored)         → Contains: real_api_key_123456
```

**Incorrect pattern** (what happened):
```
❌ .env.template (committed) → Contains: real_api_key_123456
```

---

## Prevention Measures

### Already Implemented ✅

1. **Database-only API key storage** - All provider API keys now stored encrypted in PostgreSQL
2. **`.env` in `.gitignore`** - Environment file properly ignored
3. **Security comments** in `.env.template` - Warning against committing real keys
4. **Removed API keys from `config.py`** - No hardcoded secrets in code

### Additional Recommendations

1. **Pre-commit hooks** - Install git hooks to scan for secrets:
   ```bash
   # Install gitleaks
   brew install gitleaks

   # Add pre-commit hook
   cat > .git/hooks/pre-commit << 'EOF'
   #!/bin/sh
   gitleaks protect --staged --verbose
   EOF
   chmod +x .git/hooks/pre-commit
   ```

2. **GitHub Secret Scanning** - Enable push protection:
   - Go to: Repository Settings → Code security and analysis
   - Enable: "Push protection for secret scanning"

3. **Environment variable verification**:
   - Never echo/print API keys
   - Use masked output in logs
   - Audit any file named `*.template` or `*.example` before commits

4. **Regular audits**:
   ```bash
   # Check for potential secrets in staged changes
   git diff --cached | grep -E "(api_key|API_KEY|secret|password)" -i
   ```

---

## Impact Assessment

**Severity**: CRITICAL

**Potential Impact**:
- ✅ **Google AI API**: Could be used for unauthorized API calls → Rotate key immediately
- ✅ **Mistral AI API**: Could be used for unauthorized API calls → Rotate key immediately
- ✅ **Cost**: Potential unauthorized usage charges on your accounts
- ✅ **Rate Limits**: Could exhaust your API quotas
- ✅ **Data**: Attackers could generate/access content using your credentials

**Actual Impact** (after key rotation):
- ⏰ **0 hours exposed** (if rotated within 1 hour)
- ✅ **No charges** (monitor your billing dashboards)
- ✅ **No unauthorized usage** (check API logs)

---

## Timeline

| Time | Event |
|------|-------|
| 2025-10-18 16:17 UTC | Keys pushed to GitHub in commit `60e7902` |
| 2025-10-18 ~16:20 UTC | GitGuardian detected exposed keys |
| 2025-10-18 ~16:25 UTC | Response initiated, template file fixed |
| 2025-10-18 ~16:30 UTC | Commit `47d8c88` - Removed keys from template |
| **PENDING** | **User rotates Google API key** |
| **PENDING** | **User rotates Mistral API key** |
| **PENDING** | **Git history cleaned and force pushed** |

---

## Monitoring

**Check for unauthorized usage**:

1. **Google Cloud Console**:
   - Go to: APIs & Services → Credentials → Usage
   - Look for unusual spikes or unrecognized locations

2. **Mistral Console**:
   - Go to: https://console.mistral.ai/usage/
   - Check for unexpected API calls

3. **Billing Alerts**:
   - Set up billing alerts for both services
   - Monitor for unusual charges

---

## Lessons Learned

1. ✅ **Database-driven config is correct approach** - API keys stored encrypted, not in files
2. ⚠️  **Template files need careful review** - Always use placeholders in committed templates
3. ✅ **GitGuardian caught the issue** - Security monitoring works, but prevention is better
4. 📝 **Need pre-commit hooks** - Catch secrets before they're committed

---

## Status Checklist

- [x] Template file fixed with placeholders
- [x] Security fix committed (`47d8c88`)
- [ ] **URGENT: Google API key rotated**
- [ ] **URGENT: Mistral API key rotated**
- [ ] Git history cleaned (script ready at `/tmp/git_security_cleanup.sh`)
- [ ] Force pushed to GitHub
- [ ] Verified cleanup in GitHub
- [ ] Monitored for unauthorized usage (24-48 hours)
- [ ] Installed pre-commit hooks (gitleaks)
- [ ] Enabled GitHub push protection

---

## Questions?

Contact: rzeraat.tur@gmail.com
Documentation: This file (`SECURITY_INCIDENT_RESPONSE.md`)

**🔴 PRIORITY: Rotate the API keys immediately before proceeding with git history cleanup!**
