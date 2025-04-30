# Story Diagram Generator

A powerful tool that automatically generates visual diagrams from story text using advanced AI models. This project leverages either Azure OpenAI or Google's Gemini API to analyze stories and create detailed relationship diagrams.

## 🌟 Features

- **Multi-API Support**: Choose between Azure OpenAI or Google's Gemini API
- **Intelligent Story Analysis**: Deep analysis of story elements including:
  - Characters and their relationships
  - Plot structure and themes
  - Locations and events
  - Groups and organizations
  - Objects and their significance
  - Abstract concepts and symbolism
- **Visual Diagram Generation**: Creates detailed JSON-based diagrams that can be visualized
- **Flexible Configuration**: Easy setup through environment variables or command-line arguments

## 🚀 Use Cases

1. **Literary Analysis**: Help students and teachers visualize complex character relationships in literature
2. **Story Planning**: Assist writers in organizing and visualizing their story elements
3. **Content Creation**: Generate visual aids for book reviews or literary discussions
4. **Educational Tools**: Create interactive learning materials for literature classes
5. **Writing Workshops**: Help writers identify gaps in their character development or plot structure

## 📋 Prerequisites

- Python 3.8 or higher
- API key for either:
  - Azure OpenAI API, or
  - Google Gemini API

## 🔧 Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your API configuration:

For Azure OpenAI:
```
API_CHOICE=azure
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
```

For Gemini:
```
API_CHOICE=gemini
GEMINI_API_KEY=your_api_key
GEMINI_MODEL_NAME=gemini-2.0-flash-latest
```

## 💻 Usage

1. Create a text file named `my_story.txt` containing your story text.

2. Run the script:
```bash
# Using Azure OpenAI (default)
python main.py

# Using Gemini
python main.py gemini
```

3. The script will generate a `diagram.json` file containing the visual representation of your story.

## 📊 Output Format

The generated diagram is saved in JSON format with the following structure:
- Shapes representing characters, locations, and other story elements
- Connections showing relationships between elements
- Metadata about the diagram elements

## 🔍 How It Works

1. **Story Analysis**: The AI model analyzes the story text to identify key elements and relationships
2. **Structure Extraction**: The analysis is converted into a structured format
3. **Diagram Generation**: The structured data is transformed into a visual diagram representation
4. **JSON Output**: The diagram is saved in a JSON format that can be used for visualization

## ⚙️ Configuration Options

### Environment Variables
- `API_CHOICE`: Choose between 'azure' or 'gemini'
- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Your Azure OpenAI deployment name
- `GEMINI_API_KEY`: Your Google Gemini API key
- `GEMINI_MODEL_NAME`: Gemini model name (default: gemini-2.0-flash-latest)

### Command Line Arguments
You can override the API choice using command line arguments:
```bash
python main.py azure  # Use Azure OpenAI
python main.py gemini # Use Gemini
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Azure OpenAI API
- Google Gemini API
- All contributors and users of this project 