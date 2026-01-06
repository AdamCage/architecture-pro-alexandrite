import os
import time

from fastapi import FastAPI

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.resources import SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_tracing() -> None:
    service_name = os.getenv("OTEL_SERVICE_NAME", "service-b")
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

app = FastAPI(title="service-b")
FastAPIInstrumentor.instrument_app(app)

tracer = trace.get_tracer(__name__)


@app.get("/")
def root():
    with tracer.start_as_current_span("service-b:work") as span:
        # имитируем небольшую работу
        time.sleep(0.05)
        span.set_attribute("app.demo", True)

    return {"service": "service-b", "status": "ok"}
