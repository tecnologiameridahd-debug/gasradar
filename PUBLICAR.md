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

### 3. Crear el servicio web en Render
1. Dashboard → **New** → **Web Service**
2. Conecta el repo `gasradar`
3. Configura:
   - **Name:** `gasradar`
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Plan: **Free**
5. **Create Web Service**

### 4. Espera 2–5 minutos
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
