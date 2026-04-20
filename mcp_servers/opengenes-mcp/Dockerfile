FROM python:3.10-slim

WORKDIR /app

# Install curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (frozen)
RUN uv sync --frozen --no-install-project --no-dev

# Copy source
COPY src ./src
COPY README.md ./

# Create data directory and download files
RUN mkdir -p src/opengenes_mcp/data && \
    touch src/opengenes_mcp/data/__init__.py && \
    curl -L -o src/opengenes_mcp/data/open_genes.sqlite https://huggingface.co/datasets/longevity-genie/bio-mcp-data/resolve/main/opengenes/open_genes.sqlite && \
    curl -L -o src/opengenes_mcp/data/prompt.txt https://huggingface.co/datasets/longevity-genie/bio-mcp-data/resolve/main/opengenes/prompt.txt

# Install project
RUN uv sync --frozen --no-dev

# Set environment variables
ENV HOST=0.0.0.0

# Expose port
EXPOSE 8080

# Entrypoint
# The standalone cli_app_sse function reads from MCP_PORT and MCP_HOST env vars
# It does NOT accept CLI arguments for port/host due to function redefinition in server.py
CMD ["sh", "-c", "MCP_PORT=${PORT:-8080} MCP_HOST=0.0.0.0 uv run opengenes-mcp-sse"]
