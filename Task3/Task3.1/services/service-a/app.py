import os
import time
import requests
from flask import Flask, jsonify

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor


def setup_tracing(service_name: str) -> None:
    # Export traces to Jaeger Collector via OTLP/HTTP.
    # Default endpoint works with Jaeger Operator "simplest" example.
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://simplest-collector:4318/v1/traces")

    resource = Resource.create({
        "service.name": service_name,
        "deployment.environment": os.getenv("DEPLOYMENT_ENVIRONMENT", "minikube"),
    })

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


setup_tracing("service-a")
RequestsInstrumentor().instrument()

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

tracer = trace.get_tracer("service-a")
SERVICE_B_URL = os.getenv("SERVICE_B_URL", "http://service-b:8080/")


@app.get("/")
def root():
    with tracer.start_as_current_span("call-service-b") as span:
        span.set_attribute("service_b.url", SERVICE_B_URL)
        r = requests.get(SERVICE_B_URL, timeout=3)
        r.raise_for_status()
        data_b = r.json()

    return jsonify({
        "service": "service-a",
        "message": "ok",
        "service_b": data_b,
        "ts": int(time.time()),
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
