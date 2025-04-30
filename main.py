import os
import json
from dotenv import load_dotenv
from diagram_agent import create_diagram

def main():
    # Load environment variables
    load_dotenv()
    
    # Get Azure OpenAI configuration
    openai_api_key = os.getenv('AZURE_OPENAI_API_KEY')
    azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'GPT4o')
    
    if not all([openai_api_key, azure_endpoint]):
        print("Error: Required Azure OpenAI configuration not found in environment variables")
        print("Please ensure AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT are set")
        return
    
    # Read story from file
    try:
        with open('my_story.txt', 'r', encoding='utf-8', errors='replace') as f:
            story_text = f.read()
    except Exception as e:
        print(f"Error reading story file: {str(e)}")
        return
    
    # Create diagram
    try:
        # We know openai_api_key is not None here because of the check above
        diagram = create_diagram(
            story_text=story_text,
            prompt="Generate a diagram showing the main characters and their relationships (if relationship exists) in the story.",
            openai_api_key=openai_api_key  # type: ignore
        )
        
        # Save diagram to file
        try:
            with open('diagram.json', 'w', encoding='utf-8') as f:
                json.dump(diagram, f, indent=2)
            
            # Verify the file was created and contains valid JSON
            try:
                with open('diagram.json', 'r', encoding='utf-8') as f:
                    json.load(f)  # Verify JSON is valid
                print("Diagram created successfully and saved to diagram.json")
                print(f"Diagram contains {len(diagram.get('shapes', []))} shapes")
            except json.JSONDecodeError:
                print("Error: Saved diagram.json contains invalid JSON")
            except Exception as e:
                print(f"Error verifying diagram.json: {str(e)}")
                
        except Exception as e:
            print(f"Error saving diagram to file: {str(e)}")
        
    except Exception as e:
        print(f"Error creating diagram: {str(e)}")

if __name__ == "__main__":
    main() 
