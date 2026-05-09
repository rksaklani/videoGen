# videoGen — Frontend

**React 18 + Vite + Redux Toolkit** UI for **videoGen**: marketing pages and a **`/dashboard`** hub for text-to-video, audio-to-video, video reference, dialogue, saved avatars, and billing hooks. Data layer: **RTK Query** in **`src/store/api.js`**.

→ **Full stack:** [`../README.md`](../README.md)  
→ **Backend API:** [`../Backend/README.md`](../Backend/README.md)

---

## Quick start

```bash
cd Frontend
cp .env.example .env
npm ci
npm run dev
```

Open **http://localhost:3000** · API default origin: **http://localhost:8000** (`VITE_API_URL`).

---

## Environment

Create **`.env`** from **`.env.example`**:

| Variable | Purpose |
|----------|---------|
| **`VITE_API_URL`** | Backend base URL **without** `/api/v1` |
| **`VITE_APP_NAME`** | Optional branding string (e.g. **videoGen**) |
| **`VITE_APP_VERSION`** | Optional version string |

Origins must be allowed under **`cors.origins`** in **`Backend/config.yaml`**.

---

## Scripts

| Command | Description |
|---------|--------------|
| **`npm ci`** | Install from lockfile (CI/production) |
| **`npm run dev`** | Dev server + HMR |
| **`npm run build`** | Production build → **`dist/`** |
| **`npm run preview`** | Preview production bundle |

---

## App routes

- **`/`** — Landing / marketing  
- **`/dashboard`** — Hub (authenticated flow per your deployment)  
- **`/dashboard/text-to-video`**, **`audio-to-video`**, **`video-reference`**, **`dialogue`**, **`my-avatars`**, etc.

API calls go through **`src/store/api.js`** and related slices under **`src/store/`**.
