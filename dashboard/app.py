import truststore

truststore.inject_into_ssl()  # trust the operating system's certificate store

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from dashboard import paths
from dashboard.routes import demo, eval_routes, metrics, overview

app = FastAPI(title="ENG-07: The Cost of an Agent Is NOT Tokens", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=paths.STATIC), name="static")

app.include_router(overview.router)
app.include_router(demo.router)
app.include_router(metrics.router)
app.include_router(eval_routes.router)
