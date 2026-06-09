import os
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME


def init_opentelemetry(app) -> None:
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    service_name = os.getenv("OTEL_SERVICE_NAME", "activia-trace-api")

    if not otel_endpoint:
        return

    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(endpoint=otel_endpoint, insecure=True)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)