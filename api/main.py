from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

app = FastAPI(title="Saúde GO API")

# ⬇️ ADICIONE ISTO
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # pode filtrar depois
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# se estiver usando frontend na porta 8000, pode trocar:
# allow_origins=["http://localhost:8000"]

app.include_router(router)
