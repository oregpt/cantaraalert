"""
Canton Rewards Monitor - Scheduler
Runs threshold alerts and status reports on independent schedules
"""

import os
import json
import time
import threading
import schedule
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone
from dotenv import load_dotenv
from canton_monitor import (
    run_check, run_status_report, send_notification, init_db,
    scrape_canton_rewards, parse_metrics, DATABASE_URL, DB_ENABLED
)

load_dotenv()

def verify_api_key(headers):
    """Check if request has valid API key (validates against DB)"""
    if not DB_ENABLED:
        return False

    # Get key from header
    key = None
    auth_header = headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        key = auth_header[7:]
    else:
        key = headers.get("X-API-Key", "")

    if not key:
        return False

    # Validate against database
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM api_keys WHERE key = %s", (key,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count > 0
    except Exception:
        return False


def get_db_connection():
    """Get database connection"""
    if not DB_ENABLED:
        return None
    import psycopg2
    return psycopg2.connect(DATABASE_URL)


class APIHandler(BaseHTTPRequestHandler):
    """HTTP handler for health checks and API endpoints"""

    def send_json(self, data, status=200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_error_json(self, message, status=400):
        """Send JSON error response"""
        self.send_json({"error": message}, status)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Health check - no auth required
        if path == "/" or path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            return

        # All /api/* endpoints require auth
        if path.startswith("/api/"):
            if not DB_ENABLED:
                self.send_error_json("API not enabled (DATABASE_URL not configured)", 503)
                return
            if not verify_api_key(self.headers):
                self.send_error_json("Unauthorized - valid API key required", 401)
                return

            # Route to appropriate handler
            if path == "/api/status":
                self.handle_status()
            elif path == "/api/metrics":
                self.handle_metrics(query)
            elif path == "/api/metrics_v2":
                self.handle_metrics_v2(query)
            elif path == "/api/metrics/latest":
                self.handle_metrics_latest(query)
            elif path == "/api/schema":
                self.handle_schema(query)
            elif path == "/api/keys":
                self.handle_keys(query)
            else:
                self.send_error_json("Not found", 404)
            return

        self.send_error_json("Not found", 404)

    def handle_status(self):
        """GET /api/status - Get current values (live scrape)"""
        try:
            raw_text = scrape_canton_rewards()
            metrics = parse_metrics(raw_text)

            # Format response
            response = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "canton-rewards.noves.fi",
                "metrics": {},
                "alerts": []
            }

            type_mapping = {
                'Latest Round': 'latest_round',
                '1-Hour Average': '1hr_avg',
                '24-Hour Average': '24hr_avg'
            }

            for period, values in metrics.items():
                key = type_mapping.get(period, period)
                gross = values.get("gross")
                est = values.get("est_traffic")
                response["metrics"][key] = {
                    "gross_cc": gross,
                    "est_traffic_cc": est
                }
                # Check for alerts
                if gross is not None and est is not None and est > gross:
                    response["alerts"].append({
                        "period": period,
                        "message": f"Est.Traffic ({est}) > Gross ({gross})"
                    })

            self.send_json(response)

        except Exception as e:
            self.send_error_json(f"Failed to get status: {str(e)}", 500)

    def handle_metrics(self, query):
        """GET /api/metrics - Query historical data from DB"""
        if not DB_ENABLED:
            self.send_error_json("Database not configured", 503)
            return

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Build query with filters
            sql = "SELECT id, obtained_timestamp, source, type, value1, value2, value3, value4, value5 FROM metrics_raw WHERE 1=1"
            params = []

            if "source" in query:
                sql += " AND source = %s"
                params.append(query["source"][0])

            if "type" in query:
                sql += " AND type = %s"
                params.append(query["type"][0])

            if "from" in query:
                sql += " AND obtained_timestamp >= %s"
                params.append(query["from"][0])

            if "to" in query:
                sql += " AND obtained_timestamp <= %s"
                params.append(query["to"][0])

            sql += " ORDER BY obtained_timestamp DESC"

            limit = min(int(query.get("limit", [100])[0]), 1000)
            sql += f" LIMIT {limit}"

            cur.execute(sql, params)
            rows = cur.fetchall()

            data = []
            for row in rows:
                data.append({
                    "id": row[0],
                    "obtained_timestamp": row[1].isoformat() if row[1] else None,
                    "source": row[2],
                    "type": row[3],
                    "value1": row[4],
                    "value2": row[5],
                    "value3": row[6],
                    "value4": row[7],
                    "value5": row[8]
                })

            cur.close()
            conn.close()

            self.send_json({"count": len(data), "data": data})

        except Exception as e:
            self.send_error_json(f"Database query failed: {str(e)}", 500)

    def handle_metrics_v2(self, query):
        """GET /api/metrics_v2 - Query historical data with schema-mapped column names"""
        if not DB_ENABLED:
            self.send_error_json("Database not configured", 503)
            return

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # First, load all schema definitions into a lookup dict
            cur.execute("""
                SELECT source, type,
                       value1_name, value2_name, value3_name, value4_name, value5_name,
                       value6_name, value7_name, value8_name, value9_name, value10_name,
                       value11_name, value12_name, value13_name, value14_name, value15_name,
                       value16_name, value17_name, value18_name, value19_name, value20_name
                FROM metrics_schema
            """)
            schema_rows = cur.fetchall()

            # Build schema lookup: (source, type) -> {value1: name, value2: name, ...}
            schema_lookup = {}
            for row in schema_rows:
                key = (row[0], row[1])
                schema_lookup[key] = {}
                for i in range(2, 22):  # value1_name through value20_name
                    if row[i]:
                        schema_lookup[key][f"value{i-1}"] = row[i]

            # Build query with filters (same as handle_metrics)
            sql = """SELECT id, obtained_timestamp, source, type,
                            value1, value2, value3, value4, value5,
                            value6, value7, value8, value9, value10,
                            value11, value12, value13, value14, value15,
                            value16, value17, value18, value19, value20
                     FROM metrics_raw WHERE 1=1"""
            params = []

            if "source" in query:
                sql += " AND source = %s"
                params.append(query["source"][0])

            if "type" in query:
                sql += " AND type = %s"
                params.append(query["type"][0])

            if "from" in query:
                sql += " AND obtained_timestamp >= %s"
                params.append(query["from"][0])

            if "to" in query:
                sql += " AND obtained_timestamp <= %s"
                params.append(query["to"][0])

            sql += " ORDER BY obtained_timestamp DESC"

            limit = min(int(query.get("limit", [100])[0]), 1000)
            sql += f" LIMIT {limit}"

            cur.execute(sql, params)
            rows = cur.fetchall()

            data = []
            for row in rows:
                source = row[2]
                type_ = row[3]
                schema_key = (source, type_)
                column_names = schema_lookup.get(schema_key, {})

                record = {
                    "id": row[0],
                    "obtained_timestamp": row[1].isoformat() if row[1] else None,
                    "source": source,
                    "type": type_
                }

                # Map value columns using schema names (same flat structure as /api/metrics)
                for i in range(5):  # value1 through value5 (matching /api/metrics output)
                    value = row[4 + i]
                    col_key = f"value{i+1}"
                    col_name = column_names.get(col_key, col_key)  # Use schema name or fallback to valueN
                    record[col_name] = value

                data.append(record)

            cur.close()
            conn.close()

            self.send_json({"count": len(data), "data": data})

        except Exception as e:
            self.send_error_json(f"Database query failed: {str(e)}", 500)

    def handle_metrics_latest(self, query):
        """GET /api/metrics/latest - Get most recent value for each source/type"""
        if not DB_ENABLED:
            self.send_error_json("Database not configured", 503)
            return

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Get latest entry for each source/type combo
            sql = """
                SELECT DISTINCT ON (source, type)
                    id, obtained_timestamp, source, type, value1, value2
                FROM metrics_raw
                ORDER BY source, type, obtained_timestamp DESC
            """
            cur.execute(sql)
            rows = cur.fetchall()

            data = []
            for row in rows:
                data.append({
                    "id": row[0],
                    "obtained_timestamp": row[1].isoformat() if row[1] else None,
                    "source": row[2],
                    "type": row[3],
                    "value1": row[4],
                    "value2": row[5]
                })

            cur.close()
            conn.close()

            self.send_json({"count": len(data), "data": data})

        except Exception as e:
            self.send_error_json(f"Database query failed: {str(e)}", 500)

    def handle_schema(self, query):
        """GET /api/schema - List all source/type definitions"""
        if not DB_ENABLED:
            self.send_error_json("Database not configured", 503)
            return

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            sql = "SELECT source, type, value1_name, value2_name, value3_name, value4_name, value5_name FROM metrics_schema"
            params = []

            if "source" in query:
                sql += " WHERE source = %s"
                params.append(query["source"][0])

            sql += " ORDER BY source, type"

            cur.execute(sql, params)
            rows = cur.fetchall()

            data = []
            for row in rows:
                schema = {
                    "source": row[0],
                    "type": row[1],
                    "columns": {}
                }
                if row[2]:
                    schema["columns"]["value1"] = row[2]
                if row[3]:
                    schema["columns"]["value2"] = row[3]
                if row[4]:
                    schema["columns"]["value3"] = row[4]
                if row[5]:
                    schema["columns"]["value4"] = row[5]
                if row[6]:
                    schema["columns"]["value5"] = row[6]
                data.append(schema)

            cur.close()
            conn.close()

            self.send_json({"count": len(data), "data": data})

        except Exception as e:
            self.send_error_json(f"Database query failed: {str(e)}", 500)

    def handle_keys(self, query):
        """GET /api/keys - List all API keys (for admin to distribute)"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            limit = min(int(query.get("limit", [100])[0]), 100)
            offset = int(query.get("offset", [0])[0])

            cur.execute(
                "SELECT id, key, created_at FROM api_keys ORDER BY id LIMIT %s OFFSET %s",
                (limit, offset)
            )
            rows = cur.fetchall()

            cur.execute("SELECT COUNT(*) FROM api_keys")
            total = cur.fetchone()[0]

            data = []
            for row in rows:
                data.append({
                    "id": row[0],
                    "key": row[1],
                    "created_at": row[2].isoformat() if row[2] else None
                })

            cur.close()
            conn.close()

            self.send_json({"total": total, "count": len(data), "data": data})

        except Exception as e:
            self.send_error_json(f"Database query failed: {str(e)}", 500)

    def log_message(self, format, *args):
        # Only log API calls, not health checks
        if "/api/" in (args[0] if args else ""):
            print(f"API: {args[0]}")


def start_api_server():
    """Start the HTTP server for health checks and API"""
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), APIHandler)
    print(f"API server running on port {port}")
    if DB_ENABLED:
        print("API endpoints enabled (keys stored in database)")
    else:
        print("API endpoints disabled (DATABASE_URL not configured)")
    server.serve_forever()

# Alert 1: Threshold alerts (Est.Traffic > Gross)
ALERT1_ENABLED = os.getenv("ALERT1_ENABLED", "true").lower() == "true"
ALERT1_INTERVAL_MINUTES = int(os.getenv("ALERT1_INTERVAL_MINUTES", "15"))

# Alert 2: Status reports (all values)
ALERT2_ENABLED = os.getenv("ALERT2_ENABLED", "true").lower() == "true"
ALERT2_INTERVAL_MINUTES = int(os.getenv("ALERT2_INTERVAL_MINUTES", "60"))


def threshold_check_job():
    """Alert 1: Check thresholds and alert if exceeded"""
    print(f"\n{'='*50}")
    print("Running threshold check (Alert 1)...")
    print(f"{'='*50}")
    try:
        run_check()
    except Exception as e:
        error_msg = f"Error during threshold check: {e}"
        print(error_msg)
        send_notification(
            title="Canton Monitor ERROR",
            message=error_msg,
            priority=1
        )


def status_report_job():
    """Alert 2: Send status report with current values"""
    print(f"\n{'='*50}")
    print("Running status report (Alert 2)...")
    print(f"{'='*50}")
    try:
        run_status_report()
    except Exception as e:
        error_msg = f"Error during status report: {e}"
        print(error_msg)
        send_notification(
            title="Canton Monitor ERROR",
            message=error_msg,
            priority=1
        )


if __name__ == "__main__":
    # Start API server in background thread (includes health check)
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()

    print("Canton Rewards Monitor starting...")

    # Initialize database tables (creates if not exist, retries if DB not ready)
    init_db()

    print(f"Alert 1 (Threshold): {'ENABLED' if ALERT1_ENABLED else 'DISABLED'} - every {ALERT1_INTERVAL_MINUTES} mins")
    print(f"Alert 2 (Status):    {'ENABLED' if ALERT2_ENABLED else 'DISABLED'} - every {ALERT2_INTERVAL_MINUTES} mins")

    # Build startup message
    config_lines = []
    if ALERT1_ENABLED:
        config_lines.append(f"• Threshold alerts: every {ALERT1_INTERVAL_MINUTES} mins")
    if ALERT2_ENABLED:
        config_lines.append(f"• Status reports: every {ALERT2_INTERVAL_MINUTES} mins")
    if not config_lines:
        config_lines.append("• No alerts enabled!")

    send_notification(
        title="Canton Monitor Started",
        message="Running on Railway.\n" + "\n".join(config_lines),
        priority=0
    )

    # Run enabled checks immediately on start (with is_startup=True for Alert 1)
    if ALERT1_ENABLED:
        print(f"\n{'='*50}")
        print("Running startup threshold check (Alert 1)...")
        print(f"{'='*50}")
        try:
            run_check(is_startup=True)
        except Exception as e:
            error_msg = f"Error during startup threshold check: {e}"
            print(error_msg)
            send_notification(
                title="Canton Monitor ERROR",
                message=error_msg,
                priority=1
            )

    if ALERT2_ENABLED:
        status_report_job()

    # Schedule recurring checks
    if ALERT1_ENABLED:
        schedule.every(ALERT1_INTERVAL_MINUTES).minutes.do(threshold_check_job)

    if ALERT2_ENABLED:
        schedule.every(ALERT2_INTERVAL_MINUTES).minutes.do(status_report_job)

    print("Scheduler running. Next jobs:", schedule.get_jobs())

    while True:
        schedule.run_pending()
        time.sleep(60)
