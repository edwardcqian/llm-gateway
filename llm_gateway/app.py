# llm-gateway - A proxy service in front of llm models to encourage the
# responsible use of AI.
#
# Copyright 2023 Wealthsimple Technologies
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import loguru

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_route_logger_middleware import RouteLoggerMiddleware
from starlette_exporter import PrometheusMiddleware, handle_metrics

from llm_gateway.routers import cohere_api, openai_api
from llm_gateway.utils import setup_tracing
from llm_gateway.log import add_trace_id, init_logging


APP_NAME = "llm_gateway"

app = FastAPI()
app.title = "LLM Proxy"
app.description = "LLM Proxy Developed by Wealthsimple"


api = FastAPI(openapi_prefix="/api")
api.include_router(openai_api.router, prefix="/openai")
api.include_router(cohere_api.router, prefix="/cohere")

app.mount("/api", api, name="api")

# Allow Front-end Origin in local development
origins = ["http://localhost:3000"]



app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger = loguru.logger.patch(add_trace_id)
app.add_middleware(RouteLoggerMiddleware, logger=logger)
app.add_middleware(
    PrometheusMiddleware,
    app_name="llm_gateway",
    prefix="llm_gateway",
    group_paths=True,
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
)
app.add_route("/metrics", handle_metrics)
init_logging()
setup_tracing(app, APP_NAME)


@api.get("/healthcheck")
async def healthcheck():
    """
    Endpoint to verify that the service is up and running
    """
    return {"message": "llm-gateway is healthy"}
