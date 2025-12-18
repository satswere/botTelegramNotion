"""
Bet Enrichment Service - Domain Service

Enriquece las apuestas con metadata calculada y validaciones.
Este servicio de dominio NO depende de infraestructura externa.

Responsabilidades:
- Calcular ROI cuando hay resultado
- Detectar liga/competición desde evento
- Detectar casa de apuestas desde patrones
- Enriquecer datos extraídos con lógica de negocio
"""

from typing import Dict, Any, Optional
from decimal import Decimal
import re


class BetEnrichmentService:
    """Domain service para enriquecer datos de apuestas con metadata calculada"""

    # Patrones de equipos NBA para detección
    NBA_TEAMS = [
        "lakers", "celtics", "warriors", "heat", "bulls", "knicks", "nets", "sixers",
        "bucks", "raptors", "cavaliers", "pistons", "pacers", "hornets", "hawks",
        "wizards", "magic", "mavericks", "rockets", "spurs", "grizzlies", "pelicans",
        "thunder", "jazz", "suns", "kings", "clippers", "trail blazers", "nuggets", "timberwolves"
    ]

    # Patrones de ligas de fútbol
    FOOTBALL_LEAGUES = {
        "premier league": ["arsenal", "chelsea", "liverpool", "manchester", "tottenham", "everton"],
        "la liga": ["barcelona", "real madrid", "atletico", "sevilla", "valencia", "villarreal"],
        "serie a": ["juventus", "milan", "inter", "napoli", "roma", "lazio"],
        "bundesliga": ["bayern", "dortmund", "leipzig", "leverkusen", "frankfurt"],
    }

    # Casas de apuestas comunes
    BOOKMAKERS = [
        ("bet365", ["bet365", "bet 365"]),
        ("codere", ["codere"]),
        ("betway", ["betway"]),
        ("william hill", ["william hill", "williamhill"]),
        ("sportium", ["sportium"]),
        ("bwin", ["bwin"]),
        ("marathonbet", ["marathonbet", "marathon"]),
    ]

    def determine_bet_type(self, number_of_bets: int) -> str:
        """
        Determina el tipo de apuesta basado en el número de selecciones.

        Args:
            number_of_bets: Número de apuestas en el ticket

        Returns:
            "Simple" si es 1, "Combinada" si es más de 1
        """
        return "Simple" if number_of_bets == 1 else "Combinada"

    def determine_league(self, sport: str, event: str) -> str:
        """
        Detecta la liga/competición basándose en el deporte y el evento.

        Args:
            sport: Deporte de la apuesta
            event: Nombre del evento

        Returns:
            Nombre de la liga o "No identificado"
        """
        if not sport or not event:
            return "No identificado"

        sport_lower = sport.lower()
        event_lower = event.lower()

        # Detección de NBA
        if "baloncesto" in sport_lower or "basketball" in sport_lower:
            if self._is_nba_event(event_lower):
                return "NBA"

        # Detección de ligas de fútbol
        if "fútbol" in sport_lower or "futbol" in sport_lower or "football" in sport_lower or "soccer" in sport_lower:
            for league, teams in self.FOOTBALL_LEAGUES.items():
                if any(team in event_lower for team in teams):
                    return league.upper()

        return "No identificado"

    def detect_bookmaker(self, analysis_data: Dict[str, Any]) -> str:
        """
        Detecta la casa de apuestas desde los datos extraídos.

        Args:
            analysis_data: Datos extraídos del análisis

        Returns:
            Nombre de la casa de apuestas o "bet365" por defecto
        """
        # Buscar en todos los campos de texto
        searchable_text = " ".join([
            str(analysis_data.get("ID_Ticket", "")),
            str(analysis_data.get("Evento", "")),
            str(analysis_data.get("Mercado", "")),
            str(analysis_data.get("raw_analysis", "")),
        ]).lower()

        for bookmaker_name, patterns in self.BOOKMAKERS:
            if any(pattern in searchable_text for pattern in patterns):
                return bookmaker_name

        # Default a bet365
        return "bet365"

    def calculate_roi(
        self,
        stake_amount: Optional[float],
        ganancia_perdida: Optional[float],
        status: str
    ) -> Optional[float]:
        """
        Calcula el ROI (Return on Investment) de una apuesta.

        Formula: ROI = ((Ganancia - Apuesta) / Apuesta) * 100

        Args:
            stake_amount: Monto apostado
            ganancia_perdida: Ganancia real (positiva) o pérdida (negativa)
            status: Estado de la apuesta ("Ganada", "Perdida", "Pendiente")

        Returns:
            ROI como porcentaje, o None si no se puede calcular
        """
        if not stake_amount or stake_amount <= 0:
            return None

        # Solo calcular ROI para apuestas resueltas
        if status not in ["Ganada", "Perdida"]:
            return None

        if status == "Ganada" and ganancia_perdida:
            # Ganancia neta = ganancia total - apuesta
            net_profit = ganancia_perdida - stake_amount
            roi = (net_profit / stake_amount) * 100
            return round(roi, 2)

        elif status == "Perdida":
            # Pérdida total = -100%
            return -100.0

        return None

    def extract_stake_from_string(self, stake_str: str) -> tuple[Optional[float], str]:
        """
        Extrae el monto y la moneda de un string.

        Args:
            stake_str: String con el monto (ej: "€50", "$100", "50 EUR")

        Returns:
            Tupla (monto, moneda)
        """
        if not stake_str or stake_str == "No especificado":
            return None, "EUR"

        stake_str = stake_str.strip()

        # Mapeo de símbolos a códigos
        currency_map = {"€": "EUR", "$": "USD", "£": "GBP"}
        currency = "EUR"  # Default

        # Detectar símbolo de moneda
        for symbol, code in currency_map.items():
            if symbol in stake_str:
                currency = code
                stake_str = stake_str.replace(symbol, "").strip()
                break

        # Detectar código de moneda al final
        parts = stake_str.split()
        if len(parts) == 2 and len(parts[1]) == 3:
            currency = parts[1].upper()
            stake_str = parts[0]

        # Parsear monto
        try:
            stake_str = stake_str.replace(",", ".")
            amount = float(stake_str)
            return amount, currency
        except (ValueError, ArithmeticError):
            return None, currency

    def enrich_analysis_data(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece los datos del análisis con metadata calculada.

        Args:
            analysis_data: Datos extraídos del análisis de imagen

        Returns:
            Datos enriquecidos con campos adicionales
        """
        enriched = analysis_data.copy()

        # 1. Detectar tipo de apuesta
        numero_apuestas = analysis_data.get("Numero_Apuestas", 1)
        try:
            num_bets = int(numero_apuestas)
        except (ValueError, TypeError):
            num_bets = 1
        enriched["Tipo_Apuesta_Calculado"] = self.determine_bet_type(num_bets)

        # 2. Detectar liga/competición
        deporte = analysis_data.get("Deporte", "")
        evento = analysis_data.get("Evento", "")
        enriched["Liga_Calculada"] = self.determine_league(deporte, evento)

        # 3. Detectar casa de apuestas
        enriched["Casa_Apuestas_Detectada"] = self.detect_bookmaker(analysis_data)

        # 4. Extraer montos numéricos
        monto_str = analysis_data.get("Monto_Apostado", "")
        if monto_str:
            amount, currency = self.extract_stake_from_string(str(monto_str))
            if amount:
                enriched["Stake_Amount"] = amount
                enriched["Stake_Currency"] = currency

        ganancia_str = analysis_data.get("Ganancia_Potencial", "")
        if ganancia_str:
            amount, currency = self.extract_stake_from_string(str(ganancia_str))
            if amount:
                enriched["Potential_Profit_Amount"] = amount
                enriched["Potential_Profit_Currency"] = currency

        # 5. Calcular ROI si hay resultado
        status = analysis_data.get("Estado_Apuesta", "Pendiente")
        if status in ["Ganada", "Perdida"]:
            stake = enriched.get("Stake_Amount")
            potential = enriched.get("Potential_Profit_Amount")
            if stake and potential:
                if status == "Ganada":
                    roi = self.calculate_roi(stake, potential, status)
                    enriched["ROI"] = roi
                elif status == "Perdida":
                    enriched["ROI"] = -100.0

        return enriched

    def _is_nba_event(self, event: str) -> bool:
        """Verifica si un evento es de la NBA"""
        return "nba" in event or any(team in event for team in self.NBA_TEAMS)

    def validate_extracted_data(self, data: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Valida que los datos extraídos sean coherentes.

        Args:
            data: Datos extraídos

        Returns:
            Tupla (es_válido, lista_de_errores)
        """
        errors = []

        # Validar cuota
        cuota_str = data.get("Cuota", "")
        if cuota_str and cuota_str != "No especificado":
            try:
                cuota = float(str(cuota_str).replace(",", "."))
                if cuota < 1.01 or cuota > 1000:
                    errors.append(f"Cuota fuera de rango razonable: {cuota}")
            except ValueError:
                errors.append(f"Cuota inválida: {cuota_str}")

        # Validar monto
        monto_str = data.get("Monto_Apostado", "")
        if monto_str and monto_str != "No especificado":
            amount, _ = self.extract_stake_from_string(str(monto_str))
            if amount and (amount < 0.01 or amount > 1000000):
                errors.append(f"Monto fuera de rango razonable: {amount}")

        # Validar estado
        estado = data.get("Estado_Apuesta", "")
        valid_states = ["Ganada", "Perdida", "Pendiente", "Anulada", "Cashout"]
        if estado and estado not in valid_states:
            errors.append(f"Estado inválido: {estado}")

        return len(errors) == 0, errors
