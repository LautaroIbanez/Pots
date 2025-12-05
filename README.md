# Pots - Resumidor de Videos de YouTube

Una aplicación web minimalista que obtiene los últimos videos de canales de YouTube sobre economía y finanzas, obtiene sus transcripciones y genera resúmenes usando OpenAI.

## Requisitos

- Python 3.11+
- Cuenta de Google Cloud con YouTube Data API v3 habilitada
- Cuenta de OpenAI con API key

## Instalación

1. Clonar o descargar el proyecto

2. Crear un entorno virtual:
```bash
python -m venv venv
```

3. Activar el entorno virtual:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Instalar dependencias:
```bash
pip install -r requirements.txt
```

5. Configurar variables de entorno:
   - Copiar `.env.example` a `.env`
   - Editar `.env` y agregar tus API keys:
```
YOUTUBE_API_KEY=tu_youtube_api_key_aqui
OPENAI_API_KEY=tu_openai_api_key_aqui
```

## Ejecución

```bash
uvicorn app.main:app --reload
```

Luego abrir http://127.0.0.1:8000 en el navegador.

## Uso

1. Al abrir la aplicación, verás los resúmenes guardados en caché (si existen)
2. Haz click en el botón "Refresh" para:
   - Obtener los últimos 3 videos de cada canal configurado
   - Intentar obtener las transcripciones
   - Generar resúmenes con OpenAI (solo para videos nuevos)
   - Actualizar la interfaz con los nuevos datos

## Estructura del Proyecto

```
Pots/
  app/
    __init__.py
    config.py              # Configuración y variables de entorno
    main.py                # FastAPI app y endpoints
    models.py              # Modelos Pydantic
    youtube_client.py      # Cliente de YouTube Data API
    transcript_client.py   # Cliente para obtener transcripciones
    summarizer.py          # Generación de resúmenes con OpenAI
    storage.py             # Persistencia en JSON
    static/
      style.css            # Estilos CSS
      app.js               # JavaScript del frontend
    templates/
      index.html           # Página principal
  data/
    summaries.json         # Cache de resúmenes (se crea automáticamente)
  .env                     # Variables de entorno (no incluido en git)
  .env.example            # Ejemplo de variables de entorno
  requirements.txt         # Dependencias Python
  README.md               # Este archivo
```

## Características

- Obtiene los últimos 3 videos de cada canal configurado
- Intenta obtener transcripciones en español o inglés
- Genera resúmenes en español usando GPT-4o-mini
- Cachea resúmenes en `data/summaries.json` para evitar llamadas repetidas a la API
- Interfaz web simple y minimalista
- Sin base de datos, sin Docker, sin autenticación

## Canales Configurados

Los canales están definidos en `app/config.py`. Puedes modificarlos según tus necesidades.

## Notas

- Los resúmenes se cachean por `video_id` para evitar gastar tokens innecesariamente
- Si un video no tiene transcripción disponible, se muestra un mensaje indicándolo
- La aplicación maneja errores de forma robusta y continúa procesando otros canales si uno falla

