# diagram_agent/diagram_generator.py
from typing import Dict, Any, List, Optional, Literal
# Ensure all necessary tools are imported
from .tools import Diagram, DrawingTool, Position, Size, ImageSource
from datetime import datetime
import uuid
import math # Needed for hypot in circle validation (optional)

class DiagramGenerator:

    def __init__(self, canvas_width: int = 1200, canvas_height: int = 1000):
        if canvas_width <= 0 or canvas_height <= 0:
            raise ValueError("Canvas dimensions must be positive")
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.shapes: List[DrawingTool] = []

    def _validate_position(self, x: float, y: float) -> None:
        # Relaxed validation - uncomment if strict bounds checking is needed
        # if x < 0 or x > self.canvas_width or y < 0 or y > self.canvas_height:
        #     print(f"Warning: Position ({x}, {y}) may be outside canvas bounds ({self.canvas_width}x{self.canvas_height})")
        pass

    def _create_tool_from_params(self, tool_type: Literal["circle", "arrow", "line", "triangle", "star", "text", "image", "rectangle"],
                                 params: Dict[str, Any]) -> DrawingTool:
        # Ensure basic structure
        if "position" not in params or "size" not in params:
             raise ValueError(f"Tool '{tool_type}' missing required position or size parameters.")

        # Extract required base fields with defaults matching the target JSON structure
        pos_data = params["position"]
        size_data = params["size"]
        position = Position(x=float(pos_data.get("x", 0)), y=float(pos_data.get("y", 0)))
        # Size interpretation depends on shape: width/height for most, vector for line/arrow
        size = Size(width=float(size_data.get("width", 1)), height=float(size_data.get("height", 1)))

        color = int(params.get("color", 4278190080)) # Default black ARGB
        # Default stroke width based on type (matches target JSON examples)
        stroke_width = int(params.get("strokeWidth", 1 if tool_type == "text" or tool_type == "image" else 2))
        rotation = float(params.get("rotation", 0.0))
        stroke_type = params.get("strokeType", "solid")
         # Default canBeOverlapped based on type (matches target JSON examples)
        can_be_overlapped = bool(params.get("canBeOverlapped", False if tool_type == "text" or tool_type == "image" else True))

        # Prepare creation arguments for the DrawingTool model
        tool_args = {
            "id": str(uuid.uuid4()),
            "type": tool_type,
            "position": position,
            "size": size,
            "color": color,
            "strokeWidth": stroke_width,
            "rotation": rotation,
            "strokeType": stroke_type,
            "canBeOverlapped": can_be_overlapped,
        }

        # Add optional fields based on type and presence in params
        if tool_type == "text":
            tool_args["text"] = params.get("text", "") # Default to empty string if missing
            tool_args["fontSize"] = int(params.get("fontSize", 16))
            tool_args["fontFamily"] = params.get("fontFamily", "Roboto")
            tool_args["isBold"] = bool(params.get("isBold", False))
            tool_args["isItalic"] = bool(params.get("isItalic", False))
            tool_args["isStrikethrough"] = bool(params.get("isStrikethrough", False))
            tool_args["textAlignment"] = params.get("textAlignment", "left")
            tool_args["isFixedWidth"] = bool(params.get("isFixedWidth", True))
            # Override potentially incorrect defaults coming from params for text
            tool_args["strokeWidth"] = 1
            tool_args["canBeOverlapped"] = False

        elif tool_type == "image":
            img_src_data = params.get("imageSource")
            img_name = params.get("imageName") # Get top-level imageName if present
            # Ensure imageSource is valid before trying to access url
            if isinstance(img_src_data, dict) and "url" in img_src_data:
                 tool_args["imageSource"] = ImageSource(
                     sourceType=img_src_data.get("sourceType", "network"),
                     url=img_src_data.get("url"),
                     imageName=img_src_data.get("imageName", img_name) # Prioritize inner imageName
                 )
                 # Ensure top-level imageName matches or is set
                 tool_args["imageName"] = tool_args["imageSource"].imageName or (tool_args["imageSource"].url.split("/")[-1] if tool_args["imageSource"].url else None)
            elif img_name: # Fallback if only top-level imageName is provided (unlikely based on prompt)
                 print(f"Warning: Image tool called without valid imageSource, using imageName '{img_name}' only.")
                 tool_args["imageName"] = img_name
            else:
                 print(f"Warning: Invalid or missing imageSource/imageName for image tool: {params}")
                 # Raise error as image is unusable without source/name
                 raise ValueError("Image tool requires valid imageSource with URL or imageName")

            tool_args["maintainAspectRatio"] = bool(params.get("maintainAspectRatio", True))
            # Override potentially incorrect defaults coming from params for image
            tool_args["strokeWidth"] = 1
            tool_args["canBeOverlapped"] = False

        elif tool_type in ["arrow", "line", "circle"]: # Add circle if it can have controlPoint
            cp_data = params.get("controlPoint")
            if cp_data and isinstance(cp_data, dict) and "x" in cp_data and "y" in cp_data:
                 tool_args["controlPoint"] = Position(x=float(cp_data["x"]), y=float(cp_data["y"]))
            # Ensure specific defaults for these shapes match target JSON
            tool_args["strokeWidth"] = 2
            tool_args["canBeOverlapped"] = True

        else: # rectangle, triangle, star
             # Ensure specific defaults for these shapes match target JSON
             tool_args["strokeWidth"] = 2
             tool_args["canBeOverlapped"] = True

        # Validate position (optional check)
        self._validate_position(position.x, position.y)
        if tool_args.get("controlPoint"):
             self._validate_position(tool_args["controlPoint"].x, tool_args["controlPoint"].y)

        # Create the tool using Pydantic validation
        try:
             tool = DrawingTool(**tool_args)
             return tool
        except Exception as e:
             print(f"Error creating DrawingTool model for type {tool_type} with args {tool_args}: {e}")
             # Optionally include more details about the Pydantic validation error if available
             raise # Re-raise the error after logging


    def add_shape_from_params(self, tool_type: Literal["circle", "arrow", "line", "triangle", "star", "text", "image", "rectangle"],
                              params: Dict[str, Any]) -> None:
        try:
            tool = self._create_tool_from_params(tool_type, params)
            if tool: # Ensure tool creation was successful
                 self.shapes.append(tool)
        except Exception as e:
            # Log the error but continue processing other shapes if possible
            print(f"Failed to add shape type {tool_type} with params {params}. Error: {e}")
            # Remove the `raise` if you want the process to continue even if one shape fails


    def add_rectangle(self, x: float, y: float, width: float, height: float, params: Optional[Dict[str, Any]] = None) -> None:
        self._validate_position(x, y)
        if width <= 0 or height <= 0:
            print(f"Warning: Non-positive dimensions for rectangle ({width}x{height}). Using absolute values.")
            width = abs(width) or 1 # Use 1 if 0
            height = abs(height) or 1 # Use 1 if 0

        if params is None: params = {}
        # Construct the parameters dictionary expected by add_shape_from_params
        base_params = {
            "position": {"x": x, "y": y},
            "size": {"width": width, "height": height},
            "color": params.get("color", 4278190080),
            "strokeWidth": params.get("strokeWidth", 2),
            "rotation": params.get("rotation", 0.0),
            "strokeType": params.get("strokeType", "solid"),
            "canBeOverlapped": params.get("canBeOverlapped", True),
        }
        self.add_shape_from_params("rectangle", base_params)

    def add_circle(self, x: float, y: float, radius: float, params: Optional[Dict[str, Any]] = None) -> None:
        if radius <= 0:
            print(f"Warning: Non-positive radius for circle ({radius}). Using absolute value or 1.")
            radius = abs(radius) or 1

        # Position for the tool is top-left of bounding box
        top_left_x = x - radius
        top_left_y = y - radius
        diameter = radius * 2
        self._validate_position(top_left_x, top_left_y) # Validate top-left

        if params is None: params = {}
        base_params = {
            "position": {"x": top_left_x, "y": top_left_y},
            "size": {"width": diameter, "height": diameter},
            "color": params.get("color", 4278190080),
            "strokeWidth": params.get("strokeWidth", 2),
            "rotation": params.get("rotation", 0.0),
            "strokeType": params.get("strokeType", "solid"),
            "canBeOverlapped": params.get("canBeOverlapped", True),
            "controlPoint": params.get("controlPoint") # Pass controlPoint if provided
        }
        self.add_shape_from_params("circle", base_params)

#
# --------------SAME FOR OTHER TOOLS---------CANT SHARE HERE PLEASE CONTACT PERSONALLY----------RITTIKHALDER.DS@GMAIL.COM---
#

    def generate_diagram(self) -> Diagram:
        if not self.shapes:
             print("Warning: Generating diagram with no shapes.")
             #Ignore this for now
             return Diagram(shapes=[], metadata={"timestamp": datetime.now().isoformat()})

        return Diagram(
            version="2.0",
            shapes=self.shapes,
            metadata={
                "timestamp": datetime.now().isoformat()
            }
        )
