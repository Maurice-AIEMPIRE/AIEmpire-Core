# IPAD COMPUTE NODE SETUP

Turn your iPad (M1/M2/M4 recommended) into a local AI inference server that takes the load off your Mac.

## 1. Get the App (iPad)

Download **LLM Farm** (free) or **Layla** (€) from the App Store.
*Recommendation: LLM Farm because it's free and fast.*

## 2. Load a Model

In LLM Farm:

1. Go to "Models"
2. Download a GGUF model (e.g., `Llama-3-8B-Instruct-Q4_K_M.gguf` from HuggingFace).
3. ~4-5GB download.

## 3. Enable Server Mode

1. Ensure iPad and Mac are on the same WiFi (or connect via USB-C for speed).
2. Open the model chat in LLM Farm.
3. Tap "Settings" (gear icon).
4. **Enable "API Server"**.
5. Note the URL! usually `http://192.168.178.45:3000` or similar.

## 4. Connect to Kimi Bridge

On your Mac, when you run any script, just set the environment variable:

```bash
export IPAD_LLM_URL="http://YOUR_IPAD_IP:3000/v1"
```

Then run your swarm:

```bash
python3 kimi-swarm/universal_swarm.py --count 10
```

## How it works

- The system automatically checks `IPAD_LLM_URL` availability.
- If the iPad is ON and Server is ACTIVE -> **Tasks go to iPad**.
- If iPad is OFF or busy -> **Tasks go to Mac (Ollama)**.
- If Mac is overloaded -> **Tasks go to Cloud**.

## Pro Tip: USB Connection

Connect iPad via USB-C to Mac.
The iPad will show up as a network interface (check System Settings -> Network -> iPad USB).
The IP is usually fixed (e.g., `172.20.10.1`). Use that IP for ultra-low latency!
