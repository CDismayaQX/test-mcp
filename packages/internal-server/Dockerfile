FROM python:3.13-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY . .
RUN uv sync --package prolook-mcp-internal --no-dev
EXPOSE 8001
CMD ["uv", "run", "--package", "prolook-mcp-internal", "python", "-m", "internal_server.main"]
