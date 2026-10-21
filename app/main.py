from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# 1. Імпортуємо головний роутер версії v1
from app.api.v1.router import api_router

# 2. Створюємо додаток
app = FastAPI(
    title="Baracholka API",
    version="1.0.0",
    docs_url="/docs",      # сторінка Swagger
    redoc_url="/redoc"     # альтернативна документація ReDoc
)

# 3. Налаштовуємо CORS (щоб фронтенд міг надсилати запити без блокувань браузера)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # адреси твого фронтенду (React/Next/Vite)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Підключаємо всі ендпоінти
app.include_router(api_router, prefix="/api/v1")


# 5. Базовий роут для перевірки працездатності сервера (Health Check)
@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "message": "Service is running"}