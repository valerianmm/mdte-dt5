import psycopg2
import json

# ─── PostgreSQL Config ───────────────────────────────────────
PG_HOST = "postgres"
PG_DB = "iotdata"
PG_USER = "postgres"
PG_PASSWORD = "password"

# ─── MODIFY THIS VALUE ANY TIME YOU WANT ─────────────────────
MINUTES_TO_FETCH = 5      # ← change this number

def fetch_last_minutes(minutes: int):
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cursor = conn.cursor()

        query = """
        SELECT timestamp, sample_id, ax, ay, az, gx, gy, gz, received_at
        FROM imu_data
        WHERE received_at >= NOW() - INTERVAL %s
        ORDER BY received_at DESC;
        """

        interval = f"{minutes} minutes"
        cursor.execute(query, (interval,))
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return rows

    except Exception as e:
        print("Database error:", e)
        return []

if __name__ == "__main__":
    # <<< use the variable here >>>
    rows = fetch_last_minutes(MINUTES_TO_FETCH)

    print(json.dumps(rows, indent=2, default=str))
