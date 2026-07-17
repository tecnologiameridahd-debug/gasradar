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
2. Activa el webhook (una vez):

```
https://gasradarapp.com/api/telegram/setup?key=TU_ALERTS_SECRET
```

Debe devolver `"ok": true` y el username del bot.

3. Abre https://t.me/GasRadar_bot → `/start` → `/zona 80903` → `/alerta 3.50`

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
