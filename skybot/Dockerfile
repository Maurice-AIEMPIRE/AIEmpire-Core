FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY skybot/requirements.txt /app/skybot/requirements.txt
RUN pip install --no-cache-dir -r skybot/requirements.txt

# Copy skybot package
COPY skybot/ /app/skybot/

# Create workspace directory
RUN mkdir -p /app/skybot_workspace/websites

# Run as non-root user
RUN useradd -m -r skybot && chown -R skybot:skybot /app
USER skybot

CMD ["python3", "-m", "skybot.bot"]
