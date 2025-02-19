import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import init_db
from app.routers import report
from app.models.inference import load_model

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="AI Inference API",
    docs_url="/v1/ssafyA104/AI/docs",
    redoc_url="/v1/ssafyA104/AI/redoc"
)

origins = [
    "http://i12a104.p.ssafy.io",
    "http://localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    report.router,
    prefix="/v1/ssafyA104/AI"
)

tokenizer, model = None, None

@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Application startup complete. Database initialized.")

    tokenizer, model = load_model()
    if model:
        app.state.tokenizer = tokenizer
        app.state.model = model
        logger.info("AI Model loaded successfully and stored in app.state.")
    else:
        logger.error("Failed to load AI model. Check logs for details.")