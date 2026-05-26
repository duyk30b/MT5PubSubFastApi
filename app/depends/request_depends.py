from typing import TypedDict

from fastapi import Request, HTTPException


class RequestState(TypedDict):
    clientId: str
    ip: str
    userId: int | None


class RequestDepends:
    @staticmethod
    def state(request: Request) -> RequestState:
        return {
            "clientId": request.state.clientId,
            "ip": request.state.ip,
            "userId": request.state.userId,
        }

    @staticmethod
    def require_auth(request: Request) -> int:
        userId = request.state.userId
        if not userId:
            raise HTTPException(status_code=401, detail="Authentication required")
        return userId
