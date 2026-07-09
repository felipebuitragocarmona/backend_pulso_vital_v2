import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from presentation.rest.routes import router

load_dotenv()

app = FastAPI(
    title="Medical ECG API",
    description="API por capas para gestionar pacientes y PDFs ECG exportados desde Apple Watch.",
    version="2.0.0",
)
app.include_router(router)

# Permite servir/consultar los PDF guardados si se requiere desde navegador o cliente HTTP.
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
