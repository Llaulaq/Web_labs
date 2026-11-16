import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app")


class AppError(Exception):
    """Ошибка приложения с кодом для клиента и HTTP-статусом."""

    def __init__(self, code: str, message: str, status_code: int = 400, details: Any = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Требуется аутентификация"):
        super().__init__("unauthorized", message, status_code=401)


class ConflictError(AppError):
    def __init__(self, message: str, details: Any = None):
        super().__init__("conflict", message, status_code=409, details=details)


class NotFoundError(AppError):
    def __init__(self, message: str = "Ресурс не найден"):
        super().__init__("not_found", message, status_code=404)


def error_body(code: str, message: str, details: Any = None) -> dict:
    body: dict[str, Any] = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return body


def _format_validation_errors(exc: RequestValidationError) -> dict[str, str]:
    """Сводит ошибки pydantic к виду {поле: сообщение}."""
    fields: dict[str, str] = {}
    for err in exc.errors():
        loc = ".".join(str(part) for part in err["loc"] if part not in ("body", "query", "path"))
        fields[loc or "request"] = err["msg"]
    return fields


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException):
        code = {
            404: "not_found",
            401: "unauthorized",
            403: "forbidden",
            405: "method_not_allowed",
        }.get(exc.status_code, "http_error")
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(code, str(exc.detail)),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        fields = _format_validation_errors(exc)
        logger.warning("Ошибка валидации %s %s: %s", request.method, request.url.path, fields)
        return JSONResponse(
            status_code=422,
            content=error_body("validation_error", "Некорректные данные запроса", fields),
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception):
        # Клиенту — общее сообщение, в лог — полную информацию со стеком
        logger.exception("Необработанная ошибка при %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=error_body("internal_error", "Внутренняя ошибка сервера"),
        )
