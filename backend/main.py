from fastapi import FastAPI
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


def get_connection():
    server = os.getenv("AZURE_SQL_SERVER")
    database = os.getenv("AZURE_SQL_DATABASE")
    username = os.getenv("AZURE_SQL_USERNAME")
    password = os.getenv("AZURE_SQL_PASSWORD")
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER=tcp:{server},1433;"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)


@app.get("/")
def root():
    return {"status": "ok", "message": "HoloInsights backend running"}


@app.get("/api/test-db")
def test_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 AS test_value")
    row = cursor.fetchone()
    conn.close()
    return {"connection": "success", "result": row.test_value}


@app.get("/api/sales-data")
def get_sales_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, region, quarter, revenue FROM SalesData")
    rows = cursor.fetchall()
    conn.close()
    result = []
    for row in rows:
        result.append({
            "product_name": row.product_name,
            "region": row.region,
            "quarter": row.quarter,
            "revenue": float(row.revenue),
        })
    return {"data": result}