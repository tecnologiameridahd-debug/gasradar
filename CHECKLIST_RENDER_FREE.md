# Checklist GasRadar en Render Free

Mini guía de lo que te afecta **día a día**.

---

## Cada día / al usarla

- [ ] Abre **solo** el link de Render: `https://….onrender.com`
- [ ] Si tarda ~1 minuto la primera vez → se estaba **despertando** (normal)
- [ ] Si no carga en 2–3 min → Dashboard Render → **Logs** → **Manual Deploy**

---

## Qué es normal (no te asustes)

| Lo que ves | Por qué |
|------------|---------|
| Primera visita lenta | 15 min sin uso → se duerme |
| Después va rápido | Ya está despierta |
| Apagas tu PC y sigue el link | Corre en Render, no en tu casa |
| Un precio reportado “desapareció” | Free **no guarda** bien SQLite al dormir/redeploy |

---

## Qué NO hacer (plan Free)

- No dejes `iniciar.bat` como “la app oficial” (solo pruebas en casa)
- No esperes precios reportados eternos sin base de datos de pago
- No hagas 50 deploys al día (gastas minutos de build del mes)

---

## Cada vez que cambias código

```powershell
cd C:\Users\Alberto\gasolina_app
git add .
git commit -m "descripcion del cambio"
git push origin main
```

- [ ] Espera el deploy en Render (o **Manual Deploy**)
- [ ] Prueba el link público

---

## Una vez al mes (2 minutos)

- [ ] Dashboard → **Billing** → **Monthly Included Usage**
- [ ] Revisa: horas Free (750), bandwidth, build minutes
- [ ] Si te llega email de límite → no ignores (pueden suspender Free)

---

## Si se “cae” de verdad

1. [ ] Abre el link otra vez y espera 1 min  
2. [ ] Render → servicio GasRadar → **Logs** (errores en rojo)  
3. [ ] **Manual Deploy** → Deploy latest commit  
4. [ ] Si dice suspended / out of hours → espera el **próximo mes** o sube de plan  

---

## Opcional: que se duerma menos

| Opción | Efecto |
|--------|--------|
| Nada | Se duerme a los 15 min sin visitas |
| cron-job.org cada 10 min a `/api/health` | Se despierta más a menudo (gasta horas Free) |
| Plan de pago del **Web Service** | Casi no se duerme |

---

## Cron cada hora: actualizar precios base (EIA gratis)

Sin Zyla. El cron llama a este **link** (GET):

```
https://gasradarapp.com/api/eia/refresh?key=TU_STATS_KEY
```

Alias igual:

```
https://gasradarapp.com/api/cron/eia?key=gasradar2026
```

### ¿Sirve para cualquier ZIP?

**Sí.** No hay un precio por cada ZIP; el flujo es:

1. Usuario pone **cualquier ZIP USA** (ej. 90210, 10001, 33101, 80903)  
2. GasRadar saca el **estado** (CA, NY, FL, CO…)  
3. Usa el **promedio EIA de ese estado** (actualizado por el cron)  
4. Ajusta un poco por **marca** (Shell más caro, Costco más barato…)  

El cron calienta **los 50 estados + promedio nacional**, así cualquier ZIP tiene base.

### En [cron-job.org](https://cron-job.org) (gratis)

1. Create cronjob  
2. **URL** = el link de arriba (cambia `TU_STATS_KEY` por tu `STATS_KEY` de Render; si no pusiste una, la default es `gasradar2026`)  
3. **Schedule** = every hour (`0 * * * *` o “every 1 hour”)  
4. Request method = **GET**  
5. Enable → Save  

Respuesta OK ejemplo: `{"ok":true,"cron":true,"ok_count":51,"covers":"all_us_zips",...}`  

También despierta la app en Render free (doble beneficio).

---

## Contacto en la app

- Contacto: contact@gasradarapp.com  

---

## En una frase

> **Free = funciona y es gratis. A veces se duerme. Archivos locales no son fiables. Usa siempre el link de Render.**
