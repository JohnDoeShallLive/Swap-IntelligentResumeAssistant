# Intelligent Resume Assistant

An agentic AI system for evaluating candidate resumes against job descriptions, asking questions, and getting reliable, sourced answers.

## Architecture
- **Frontend**: Next.js 14, Tailwind CSS, App Router.
- **Backend**: FastAPI, Pydantic, Python 3.11.
- **LLM**: Groq (Llama-3.1-8b)
- **Tools**: PDF Parsing (`pdfplumber`), Keyword Extraction & Skill Matching (`spaCy`).

## Features
- **Upload & Parse**: Ingests PDF or text resumes and extracts core details.
- **Agentic Q&A Chat**: Ask questions about the candidate. The system will strictly attribute answers to the resume or flag missing data.
- **Skill Matching**: Compare a resume against a job description.

## Setup Instructions

### Prerequisites
- Python 3.11
- Node.js 18+
- Docker & Docker Compose (optional for local deployment)

### Environment Variables
1. Copy `.env.example` to `backend/.env`
2. Provide your `GROQ_API_KEY`.
3. In `frontend/`, copy `.env.local.example` to `.env.local`.

### Local Execution (No Docker)
**Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Docker Execution
```bash
docker-compose up --build
```
Navigate to `http://localhost:3000`.

## Design Decisions & Trade-offs
- Used `Groq` instead of OpenAI for zero-cost, high-performance structured JSON inference.
- Utilized heuristic and regex-based parsing to extract base resume data before engaging the LLM to save token limits and increase deterministic behavior.
- Built a custom agent loop in Python to clearly demonstrate the underlying process (Intent -> Tool -> Context -> LLM) without black-box framework abstractions like LangChain.
