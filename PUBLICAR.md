# Cómo publicar GasRadar en internet

GasRadar **ya es una app web**. En tu PC solo la ves tú.
Para que cualquiera (y el GPS del teléfono) la abra, hay que **publicarla**.

---

## Opción A — Rápida (recomendado para empezar): Render.com gratis

### 1. Cuenta
- Entra a https://render.com y regístrate (GitHub)

### 2. Sube el código a GitHub

Si no tienes Git:
1. Instala **GitHub Desktop**: https://desktop.github.com  
2. File → Add Local Repository → elige `C:\Users\Alberto\gasolina_app`  
   (o Publish repository y arrastra la carpeta)

Con Git en PowerShell:

```powershell
cd C:\Users\Alberto\gasolina_app
git init
git add .
git commit -m "GasRadar MVP"
```

Crea un repo en GitHub llamado `gasradar` y:

```powershell
git remote add origin https://github.com/TU_USUARIO/gasradar.git
git branch -M main
git push -u origin main
```

### 3. Base de datos Postgres (importante — stats e IPs)

Sin Postgres, Render usa SQLite y **borra visitas/IPs en cada redeploy**.

**Opción recomendada — Blueprint:**
1. Dashboard → **New** → **Blueprint**
2. Repo `gasradar` (incluye `render.yaml`)
3. Crea el web service **y** la DB `gasradar-db`
4. `DATABASE_URL` se enlaza sola

**Si ya tienes el Web Service sin DB:**
1. **New** → **PostgreSQL** (plan Free) → nombre `gasradar-db`
2. Copia **Internal Database URL**
3. En el servicio **gasradar** → **Environment** → `DATABASE_URL` = esa URL
4. **Manual Deploy** → Clear build cache + deploy

Comprueba: `https://TU-URL/api/health` → `"backend":"postgres"`, `"persistent":true`.

### 4. Crear el servicio web en Render (manual, si no usas Blueprint)
1. Dashboard → **New** → **Web Service**
2. Conecta el repo `gasradar`
3. Configura:
   - **Name:** `gasradar`
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Plan: **Free**
5. Env: `DATABASE_URL` (paso 3), `STATS_KEY`, etc.
6. **Create Web Service**

### 5. Espera 2–5 minutos
Te dan una URL tipo:

```text
https://gasradar-xxxx.onrender.com
```

Esa es tu app **en internet** (con HTTPS → el GPS del teléfono puede funcionar).

---

## Opción B — Solo para pruebas (túnel desde tu PC)

Mientras `iniciar.bat` corre en la PC, un túnel da URL pública temporal.
(Requiere instalar Cloudflare Tunnel o ngrok.)

---

## Después de publicar

| Antes (solo casa) | Después (web pública) |
|-------------------|------------------------|
| `http://127.0.0.1:8787` | `https://gasradar-xxx.onrender.com` |
| `http://172.20.x.x:8787` | La misma URL en el teléfono con datos o WiFi |
| GPS a veces bloqueado | GPS suele funcionar (HTTPS) |

Comparte el enlace con quien quieras.

---

## Nota plan free de Render

- La app se “duerme” si nadie la usa ~15 min.
- El primer click puede tardar 30–60 s en despertar.
- Los reportes de precio en SQLite se pueden borrar al redesplegar (luego se puede poner base de datos real).
