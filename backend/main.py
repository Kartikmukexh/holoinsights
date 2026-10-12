from fastapi import FastAPI, HTTPException
import pyodbc
import os
import requests
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


def fetch_sales_rows():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, region, quarter, revenue FROM SalesData")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "product_name": row.product_name,
            "region": row.region,
            "quarter": row.quarter,
            "revenue": float(row.revenue),
        }
        for row in rows
    ]


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
    return {"data": fetch_sales_rows()}


@app.get("/api/insight")
def get_insight(question: str = "Summarise how sales are performing."):
    data = fetch_sales_rows()
    lines = [
        f"{r['product_name']} | {r['region']} | {r['quarter']} | ${r['revenue']:,.0f}"
        for r in data
    ]
    prompt = (
        "You are a business analyst inside a mixed reality dashboard. "
        "Using only the sales data below, answer the question in one or two "
        "plain sentences, with specific numbers. No markdown.\n\n"
        "Data (product | region | quarter | revenue):\n"
        + "\n".join(lines)
        + f"\n\nQuestion: {question}"
    )

    try:
        response = requests.post(
            os.getenv("LLM_ENDPOINT"),
            headers={
                "Authorization": f"Bearer {os.getenv('LLM_TOKEN')}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv("LLM_MODEL"),
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150,
            },
            timeout=30,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"LLM returned {response.status_code}: {response.text[:300]}",
        )

    try:
        insight = response.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected LLM response ({response.status_code}): {response.text[:300]!r}",
        )

    return {"question": question, "insight": insight, "data": data}