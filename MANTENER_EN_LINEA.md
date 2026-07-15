# Cómo mantener GasRadar en línea (que no se caiga)

## Lo importante

| Dónde corre | ¿Se cae? | Qué hacer |
|-------------|----------|-----------|
| Tu PC (`iniciar.bat`) | Sí, si apagas la PC o cierras la ventana | Solo para pruebas en casa |
| **Render Free** | Se **duerme** ~15 min sin visitas | Keep-alive o plan de pago |
| **Render Starter** (~$7/mes) | Casi no se duerme | Mejor para “siempre online” |

**Regla:** la web pública debe vivir en **Render (o similar)**, no en tu computadora.

---

## Checklist semanal (2 minutos)

1. Abre tu URL: `https://TU-APP.onrender.com`
2. Si carga → OK  
3. Si tarda 30–60 s la primera vez → se despertó (normal en Free)
4. Si da error 502/404 → Dashboard Render → **Logs** → **Manual Deploy**

---

## 1) Render Free: que no se duerma tanto

El plan gratis apaga la app si nadie la usa. Soluciones:

### A) Keep-alive desde tu PC (gratis)

1. Copia `keep_alive.example.bat` → `keep_alive.bat`
2. Edita y pon tu URL real de Render
3. Déjalo corriendo (o en el Programador de tareas de Windows cada 10 min)

```bat
keep_alive.bat
```

Pings `/api/health` cada 10 minutos para “despertar” la app.

### B) Cron externo gratis

- https://cron-job.org  
- URL: `https://TU-APP.onrender.com/api/health`  
- Cada **10 minutos**

### C) Plan de pago (más estable)

Render → tu servicio → **Change plan** → Starter  
Ahí no se duerme por inactividad.

---

## 2) Después de cambiar código

```powershell
cd C:\Users\Alberto\gasolina_app
git add .
git commit -m "cambio"
git push origin main
```

Si Render no actualiza solo:  
Dashboard → **Manual Deploy** → **Deploy latest commit**

---

## 3) Si se cae: qué mirar

| Síntoma | Causa típica | Arreglo |
|---------|--------------|---------|
| Tarda 1 min y luego va | Free dormido | Keep-alive o esperar |
| 502 Bad Gateway | App crasheó | Logs → redeploy |
| Build failed | Error en código/deps | Logs de Build, arreglar y push |
| Precios raros / EIA | Rate limit | Normal; usa caché; key propia EIA |

---

## 4) Datos que se pierden en Free

En plan free, el disco es **efímero**:
- Reportes de precios (SQLite) pueden borrarse al redesplegar
- Más adelante: base de datos Postgres en Render (persistente)

---

## 5) Resumen “no se cae”

1. App solo en **Render**, no depende de tu PC  
2. Keep-alive cada 10 min **o** plan Starter  
3. Tras cambios: `git push`  
4. Si falla: Logs + Manual Deploy  
5. Guarda tu URL de Render en un lugar seguro  

Tu URL se ve en Render arriba del servicio (botón que abre el sitio).
