from flask import Flask, jsonify, request
import os
import time
import logging
import mysql.connector
import redis

app = Flask(__name__)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# MySQL configuration
DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "changeme")
DB_NAME = os.getenv("DB_NAME", "appdb")

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_APP_PORT", "6379"))


def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


def get_redis_connection():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )


def ensure_table():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS statistics (
            id INT PRIMARY KEY,
            visits INT NOT NULL
        )
    """)

    cur.execute("""
        INSERT IGNORE INTO statistics (id, visits)
        VALUES (1, 0)
    """)

    conn.commit()
    cur.close()
    conn.close()


# --------------------------------------------------
# Week 6 - Structured request logging
# --------------------------------------------------

@app.before_request
def start_timer():
    request.start_time = time.time()


@app.after_request
def log_request(response):
    duration = round((time.time() - request.start_time) * 1000, 2)

    app.logger.info(
        "method=%s path=%s status=%s duration_ms=%s",
        request.method,
        request.path,
        response.status_code,
        duration
    )

    return response


# --------------------------------------------------
# Week 6 - Health checks
# --------------------------------------------------

@app.get("/healthz")
def healthz():
    """Liveness check: confirms the Flask application is alive."""
    return jsonify(
        status="alive"
    ), 200


@app.get("/readyz")
def readyz():
    """Readiness check: confirms the database is reachable."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT 1")
        cur.fetchone()

        cur.close()
        conn.close()

        return jsonify(
            status="ready",
            database="connected"
        ), 200

    except Exception as e:
        app.logger.error("Database readiness check failed: %s", str(e))

        return jsonify(
            status="not ready",
            database="disconnected"
        ), 503


# --------------------------------------------------
# Existing API routes
# --------------------------------------------------

@app.get("/api/health")
def health():
    return jsonify(status="ok")


@app.get("/api/dbtime")
def dbtime():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT NOW()")
    row = cur.fetchone()

    cur.close()
    conn.close()

    return jsonify(
        database_time=str(row[0])
    )


@app.get("/api/visit")
def visit():
    ensure_table()

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE statistics
        SET visits = visits + 1
        WHERE id = 1
    """)

    conn.commit()

    cur.execute("""
        SELECT visits
        FROM statistics
        WHERE id = 1
    """)

    row = cur.fetchone()

    cur.close()
    conn.close()

    return jsonify(
        visits=row[0]
    )


@app.get("/api/status")
def status():
    ensure_table()

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT NOW()")
    db_time = cur.fetchone()[0]

    cur.execute("""
        SELECT visits
        FROM statistics
        WHERE id = 1
    """)

    visits = cur.fetchone()[0]

    cur.close()
    conn.close()

    return jsonify(
        name="Jagrit Handa",
        database="connected",
        database_time=str(db_time),
        visits=visits
    )


@app.get("/api/cache")
def cache():
    try:
        r = get_redis_connection()

        cached_value = r.get("week5-demo")

        if cached_value is None:
            cached_value = "Hello from Redis!"
            r.setex("week5-demo", 300, cached_value)
            source = "new value stored in Redis"
        else:
            source = "value retrieved from Redis cache"

        return jsonify(
            redis="connected",
            value=cached_value,
            source=source
        )

    except Exception as e:
        return jsonify(
            redis="error",
            message=str(e)
        ), 500


if __name__ == "__main__":
    ensure_table()
    app.run(host="0.0.0.0", port=8000)