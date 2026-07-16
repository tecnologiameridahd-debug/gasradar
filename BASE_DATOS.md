# GasRadar — Base de datos en la nube (gratis)

## Por qué

En el plan **free de Render**, el disco se borra al redeploy o al “dormir”.
Si guardas reportes solo en SQLite local, **se pierden**.

Con **Postgres gratis (Neon)** + variable `DATABASE_URL`, los reportes **quedan guardados**.

| Sitio | Qué usa |
|-------|---------|
| Tu PC sin configurar | SQLite `data/prices.db` (pruebas) |
| Internet con `DATABASE_URL` | Postgres en la nube (producción) |

---

## Plan en 3 pasos (recomendado: Neon)

### Paso 1 — Crear la base (Neon, gratis)

1. Entra a **https://neon.tech** y regístrate (GitHub o email).
2. **Create a project**
   - Name: `gasradar`
   - Region: la más cercana a tu Render (ej. US East o US West)
3. Cuando abra el proyecto, busca **Connection string** / **Connection details**.
4. Copia la URL que empieza así:

```text
postgresql://usuario:password@ep-xxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

Esa es tu `DATABASE_URL`. **No la compartas en público.**

> También sirve Supabase (Settings → Database → Connection string URI).

---

### Paso 2 — Pegarla en Render

1. Entra a **https://dashboard.render.com**
2. Abre tu servicio web **gasradar**
3. Menú **Environment** (Variables de entorno)
4. **Add Environment Variable**
   - Key: `DATABASE_URL`
   - Value: (pega la URL de Neon, toda en una línea)
5. **Save Changes**
6. Render hará **redeploy** solo (o Manual Deploy → Deploy latest commit)

Espera 2–5 minutos hasta que diga **Live**.

---

### Paso 3 — Comprobar

Abre en el navegador:

```text
https://gasradarapp.com/api/health
```

Debes ver algo así:

```json
{
  "ok": true,
  "version": "0.2.2",
  "db": {
    "backend": "postgres",
    "persistent": true,
    "ok": true,
    "reports_count": 0,
    "note": "Postgres en la nube — reportes se conservan."
  }
}
```

Si `backend` dice `"sqlite"`, **no** se pegó bien `DATABASE_URL` en Render.

Prueba real:

1. Abre https://gasradarapp.com  
2. Busca un ZIP  
3. **Reportar** un precio en una estación  
4. Recarga: debe salir badge **reportado**  
5. Vuelve a mirar `/api/health` → `reports_count` sube  

---

## En tu PC (opcional, misma nube)

PowerShell:

```powershell
cd C:\Users\Alberto\gasolina_app
$env:DATABASE_URL = "postgresql://...tu-url-de-neon..."
.\iniciar.bat
```

Así pruebas en local contra la misma base que producción.

Sin `DATABASE_URL`, usa el archivo local `data/prices.db`.

---

## Si algo falla

| Problema | Qué hacer |
|----------|-----------|
| `db.ok: false` + error SSL | Asegúrate que la URL tenga `?sslmode=require` |
| Sigue en `sqlite` en health | Revisa nombre exacto: `DATABASE_URL` en Render |
| Deploy falla por psycopg | Espera a que el commit con `requirements.txt` esté desplegado |
| Neon “suspende” por inactividad | Se despierta sola al primer uso (1–2 s) |

---

## Resumen

```text
Neon (crear DB gratis)
   → copiar DATABASE_URL
   → Render → Environment → pegar
   → esperar Live
   → /api/health → backend: postgres
```

El código de GasRadar **ya está listo** para esto (v0.2.2+).
Solo falta que tú crees la base y pegues la URL en Render.
