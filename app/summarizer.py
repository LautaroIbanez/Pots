from openai import OpenAI
from app.config import OPENAI_API_KEY

def summarize_transcript(text: str, video_title: str, channel_name: str) -> str:
    """Generate a summary of the transcript using OpenAI."""
    if not OPENAI_API_KEY:
        return "Error: OPENAI_API_KEY no configurada"
    client = OpenAI(api_key=OPENAI_API_KEY)
    max_chunk_length = 12000
    if len(text) > max_chunk_length:
        text = text[:max_chunk_length] + "..."
    prompt = f"""Eres un analista económico y financiero. Resumes el contenido de videos de YouTube sobre realidad económica y mercados.

Video: {video_title}
Canal: {channel_name}

Transcripción:
{text}

Objetivo: dar un resumen breve y claro, en español, de lo que se dijo en el video, destacando:
- Contexto económico principal
- Mensajes clave del expositor
- Impacto potencial en Argentina y/o mercados financieros
- Riesgos y oportunidades mencionadas (si aplica)

Estilo: frases cortas, claras, sin opinión personal.
Longitud: máximo 6-8 líneas.

Resumen:"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un analista económico y financiero experto en resumir contenido de videos sobre economía y mercados financieros."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        return f"Error al generar resumen: {str(e)}"

