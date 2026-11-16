def validate_email(email: str) -> bool:
    """Проверка формата email: ровно одна @, непустые локальная и доменная части, точка в домене."""
    if "@" not in email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    local, domain = parts
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    return True
