from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.analysis import router as analysis_router
from api.auth import router as auth_router
from api.insights import router as insights_router
from api.market_products import alternatives_router, router as market_products_router
from api.price_comparison import router as price_comparison_router
from api.products import router as products_router
from api.purchases import router as purchases_router
from api.saved_products import router as saved_products_router
from api.spending import router as spending_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="Spendly API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router)
app.include_router(auth_router)
app.include_router(insights_router)
app.include_router(market_products_router)
app.include_router(alternatives_router)
app.include_router(price_comparison_router)
app.include_router(products_router)
app.include_router(purchases_router)
app.include_router(saved_products_router)
app.include_router(spending_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
