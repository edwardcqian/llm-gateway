import logging

from opentelemetry import trace
from opentelemetry.exporter.jaeger import thrift
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.jaeger import JaegerPropagator
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import get_current_span
from opentelemetry.trace.span import format_trace_id
from starlette.types import ASGIApp

level = logging.INFO
logging.basicConfig(level=level)
logger = logging.getLogger(__name__)


def max_retries(times: int, exceptions: tuple = (Exception)):
    """
    Max Retry Decorator
    Retries the wrapped function/method `times` times
    :param times: The max number of times to repeat the wrapped function/method
    :type times: int
    :param Exceptions: Lists of exceptions that trigger a retry attempt
    :type Exceptions: List of Exceptions
    """

    def decorator(func):
        def newfn(*args, **kwargs):
            attempt = 0
            while attempt < times:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.error(
                        f"Exception '{e}' thrown when running '{func}'"
                        + f"(attempt {attempt} of {times} times)"
                    )
                    attempt += 1
            return func(*args, **kwargs)

        return newfn

    return decorator


def setup_tracing(app: ASGIApp, app_name: str, log_correlation: bool = True) -> None:
    # Setting OpenTelemetry
    # set the service name to show in traces
    set_global_textmap(JaegerPropagator())
    tracer_provider = TracerProvider(resource=Resource.create({SERVICE_NAME: app_name}))
    trace.set_tracer_provider(tracer_provider)
    
    tracer_provider.add_span_processor(
        BatchSpanProcessor(thrift.JaegerExporter())
    )


    if log_correlation:
        LoggingInstrumentor().instrument(set_logging_format=True)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)


def add_trace_id(record) -> None:
    sp = get_current_span()
    if sp is None:
        return

    trace_id = sp.get_span_context().trace_id
    record["extra"].update(trace_id=format_trace_id(trace_id))