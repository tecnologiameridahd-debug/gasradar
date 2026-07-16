# Zyla Labs — Gas Price Locator (API #4808)

Hallado en tu carpeta Descargas:
`Gas Price Locator API_collection_Zyla Api Hub (1).json`

## Endpoints correctos

```text
# Precios por ZIP (nota: "pices" es el nombre real en Zyla)
GET https://zylalabs.com/api/4808/gas+price+locator+api/5997/get+pices?zip=80903&type=regular

# Detalle de estación
GET https://zylalabs.com/api/4808/gas+price+locator+api/23308/station+data?station_id=179035
```

Auth:

```http
Authorization: Bearer 14766|tu_token
```

## Variables (config_local / Render)

| Key | Value |
|-----|--------|
| `ZYLA_API_KEY` | `14766\|...` |
| `ZYLA_GAS_URL` | `https://zylalabs.com/api/4808/gas+price+locator+api/5997/get+pices` |
| `ZYLA_STATION_URL` | `https://zylalabs.com/api/4808/gas+price+locator+api/23308/station+data` |

## Respuesta ejemplo (ZIP 80903)

- average: **$3.87**
- lowest: **$3.66** (Sam's Club)
- estaciones con precio + nombre + coords

## Nota

El API **3109** (US Gas Prices) daba 401 sin suscripción.
El que **sí funciona** con tu key es **4808 Gas Price Locator**.
