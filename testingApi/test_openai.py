import asyncio
import os
from dotenv import load_dotenv
from openai_handler import OpenAIHandler

# Cargar variables de entorno
load_dotenv()

async def test_openai_functions():
    try:
        # Inicializar el manejador de OpenAI
        openai_handler = OpenAIHandler()
        
        # Probar la función de texto
        text_response = await openai_handler.send_message_to_gpt(
            "¿Cuál es la capital de Francia?",
            "Eres un asistente útil que responde preguntas de manera concisa y directa."
        )
        print("Respuesta a texto:", text_response)
        
        # Probar la función de análisis de imagen
        # Puedes usar una ruta local o una URL
        image_path = "storage/images/logo.png"  # Ajusta esta ruta según tu estructura
        # Usar el prompt de extracción de tickets para el análisis de imagen
        extraction_prompt = """Eres un sistema de extracción de campos para tickets de apuesta generados por Bet365. Tu tarea es identificar y extraer información clave a partir de un texto que describe los detalles de un ticket. La información debe estructurarse en campos específicos según el formato definido.

# Campos que debes identificar y extraer:

1. **ID del Ticket:** El número identificador único del ticket (ej: "123456")
2. **Deporte:** El deporte relacionado con el evento (ej: "Fútbol", "Tenis", "Baloncesto")
3. **Evento:** Nombre específico del evento o partido (ej: "Barcelona vs Real Madrid")
4. **Mercado:** El tipo de apuesta realizada (ej: "Ganador del partido", "Over/Under 2.5")
5. **Selección:** La elección del apostador (ej: "Barcelona", "Más de 2.5 goles")
6. **Cuota:** La cuota asociada a la apuesta (ej: "1.75", "2.10")
7. **Monto apostado:** Cantidad en la moneda definida (ej: "€20", "€50")
8. **Ganancia potencial:** Cantidad que se puede ganar (ej: "€35", "€105")
9. **Estado de la apuesta:** Estado actual del ticket (ej: "Ganada", "Perdida", "Pendiente")

# Formato de salida esperado:
Debes devolver SIEMPRE un objeto JSON con esta estructura exacta:

```json
{
  "ID_Ticket": "123456",
  "Deporte": "Fútbol",
  "Evento": "Barcelona vs Real Madrid",
  "Mercado": "Ganador del partido",
  "Seleccion": "Barcelona",
  "Cuota": "1.80",
  "Monto_Apostado": "€50",
  "Ganancia_Potencial": "€90",
  "Estado_Apuesta": "Pendiente"
}
```

# Ejemplos adicionales:

Ejemplo 1 (Tenis):
```json
{
  "ID_Ticket": "789012",
  "Deporte": "Tenis",
  "Evento": "Nadal vs Djokovic",
  "Mercado": "Ganador del partido",
  "Seleccion": "Nadal",
  "Cuota": "2.10",
  "Monto_Apostado": "€30",
  "Ganancia_Potencial": "€63",
  "Estado_Apuesta": "Ganada"
}
```

Ejemplo 2 (Campos no identificados):
```json
{
  "ID_Ticket": "No especificado",
  "Deporte": "Baloncesto",
  "Evento": "Lakers vs Bulls",
  "Mercado": "Total puntos",
  "Seleccion": "Más de 198.5",
  "Cuota": "1.90",
  "Monto_Apostado": "No especificado",
  "Ganancia_Potencial": "No especificado",
  "Estado_Apuesta": "Pendiente"
}
```

# Reglas importantes:
1. SIEMPRE devuelve un objeto JSON con TODOS los campos.
2. Si no puedes identificar un campo, usa EXACTAMENTE "No especificado" como valor.
3. Mantén los nombres de los campos EXACTAMENTE como se muestran en los ejemplos.
4. Las cuotas deben ser strings con formato decimal (ej: "1.90", "2.10").
5. Los montos deben incluir el símbolo de la moneda (ej: "€50", "€100").
6. El estado de la apuesta debe ser "Ganada", "Perdida" o "Pendiente"."""
        
        image_response = await openai_handler.analyze_image(
            image_path,
            extraction_prompt
        )
        print("Análisis de imagen:", image_response)
        
    except Exception as e:
        print(f"Error en las pruebas: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_openai_functions())