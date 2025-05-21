import logging
import sys
import structlog

def setup_logging(log_level: str = "INFO"):
    """
    Configures structlog for JSON output and integrates with stdlib logging.
    """
    log_level_upper = log_level.upper()
    numeric_log_level = getattr(logging, log_level_upper, None)
    if not isinstance(numeric_log_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Common processors for both stdlib and structlog
    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info, # Add exception info to log entries if True
        structlog.dev.format_exc_info, # Format exception info
    ]

    structlog.configure(
        processors=[
            # Filter out logs below the configured level early
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        # Cache logger instances for performance
        cache_logger_on_first_use=True,
    )

    # Configure the stdlib root logger to pass everything to structlog
    # This is how structlog integrates with logs from other libraries.
    # We use a custom formatter for stdlib logs that will render them as JSON.
    stdlib_formatter = structlog.stdlib.ProcessorFormatter.wrap_for_formatter(
        # The "formatter" argument to wrap_for_formatter is the final step,
        # which should render the event dict as a JSON string.
        processor=structlog.processors.JSONRenderer(),
        # These processors are applied to logs that originate in stdlib
        foreign_pre_chain=shared_processors,
    )

    # Get the root logger and add our structlog-based handler
    root_logger = logging.getLogger()
    # Remove any existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = logging.StreamHandler(sys.stdout)
    # Set the formatter for the handler
    handler.setFormatter(stdlib_formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_log_level)

    # Optionally, configure specific noisy loggers from libraries
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING) # Example

    # Test message
    # logger = structlog.get_logger("logging_config")
    # logger.info("Structlog logging configured.", log_level=log_level_upper)

if __name__ == "__main__":
    # Example of running the setup
    setup_logging(log_level="DEBUG")
    logger = structlog.get_logger("my_app")
    logger.info("Hello, world!", user="test_user", event_id=42)
    logging.getLogger("stdlib_logger").info("This is a stdlib log message.")
    try:
        raise ValueError("This is a test exception.")
    except ValueError:
        logger.error("An exception occurred", exc_info=True)
