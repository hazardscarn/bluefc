# BlueFC - AI-Powered Football Content & Merchandise Platform

BlueFC is an advanced AI platform that combines intelligent merchandise recommendations with automated content creation for football fans. Built with Google's Agent Development Kit (ADK) and powered by Gemini models, it delivers personalized experiences through two specialized AI agents.

## 🏗️ Architecture Overview

```
bluefc/
├── contentagent/          # Content creation agent
├── merchagent/           # Merchandise recommendation agent  
├── src/                  # Shared utilities and configurations
├── simple_app.py         # Streamlit web application
├── requirements.txt      # Main dependencies
├── Dockerfile           # Container deployment
└── deploy_*.py          # Cloud deployment scripts
```

## 🤖 AI Agents

### 1. ContentAgent
A sophisticated content creation agent that generates professional Chelsea FC video content.

**Capabilities:**
- **Scene Generation**: Creates detailed video scene structures
- **Image Creation**: Generates cartoonistic Chelsea FC themed images using Imagen models
- **Audio Production**: Converts scripts to professional narration using Google Text-to-Speech
- **Video Assembly**: Combines images and audio into complete video content

**Core Components:**
- `content_agents.py` - Main agent coordination and pipeline management
- Scene structure planning and storyboard creation
- Multi-step content generation pipeline (scenes → images → audio → video)
- Cultural and audience-aware content adaptation

### 2. MerchAgent  
An intelligent merchandise recommendation system with cultural personalization.

**Capabilities:**
- **Signal Detection**: Extracts demographic signals (age, gender, location) from user queries
- **Audience Analysis**: Identifies specific interests and audience segments 
- **Cultural Insights**: Generates detailed cultural and demographic insights
- **Product Recommendations**: Provides personalized product suggestions with detailed reasoning
- **Image Customization**: Creates culturally-adapted product images using Gemini 2.0 Flash

**Workflow:**
1. Extract demographics from user input
2. Detect specific audiences/interests  
3. Generate cultural insights report
4. Create consumer persona
5. Provide personalized recommendations
6. Customize product images (optional)

**Example Usage:**
```
Standard: "What products for sports fans under 40 with no kids in LA?"
Customization: "Can you customize product prod_244 for this audience?"
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.11+
- Google Cloud Project with Vertex AI enabled
- Google API key or Google Cloud authentication

### 1. Clone Repository
```bash
git clone https://github.com/hazardscarn/bluefc.git
cd bluefc
```

### 2. Environment Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory:

```env
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=TRUE

# API Keys (if using Google AI Studio instead)
GOOGLE_API_KEY=your-api-key-here

# Agent Resources (update with your deployed agent IDs)
RESOURCE_ID=your-merchagent-resource-id
CONTENT_RESOURCE_ID=your-contentagent-resource-id
```

### 4. Agent-Specific Dependencies

**For ContentAgent:**
```bash
cd contentagent
pip install -r requirements.txt
```

**For MerchAgent:**
```bash
cd merchagent  
pip install -r requirements.txt
```

## 🌐 Running the Streamlit Application

### Local Development
```bash
# From project root
streamlit run simple_app.py --server.port=8080 --server.address=0.0.0.0
```

### Using Docker
```bash
# Build image
docker build -t bluefc .

# Run container
docker run -p 8080:8080 bluefc
```

### Access the Application
- Local: http://localhost:8080
- Docker: http://localhost:8080

## 📱 Application Features

The Streamlit app provides a modern, responsive interface with:

- **Home**: Overview and navigation
- **Recommendations**: Interactive merchandise recommendations with cultural insights
- **Customization**: Product image customization based on user personas  
- **Content Creation**: Video content generation for Chelsea FC
- **About**: Platform information and features

### Key UI Components
- Real-time agent communication
- Dynamic content updates during streaming
- Cultural insights visualization
- Product recommendation cards
- Video generation progress tracking

## ☁️ Cloud Deployment

### Deploy ContentAgent
```bash
python deploy_contentagent_to_agent_engine.py
```

### Deploy MerchAgent  
```bash
python deploy_merchagent_to_agent_engine.py
```

Both scripts will:
- Validate prerequisites
- Deploy agents to Google Cloud Agent Engine
- Run integration tests
- Provide access URLs

### Access Deployed Agents
After deployment, access agents at:
```
https://console.cloud.google.com/vertex-ai/reasoning-engines?project=YOUR_PROJECT_ID
```

## 🛠️ Development

### Project Structure Details

**ContentAgent** (`/contentagent/`)
- `agent.py` - Main agent definition
- `content_agents.py` - Agent pipeline and coordination
- `tools.py` - Content generation tools
- `config.py` - Configuration management

**MerchAgent** (`/merchagent/`)
- `agent.py` - Main agent definition  
- `tools.py` - Recommendation and customization tools
- `audience_agent.py` - Audience detection sub-agent
- `subagent.py` - Product recommendation sub-agent
- `product_customization.py` - Image customization functionality

**Shared** (`/src/`)
- `qloo.py` - External API integrations
- `secret_manager.py` - Secure configuration management

### Key Dependencies
- `google-cloud-aiplatform[adk,agent_engines]>=1.96.0` - Core Agent Engine
- `google-adk>=0.1.0` - Agent Development Kit
- `vertexai>=1.0.0` - Vertex AI integration
- `streamlit>=1.25.0` - Web application framework
- `moviepy==2.2.1` - Video processing (ContentAgent)
- `supabase>=2.0.0` - Database integration (MerchAgent)

## 🧪 Testing

### Test MerchAgent
```bash
# Standard recommendation flow
"What products for soccer fans in New York?"

# Image customization  
"Can you customize product prod_123 for sports fans in London?"
```

### Test ContentAgent
```bash
# Video content creation
"Create a Chelsea FC highlight video about recent victories"
```

## 📊 Features & Capabilities

### Advanced AI Features
- **Multi-modal Generation**: Text, image, audio, and video content
- **Cultural Personalization**: Audience-aware customization
- **Real-time Streaming**: Live agent communication
- **Sequential Processing**: Multi-step agent workflows

### Technical Features  
- **Containerized Deployment**: Docker support for easy deployment
- **Cloud-Native**: Google Cloud integration with Vertex AI
- **Scalable Architecture**: Microservices-based agent design
- **Secure Configuration**: Secret management and API key protection

## 🔧 Configuration

### Model Configuration
Models are configured in `src/config.py`:
- `gemini-2.5-flash` - Primary model for fast responses
- `gemini-2.5-pro` - Advanced model for complex tasks  
- `gemini-2.0-flash-lite-001` - Lightweight model for simple operations
- `imagen-4.0-generate-preview-06-06` - Image generation

### Custom Configuration
Modify `merchagent/config.py` and `contentagent/config.py` for agent-specific settings.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and support:
1. Check the project documentation
2. Review Google Cloud Agent Engine documentation
3. Open an issue on GitHub
4. Contact the development team

## 🚀 Getting Started Quick Guide

1. **Clone** the repository
2. **Install** dependencies with `pip install -r requirements.txt`
3. **Configure** environment variables in `.env`
4. **Run** the app with `streamlit run simple_app.py`
5. **Access** at http://localhost:8080
6. **Test** with "What products for Chelsea fans in London?"

---

**Built with ❤️ for football fans worldwide by David Babu**