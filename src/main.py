import os
import uvicorn

from requests import JSONDecodeError
from typing_extensions import Annotated

from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from contextlib import asynccontextmanager

from fastapi_utilities import add_timer_middleware

from src.api.routes.base_routes import base_router
from src.api.routes.auth_routes import auth_router
from src.api.routes.user_routes import user_router
from src.api.routes.enterprise_routes import ent_router
from src.api.routes.stars_payment_routes import stars_payment_router
from src.api.routes.country_routes import country_router
from src.api.routes.boost_routes import boost_router
from src.api.routes.case_routes import case_router
from api.routes.market_routes import market_router

# from src.core.queque import get_broker, get_stream, get_config
from src.settings import get_settings
from loguru import logger as log

cfg = get_settings()


if cfg.run_type != "local":
    from src.telegram.dispatcher import get_dispatcher
    from src.telegram.handlers.base import bot, start_telegram, end_telegram
    from aiogram.types import Update


@asynccontextmanager
async def lifespan(application: FastAPI):
    log.info("🚀 Starting FastAPI application")
    log.info(f"Run type: {cfg.run_type}")
    if cfg.run_type != 'local':
        await start_telegram()
    # await get_broker().start()
    yield
    # await get_broker().close()
    if cfg.run_type != 'local':
        await end_telegram()
    log.info("⛔ Stopping FastAPI application")


app = FastAPI(
    title="Some API",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    root_path="/api/v1",
)

if cfg.run_type == "local":
    add_timer_middleware(app, show_avg=True)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.cors_origins,
    allow_credentials=cfg.cors_credentials,
    allow_methods=cfg.cors_methods,
    allow_headers=cfg.cors_headers
)

app.include_router(base_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(stars_payment_router)
app.include_router(market_router)
app.include_router(ent_router)
app.include_router(country_router)
app.include_router(boost_router)
app.include_router(case_router)


@app.get("/")
def root():
    return 'Hello World!'


@app.post(cfg.webhook_path)
async def bot_webhook(
        request: Request,
        x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None
) -> dict:
    """ Register webhook endpoint for telegram bot"""
    try:
        payload = await request.body()
        if not payload:
            raise HTTPException(status_code=400, detail="Empty payload")

        if x_telegram_bot_api_secret_token != cfg.tg_secret_token:
            cfg.debug and log.error(f"Wrong secret token ! : {x_telegram_bot_api_secret_token}")
            return {"status": "error", "message": "Wrong secret token!"}

        update = await request.json()
        # await get_broker().publish(
        #     stream=cfg.stream_name,
        #     subject=cfg.stream_subject,
        #     message=update
        # )
        update = Update.model_validate(update, context={"bot": bot})
        await get_dispatcher().feed_update(bot, update)
        return {'status': 'ok'}
    except JSONDecodeError:
        return {'status': 'error', 'message': 'Invalid JSON'}
    except HTTPException as e:
        cfg.debug and log.error(f"Ошибка вебхука: {e.detail}")
        return {'status': 'error', 'message': e.detail}



if __name__ == "__main__":
    log.info(f"Current working directory: {os.getcwd()}")
    log.info(f"Python path: {os.environ.get('PYTHONPATH')}")

    try:
        if cfg.run_type == "local":
            # !!! Запустить gunicorn на винде не получится (ибо нет fcntl)
            # но можно запустить в docker контейнере для теста
            uvicorn.run(
                'main:app',
                workers=2,
            )
        elif cfg.run_type == "dev" or cfg.run_type == "prod":
            from core.gunicorn.app_options import get_app_options
            from core.gunicorn.application import Application

            Application(
                application=app,
                options=get_app_options(
                    host=cfg.host,
                    port=cfg.port,
                    timeout=cfg.timeout,
                    workers=cfg.workers,
                    log_level=cfg.log_level,
                ),
            ).run()
    except KeyboardInterrupt:
        print("Приложение было остановлено.")
