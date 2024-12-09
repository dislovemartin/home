"""OpenTelemetry configuration for distributed tracing and monitoring."""

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_telemetry(app=None, service_name="srt-model-quantizing"):
    """Configure OpenTelemetry with Jaeger exporter."""
    # Create a TracerProvider
    resource = Resource.create({"service.name": service_name})
    trace.set_tracer_provider(TracerProvider(resource=resource))

    # Create and register Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
    )
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    # Get tracer
    tracer = trace.get_tracer(__name__)

    if app:
        # Instrument FastAPI application
        FastAPIInstrumentor.instrument_app(app)

    return tracer 