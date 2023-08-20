FROM python:3.10.9-slim as base

LABEL org.opencontainers.image.source="https://github.com/null2264/SpeedrunBot"
LABEL org.opencontainers.image.description="A Discord Bot created for Obscure Minecraft Speedrunning Discord Server"
LABEL org.opencontainers.image.licenses=Unlicense

ENV PATH="/venv/bin:/root/.local/bin:${PATH}" \
    VIRTUAL_ENV="/venv"

# ---
FROM base as builder

WORKDIR /app

RUN apt-get update && apt-get install -y patch git
RUN pip install -U pip setuptools wheel
RUN pip install pdm
RUN python -m venv /venv

COPY pyproject.toml pdm.lock LICENSE ./
ADD src/ ./src
RUN pdm sync --prod --no-editable

# ---
FROM base as final

WORKDIR /app

COPY --from=builder /venv /venv
COPY --from=builder /app/src/ /app/src/

CMD ["python", "main.py"]
