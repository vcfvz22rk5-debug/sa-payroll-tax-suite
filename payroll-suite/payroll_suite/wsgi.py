"""
wsgi.py - a WSGI entry point for the dashboard.

The free Python hosts (PythonAnywhere, Render, Fly.io, Railway) all want
a WSGI callable rather than a script you run yourself. This wraps the
same API and the same static files in one, so the code that runs on your
laptop is the code that runs in the cloud.

On a WSGI host, point it at:

    from payroll_suite.wsgi import application

The database path comes from the PAYROLL_DB environment variable, and
falls back to the one in the project folder.
"""

import json
import mimetypes
import os
import posixpath
import sys
from urllib.parse import parse_qs, unquote

from payroll_suite.db import DEFAULT_DB
from payroll_suite.server import WEB_ROOT, Api, ApiError

# Make sure the package is importable when the host only points at the
# project folder.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _json_response(start_response, payload, status="200 OK"):
    body = json.dumps(payload, default=str).encode("utf-8")
    start_response(status, [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-store"),
    ])
    return [body]


def _file_response(start_response, path):
    if not os.path.isfile(path):
        return _json_response(start_response, {"error": "Not found"}, "404 Not Found")
    content_type, _ = mimetypes.guess_type(path)
    with open(path, "rb") as handle:
        body = handle.read()
    start_response("200 OK", [
        ("Content-Type", content_type or "application/octet-stream"),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-cache"),
    ])
    return [body]


def create_app(db_path: str = None):
    """Build the WSGI application."""
    resolved = db_path or os.environ.get("PAYROLL_DB") or DEFAULT_DB
    api = Api(resolved)

    def application(environ, start_response):
        path = posixpath.normpath(unquote(environ.get("PATH_INFO", "/")))
        query = parse_qs(environ.get("QUERY_STRING", ""))

        def first(name, default=None):
            values = query.get(name)
            return values[0] if values else default

        try:
            if path.startswith("/api/"):
                if path == "/api/overview":
                    return _json_response(start_response, api.overview())
                if path == "/api/employees":
                    return _json_response(start_response, api.employees())
                if path == "/api/payslips":
                    period = first("period")
                    if not period:
                        raise ApiError("A period is needed, e.g. ?period=2026-10")
                    return _json_response(start_response, api.payslips(period))
                if path == "/api/emp201":
                    period = first("period")
                    if not period:
                        raise ApiError("A period is needed, e.g. ?period=2026-10")
                    return _json_response(start_response, api.emp201(period))
                if path == "/api/deadlines":
                    return _json_response(
                        start_response, api.deadlines(first("year", "2027"))
                    )
                if path == "/api/irp5":
                    return _json_response(start_response, api.irp5(first("year", "2027")))
                if path == "/api/emp501":
                    return _json_response(
                        start_response, api.emp501(first("year", "2027"))
                    )
                return _json_response(start_response, {"error": "Not found"}, "404 Not Found")

            if path in ("/", "\\"):
                path = "/index.html"
            target = os.path.normpath(os.path.join(WEB_ROOT, path.lstrip("/")))
            if not target.startswith(WEB_ROOT):
                return _json_response(start_response, {"error": "Not found"}, "404 Not Found")
            return _file_response(start_response, target)

        except ApiError as problem:
            return _json_response(
                start_response, {"error": problem.message}, "400 Bad Request"
            )
        except Exception as problem:                      # pragma: no cover
            return _json_response(
                start_response, {"error": str(problem)}, "500 Internal Server Error"
            )

    return application


# The callable a WSGI host will look for.
application = create_app()


if __name__ == "__main__":
    # A tiny development server, so you can try the WSGI version locally.
    from wsgiref.simple_server import make_server

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    print(f"  Payroll Suite (WSGI) on http://{host}:{port}")
    with make_server(host, port, application) as server:
        server.serve_forever()
