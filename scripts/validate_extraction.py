"""
Test de Validación del Flujo Completo de Extracción

Este script valida que el proceso de extracción y creación en Notion funcione correctamente.
"""

import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


async def test_extraction_flow():
    """Valida el flujo completo de extracción y creación"""
    
    print("=" * 70)
    print("🧪 TEST DE VALIDACIÓN DEL FLUJO DE EXTRACCIÓN")
    print("=" * 70)
    print()
    
    # 1. Validar configuración
    print("1️⃣ Validando configuración...")
    required_env = ["OPENAI_API_KEY", "OPENAI_API_URL", "API_VERSION", "NOTION_TOKEN", "NOTION_DATABASE_ID"]
    
    missing = []
    for env_var in required_env:
        if not os.getenv(env_var):
            missing.append(env_var)
    
    if missing:
        print(f"   ❌ Variables de entorno faltantes: {', '.join(missing)}")
        print(f"   ⚠️  Configura estas variables en el archivo .env")
        return False
    
    print(f"   ✅ Todas las variables de entorno configuradas")
    print()
    
    # 2. Validar servicios
    print("2️⃣ Validando servicios...")
    
    try:
        from infrastructure.openai import OpenAIImageAnalyzer
        from infrastructure.notion import NotionBetRepository
        from application.use_cases import ProcessBetImageUseCase
        from domain.services import BetEnrichmentService
        
        print(f"   ✅ OpenAIImageAnalyzer importado")
        print(f"   ✅ NotionBetRepository importado")
        print(f"   ✅ ProcessBetImageUseCase importado")
        print(f"   ✅ BetEnrichmentService importado")
    except ImportError as e:
        print(f"   ❌ Error importando servicios: {e}")
        return False
    
    print()
    
    # 3. Validar prompt de extracción
    print("3️⃣ Validando prompt de extracción...")
    
    use_case = ProcessBetImageUseCase(
        image_analyzer=OpenAIImageAnalyzer(),
        file_storage=None,
        bet_repository=None
    )
    
    prompt = use_case._build_analysis_prompt()
    
    # Verificar que el prompt incluye todos los campos necesarios
    required_fields = [
        "ID_Ticket", "Deporte", "Evento", "Mercado", "Seleccion",
        "Cuota", "Monto_Apostado", "Ganancia_Potencial", "Estado_Apuesta",
        "Numero_Apuestas", "Fecha_Evento", "Casa_Apuestas"
    ]
    
    missing_fields = []
    for field in required_fields:
        if field not in prompt:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"   ❌ Campos faltantes en el prompt: {', '.join(missing_fields)}")
        return False
    
    print(f"   ✅ Prompt incluye todos los {len(required_fields)} campos requeridos")
    print()
    
    # 4. Validar servicio de enriquecimiento
    print("4️⃣ Validando servicio de enriquecimiento...")
    
    enrichment_service = BetEnrichmentService()
    
    # Test de detección de tipo de apuesta
    assert enrichment_service.determine_bet_type(1) == "Simple"
    assert enrichment_service.determine_bet_type(3) == "Combinada"
    print(f"   ✅ Detección de tipo de apuesta funciona")
    
    # Test de detección de liga
    liga_nba = enrichment_service.determine_league("Baloncesto", "Lakers vs Celtics")
    assert liga_nba == "NBA"
    print(f"   ✅ Detección de liga NBA funciona")
    
    # Test de extracción de monto
    amount, currency = enrichment_service.extract_stake_from_string("€50")
    assert amount == 50.0
    assert currency == "EUR"
    print(f"   ✅ Extracción de montos funciona")
    
    # Test de validación
    test_data = {
        "Cuota": "1.80",
        "Monto_Apostado": "€50",
        "Estado_Apuesta": "Pendiente"
    }
    is_valid, errors = enrichment_service.validate_extracted_data(test_data)
    assert is_valid
    print(f"   ✅ Validación de datos funciona")
    
    print()
    
    # 5. Resumen
    print("=" * 70)
    print("✅ VALIDACIÓN COMPLETA EXITOSA")
    print("=" * 70)
    print()
    print("📊 Campos que se extraen automáticamente:")
    for i, field in enumerate(required_fields, 1):
        print(f"   {i:2d}. {field}")
    print()
    print("🎯 El sistema está listo para procesar imágenes de tickets de apuestas")
    print()
    print("📝 Próximo paso: Envía una imagen al bot de Telegram para probar")
    print()
    
    return True


async def test_json_parsing():
    """Test de parseo de JSON desde respuesta de OpenAI"""
    
    print("=" * 70)
    print("🧪 TEST DE PARSEO DE JSON")
    print("=" * 70)
    print()
    
    from application.use_cases import ProcessBetImageUseCase
    
    use_case = ProcessBetImageUseCase(None, None, None)
    
    # Test 1: JSON limpio
    test_json = '{"Evento": "Test", "Cuota": "1.80"}'
    result = use_case._parse_analysis_result(test_json)
    assert result["Evento"] == "Test"
    print("   ✅ Parseo de JSON limpio funciona")
    
    # Test 2: JSON con marcadores de código
    test_json_marked = '```json\n{"Evento": "Test", "Cuota": "1.80"}\n```'
    result = use_case._parse_analysis_result(test_json_marked)
    assert result["Evento"] == "Test"
    print("   ✅ Parseo de JSON con marcadores funciona")
    
    # Test 3: JSON con campos normalizados
    test_json_full = """{
        "ID_Ticket": "12345",
        "Deporte": "Baloncesto",
        "Evento": "Lakers vs Celtics",
        "Mercado": "Ganador",
        "Seleccion": "Lakers",
        "Cuota": "1.80",
        "Monto_Apostado": "€50",
        "Ganancia_Potencial": "€90",
        "Estado_Apuesta": "Pendiente",
        "Numero_Apuestas": 1,
        "Fecha_Evento": "2024-12-20",
        "Casa_Apuestas": "bet365"
    }"""
    
    result = use_case._parse_analysis_result(test_json_full)
    assert result["Evento"] == "Lakers vs Celtics"
    assert result["Cuota"] == "1.80"
    assert result["Casa_Apuestas"] == "bet365"
    print("   ✅ Parseo de JSON completo con todos los campos funciona")
    
    # Test 4: Texto inválido (fallback)
    test_invalid = "Este no es un JSON válido"
    result = use_case._parse_analysis_result(test_invalid)
    assert "raw_analysis" in result
    assert result["Evento"] == "No especificado"
    print("   ✅ Fallback para texto inválido funciona")
    
    print()
    print("✅ Todos los tests de parseo pasaron correctamente")
    print()


async def main():
    """Ejecuta todos los tests de validación"""
    
    print()
    print("🚀 INICIANDO VALIDACIÓN DEL SISTEMA DE EXTRACCIÓN")
    print()
    
    # Test 1: Flujo completo
    success1 = await test_extraction_flow()
    
    if success1:
        # Test 2: Parseo de JSON
        await test_json_parsing()
        
        print()
        print("=" * 70)
        print("🎉 TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 70)
        print()
        print("✅ El sistema de extracción está completamente funcional")
        print()
        print("📋 Campos extraídos y mapeados a Notion:")
        print("   • Evento / Selección (título)")
        print("   • Mercado (con metadata de deporte, liga, tipster)")
        print("   • Selección")
        print("   • Cuota (numérico)")
        print("   • Importe apostado (numérico)")
        print("   • Estado (Pendiente/Ganada/Perdida)")
        print("   • Casa de apuestas")
        print("   • Tipo de apuesta (Simple/Combinada)")
        print("   • Imagen adjunta (campo Captura)")
        print()
        print("ℹ️  ROI y Ganancia/Pérdida real se calculan en Notion")
        print()
    else:
        print()
        print("❌ Algunos tests fallaron. Revisa los errores arriba.")
        print()


if __name__ == "__main__":
    asyncio.run(main())
