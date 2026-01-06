import os
import time

import requests
from fastapi import FastAPI

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.resources import SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_tracing() -> None:
    service_name = os.getenv("OTEL_SERVICE_NAME", "service-a")
    endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "simplest-collector.observability.svc.cluster.local:4317",
    )

    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)


setup_tracing()

app = FastAPI(title="service-a")
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()

tracer = trace.get_tracer(__name__)


@app.get("/")
def root():
    service_b_url = os.getenv("SERVICE_B_URL", "http://service-b:8080/")

    # Child span inside the server span (created by FastAPI instrumentation)
    with tracer.start_as_current_span("service-a:call-service-b") as span:
        span.set_attribute("app.service_b.url", service_b_url)
        t0 = time.time()
        resp = requests.get(service_b_url, timeout=5)
        dt_ms = int((time.time() - t0) * 1000)
        span.set_attribute("app.service_b.latency_ms", dt_ms)
        span.set_attribute("http.status_code", resp.status_code)

    return {
        "service": "service-a",
        "service_b_status": resp.status_code,
        "service_b_body": resp.text,
    }
