import logging.config

import uvicorn
import yaml
from fastapi import FastAPI

from src.routes import register_routes
from src.services import base_init

app = FastAPI()
register_routes(app)


if __name__ == "__main__":
    with open("src/config/config.yaml", encoding="utf-8") as stream:
        try:
            cfg = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print("Can't read config file")
            raise exc
    logging.config.dictConfig(cfg["logger"])
    logger = logging.getLogger("app")

    base_init(cfg["db_path"])
    uvicorn.run("main:app", port=8000, reload=False, log_level="info")
