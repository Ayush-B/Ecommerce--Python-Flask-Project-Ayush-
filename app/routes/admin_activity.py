"""
Admin activity log routes.

Provides:
- GET /admin/activity           : paginated listing with filters
- GET /admin/activity/stream    : streaming endpoint (Server-Sent Events style)
"""

import json
import time
from flask import Blueprint, jsonify, request, Response, current_app

from ..models import ActivityLog
from ..services.activity_log import ActivityLogService
from ..utils.auth_decorators import admin_required

admin_activity_bp = Blueprint("admin_activity", __name__, url_prefix="/admin/activity")


@admin_activity_bp.get("")
@admin_required
def activity_list():
    """
    Paginated activity log listing.

    Query parameters:
      - page (int, default 1)
      - admin_id (optional, int)
      - action_type (optional, str)
      - target_type (optional, str)
    """
    page = request.args.get("page", default=1, type=int)
    admin_id = request.args.get("admin_id", type=int)
    action_type = request.args.get("action_type")
    target_type = request.args.get("target_type")

    data = ActivityLogService.list_logs(
        page=page,
        per_page=10,
        admin_id=admin_id,
        action_type=action_type,
        target_type=target_type,
    )
    return jsonify(data)


@admin_activity_bp.get("/stream")
@admin_required
def activity_stream():
    """
    Streaming endpoint for activity logs.

    Produces JSON objects as Server-Sent Events (SSE), one per line:

        data: {"id": ..., "action_type": ...}

    Query parameters:
      - last_id (optional, int): start streaming logs AFTER this id.
    """
    start_last_id = request.args.get("last_id", type=int) or 0

    # Mutable state container so we do not need 'nonlocal'
    state = {"last_id": start_last_id}

    # Capture the real Flask app object while a request context is active
    app = current_app._get_current_object()

    def generate():
        # Keep an application context alive for the lifetime of this generator
        with app.app_context():
            while True:
                logs = (
                    ActivityLog.query
                    .filter(ActivityLog.id > state["last_id"])
                    .order_by(ActivityLog.id.asc())
                    .all()
                )

                for log in logs:
                    state["last_id"] = log.id
                    payload = json.dumps(log.to_dict())
                    # SSE format: "data: <payload>\n\n"
                    yield f"data: {payload}\n\n"

                # Avoid a tight polling loop
                time.sleep(1)

    return Response(generate(), mimetype="text/event-stream")