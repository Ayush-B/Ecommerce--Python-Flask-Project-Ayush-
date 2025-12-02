"""
Admin activity log routes.

Provides:
- GET /admin/activity           : paginated listing with filters
- GET /admin/activity/stream    : streaming endpoint (Server-Sent Events style)
"""

import json
import time
from flask import Blueprint, jsonify, request, Response, current_app, render_template

from ..models import ActivityLog
from ..services.activity_log import ActivityLogService
from ..utils.auth_decorators import admin_required

admin_activity_bp = Blueprint("admin_activity", __name__, url_prefix="/admin/activity")


@admin_activity_bp.get("/")
@admin_required
def activity_list():
    page = request.args.get("page", type=int, default=1)
    per_page = 10

    pagination = (
        ActivityLog.query.order_by(ActivityLog.timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    logs = pagination.items

    if request.args.get("format") == "json" or (
        request.accept_mimetypes["application/json"]
        > request.accept_mimetypes["text/html"]
    ):
        return jsonify(
            {
                "logs": [log.to_dict() for log in logs],
                "page": pagination.page,
                "pages": pagination.pages,
                "total": pagination.total,
            }
        )

    return render_template(
        "admin/activity/list.html",
        logs=logs,
        page=pagination.page,
        pages=pagination.pages,
        total=pagination.total,
    )


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