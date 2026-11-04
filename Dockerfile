FROM python:3.12-slim

LABEL org.opencontainers.image.title="Karma-Analyser" \
      org.opencontainers.image.description="Karma-Analyser Discord Bot built with discord.py" \
      org.opencontainers.image.source="https://github.com/Lachlan-Hollis/karma-analyser"

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Copy source code in layers
COPY requirements.txt .
COPY bot.py .
COPY deductions.json .
COPY petition.gif .
COPY tools.py .
COPY utils.py .
COPY askbot.py .
COPY cogs/ ./cogs/

# Install Deno runtime
RUN apt update && \
    apt install -y \
    	unzip \
    	curl && \
    curl -L -o deno.zip https://github.com/denoland/deno/releases/download/v2.7.1/deno-x86_64-unknown-linux-gnu.zip && \
	unzip deno.zip -d /usr/bin && \
    rm deno.zip && \
    rm -rf /var/lib/apt/lists/*

# discord.py voice client requirements
RUN apt update && \
    apt install -y \
    	libffi-dev \
    	libnacl-dev \
    	python3-dev \
    	ffmpeg && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "bot.py", "--health-check"]