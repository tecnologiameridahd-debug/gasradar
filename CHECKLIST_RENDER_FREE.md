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

## Cron de precios (scrapers propios, gratis)

### 1) AAA diario — **todo USA** (recomendado para cron-job.org)
**1 solo link** (responde en segundos, no hace timeout):

```
https://gasradarapp.com/api/cron/aaa?key=gasradar2026
```

- Method: **GET**  
- Schedule: **Every day**  
- Timeout del cron: 30–60 s basta  
- Actualiza **50 estados** → cualquier ZIP USA  

Opcional (metros en background, sigue respondiendo rápido):

```
https://gasradarapp.com/api/cron/aaa?key=gasradar2026&full=1
```

Estado del job:

```
https://gasradarapp.com/api/cron/aaa/status?key=gasradar2026
```

### 2) EIA semanal — respaldo oficial

```
https://gasradarapp.com/api/eia/refresh?key=gasradar2026
```

- Schedule: **Every Monday**  

### ¿Cualquier ZIP de USA?

**Sí.** Flujo:

1. ZIP → ciudad + estado (ej. 90210 → Beverly Hills, CA)  
2. Si hay **metro AAA** (Los Angeles, Denver…) → ese promedio  
3. Si no → **promedio del estado AAA**  
4. + ajuste por marca (Shell, Costco…)  
5. Si alguien **reportó** → precio de esa bomba / zona

### Precios más rápidos

Reportes de usuarios en la app → reajustan la zona al instante.

### Nota

GasBuddy por bomba sigue bloqueado (Cloudflare). No usamos Apify de pago.

---

## Contacto en la app

- Contacto: contact@gasradarapp.com  

---

## En una frase

> **Free = funciona y es gratis. A veces se duerme. Archivos locales no son fiables. Usa siempre el link de Render.**
