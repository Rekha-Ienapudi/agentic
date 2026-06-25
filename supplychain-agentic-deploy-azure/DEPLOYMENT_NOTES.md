# ACA deployment notes

This package keeps the React and backend business logic unchanged. The deployment files were updated so the app can start cleanly in Azure Container Apps with a backend Postgres sidecar.

## Files changed for auto seed

- `backend/init_db.py`
  - Waits for the database to accept connections before creating tables.
  - Creates tables if needed.
  - Checks whether the `suppliers` table has data.
  - Runs `backend/seed_scenarios.py` automatically only when the database is empty.

## Where to edit seed data

- Edit `backend/seed_scenarios.py` to change the demo suppliers, materials, shipments, orders, inventory, customers, plant risk profiles, or quantities.
- Do not put destructive seed logic directly in `backend/app.py`; `backend/app.py` already calls `init_db()` at startup.

## Files changed for ACA deployment

- `.github/workflows/build-and-push.yml`
  - Uses `az login --use-device-code`.
  - Uses workflow inputs for DB user, DB name, DB password, FastAPI secret key, and Azure OpenAI values.
  - Builds and pushes backend and frontend images to ACR.
  - Creates or updates the backend Container App.
  - Creates or updates the frontend Container App.
  - Deploys the backend and Postgres as two containers in the same backend Container App.

- `frontend/Dockerfile`
  - Uses the official Nginx template mechanism so runtime environment variables can be used.

- `frontend/nginx.conf`
  - Proxies browser calls from `/api/*` on the frontend app to the backend app inside the same Container Apps Environment.
  - This keeps the backend ingress internal and exposes only the frontend publicly.

## Important note about the Postgres sidecar

The Postgres sidecar is suitable for demos and development. Without persistent storage, sidecar data can be lost when the revision/container is replaced or restarted. The startup seed logic will repopulate an empty database automatically. For production, use managed PostgreSQL or configure persistent storage.
