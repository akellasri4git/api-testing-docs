# LLM Configuration Guide

This guide explains how to configure different LLM providers for the SoapUI AI Documentation Generator.

## Quick Start

1. Copy `.env.example` to `.env` (or edit the existing `.env`)
2. Set `INPUT_PROJECT_FILE` to your SoapUI project
3. Set `LLM_PROVIDER` to your chosen provider
4. Configure provider-specific settings
5. Run the documentation generator

## Supported Providers

- **Ollama** (local, free)
- **OpenAI** (cloud, API key required)
- **Anthropic Claude** (cloud, API key required)
- **Groq** (cloud, API key required)
- **Azure OpenAI** (cloud, API key + endpoint required)

---

## Provider Setup Instructions

### 1. Ollama (Local - Default)

**Best for**: Free local inference, privacy, no API costs

**Setup**:
```bash
# Install Ollama
# Visit: https://ollama.ai

# Pull a model
ollama pull mistral:latest

# Start Ollama (runs automatically as service on most systems)
```

**Configuration** (.env):
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=mistral:latest
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

**Recommended Models**:
- `mistral:latest` (7B, good balance) ✓ Currently configured
- `llama3.1:8b` (8B, Meta's model)
- `phi3:latest` (3.8B, faster, smaller)
- `qwen2.5:14b` (14B, best quality, slower)

---

### 2. OpenAI

**Best for**: High quality, fast responses, GPT-4

**Setup**:
1. Get API key from https://platform.openai.com/api-keys
2. Update `.env`:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o
```

**Recommended Models**:
- `gpt-4o` (best quality, multimodal)
- `gpt-4o-mini` (faster, cheaper)
- `gpt-3.5-turbo` (cheapest)

**Pricing** (as of 2024):
- GPT-4o: $2.50/1M input tokens, $10/1M output tokens
- GPT-4o-mini: $0.15/1M input tokens, $0.60/1M output tokens

---

### 3. Anthropic Claude

**Best for**: Long context, detailed analysis, safety

**Setup**:
1. Get API key from https://console.anthropic.com/
2. Update `.env`:

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

**Recommended Models**:
- `claude-3-5-sonnet-20241022` (best balance) ✓ Recommended
- `claude-3-5-haiku-20241022` (faster, cheaper)
- `claude-3-opus-20240229` (highest quality)

**Pricing** (as of 2024):
- Claude 3.5 Sonnet: $3/1M input tokens, $15/1M output tokens
- Claude 3.5 Haiku: $0.80/1M input tokens, $4/1M output tokens

---

### 4. Groq

**Best for**: Ultra-fast inference, free tier available

**Setup**:
1. Get API key from https://console.groq.com/
2. Update `.env`:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_xxxxxxxxxxxxx
GROQ_MODEL=llama-3.1-70b-versatile
```

**Recommended Models**:
- `llama-3.1-70b-versatile` (best quality)
- `llama-3.1-8b-instant` (faster)
- `mixtral-8x7b-32768` (good balance)

**Pricing**: Free tier available with rate limits

---

### 5. Azure OpenAI

**Best for**: Enterprise deployments, compliance requirements

**Setup**:
1. Deploy a model in Azure OpenAI Studio
2. Update `.env`:

```env
LLM_PROVIDER=azure
AZURE_OPENAI_API_KEY=xxxxxxxxxxxxx
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

---

## Generation Parameters

These apply to all providers:

```env
LLM_TEMPERATURE=0.1      # Lower = more focused (0.0-1.0)
LLM_MAX_TOKENS=2000      # Maximum response length
LLM_TIMEOUT=600          # Request timeout in seconds
```

**Recommendations**:
- **Temperature**: Keep at `0.1` for consistent, factual documentation
- **Max Tokens**: `2000` is sufficient for most test case explanations
- **Timeout**: Increase if using slower models or experiencing timeouts

---

## Switching Between Providers

### Example 1: Switch from Ollama to OpenAI

Edit `.env`:
```env
# Change this line
LLM_PROVIDER=openai

# Add your API key
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o
```

### Example 2: Switch from OpenAI to Anthropic

Edit `.env`:
```env
# Change these lines
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### Example 3: Switch back to Ollama

Edit `.env`:
```env
# Change this line
LLM_PROVIDER=ollama

# Ensure Ollama is running
# No API key needed
```

---

## Testing Your Configuration

After configuring, test with:

```bash
# Run the pipeline
python -m scripts.xml_to_json_runner
python -m scripts.generate_docs
```

Check the logs for:
```
LLM initialized | provider=ollama | model=mistral:latest
```

---

## Troubleshooting

### "API key not found"
- Check that your `.env` file exists in the project root
- Verify the API key variable name matches the provider
- Ensure no extra spaces around the `=` sign

### "Model not found" (Ollama)
```bash
# List available models
ollama list

# Pull the model
ollama pull mistral:latest
```

### "Connection refused" (Ollama)
```bash
# Check if Ollama is running
curl http://127.0.0.1:11434/api/tags

# Start Ollama
ollama serve
```

### Rate Limits (Cloud Providers)
- OpenAI: 3 requests/min (free tier), 10,000/min (paid)
- Anthropic: 5 requests/min (free tier), higher for paid
- Groq: 30 requests/min (free tier)

**Solution**: Add delays between requests or upgrade tier

---

## Cost Estimation

For a typical SoapUI project with 10 test cases:

| Provider | Model | Estimated Cost |
|----------|-------|----------------|
| Ollama | mistral:latest | **FREE** (local) |
| OpenAI | gpt-4o-mini | ~$0.02-0.05 |
| OpenAI | gpt-4o | ~$0.15-0.30 |
| Anthropic | claude-3-5-haiku | ~$0.05-0.10 |
| Anthropic | claude-3-5-sonnet | ~$0.20-0.40 |
| Groq | llama-3.1-70b | **FREE** (with limits) |

**Note**: Costs vary based on test complexity and response length

---

## Best Practices

1. **Start with Ollama** for free local testing
2. **Use cloud providers** for production or when quality matters
3. **Monitor costs** when using cloud APIs
4. **Keep API keys secure** - never commit `.env` to git
5. **Use haiku/mini models** for cost optimization
6. **Cache results** to avoid re-generating documentation

---

## Security Notes

- `.env` file is gitignored by default
- Never share API keys publicly
- Rotate keys if exposed
- Use environment-specific keys for dev/staging/prod
- Consider using secret management tools for production

---

## Additional Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic Claude Documentation](https://docs.anthropic.com)
- [Groq Documentation](https://console.groq.com/docs)
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
