import logging

from fastapi import FastAPI, Request

from app.errors import install_exception_handlers
from app.users import router as users_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(title="Web Labs API", version="1.0.0")
install_exception_handlers(app)
app.include_router(users_router)


@app.get("/")
def root():
    return {
        "service": "web-labs-api",
        "version": "1.0.0",
        "endpoints": ["/", "/health", "/echo"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/debug/boom")
def boom():
    """Демонстрация обработки необработанной ошибки (500)."""
    raise RuntimeError("Преднамеренная ошибка для демонстрации")


@app.get("/echo")
def echo(request: Request):
    """Возвращает детали HTTP-запроса — для изучения структуры запроса/ответа."""
    return {
        "method": request.method,
        "url": str(request.url),
        "http_version": request.scope["http_version"],
        "headers": dict(request.headers),
        "client": request.client.host if request.client else None,
        "query_params": dict(request.query_params),
    }
