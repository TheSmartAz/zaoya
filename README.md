# Zaoya (造鸭)

AI-powered mobile page generator - Create mobile web pages through chat.

## Project Structure

```
zaoya/
├── frontend/       # Vite + React + TypeScript
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── hooks/       # Custom hooks
│   │   ├── pages/       # Page components
│   │   ├── stores/      # Zustand state
│   │   ├── types/       # TypeScript types
│   │   └── utils/       # Utilities
│   └── public/
│       └── zaoya-runtime.js  # Runtime for generated pages
├── backend/        # FastAPI Python
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── services/    # Business logic
│   │   └── models/      # Pydantic models
│   └── requirements.txt
└── docs/           # Documentation
```

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Usage

1. Type a description of the mobile page you want
2. AI generates HTML with Tailwind CSS
3. Preview appears in the phone frame on the right
4. Generated code uses Zaoya.* helpers for interactivity

## Tech Stack

- **Frontend**: Vite, React, TypeScript, Tailwind CSS, Zustand
- **Backend**: FastAPI, Uvicorn, OpenAI SDK
- **AI Models**: GLM-4.7, DeepSeek, Doubao, Qwen, Hunyuan, Kimi, MiniMax

## Development

### Running both servers

Terminal 1 (Backend):
```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload
```

Terminal 2 (Frontend):
```bash
cd frontend && npm run dev
```

### Environment Variables

See `backend/.env.example` for all required API keys.

## License

MIT
