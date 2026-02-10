# 🔐 SECURITY NOTES - 500K Swarm System

## API Key Management

### ⚠️ CRITICAL: Never Commit API Keys

The 500K swarm system has been designed with security in mind:

### ✅ Security Improvements in `swarm_500k.py`

```python
# SECURE: Requires environment variable
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY")
if not MOONSHOT_API_KEY:
    raise ValueError("MOONSHOT_API_KEY environment variable must be set")
```

**Benefits:**
- No hardcoded API keys in code
- Keys stored in environment variables
- Fails fast if key is missing
- Safe to commit to git

### How to Set Environment Variables

#### Linux/macOS (bash/zsh)

```bash
# Temporary (current session)
export MOONSHOT_API_KEY="your-actual-key-here"
export ANTHROPIC_API_KEY="your-claude-key-here"  # Optional

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export MOONSHOT_API_KEY="your-actual-key-here"' >> ~/.bashrc
source ~/.bashrc
```

#### Windows (PowerShell)

```powershell
# Temporary (current session)
$env:MOONSHOT_API_KEY="your-actual-key-here"
$env:ANTHROPIC_API_KEY="your-claude-key-here"  # Optional

# Permanent (system environment variables)
[System.Environment]::SetEnvironmentVariable("MOONSHOT_API_KEY", "your-actual-key-here", "User")
```

#### Using .env File (Development)

Create a `.env` file (add to .gitignore!):

```bash
MOONSHOT_API_KEY=your-actual-key-here
ANTHROPIC_API_KEY=your-claude-key-here
```

Load with python-dotenv:

```python
from dotenv import load_dotenv
load_dotenv()
# Now environment variables are available
```

---

## Error Handling Security

### ✅ Specific Exception Handling

The system uses specific exception types instead of bare `except:` clauses:

```python
# SECURE: Specific exceptions
except (json.JSONDecodeError, IndexError, KeyError) as e:
    # Handle parsing errors specifically
    print(f"Parse error: {e}")
```

**Benefits:**
- Doesn't catch system exits (Ctrl+C)
- Doesn't hide unexpected errors
- Easier debugging
- Better error messages

---

## Rate Limiting & API Abuse Prevention

### Built-in Protections

1. **Concurrent Worker Limits**
   - Max 500 concurrent requests
   - Prevents overwhelming the API
   - Respects rate limits

2. **Exponential Backoff**
   ```python
   wait = (2 ** attempt) + random.uniform(0, 1)
   ```
   - Automatic retry with increasing delays
   - Prevents hammering failed endpoints

3. **Budget Controls**
   - Auto-stops at 95% of budget
   - Prevents runaway costs
   - Configurable per-run

4. **Request Timeouts**
   - 60-second timeout per request
   - Prevents hanging connections
   - Clean resource management

---

## Data Security

### Output File Security

- All outputs saved locally
- No automatic uploads
- Review before sharing
- Sensitive data in JSON format

### Recommendations

1. **Review Outputs**
   - Check generated content before using
   - Verify no sensitive data leaked
   - Validate quality before distribution

2. **Secure Storage**
   - Keep `output_500k/` in .gitignore
   - Don't commit generated data
   - Use encryption for sensitive results

3. **Access Control**
   - Restrict access to output directories
   - Use appropriate file permissions
   - Consider encryption at rest

---

## Network Security

### HTTPS Only

All API calls use HTTPS:
- Moonshot API: `https://api.moonshot.ai/v1/`
- Anthropic API: `https://api.anthropic.com/v1/`

### No Data Leakage

- API keys sent in headers only
- No keys in URL parameters
- No logging of sensitive data
- Clean error messages

---

## Comparison: Old vs New

### ❌ Old Code (Less Secure)

```python
# Hardcoded key in code
MOONSHOT_API_KEY = "sk-e57Q5aDfcpXpHkYfgeWCU3xjuqf2ZPoYxhuRH0kEZXGBeoMF"

# Bare exception handling
try:
    do_something()
except:
    pass  # Silent failure

# No specific error types
except Exception as e:
    pass  # Catches everything
```

**Problems:**
- API key exposed in code
- Keys committed to git
- Silent failures hide bugs
- Catches system exits
- No debugging information

### ✅ New Code (Secure)

```python
# Environment variable required
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY")
if not MOONSHOT_API_KEY:
    raise ValueError("MOONSHOT_API_KEY environment variable must be set")

# Specific exception handling
try:
    do_something()
except json.JSONDecodeError as e:
    print(f"Parse error: {e}")
    # Appropriate fallback

# Network-specific handling
except (aiohttp.ClientError, asyncio.TimeoutError) as e:
    print(f"Network error: {type(e).__name__}: {str(e)[:100]}")
    # Appropriate fallback
```

**Benefits:**
- No hardcoded secrets
- Safe to commit
- Clear error messages
- Doesn't hide bugs
- Proper error handling
- Better debugging

---

## Security Checklist

Before running in production:

- [ ] API keys set as environment variables
- [ ] No hardcoded secrets in code
- [ ] `.gitignore` includes `output_500k/`
- [ ] Budget limits configured appropriately
- [ ] Output directory permissions set correctly
- [ ] Test run completed successfully
- [ ] Error handling verified
- [ ] Rate limiting tested
- [ ] Timeout behavior confirmed
- [ ] Output data reviewed for sensitivity

---

## Incident Response

### If API Key is Compromised

1. **Immediately Revoke** the compromised key
2. **Generate New Key** from provider dashboard
3. **Update Environment Variable** with new key
4. **Review Usage Logs** for unauthorized activity
5. **Check Git History** - if committed, consider key rotation
6. **Notify Team** if applicable

### If Unauthorized Charges Occur

1. **Stop All Running Swarms** (Ctrl+C or kill process)
2. **Check `stats_500k_*.json`** for cost tracking
3. **Review API Provider Dashboard** for usage
4. **Revoke API Keys** if suspicious activity
5. **Contact API Provider Support** if needed

---

## Best Practices

### Development

1. **Use Test Mode** (`--test`) for development
2. **Start Small** (100-1000 tasks) before scaling
3. **Monitor Costs** in real-time during runs
4. **Review Outputs** frequently
5. **Test Error Handling** with invalid inputs

### Production

1. **Set Conservative Budgets** initially
2. **Monitor Performance** metrics
3. **Review Claude Insights** for optimization
4. **Scale Gradually** based on results
5. **Keep Backups** of valuable outputs

### Team Environment

1. **Individual API Keys** for each team member
2. **Shared Budget Limits** agreed upon
3. **Output Review Process** before sharing
4. **Incident Response Plan** documented
5. **Regular Security Audits** scheduled

---

## Further Reading

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [GitHub: Managing Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)

---

**Remember: Security is not a one-time setup, it's an ongoing practice.**

*Last Updated: 2026-02-08*
*Security Review: Passed*
