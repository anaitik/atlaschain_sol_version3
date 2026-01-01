"""
Reference Tools - Lookup Emissions, Material Lookup, Transport Distance
"""
from typing import Dict, Optional, List


class ReferenceTools:
    """Reference data lookup tools for ESG calculations."""
    
    # Emission factors (kg CO2e per unit)
    EMISSION_FACTORS = {
        "electricity": {
            "grid_average": 0.5,  # kg CO2e per kWh (varies by region)
            "renewable": 0.0
        },
        "natural_gas": 0.2,  # kg CO2e per kWh
        "diesel": 2.68,  # kg CO2e per liter
        "petrol": 2.31,  # kg CO2e per liter
        "air_freight": 0.5,  # kg CO2e per ton-km
        "sea_freight": 0.01,  # kg CO2e per ton-km
        "road_freight": 0.1,  # kg CO2e per ton-km
    }
    
    # Material carbon footprints (kg CO2e per kg)
    MATERIAL_FOOTPRINTS = {
        "steel": 1.85,
        "aluminum": 8.24,
        "plastic": 2.5,
        "concrete": 0.13,
        "glass": 0.85,
        "paper": 0.7,
        "wood": 0.3,
    }
    
    @staticmethod
    def lookup_emissions(
        activity_type: str,
        amount: float,
        unit: str = "kg"
    ) -> float:
        """
        Lookup emission factor and calculate emissions.
        
        Args:
            activity_type: Type of activity (e.g., "electricity", "diesel")
            amount: Amount of activity
            unit: Unit of amount
        
        Returns:
            Emissions in kg CO2e
        """
        factors = ReferenceTools.EMISSION_FACTORS
        
        if activity_type in factors:
            factor = factors[activity_type]
            if isinstance(factor, dict):
                # Use default if specific not provided
                factor = factor.get("grid_average", 0.0)
            return factor * amount
        
        return 0.0
    
    @staticmethod
    def lookup_material(material_name: str) -> Optional[Dict]:
        """
        Lookup material carbon footprint.
        
        Returns:
            Dict with carbon_footprint (kg CO2e per kg) and other properties
        """
        material_lower = material_name.lower()
        
        for mat, footprint in ReferenceTools.MATERIAL_FOOTPRINTS.items():
            if mat in material_lower:
                return {
                    "material": mat,
                    "carbon_footprint": footprint,  # kg CO2e per kg
                    "unit": "kg CO2e/kg"
                }
        
        return None
    
    @staticmethod
    def calculate_transport_distance(
        origin: str,
        destination: str,
        transport_mode: str = "road"
    ) -> Optional[Dict]:
        """
        Calculate transport distance and emissions.
        
        Note: In production, this would use a geocoding API.
        For now, returns mock data.
        """
        # Mock implementation
        # In production, use geopy or similar
        return {
            "origin": origin,
            "destination": destination,
            "distance_km": 100.0,  # Mock
            "transport_mode": transport_mode,
            "emissions_kg_co2e": ReferenceTools.lookup_emissions(
                f"{transport_mode}_freight", 100.0, "ton-km"
            ),
            "note": "Mock data - use geocoding API in production"
        }

