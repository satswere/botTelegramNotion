"""
Script de Debug para Ver Respuesta de OpenAI

Este script muestra exactamente qué está extrayendo OpenAI de la última imagen procesada.
"""

import asyncio
import json
from pathlib import Path
from infrastructure.openai import OpenAIImageAnalyzer


async def debug_last_image():
    """Debug de la última imagen procesada"""
    
    print("=" * 70)
    print("🔍 DEBUG: Análisis de OpenAI")
    print("=" * 70)
    print()
    
    # Buscar última imagen
    images_path = Path("storage/images")
    if not images_path.exists():
        print("❌ No existe la carpeta storage/images")
        return
    
    images = list(images_path.glob("*.jpg"))
    if not images:
        print("❌ No hay imágenes en storage/images")
        print("ℹ️  Las imágenes se eliminan después de procesarse")
        print("ℹ️  Envía una nueva imagen al bot para debuggear")
        return
    
    # Tomar la más reciente
    latest_image = max(images, key=lambda p: p.stat().st_mtime)
    
    print(f"📸 Imagen encontrada: {latest_image.name}")
    print(f"📏 Tamaño: {latest_image.stat().st_size:,} bytes")
    print()
    
    # Analizar con OpenAI
    print("🤖 Analizando con OpenAI Vision...")
    print()
    
    analyzer = OpenAIImageAnalyzer()
    
    prompt = """Eres un sistema de extracción de campos para tickets de apuesta. Tu tarea es identificar y extraer información clave a partir de la imagen de un ticket. La información debe estructurarse en campos específicos según el formato definido.

# Campos que debes identificar y extraer:

1. **ID_Ticket:** El número identificador único del ticket (ej: "123456")
2. **Deporte:** El deporte relacionado con el evento (ej: "Baloncesto", "Fútbol", "Tenis", "Béisbol"). Si no se identifica, pon "No identificado"
3. **Evento:** Nombre específico del evento o partido (ej: "Barcelona vs Real Madrid")
4. **Mercado:** El tipo de apuesta realizada (ej: "Ganador del partido", "Over/Under 2.5", "Ambos equipos marcan")
5. **Seleccion:** La elección del apostador (ej: "Barcelona", "Más de 2.5 goles", "Sí")
6. **Cuota:** La cuota asociada a la apuesta (ej: "1.75", "2.10")
7. **Monto_Apostado:** Cantidad en la moneda definida (ej: "€20", "€50"). IMPORTANTE: Extrae este valor de la imagen, no uses un valor por defecto
8. **Ganancia_Potencial:** Cantidad que se puede ganar (ej: "€35", "€105")
9. **Estado_Apuesta:** Estado actual del ticket. USA SOLO: "Ganada", "Perdida" o "Pendiente" (no uses otros estados)
10. **Numero_Apuestas:** El número total de apuestas en el ticket. Si es una sola apuesta, pon 1. Si hay múltiples apuestas combinadas, pon el número total (ej: 2, 3, 4, etc.)
11. **Fecha_Evento:** Fecha del evento deportivo si es visible (formato: "YYYY-MM-DD" o "DD/MM/YYYY")
12. **Casa_Apuestas:** Nombre de la casa de apuestas visible en la imagen (ej: "bet365", "Codere", "Betway", "Sportium")

# Formato de salida esperado:
Debes devolver SIEMPRE un objeto JSON con esta estructura exacta:

```json
{
  "ID_Ticket": "123456",
  "Deporte": "Baloncesto",
  "Evento": "Lakers vs Celtics",
  "Mercado": "Ganador del partido",
  "Seleccion": "Lakers",
  "Cuota": "1.80",
  "Monto_Apostado": "€50",
  "Ganancia_Potencial": "€90",
  "Estado_Apuesta": "Pendiente",
  "Numero_Apuestas": 1,
  "Fecha_Evento": "2024-12-20",
  "Casa_Apuestas": "bet365"
}
```

# Reglas importantes:
1. SIEMPRE devuelve un objeto JSON con TODOS los campos.
2. Si no puedes identificar un campo, usa EXACTAMENTE "No especificado" como valor.
3. Mantén los nombres de los campos EXACTAMENTE como se muestran (con mayúsculas y guiones bajos).
4. Las cuotas deben ser strings con formato decimal (ej: "1.90", "2.10").
5. Los montos deben incluir el símbolo de la moneda (ej: "€50", "€100") y deben ser extraídos de la imagen.
6. El estado de la apuesta SOLO puede ser: "Ganada", "Perdida" o "Pendiente".
7. El Mercado y la Selección son CAMPOS DIFERENTES: Mercado es el tipo de apuesta, Selección es la opción elegida.
8. Deporte: Identificar el deporte específico (ej: "Baloncesto", "Fútbol", "Tenis"). Si no se puede identificar, usar "No identificado".
9. Numero_Apuestas debe ser un número entero (1 para simple, 2+ para combinada).
10. Fecha_Evento: Extraer la fecha del evento si está visible en formato ISO o europeo. Si no está visible, usar "No especificado".
11. Casa_Apuestas: Buscar logos, nombres o marcas de agua en la imagen. Casas comunes: bet365, Codere, Betway, Sportium, William Hill.
"""
    
    try:
        result = await analyzer.analyze_image(str(latest_image), prompt)
        
        print("✅ Respuesta de OpenAI:")
        print("━" * 70)
        print(result)
        print("━" * 70)
        print()
        
        # Intentar parsear como JSON
        try:
            # Limpiar marcadores de código
            cleaned = result.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "").replace("```", "").strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned.replace("```", "").strip()
            
            parsed = json.loads(cleaned)
            
            print("📊 Campos extraídos:")
            print()
            for i, (key, value) in enumerate(parsed.items(), 1):
                print(f"   {i:2d}. {key:20s} = {value}")
            
            print()
            print("=" * 70)
            print("✅ JSON válido - La extracción funcionó correctamente")
            print("=" * 70)
            
        except json.JSONDecodeError as e:
            print(f"⚠️ No es JSON válido: {e}")
            print("La respuesta se guardará como texto plano")
        
    except Exception as e:
        print(f"❌ Error analizando imagen: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_last_image())
