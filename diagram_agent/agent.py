# diagram_agent/agent.py
from typing import Dict, Any, Optional, List
import json
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from .diagram_generator import DiagramGenerator
from .tools import Position, Size, ImageSource, DrawingTool 
import uuid
import traceback 

class DiagramAgent:

    def __init__(self, openai_api_key: str):
        if not openai_api_key:
            raise ValueError("Azure OpenAI API key is required")

        load_dotenv()

        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if not azure_endpoint:
            raise ValueError("Azure OpenAI endpoint is required in environment variables")

        self.client = AzureOpenAI(
            api_key=openai_api_key,
            api_version="2024-02-01",
            azure_endpoint=azure_endpoint
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "GPT4o")
        self.diagram_generator = DiagramGenerator(canvas_width=1200, canvas_height=1000)
        self.story_analysis = None

    def analyze_story(self, story_text: str) -> Dict[str, Any]:
        if not story_text:
            raise ValueError("Story text cannot be empty")

        try:
            print("\n--- Analyzing Story ---")
            analysis_response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": """You are a comprehensive story analyst. Your task is to deeply analyze the story and provide a structured analysis in JSON format. Include the following components:

200 lines of system prompt, contact personally for the prompt- rittikhalder.ds@gmail.com


RESPOND ONLY WITH A VALID JSON OBJECT containing all these categories, even if some are empty arrays. Ensure all strings are properly escaped and all arrays/objects are properly nested."""},
                    {"role": "user", "content": story_text}
                ],
                temperature=0.3,
                max_tokens=4096,
                response_format={"type": "json_object"}
            )

            content = analysis_response.choices[0].message.content
            if not content:
                raise ValueError("No story analysis content received")

            try:
                analysis = json.loads(content)
                self.story_analysis = analysis
                analysis_file = 'story_analysis.json'
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis, f, indent=2)
                print("Story analysis completed and saved to story_analysis.json")
                return analysis
            except json.JSONDecodeError as e:
                print(f"\nError: Failed to decode JSON from story analysis: {content}\n")
                raise
            except Exception as e:
                print(f"\nError: Failed to process story analysis JSON: {str(e)}\n")
                raise

        except Exception as e:
            print(f"\nError in story analysis step: {str(e)}\n")
            raise ValueError(f"Story analysis failed: {str(e)}")

    def _validate_tool_call(self, tool_call: Dict[str, Any]) -> bool:
        if not isinstance(tool_call, dict) or "tool" not in tool_call or "params" not in tool_call:
            print(f"Warning: Invalid tool call structure: {tool_call}")
            return False

        tool_type = tool_call["tool"]
        params = tool_call["params"]

        if not isinstance(params, dict):
            print(f"Warning: Invalid params structure for tool '{tool_type}': {params}")
            return False

        valid_tools = ["circle", "arrow", "line", "triangle", "star", "text", "image", "rectangle"]
        if tool_type not in valid_tools:
            print(f"Warning: Invalid tool type: {tool_type}")
            return False

        if "position" not in params or not isinstance(params["position"], dict) or \
           "x" not in params["position"] or "y" not in params["position"]:
            print(f"Warning: Missing or invalid position in params for tool '{tool_type}': {params.get('position')}")
            return False

        if "size" not in params or not isinstance(params["size"], dict) or \
           "width" not in params["size"] or "height" not in params["size"]:
            print(f"Warning: Missing or invalid size in params for tool '{tool_type}': {params.get('size')}")
            return False

        if tool_type == "text" and not params.get("text", "").strip():
            print(f"Warning: Skipping empty text tool.")
            return False

        return True

    def _execute_tool_call(self, tool_call: Dict[str, Any]) -> None:
        tool_type = tool_call["tool"]
        params = tool_call["params"]

        try:
            self.diagram_generator.add_shape_from_params(tool_type=tool_type, params=params)
        except ValueError as e:
            print(f"Error executing tool call for {tool_type} with params {params}: {e}")
        except Exception as e:
            print(f"Unexpected error executing tool call for {tool_type}: {e}")

    def generate_diagram_from_analysis(self, prompt: str) -> Dict[str, Any]:
        if not prompt:
            raise ValueError("Prompt cannot be empty")

        if not self.story_analysis:
            try:
                with open('story_analysis.json', 'r', encoding='utf-8') as f:
                    self.story_analysis = json.load(f)
            except Exception as e:
                raise ValueError("No story analysis available. Please run analyze_story first.")

        self.diagram_generator = DiagramGenerator(canvas_width=1200, canvas_height=1000)

        try:
            print("\n--- Generating Diagram from Analysis ---")
            analysis_str = json.dumps(self.story_analysis, indent=2)

            print("\n--- Sending Request to Azure OpenAI ---")
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": DIAGRAM_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Story Analysis:\n```\n{analysis_str}\n```\n\nPrompt:\n```\n{prompt}\n```"}
                ],
                temperature=0.7,
                max_tokens=4096,
                response_format={"type": "json_object"},
                seed=42
            )

            raw_content = response.choices[0].message.content
            if not raw_content:
                raise ValueError("No response content received from Azure OpenAI")

            print("\n--- Received Raw Response ---")
            print(raw_content)
            print("--- End Raw Response ---\n")

            try:
                plan = json.loads(raw_content)
                print("\n--- Parsed Diagram Plan ---")
                print(json.dumps(plan, indent=2))
                print("--- End Parsed Plan ---\n")

                if not isinstance(plan, dict) or "tools" not in plan or not isinstance(plan["tools"], list):
                    raise ValueError("Invalid plan format: Must be a JSON object with a 'tools' array.")

                if not plan["tools"]:
                    print("Warning: Received plan with empty 'tools' array.")
                    return json.loads(self.diagram_generator.generate_diagram().to_json())

                print("\n--- Executing Plan ---")
                valid_tool_calls = 0
                self.diagram_generator = DiagramGenerator(canvas_width=1200, canvas_height=1000)
                for i, tool_call in enumerate(plan["tools"]):
                    print(f"Processing tool call {i+1}: {tool_call.get('tool')}")
                    if self._validate_tool_call(tool_call):
                        self._execute_tool_call(tool_call)
                        valid_tool_calls += 1
                    else:
                        print(f"Skipping invalid tool call {i+1}.")

                print(f"--- Plan Execution Complete ({valid_tool_calls}/{len(plan['tools'])} valid calls executed) ---")

                final_diagram_obj = self.diagram_generator.generate_diagram()
                return json.loads(final_diagram_obj.to_json())

            except json.JSONDecodeError as e:
                print(f"Error: Failed to decode JSON response from Azure OpenAI: {e}")
                print(f"Raw content was:\n{raw_content}")
                cleaned_content = raw_content.strip().removeprefix("```json").removesuffix("```").strip()
                try:
                    plan = json.loads(cleaned_content)
                    print("\n--- Parsed Cleaned Diagram Plan ---")
                    print(json.dumps(plan, indent=2))
                    print("--- End Parsed Cleaned Plan ---\n")

                    if not isinstance(plan, dict) or "tools" not in plan or not isinstance(plan["tools"], list):
                        raise ValueError("Invalid cleaned plan format: Must be a JSON object with a 'tools' array.")

                    if not plan["tools"]:
                        print("Warning: Received cleaned plan with empty 'tools' array.")
                        return json.loads(self.diagram_generator.generate_diagram().to_json())

                    print("\n--- Executing Cleaned Plan ---")
                    valid_tool_calls = 0
                    self.diagram_generator = DiagramGenerator(canvas_width=1200, canvas_height=1000)
                    for i, tool_call in enumerate(plan["tools"]):
                        print(f"Processing tool call {i+1} from cleaned plan: {tool_call.get('tool')}")
                        if self._validate_tool_call(tool_call):
                            self._execute_tool_call(tool_call)
                            valid_tool_calls += 1
                        else:
                            print(f"Skipping invalid tool call {i+1} from cleaned plan.")

                    print(f"--- Cleaned Plan Execution Complete ({valid_tool_calls}/{len(plan['tools'])} valid calls executed) ---")

                    final_diagram_obj = self.diagram_generator.generate_diagram()
                    return json.loads(final_diagram_obj.to_json())

                except Exception as e2:
                    raise ValueError(f"Invalid JSON response from Azure OpenAI, even after cleaning: {e2}")

        except Exception as e:
            print(f"Error during diagram generation: {traceback.format_exc()}")
            raise ValueError(f"Error generating diagram: {str(e)}")


# Define the system prompt content outside the class for better organization
DIAGRAM_SYSTEM_PROMPT = """ 250 line of system promt

Contact personally for the prompt -rittikhalder.ds@gmail.com """

def create_diagram(story_text: str, prompt: str, openai_api_key: str) -> Dict[str, Any]:
    agent = DiagramAgent(openai_api_key)
    agent.analyze_story(story_text)
    return agent.generate_diagram_from_analysis(prompt)
