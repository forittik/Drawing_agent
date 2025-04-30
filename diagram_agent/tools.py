# diagram_agent/tools.py
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_serializer
import uuid
from datetime import datetime
import json

class Position(BaseModel):
    x: float = Field(..., description="X coordinate on the canvas")
    y: float = Field(..., description="Y coordinate on the canvas")

    # Keep existing validators if desired, or remove if strict >= 0 check isn't needed
    # @field_validator('x', 'y')
    # @classmethod
    # def validate_coordinates(cls, v: float) -> float:
    #     if v < 0:
    #         raise ValueError("Coordinates cannot be negative")
    #     return v

class Size(BaseModel):
    width: float = Field(..., description="Width of the shape")
    height: float = Field(..., description="Height of the shape")

    # Keep existing validators if desired, or remove if non-positive check isn't needed for lines/arrows
    # @field_validator('width', 'height')
    # @classmethod
    # def validate_dimensions(cls, v: float) -> float:
    #     if v <= 0:
    #         # Allow non-positive for vectors in lines/arrows if needed by diagram format
    #         pass # Or add specific validation if needed
    #     return v

class ImageSource(BaseModel):
    sourceType: Literal["network", "local"] = Field(..., description="Type of image source")
    url: Optional[str] = Field(None, description="URL of the image if sourceType is network")
    imageName: Optional[str] = Field(None, description="Name of the image file") # Made optional to match potential use

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str], info) -> Optional[str]:
        # Pydantic v2 style validation context access
        if 'data' in info.context and info.context['data'].get('sourceType') == 'network' and not v:
             raise ValueError("URL is required for network image sources")
        # Handle case where context might not be passed as expected in all scenarios
        # Fallback or alternative check might be needed depending on usage pattern
        return v

class DrawingTool(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the shape")
    type: Literal["circle", "arrow", "line", "triangle", "star", "text", "image", "rectangle"] = Field(..., description="Type of the shape")
    position: Position = Field(..., description="Position of the shape on the canvas")
    size: Size = Field(..., description="Size of the shape")
    color: int = Field(4278190080, description="Color of the shape in ARGB format") # Default from example
    strokeWidth: int = Field(..., description="Width of the shape's stroke (e.g., 1 for text, 2 for shapes)") # Made required
    rotation: float = Field(0.0, description="Rotation angle of the shape in degrees") # Ensure float
    strokeType: Literal["solid", "dashed", "dotted"] = Field("solid", description="Type of the shape's stroke")
    canBeOverlapped: bool = Field(..., description="Whether the shape can be overlapped") # Made required

    # Optional properties - include all potential fields from the target JSON example
    text: Optional[str] = Field(None)
    fontSize: Optional[int] = Field(None)
    fontFamily: Optional[str] = Field(None)
    isBold: Optional[bool] = Field(None)
    isItalic: Optional[bool] = Field(None)
    isStrikethrough: Optional[bool] = Field(None)
    textAlignment: Optional[Literal["left", "center", "right"]] = Field(None)
    isFixedWidth: Optional[bool] = Field(None)
    maintainAspectRatio: Optional[bool] = Field(None) # For images
    imageSource: Optional[ImageSource] = Field(None) # For images
    imageName: Optional[str] = Field(None)           # For images
    controlPoint: Optional[Position] = Field(None)   # For arrow, line, circle

    # Use model_serializer for Pydantic v2 to control output, exclude None by default
    @model_serializer(when_used='json') # Or 'always' if needed outside JSON serialization
    def serialize_model(self) -> Dict[str, Any]:
        # Start with default serialization, excluding unset/None fields
        data = super().model_dump(exclude_unset=True)

        # Ensure all required fields are present even if they have default values
        # (Pydantic usually includes fields with defaults unless exclude_defaults=True)
        # Re-add base fields if they were somehow excluded and have defaults in the model
        # Note: The goal is to match the target JSON structure precisely.
        # If the target JSON *always* includes fields like 'rotation: 0', ensure they are here.
        # Pydantic's default `model_dump` should handle this if defaults are set correctly in the model definition.
        # Explicitly setting them here might be redundant but ensures presence if defaults behave unexpectedly.

        # Example: Ensure default rotation is present if needed
        if 'rotation' not in data and self.rotation == 0.0:
             data['rotation'] = 0.0
        if 'strokeType' not in data and self.strokeType == "solid":
             data['strokeType'] = "solid"
        # Add similar logic for other base fields if the target JSON always includes them

        # Remove controlPoint specifically if it's None (as it's often absent in target JSON)
        if 'controlPoint' in data and data['controlPoint'] is None:
             del data['controlPoint']
        # Add similar cleanup for other purely optional fields if needed

        return data

class Diagram(BaseModel):
    version: str = Field("2.0", description="Version of the diagram format")
    shapes: List[DrawingTool] = Field(..., description="List of shapes in the diagram")
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "timestamp": datetime.now().isoformat()
        },
        description="Metadata about the diagram"
    )

    def to_json(self) -> str:
        # Use the custom serialization defined in DrawingTool via model_dump
        # Pydantic v2 handles nested model dumping automatically when calling model_dump on the parent
        diagram_data = self.model_dump(mode='json') # Use mode='json' to trigger @model_serializer
        return json.dumps(diagram_data, indent=2)
