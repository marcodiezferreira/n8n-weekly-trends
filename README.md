# n8n-weekly-trends

**Las 5 tendencias de la semana en IA, automatización, marketing y desarrollo, en tu Telegram cada lunes.** Sin abrir veinte pestañas.

Es una plantilla para [n8n](https://n8n.io) que:

1. Lee lo que más está creciendo en los últimos 7 días:
   - **GitHub**: repositorios nuevos con más estrellas.
   - **Hacker News**: lo más votado.
   - **Hugging Face**: modelos en tendencia.
   - **Blogs** por RSS: OpenAI, Hugging Face, GitHub, TechCrunch IA y Search Engine Journal.
2. Ordena y junta todo en una lista.
3. Un modelo de OpenAI elige las 5 tendencias más útiles y explica en español por qué importan.
4. Te lo manda por Telegram.

```
Tendencias de la semana

1. Nuevo modelo abierto de generación de vídeo
Lo publican con pesos abiertos y ya está entre los más descargados de Hugging Face. Se puede probar en local.
https://huggingface.co/...

2. ...

La que más me interesa esta semana: ... porque ...
```

## Instalación

1. En n8n: **Workflows → Import from file** y elige `workflow.json`.
2. Crea dos credenciales y asígnalas:
   - **OpenAI** en el nodo «Modelo».
   - **Telegram** (token de un bot creado con [@BotFather](https://t.me/BotFather)) en «Enviar a Telegram».
3. En «Enviar a Telegram», cambia `TU_CHAT_ID` por tu chat. Para saberlo, escribe a [@userinfobot](https://t.me/userinfobot).
4. Pulsa **Probar a mano** y, si te llega el mensaje, activa el flujo.

Coste: una llamada al modelo por semana (céntimos).

## Personalizar

Edita las constantes de `generate_workflow.py` y vuelve a generar el flujo:

```bash
python generate_workflow.py
```

| Constante | Para qué |
|---|---|
| `HORARIO` | Cuándo se ejecuta (cron). Por defecto, lunes a las 8:30 |
| `ZONA` | Zona horaria |
| `MODELO` | Modelo de chat de OpenAI |
| `TEMAS` | De qué temas eres «editor» (cambia el criterio de selección) |
| `RSS` | Lista de blogs a seguir |

También puedes cambiar los nodos directamente en n8n.

## Cómo funciona por dentro

- Cada fuente es un nodo HTTP o RSS con «continuar si falla»: si una fuente se cae, el resto sigue.
- El nodo «Normalizar» convierte cada respuesta (GitHub, Hacker News, Hugging Face o RSS) al mismo formato y descarta lo que tenga más de 8 días.
- «Preparar lista» se queda con las 12 mejores de cada fuente según su señal (puntos, estrellas o tendencia) y lo manda todo en una sola llamada al modelo.
- No guarda datos ni necesita base de datos.

## Ideas para ampliarlo

- Mandar el resumen por correo o a Slack en lugar de Telegram.
- Guardar cada semana en Google Sheets o Notion.
- Pedir al modelo un borrador de post para tu blog o LinkedIn con la tendencia elegida.

## Autor

Hecho por [Marco Díez](https://marcodiez.es): apps y automatizaciones con IA, marketing digital y SEO.
¿Quieres una automatización así para tu negocio? [Escríbeme](https://marcodiez.es/contacto/).

Licencia MIT.
