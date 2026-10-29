import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("CLOUDOPS_DB", BASE_DIR / "cloudops.db"))

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "dev-only-change-before-deployment"
)

FAILURE_GUIDES = {
    "ImagePullBackOff": {
        "cause": "Kubernetes could not download the container image.",
        "action": "Check the image name/tag, registry permissions, and ECR access.",
    },
    "CrashLoopBackOff": {
        "cause": "The application container repeatedly exits after starting.",
        "action": "Inspect container logs, startup command, environment variables, and application configuration.",
    },
    "Readiness probe failed": {
        "cause": "The application did not pass its configured readiness check.",
        "action": "Verify the health endpoint, container port, startup time, and readiness-probe settings.",
    },
    "CI build failed": {
        "cause": "A build or test step failed in the CI pipeline.",
        "action": "Open the failed pipeline step and inspect the first relevant error message.",
    },
    "None": {
        "cause": "No failure has been selected for this demonstration.",
        "action": "Review the deployment status and health checks.",
    },
}


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def db_connection():
    connection = get_db()
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def init_db():
    with db_connection() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                environment TEXT NOT NULL,
                status TEXT NOT NULL,
                failure_type TEXT NOT NULL DEFAULT 'None',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)

        count = db.execute(
            "SELECT COUNT(*) FROM deployments"
        ).fetchone()[0]

        if count == 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")

            demo_rows = [
                (
                    "Sample Flask App",
                    "Development",
                    "Success",
                    "None",
                    "Demo record: successful deployment.",
                    now,
                ),
                (
                    "Sample Flask App",
                    "Staging",
                    "Failed",
                    "ImagePullBackOff",
                    "Demo record: image could not be pulled.",
                    now,
                ),
                (
                    "Inventory API",
                    "Development",
                    "Running",
                    "None",
                    "Demo record: application is running.",
                    now,
                ),
            ]

            db.executemany("""
                INSERT INTO deployments
                (project_name, environment, status, failure_type, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, demo_rows)


@app.route("/")
def dashboard():
    with db_connection() as db:
        rows = db.execute(
            "SELECT * FROM deployments ORDER BY id DESC"
        ).fetchall()

        total = db.execute(
            "SELECT COUNT(*) FROM deployments"
        ).fetchone()[0]

        successful = db.execute(
            "SELECT COUNT(*) FROM deployments "
            "WHERE status IN ('Success', 'Running')"
        ).fetchone()[0]

        failed = db.execute(
            "SELECT COUNT(*) FROM deployments WHERE status = 'Failed'"
        ).fetchone()[0]

    return render_template(
        "dashboard.html",
        deployments=rows,
        total=total,
        successful=successful,
        failed=failed,
        failure_guides=FAILURE_GUIDES,
    )


@app.route("/deployments", methods=["POST"])
def create_deployment():
    project_name = request.form.get("project_name", "").strip()
    environment = request.form.get("environment", "Development").strip()
    status = request.form.get("status", "Running").strip()
    failure_type = request.form.get("failure_type", "None").strip()
    notes = request.form.get("notes", "").strip()

    allowed_statuses = {"Running", "Success", "Failed"}
    allowed_failures = set(FAILURE_GUIDES.keys())
    allowed_environments = {"Development", "Staging", "Production"}

    if not project_name:
        flash("Project name is required.", "error")
        return redirect(url_for("dashboard"))

    if status not in allowed_statuses or failure_type not in allowed_failures:
        flash("Invalid status or failure type.", "error")
        return redirect(url_for("dashboard"))

    if environment not in allowed_environments:
        flash("Invalid environment.", "error")
        return redirect(url_for("dashboard"))

    if status != "Failed":
        failure_type = "None"

    with db_connection() as db:
        db.execute("""
            INSERT INTO deployments
            (project_name, environment, status, failure_type, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            project_name,
            environment,
            status,
            failure_type,
            notes,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ))

    flash("Deployment record added.", "success")
    return redirect(url_for("dashboard"))


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "application": "CloudOps Prototype",
    })


@app.route("/api/deployments")
def deployments_api():
    with db_connection() as db:
        rows = db.execute(
            "SELECT * FROM deployments ORDER BY id DESC"
        ).fetchall()

        result = [dict(row) for row in rows]

    return jsonify(result)


@app.route("/diagnosis/<int:deployment_id>")
def diagnosis(deployment_id):
    with db_connection() as db:
        row = db.execute(
            "SELECT * FROM deployments WHERE id = ?",
            (deployment_id,),
        ).fetchone()

        # Copy the row before closing the connection.
        deployment = dict(row) if row is not None else None

    if deployment is None:
        return "Deployment not found", 404

    guide = FAILURE_GUIDES.get(
        deployment["failure_type"],
        FAILURE_GUIDES["None"],
    )

    return render_template(
        "diagnosis.html",
        deployment=deployment,
        guide=guide,
    )


@app.route("/demo/failure")
def demo_failure():
    with db_connection() as db:
        db.execute("""
            INSERT INTO deployments
            (project_name, environment, status, failure_type, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Demo Failure App",
            "Staging",
            "Failed",
            "CrashLoopBackOff",
            "Simulated failure record for prototype demonstration.",
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ))

    flash(
        "A simulated failure was added so you can demonstrate diagnosis.",
        "success",
    )
    return redirect(url_for("dashboard"))


@app.errorhandler(500)
def internal_error(error):
    return render_template("error.html"), 500


init_db()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
