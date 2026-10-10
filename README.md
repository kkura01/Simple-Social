# Simple Social

A small social feed: JWT auth, ImageKit media uploads, and a Streamlit UI.

## Setup

Install [uv](https://docs.astral.sh/uv/), then from the repo root:

```bash
uv sync
```

Copy `.env` values for `IMAGEKIT_PRIVATE_KEY` and `IMAGEKIT_URL_ENDPOINT`.

## Run

API (http://localhost:8000, docs at http://localhost:8000/docs):

```bash
uv run python main.py
```

UI:

```bash
uv run streamlit run frontend.py
```

Auth routes live under `/auth` and `/auth/jwt`. Posts: `POST /upload`, `GET /feed`, `DELETE /post/{post_id}`.
