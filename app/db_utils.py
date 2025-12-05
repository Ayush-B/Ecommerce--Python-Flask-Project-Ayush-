import logging
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def commit_session(session, *, context_message=None):
    """
    Commit a SQLAlchemy session with consistent logging and rollback on errors.
    Use commit_session(db.session, context_message="orders:create_order")
    instead of db.session.commit().
    """
    try:
        session.commit()
    except SQLAlchemyError:
        try:
            session.rollback()
        except Exception:
            logger.exception("Rollback failed after commit error")
        logger.error(
            "Database commit failed: %s",
            context_message or "",
            exc_info=True,
        )
        raise
