"""
Vercel Python-runtime entrypoint.

Vercel's @vercel/python builder looks for a WSGI/ASGI `app` object inside
files under `api/`. This file just re-exports the real FastAPI app from
`app/main.py` so nothing about the actual application code has to change
for Vercel specifically.
"""
from app.main import app  # noqa: F401
