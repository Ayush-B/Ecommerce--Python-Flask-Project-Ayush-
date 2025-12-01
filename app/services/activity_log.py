"""
Activity log service.

Provides functions to query admin actions with filters and pagination.
"""

from sqlalchemy import desc

from ..models import ActivityLog, User


class ActivityLogService:
    """
    Business logic for reading activity logs.
    """

    @staticmethod
    def list_logs(page: int = 1, per_page: int = 10,
                  admin_id: int | None = None,
                  action_type: str | None = None,
                  target_type: str | None = None):
        """
        Retrieve a paginated list of activity logs with basic filters.

        Args:
            page: page number (1-based)
            per_page: items per page
            admin_id: filter by admin user id
            action_type: filter by action type string
            target_type: filter by target type string (e.g. 'Product', 'User')

        Returns:
            dict with logs and pagination info.
        """
        query = ActivityLog.query.order_by(desc(ActivityLog.timestamp))

        if admin_id is not None:
            query = query.filter_by(admin_id=admin_id)
        if action_type:
            query = query.filter_by(action_type=action_type)
        if target_type:
            query = query.filter_by(target_type=target_type)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        logs = [log.to_dict() for log in pagination.items]

        return {
            "logs": logs,
            "page": pagination.page,
            "pages": pagination.pages,
            "total": pagination.total,
        }

    @staticmethod
    def latest_id() -> int:
        """
        Return the latest ActivityLog id, or 0 if there are no logs.
        """
        latest = ActivityLog.query.order_by(ActivityLog.id.desc()).first()
        return latest.id if latest else 0
