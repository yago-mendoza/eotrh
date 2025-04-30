# -*- coding: utf-8 -*-
from pydantic import (
    BaseModel, Field, validator, RootModel, model_validator,
    ValidationError
)
from typing import List, Tuple, Dict, Any, Optional

# Modelo para validar los datos enviados desde el formulario manual
# NOTA: Asumimos que el frontend enviará el *valor numérico* del score
class ManualFormData(BaseModel):
    # Clinical
    fistules: int = Field(..., ge=0)
    recessio: int = Field(..., ge=0)
    bulbos: int = Field(..., ge=0)
    gingivitis: int = Field(..., ge=0)
    mossegada: int = Field(..., ge=0)
    # Radiographic
    dents_afectades: int = Field(..., ge=0)
    absents: int = Field(..., ge=0)
    forma: int = Field(..., ge=0)
    estructura: int = Field(..., ge=0)
    superficie: int = Field(..., ge=0)

# Modelo para validar el JSON de ROIs
class RoiData(RootModel[List[List[Tuple[int, int]]]]):
    """
    Modelo raíz para validar una lista de polígonos.
    Cada polígono es una lista de tuplas (x, y).
    """
    
    @model_validator(mode='before')
    @classmethod
    def validate_polygons(cls, data: Any) -> Any:
        """Valida que cada polígono en la lista tenga al menos 3 vértices."""
        if not isinstance(data, list):
            raise ValueError("Input ROI data must be a list")

        for i, polygon in enumerate(data):
            if not isinstance(polygon, list):
                raise ValueError(f"Item at index {i} is not a list (polygon)")
            if len(polygon) < 3:
                raise ValueError(f"Polygon at index {i} must have at least 3 vertices, got {len(polygon)}")

        return data

# Modelo para los detalles de análisis de una ROI individual
class RoiAnalysisDetail(BaseModel):
    roi_index: int
    dist_en: Optional[float] = None
    error: Optional[str] = None

# Modelo para la respuesta completa del análisis
class AnalysisResult(BaseModel):
    puntuacio_clinica: int
    puntuacio_radio: int
    puntuacio_digital: int
    puntuacio_total_integrada: int
    classificacio: str
    interpretacio: str
    max_dist_en_value: float
    roi_analysis_details: List[RoiAnalysisDetail]