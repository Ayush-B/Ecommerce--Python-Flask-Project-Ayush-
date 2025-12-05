import logging
import logging.handlers
import os
from flask import has_request_context, request, g
from flask_login import current_user

class RequestFilter(logging.Filter):
    """Attach request_id, username and remote_addr to each LogRecord.

    This filter is safe to call outside request context (returns "-" when no
    request is active). Access to request-scoped proxies is guarded with
    has_request_context() to avoid RuntimeError: Working outside of request context.
    """
    def filter(self, record):
        if has_request_context():
            # request context is active — safe to read g/current_user/request
            try:
                record.request_id = getattr(g, "request_id", "-")
            except Exception:
                # defensive: local proxies may still raise in edge cases
                record.request_id = "-"
            try:
                record.username = (
                    getattr(current_user, "username", None)
                    or getattr(current_user, "id", None)
                    or "-"
                )
            except Exception:
                record.username = "-"
            try:
                record.remote_addr = request.remote_addr
            except Exception:
                record.remote_addr = "-"
        else:
            # No request context: use safe defaults
            record.request_id = "-"
            record.username = "-"
            record.remote_addr = "-"
        return True

def setup_logging(app,
                  log_dir=None,
                  filename=None,
                  level=logging.INFO,
                  max_bytes=10 * 1024 * 1024,
                  backup_count=7):
    """
    Configure application logging (simple: rotating file + console).
    Call early inside create_app (before registering blueprints).
    Idempotent: safe to call multiple times for the same app instance.
    """
    if getattr(app, "_logging_configured", False):
        return logging.getLogger(app.import_name)

    if log_dir is None:
        log_dir = app.config.get("LOG_DIR", "logs")
    if filename is None:
        filename = app.config.get("LOG_FILE", "app.log")

    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, filename)

    fmt = (
        "%(asctime)s %(levelname)-8s [req:%(request_id)s] [user:%(username)s] "
        "%(module)s:%(lineno)d %(message)s"
    )
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    root = logging.getLogger()
    root.setLevel(level)

    # Rotating file handler (production / persisted logs)
    rf = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    rf.setLevel(level)
    rf.setFormatter(formatter)
    rf.addFilter(RequestFilter())
    root.addHandler(rf)

    # Console handler (useful for Docker / dev)
    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(formatter)
    sh.addFilter(RequestFilter())
    root.addHandler(sh)

    # Reduce SQLAlchemy engine noise by default
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    app_logger = logging.getLogger(app.import_name)
    app.logger.handlers = root.handlers
    app.logger.setLevel(level)

    app._logging_configured = True
    return app_logger