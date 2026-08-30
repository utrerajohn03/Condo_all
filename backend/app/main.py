"""
Condominium Management Module - FastAPI entrypoint.
Run with: uvicorn app.main:app --reload
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth, maintenance, units, users, unit_residents, billing, payments, superadmin

app = FastAPI(
    title='Condominium Management Module (condo_)',
    description='ARGO Pre-Development Assessment vertical slice — Utrera',
    version='0.1.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(maintenance.router)
app.include_router(units.router)
app.include_router(users.router)
app.include_router(unit_residents.router)
app.include_router(billing.router)
app.include_router(payments.router)
app.include_router(superadmin.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=422, content={'detail': exc.errors()})


@app.get('/health', tags=['health'])
def health_check():
    return {'status': 'ok'}


# ── Optional: serve the built frontend from this same FastAPI app ──
# Only activates when frontend/dist actually exists (i.e. `npm run build` was run
# first) — a plain `uvicorn app.main:app --reload` in local dev with no dist/ folder
# behaves exactly as before this block was added. This exists specifically for
# single-URL hosting (e.g. Replit, where "module may contain multiple routes under
# the same domain" per the PhilCEB Hosting Guide). The Vercel deployment does NOT
# use this — frontend and backend stay as two separate Vercel projects there, so
# this block is simply inert (frontend/dist won't exist inside the backend's own
# deployment) and never interferes with that setup.
_FRONTEND_DIST = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'dist')

if os.path.isdir(_FRONTEND_DIST):
    _ASSETS_DIR = os.path.join(_FRONTEND_DIST, 'assets')
    if os.path.isdir(_ASSETS_DIR):
        app.mount('/assets', StaticFiles(directory=_ASSETS_DIR), name='frontend-assets')

    @app.get('/{full_path:path}', include_in_schema=False)
    async def serve_frontend(full_path: str):
        # Registered LAST, after every API router above, so /api/..., /docs,
        # /openapi.json, and /health all still match their real handlers first —
        # this only ever catches routes nothing else claimed (i.e. React Router's
        # client-side paths like /dashboard, /maintenance-requests, /units).
        return FileResponse(os.path.join(_FRONTEND_DIST, 'index.html'))
