# Official multi-platform Python image, pinned to an immutable manifest digest.
FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MPLBACKEND=Agg

# Git supports publication-security tests; libgomp supports CPU tree ensembles.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 app

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app . .
RUN chown app:app /app
USER app

# Do not copy host Git metadata. Index only the packaged files so the same
# tracked-file publication checks run inside the container (no commit/history).
RUN git init -q && git add .
CMD ["./run.sh", "--offline"]
