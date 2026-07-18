from opentelemetry import trace
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.trace import TracerProvider

_telemetry_initialized = False


def setup_telemetry() -> None:
    """
    Initialize OpenTelemetry TracerProvider and instrument logging, HTTPX, and SQLAlchemy.

    For this template, we set a basic TracerProvider and enable auto-instrumentation
    so that trace contexts are automatically propagated and recorded.
    """
    global _telemetry_initialized
    if _telemetry_initialized:
        return

    provider = TracerProvider()
    try:
        trace.set_tracer_provider(provider)
    except RuntimeError:  # noqa: S110
        # Handle cases where provider is set externally or concurrently
        pass

    # Instrument standard logging to inject trace/span IDs (e.g. %(otelTraceID)s) into LogRecords
    LoggingInstrumentor().instrument(set_logging_format=False)

    # Instrument HTTPX client calls automatically
    HTTPXClientInstrumentor().instrument()

    # Instrument SQLAlchemy database calls globally
    SQLAlchemyInstrumentor().instrument()

    _telemetry_initialized = True
