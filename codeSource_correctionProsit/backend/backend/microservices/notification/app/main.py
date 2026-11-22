"""Notification microservice - entry point.

Run:  uvicorn app.main:app --reload --port 8084
  or: python -m app.main
"""
from contextlib import asynccontextmanager

import py_eureka_client.eureka_client as eureka_client
import os

from fastapi import FastAPI

from app.routers import notification


PORT = int(os.getenv("PORT", "8084"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: register in Eureka
    await eureka_client.init_async(
        eureka_server="http://localhost:8761/eureka",
        app_name="NOTIFICATION",
        instance_id=f"notification:{PORT}",
        instance_host="localhost",
        instance_ip="127.0.0.1",
        instance_port=PORT,
        health_check_url=f"http://localhost:{PORT}/health",
        status_page_url=f"http://localhost:{PORT}/info",
        home_page_url=f"http://localhost:{PORT}/",
    )
    yield
    # Shutdown: unregister from Eureka
    await eureka_client.stop_async()

app = FastAPI(
    title="Notification Microservice API",
    version="1.0.0",
    description=(
        "Notification microservice (Python / FastAPI, no database). "
        "Only the hello endpoint is implemented; the notification logic is to be developed by students."
    ),
    contact={"name": "Badia Abouhdid"},
    servers=[{"url": f"http://localhost:{PORT}", "description": "Local"}],
    # Same URLs as the other microservices of the project
    docs_url="/swagger-ui",       # Swagger UI
    openapi_url="/v3/api-docs",   # OpenAPI JSON
    redoc_url="/redoc",           # alternative documentation
    lifespan=lifespan,
)

app.include_router(notification.router)

# ---- Health and info (used by Eureka) ----
@app.get("/health", tags=["Actuator"], summary="Health check")
def health():
    return {"status": "UP"}


@app.get("/info", tags=["Actuator"], summary="Service information")
def info():
    return {
        "app": {
            "name": "notification",
            "version": app.version,
            "description": "Microservice de gestion des notifications",
        }
    }

# TODO (students): if you add other routers, include them here.


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)
