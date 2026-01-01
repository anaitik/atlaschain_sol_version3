"""
ESG Standards configuration service.
Manages configurable ESG standards for different regions/frameworks.
"""
from typing import Dict, List, Optional
from database import Database


class ESGService:
    """Service for managing ESG standards configurations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create_standard(
        self,
        name: str,
        config: Dict,
        region: str = "",
        framework: str = "",
        description: str = ""
    ) -> int:
        """
        Create a new ESG standard configuration.
        
        Config structure:
        {
            "environmental": {
                "emissions": {
                    "scope1_required": true,
                    "scope2_required": true,
                    "scope3_required": false,
                    "units": "CO2e",
                    "reporting_frequency": "annual"
                },
                "waste": {...},
                "water": {...}
            },
            "social": {
                "labor": {...},
                "safety": {...}
            },
            "governance": {
                "board_diversity": {...},
                "transparency": {...}
            }
        }
        """
        return self.db.create_esg_standard(
            name=name,
            config_json=config,
            region=region,
            framework=framework,
            description=description
        )
    
    def get_standard(self, standard_id: int) -> Optional[Dict]:
        """Get ESG standard configuration."""
        standard = self.db.get_esg_standard(standard_id)
        if standard:
            import json
            standard["config_json"] = json.loads(standard["config_json"])
        return standard
    
    def list_standards(self) -> List[Dict]:
        """List all ESG standards."""
        standards = self.db.list_esg_standards()
        for standard in standards:
            import json
            standard["config_json"] = json.loads(standard["config_json"])
        return standards
    
    def get_default_standards(self) -> List[Dict]:
        """Get default ESG standard configurations."""
        return [
            {
                "name": "GRI Standards",
                "region": "Global",
                "framework": "GRI",
                "description": "Global Reporting Initiative Standards",
                "config": {
                    "environmental": {
                        "emissions": {
                            "scope1_required": True,
                            "scope2_required": True,
                            "scope3_required": True,
                            "units": "CO2e",
                            "reporting_frequency": "annual"
                        }
                    },
                    "social": {
                        "labor": {
                            "working_hours_tracking": True,
                            "safety_incidents_required": True
                        }
                    },
                    "governance": {
                        "board_diversity": {
                            "gender_parity_tracking": True
                        }
                    }
                }
            },
            {
                "name": "EU CSRD",
                "region": "Europe",
                "framework": "CSRD",
                "description": "Corporate Sustainability Reporting Directive",
                "config": {
                    "environmental": {
                        "emissions": {
                            "scope1_required": True,
                            "scope2_required": True,
                            "scope3_required": True,
                            "units": "CO2e",
                            "reporting_frequency": "annual"
                        }
                    }
                }
            },
            {
                "name": "SEC Climate Disclosure",
                "region": "United States",
                "framework": "SEC",
                "description": "SEC Climate-Related Disclosures",
                "config": {
                    "environmental": {
                        "emissions": {
                            "scope1_required": True,
                            "scope2_required": True,
                            "scope3_required": False,
                            "units": "CO2e"
                        }
                    }
                }
            }
        ]

