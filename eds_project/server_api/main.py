from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from db.database import engine, Base
from db import models
from api.endpoints_auth import router as auth_router
from api.endpoints_docs import router as docs_router
# Автоматичне створення таблиць у PostgreSQL при запуску сервера
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Сервер СЕД",
    description="Бекенд для системи електронного документообігу (Zero Trust)",
    version="1.0.0"
)
# Підключення  маршрутів реєстрації та логіну
app.include_router(auth_router)

app.include_router(docs_router)
# Маршрут для автоматичного редиректу на документацію
@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")

# Тестовий ендпоінт (залишаємо для перевірки)
@app.get("/health")
async def health_check():
    return {"status": "online", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)