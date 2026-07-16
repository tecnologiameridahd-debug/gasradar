# Conectar precios Zyla Labs a GasRadar

## Endpoint que configuramos

```text
GET https://zylalabs.com/api/3109/us+gas+prices+api/24537/get+prices
```

Parámetros que usa la app: `?zip=80903&type=regular`

Auth:

```http
Authorization: Bearer 14765|tu_token
```

## Importante

Tu key **sí es de Zyla** (formato `12345|xxxx`).

Al probarla ahora, Zyla responde:

> **"You are not authorized to access this API. Please subscribe to this API."**

Eso significa:

1. La key es válida (Bearer funciona).
2. **Falta suscribirte al API #3109 — US Gas Prices API** en el dashboard de Zyla.

---

## Pasos en Zyla

1. Entra a https://zylalabs.com y inicia sesión.
2. Busca un API de gasolina USA, por ejemplo:
   - **US Gas Prices API**
   - **Gas Prices in USA by ZIP Code**
   - **ZIP Code Gas Prices API**
   - **Gas Price Locator API**
3. Pulsa **Subscribe** / **Start free trial** (el plan free del que te suscribiste).
4. Abre el API → pestaña de documentación / **cURL**.
5. Copia la URL, algo así:

```text
https://zylalabs.com/api/3109/us+gas+prices+api/24537/get+prices?zip=90001&type=regular
```

6. La parte **sin** los parámetros (o con `{zip}`) es tu `ZYLA_GAS_URL`.

---

## En tu PC (`config_local.py`)

```python
ZYLA_API_KEY = "14765|tu_token"
ZYLA_GAS_URL = "https://zylalabs.com/api/XXXX/.../get+prices"
```

---

## En Render (internet)

Environment:

| Key | Value |
|-----|--------|
| `ZYLA_API_KEY` | `14765\|...` |
| `ZYLA_GAS_URL` | URL del endpoint (copiada de Zyla) |

---

## Auth correcta (Zyla)

```http
Authorization: Bearer 14765|xxxxxxxx
```

No uses el estilo CollectAPI (`apikey ...`).

---

## Comprobar

Cuando la suscripción y la URL estén bien, al buscar un ZIP en la app o en logs:

```text
[zyla] OK zip=80903 regular=3.xx
```

Si sigue el mensaje de “subscribe to this API”, el producto aún no está activo en tu cuenta.
