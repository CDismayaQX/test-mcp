FROM python:3.13-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY . .
RUN uv sync --package prolook-mcp-brand --no-dev
EXPOSE 8002
CMD ["uv", "run", "--package", "prolook-mcp-brand", "python", "-m", "brand_server.main"]
