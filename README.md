# Simple Social

A small social feed: JWT auth, ImageKit media uploads, and a Streamlit UI.

## Run

1. Copy `.env` values for `IMAGEKIT_PRIVATE_KEY` and `IMAGEKIT_URL_ENDPOINT`.
2. Start the API: `py main.py` (http://localhost:8000). Interactive docs: http://localhost:8000/docs
3. Start the UI: `streamlit run frontend.py`

Auth routes live under `/auth` and `/auth/jwt`. Posts: `POST /upload`, `GET /feed`, `DELETE /post/{post_id}`.
