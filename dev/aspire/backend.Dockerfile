FROM python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential libpq-dev libwebp-dev libsasl2-dev libldap2-dev libssl-dev \
    ffmpeg curl unzip \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv==0.13.8
ENV UV_PROJECT_ENVIRONMENT=/opt/mealie \
    UV_FROZEN=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NLTK_DATA=/nltk_data
WORKDIR /workspace
COPY pyproject.toml uv.lock ./
RUN uv sync --extra pgsql --group dev --no-install-project
COPY docker/setup_nltk_data.sh /tmp/setup_nltk_data.sh
RUN bash /tmp/setup_nltk_data.sh

CMD ["uv", "run", "--no-sync", "uvicorn", "mealie.app:app", "--host", "0.0.0.0", "--port", "9000", "--reload", "--reload-dir", "mealie"]
