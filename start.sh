#!/usr/bin/env bash
# Replit entrypoint — builds the frontend, installs backend deps, migrates the
# database, then starts FastAPI (which also serves the built frontend — see
# backend/app/main.py). Safe to re-run: the frontend build is idempotent and
# `alembic upgrade head` is additive/idempotent by design (see
# docs/ASSUMPTIONS_AND_TRADEOFFS.md).
set -e

# Always resolve paths relative to this script's own location (the project
# root), regardless of what working directory Replit invokes it from — this is
# what makes `cd frontend` below reliable even if the platform's deployment
# step runs from an unexpected cwd.
cd "$(dirname "$0")"

echo "== [1/4] Building frontend =="
cd frontend
npm install
# VITE_API_BASE="" -> same-origin requests, since FastAPI serves this build itself.
VITE_API_BASE="" npm run build
cd ..

echo "== [2/4] Installing backend dependencies =="
cd backend
pip install -r requirements.txt

echo "== [3/4] Running database migrations =="
alembic upgrade head

echo "== [4/4] Starting server on port 8080 =="
uvicorn app.main:app --host 0.0.0.0 --port 8080
