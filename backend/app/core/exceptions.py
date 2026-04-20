from fastapi import HTTPException, status


class AppError(HTTPException):
    pass


class NotFoundError(AppError):
    def __init__(self, detail: str = "Not found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenError(AppError):
    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class UnauthorizedError(AppError):
    def __init__(self, detail: str = "Unauthorized") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ConflictError(AppError):
    def __init__(self, detail: str = "Conflict") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ValidationError(AppError):
    def __init__(self, detail: str = "Validation error") -> None:
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class BadRequestError(AppError):
    def __init__(self, detail: str = "Bad request") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class SubscriptionError(AppError):
    def __init__(self, detail: str = "Subscription required or limit reached") -> None:
        super().__init__(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=detail)
