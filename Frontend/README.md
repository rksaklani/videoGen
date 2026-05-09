# Avatar Studio — Frontend

React 18 + Vite + Redux Toolkit dashboard for **Avatar Studio**. Talks to the Backend over **`VITE_API_URL`**.

→ **Full stack guide:** **[`../README.md`](../README.md)**  
→ **Backend API:** **`../Backend/README.md`**

---

## Quick start

```bash
cd Frontend
cp .env.example .env
npm ci
npm run dev
```

Open **http://localhost:3000** (API default: **http://localhost:8000**).

---

## Environment

Create **`.env`** from **`.env.example`**:

| Variable | Purpose |
|----------|---------|
| **`VITE_API_URL`** | Backend origin **without** `/api/v1` (e.g. `http://localhost:8000`) |
| **`VITE_APP_NAME`** | Optional display name |
| **`VITE_APP_VERSION`** | Optional version string |

Must match **`cors.origins`** in **`Backend/config.yaml`** if not same-origin.

---

## Scripts

| Command | Description |
|---------|--------------|
| **`npm ci`** | Install from **`package-lock.json`** (preferred in CI/production) |
| **`npm run dev`** | Dev server with HMR |
| **`npm run build`** | Production bundle → **`dist/`** |
| **`npm run preview`** | Preview production build |

---

## App routes

- **`/`** — Marketing site · **`/dashboard`** — App hub (protected flow in your deployment)
- **`/dashboard/text-to-video`** · **`/dashboard/audio-to-video`** · **`/dashboard/video-reference`** · **`/dashboard/dialogue`** · **`/dashboard/my-avatars`**, etc.

API layer: **`src/store/api.js`** (RTK Query).
