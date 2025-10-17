# 🛡️ Safeguard AI

<div align="center">

**AI-Powered Video Intelligence for Law Enforcement & Training**

*Ask natural-language questions about incident videos and get instant, timestamped, explainable answers.*

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.1-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)

</div>

---

## 🌟 Overview

**Safeguard AI** is an intelligent video analysis system designed specifically for law enforcement, investigators, and training professionals. It transforms hours of body camera footage, traffic stops, and training sessions into searchable, queryable data that can be accessed through simple natural language questions.

### 🎯 The Problem We Solve

- **Manual Review is Time-Consuming**: Officers and investigators spend countless hours reviewing video footage frame by frame
- **Critical Details Are Missed**: Important moments can be overlooked in lengthy recordings
- **Training Is Inefficient**: Finding specific examples in training videos is tedious and imprecise
- **Documentation Is Incomplete**: Incident reports often lack precise timestamps and visual context

### ✨ Our Solution

Safeguard AI uses advanced AI and machine learning to:
- 🔍 **Semantic Search**: Ask questions like *"When did the suspect reach for their waistband?"* and get exact timestamps
- 🎥 **Frame Analysis**: Every frame is analyzed using vision AI to understand what's happening visually
- 📝 **Transcript Intelligence**: Audio transcripts are processed and linked to visual data for comprehensive understanding
- 🧠 **Contextual Reasoning**: Our AI agent understands context and provides explainable answers with evidence
- ⚡ **Real-Time Response**: Get answers in seconds, not hours

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React + TypeScript)            │
│                     Natural Language Query Interface             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               │ REST API
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    Backend (FastAPI)                             │
│                  Request Handling & Routing                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
┌───────────────▼────────────┐   ┌───────────▼──────────────────┐
│   LLM Agent System         │   │   Video Processing Pipeline   │
│                            │   │                               │
│  • Query Router            │   │  • Frame Extraction           │
│  • Reasoner Agent          │   │  • Vision AI Analysis         │
│  • LangChain Integration   │   │  • Audio Transcription        │
│  • Gemini & OpenAI         │   │  • Embedding Generation       │
└───────────────┬────────────┘   └───────────┬──────────────────┘
                │                             │
                └──────────────┬──────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    MongoDB Atlas                                 │
│                                                                  │
│  Collections:                                                    │
│  • video_intelligence_metadata  (Video info & paths)            │
│  • frame_intelligence_metadata  (Frame analysis + embeddings)   │
│  • video_intelligence_transcripts (Audio transcripts)           │
│                                                                  │
│  Vector Search Indexes:                                          │
│  • Frame embeddings (visual similarity)                          │
│  • Transcript embeddings (semantic search)                       │
│  • Hybrid search (scalar + vector)                               │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Features

### 1. **Intelligent Video Processing**
- Automatically extracts frames at configurable intervals (default: 2 seconds)
- Generates detailed descriptions using vision AI (OpenAI GPT-4 Vision)
- Creates vector embeddings for semantic similarity search
- Processes audio and generates searchable transcripts

### 2. **Advanced Search Capabilities**
- **Vector Search**: Find visually similar moments across videos
- **Full-Text Search**: Search through transcripts and frame descriptions
- **Hybrid Search**: Combine vector and text search with adjustable weights
- **Multi-Modal**: Search across both visual and audio content simultaneously

### 3. **AI-Powered Query Understanding**
- Natural language query interpretation
- Context-aware reasoning using LangChain agents
- Query routing to optimize search strategy
- Explainable results with confidence scores

### 4. **User-Friendly Interface**
- Clean, intuitive chat interface
- Real-time video playback at relevant timestamps
- Visual feedback and loading states
- Responsive design for desktop and mobile

---

## 📦 Tech Stack

### **Backend**
- **FastAPI** - Modern, high-performance web framework
- **Python 3.10+** - Core language
- **LangChain** - AI agent orchestration
- **LangGraph** - Agent workflow management
- **OpenAI GPT-4** - Vision analysis and reasoning
- **Google Gemini** - Alternative LLM for reasoning
- **Voyage AI** - Vector embeddings
- **MongoDB** - Vector database and data storage
- **OpenCV** - Video frame extraction
- **yt-dlp** - Video processing utilities

### **Frontend**
- **React 19** - UI framework
- **TypeScript** - Type-safe development
- **Vite** - Build tool and dev server
- **CSS3** - Styling

### **AI/ML Stack**
- **LangChain** - Agent framework
- **Vector Embeddings** - Semantic search
- **Vision AI** - Frame understanding
- **Speech-to-Text** - Audio transcription
- **Hybrid Search** - Multi-modal retrieval

---

## 🛠️ Installation & Setup

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** and npm
- **MongoDB Atlas** account (or local MongoDB instance)
- **API Keys**:
  - OpenAI API key
  - Voyage AI API key
  - Google Gemini API key (optional)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/safeguard-ai.git
cd safeguard-ai
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
python -m venv env
source env/bin/activate  # On macOS/Linux
# env\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys:
# OPENAI_API_KEY=your_openai_key
# VOYAGE_API_KEY=your_voyage_key
# GEMINI_API_KEY=your_gemini_key
# MONGODB_URI=your_mongodb_connection_string
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure API endpoint (if needed)
# Edit src/App.tsx to point to your backend URL
```

### 4. MongoDB Setup

1. Create a MongoDB Atlas cluster (or use local MongoDB)
2. Create a database named `video_intelligence`
3. Create collections:
   - `video_intelligence_metadata`
   - `frame_intelligence_metadata`
   - `video_intelligence_transcripts`
4. Create vector search indexes (see Configuration section)

---

## ⚙️ Configuration

### MongoDB Vector Search Indexes

You need to create vector search indexes for semantic search to work:

#### Frame Embeddings Index
```javascript
{
  "mappings": {
    "dynamic": true,
    "fields": {
      "embedding": {
        "type": "knnVector",
        "dimensions": 1024,
        "similarity": "cosine"
      }
    }
  }
}
```

#### Transcript Embeddings Index
```javascript
{
  "mappings": {
    "dynamic": true,
    "fields": {
      "embedding": {
        "type": "knnVector",
        "dimensions": 1024,
        "similarity": "cosine"
      }
    }
  }
}
```

### Environment Variables

Create a `.env` file in the root directory:

```env
# API Keys
OPENAI_API_KEY=sk-...
VOYAGE_API_KEY=...
GEMINI_API_KEY=...

# MongoDB
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DB_NAME=video_intelligence

# Video Storage
VIDEO_FOLDER=/path/to/your/videos
FRAMES_FOLDER=/path/to/frame/output

# API Configuration
BACKEND_PORT=8000
FRONTEND_PORT=5173
```

---

## 🎮 Usage

### Starting the Application

#### Terminal 1: Backend Server
```bash
# From project root
source env/bin/activate
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2: Frontend Dev Server
```bash
# From project root
cd frontend
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Processing Videos

1. **Add videos** to your `videos/` folder

2. **Process a video**:
```python
from llm.video_to_image import extract_frames
from llm.gen_frame_desc import generate_frame_descriptions
from llm.process_frames import process_and_store_frames
from transcripts.audio import process_video_transcript

# Extract frames
extract_frames("videos/incident_video.mp4", interval_seconds=2)

# Generate AI descriptions
generate_frame_descriptions()

# Store in MongoDB with embeddings
process_and_store_frames()

# Process audio transcript
process_video_transcript("videos/incident_video.mp4")
```

3. **Query the video**:
   - Open the frontend at http://localhost:5173
   - Type your question: *"When did the officer issue a warning?"*
   - Get instant results with video timestamps

---

## 📚 Project Structure

```
safeguard-ai/
├── backend/              # FastAPI backend server
│   ├── main.py          # API endpoints and CORS setup
│   └── requirements.txt # Backend dependencies
│
├── frontend/            # React + TypeScript UI
│   ├── src/
│   │   ├── App.tsx     # Main application component
│   │   ├── App.css     # Styles
│   │   └── main.tsx    # Entry point
│   ├── public/         # Static assets
│   └── package.json    # Frontend dependencies
│
├── llm/                # AI/ML core logic
│   ├── inference.py    # Semantic search functions
│   ├── mongo_client_1.py # MongoDB connection & collections
│   ├── video_to_image.py # Frame extraction
│   ├── gen_frame_desc.py # Vision AI descriptions
│   ├── process_frames.py # Embedding generation & storage
│   ├── get_voyage_embed.py # Voyage AI embeddings
│   ├── retreival_2.py  # Hybrid search logic
│   ├── agent.py        # LangChain agent setup
│   └── query_model/    # Query processing
│       ├── router.py   # Query routing logic
│       └── reasoner.py # AI reasoning agent
│
├── transcripts/        # Audio processing
│   ├── video2audio.py # Audio extraction
│   └── audio.py       # Transcription & storage
│
├── videos/            # Video storage
├── frames/            # Extracted frames
└── requirements.txt   # Python dependencies
```

---

## 🔍 How It Works

### 1. **Video Ingestion**
When a video is uploaded:
1. Video is stored with metadata (name, path, duration)
2. Frames are extracted every N seconds
3. Audio is extracted and transcribed
4. All data is linked via video_id

### 2. **Frame Analysis**
For each frame:
1. Image is encoded to base64
2. Sent to OpenAI GPT-4 Vision for description
3. Description is converted to vector embedding (Voyage AI)
4. Stored in MongoDB with timestamp and video reference

### 3. **Transcript Processing**
For audio:
1. Audio is extracted from video
2. Transcribed using speech-to-text
3. Split into chunks with timestamps
4. Each chunk gets vector embedding
5. Stored in MongoDB with video reference

### 4. **Query Processing**
When a user asks a question:
1. **Query Router** analyzes the question type
2. **Embedding** is generated for the query
3. **Hybrid Search** executes:
   - Vector search finds semantically similar frames/transcripts
   - Full-text search finds keyword matches
   - Results are merged and ranked
4. **Reasoner Agent** synthesizes results:
   - Analyzes top matches
   - Generates natural language answer
   - Provides timestamps and confidence scores
5. **Response** returns answer + video clips

### 5. **Result Presentation**
- Chat interface displays AI-generated answer
- Video player shows relevant clips at exact timestamps
- Users can review evidence and context

---

## 🎯 Use Cases

### Law Enforcement
- 📹 **Body Camera Review**: Quickly find specific moments in hours of footage
- 🚔 **Traffic Stop Analysis**: Search for compliance issues or noteworthy interactions
- 🔍 **Evidence Discovery**: Locate specific actions, objects, or statements
- 📊 **Pattern Detection**: Identify recurring situations across multiple incidents

### Training
- 👮 **Scenario Review**: Find specific training scenarios for debriefing
- 📚 **Best Practices**: Search for examples of proper procedures
- ⚠️ **Learning Moments**: Identify situations that need additional training
- 🎓 **Curriculum Development**: Build training libraries with searchable content

### Investigations
- 🕵️ **Case Building**: Gather timestamped evidence efficiently
- 📝 **Report Generation**: Create detailed reports with video references
- 🔗 **Cross-Reference**: Link related incidents across multiple videos
- ⏱️ **Timeline Construction**: Build accurate timelines of events

---

## 🔐 Privacy & Security

- **Data Encryption**: All data stored in MongoDB Atlas with encryption at rest
- **API Security**: API endpoints should be secured with authentication (implement JWT)
- **Video Storage**: Videos stored locally; can be configured for secure cloud storage
- **Audit Trail**: All queries and access can be logged for compliance
- **GDPR Compliance**: Personal data handling follows best practices
- **Role-Based Access**: (Recommended implementation) Different permission levels

> ⚠️ **Important**: This is a prototype. For production deployment, implement proper authentication, encryption, and access controls.

---

## 🚧 Roadmap

- [ ] **Authentication & Authorization** - JWT-based user management
- [ ] **Multi-Tenant Support** - Department/organization isolation
- [ ] **Advanced Analytics** - Dashboard with insights and trends
- [ ] **Mobile App** - iOS/Android apps for field use
- [ ] **Real-Time Processing** - Live video analysis from body cameras
- [ ] **Export Features** - Generate reports, clips, and documentation
- [ ] **Integration APIs** - Connect with RMS, CAD systems
- [ ] **Advanced AI Models** - Object detection, face recognition, action recognition
- [ ] **Collaborative Features** - Annotations, comments, sharing
- [ ] **Performance Optimization** - Caching, CDN, edge processing

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **OpenAI** - GPT-4 Vision for frame analysis
- **Voyage AI** - High-quality embeddings
- **MongoDB** - Vector search capabilities
- **LangChain** - Agent framework
- **FastAPI** - Excellent web framework
- **React** - Modern UI development

---

## 📧 Contact

For questions, support, or collaboration:

- **Project Lead**: [Your Name]
- **Email**: [your.email@example.com]
- **GitHub**: [@yourusername](https://github.com/yourusername)

---

<div align="center">

**Built with ❤️ for safer communities**

⭐ Star this repo if you find it useful!

</div>

