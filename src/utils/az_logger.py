import logging
import structlog

from opencensus.ext.azure.log_exporter import AzureLogHandler
from src.core.app_settings import get_settings

def az_logging():
    # Get the root logger and set its level to INFO so all INFO+ logs are captured
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Remove any existing handlers to avoid duplicate logs
    for h in list(root.handlers):
        root.removeHandler(h)

    # Add Azure Log Handler to send logs to Azure Monitor using connection string
    ai_handler = AzureLogHandler(
        connection_string=get_settings().AZURE_MONITOR_CONN_STR
    )
    ai_handler.setLevel(logging.INFO)
    root.addHandler(ai_handler)

    # Add console handler to also print logs to the terminal for local debugging
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(console)

    # Configure structlog to format logs as JSON and add useful info like timestamp and log level
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,   # include request context in logs
            structlog.processors.add_log_level,        # add log level to each log entry
            structlog.processors.TimeStamper(fmt="iso"), # add timestamp in ISO format
            structlog.processors.StackInfoRenderer(),     # include stack info if available
            structlog.processors.format_exc_info,         # format exception info for errors
            structlog.processors.JSONRenderer(),          # output logs as JSON
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Set log level to WARNING for noisy Azure SDK loggers to reduce log clutter
    for logger_name in (
        "azure.core.pipeline.policies.http_logging_policy",
        "azure.storage.blob",  # catch broader blob logs
        "azure.core.tracing.opentelemetry_span"  # if you ever see OTEL traces from azure sdk
    ):
        logging.getLogger(logger_name).setLevel(logging.WARNING)
