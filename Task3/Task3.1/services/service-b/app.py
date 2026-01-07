import os
import time
from flask import Flask, jsonify

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor


def setup_tracing(service_name: str) -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://simplest-collector:4318/v1/traces")

    resource = Resource.create({
        "service.name": service_name,
        "deployment.environment": os.getenv("DEPLOYMENT_ENVIRONMENT", "minikube"),
    })

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


setup_tracing("service-b")

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)


@app.get("/")
def root():
    return jsonify({
        "service": "service-b",
        "message": "ok",
        "ts": int(time.time()),
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
