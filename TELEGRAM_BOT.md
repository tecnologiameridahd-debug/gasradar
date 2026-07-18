# Bot Telegram GasRadar — @GasRadar_bot

Link: https://t.me/GasRadar_bot

## Qué hace

- Usuario elige **ZIP** y **precio tope**
- El bot avisa (máx. 1 vez al día) si el más barato baja de ese tope
- También: `/ahora` precios al momento

## Comandos

| Comando | Uso |
|---------|-----|
| `/start` | Ayuda |
| `/zona 80903` | Zona (ZIP USA) |
| `/alerta 3.50` | Tope de precio |
| `/fuel regular` | Combustible |
| `/radio 5` | Millas |
| `/ahora` | Precios ya |
| `/mis` | Tu config |
| `/pausa` / `/activar` | Silencio / reanudar |
| `/borrar` | Quitar alerta |
| `/es` / `/en` | Idioma |

## Variables en Render (Environment)

**Nunca subas el token a GitHub.**

```
TELEGRAM_BOT_TOKEN=***tu_token_de_BotFather***
ALERTS_SECRET=una_clave_larga_secreta
PUBLIC_APP_URL=https://gasradarapp.com
```

Opcional: si ya tienes `STATS_KEY`, se puede usar como clave del cron (si no hay `ALERTS_SECRET`).

## Tras el deploy

1. Pon las variables en Render → Environment → Save → redeploy  

2. **Webhook automático:** al arrancar la app se registra solo  
   (`AUTO_TELEGRAM_WEBHOOK=1` por defecto).  
   No hace falta el link de setup si el token está bien.

3. Comprueba sin clave secreta:

```
https://gasradarapp.com/api/health
```

Mira el bloque `"telegram"`:
- `token: true`
- `username: GasRadar_bot`
- `webhook_ok: true`
- `last_error: null`

4. (Opcional) Setup manual si falló el auto:

```
https://gasradarapp.com/api/telegram/setup?key=TU_ALERTS_SECRET
```

`ALERTS_SECRET` y `?key=` deben ser **idénticos** (mismos caracteres).

5. Abre https://t.me/GasRadar_bot → **Start**  
   - Escribe `80903` (ZIP) → precios  
   - Botones del teclado  
   - `3.50` = tope de alerta  


## Si el bot “no sirve”

| Síntoma | Qué hacer |
|---------|-----------|
| No responde nada | Corre de nuevo `/api/telegram/setup?key=...` |
| setup 401 | `ALERTS_SECRET` no coincide con `?key=` |
| Responde pero sin precios | Zyla/límite API; la web puede fallar igual |
| Pierde alertas al redeploy | SQLite se borra → usa Postgres `DATABASE_URL` |
| No avisa solo | Falta cron a `/api/alerts/run?key=...` cada hora |

## Cron de alertas (cada hora)

Render → Cron Job (o UptimeRobot / cron-job.org):

```
GET https://gasradarapp.com/api/alerts/run?key=TU_ALERTS_SECRET
```

Cada 30–60 minutos.

Prueba forzada (ignora límite 1/día):

```
GET https://gasradarapp.com/api/alerts/run?key=TU_ALERTS_SECRET&force=1
```

## Local

En `config_local.py` (gitignored):

```python
TELEGRAM_BOT_TOKEN = "..."
ALERTS_SECRET = "dev-secret"
```

Webhook en local solo funciona con túnel HTTPS (ngrok). Para probar comandos en producción usa el webhook de Render.

## Seguridad

Si el token se filtró (chat, captura, etc.):

1. BotFather → `/revoke` en el bot  
2. Pega el **nuevo** token en Render  
3. Vuelve a llamar `/api/telegram/setup?key=...`
