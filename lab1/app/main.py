from fastapi import FastAPI, Request

app = FastAPI(title="Web Labs API", version="1.0.0")


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
