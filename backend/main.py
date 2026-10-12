
from fastapi import FastAPI, HTTPException
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict
import json
import os
import pyodbc
import requests

load_dotenv()

app = FastAPI(title="HoloInsights API", version="1.1.0")

SAMPLE_DATA_PATH = Path(__file__).parent / "sample_sales.json"


# Check whether Azure SQL credentials are available.
def azure_is_configured():
    required = [
        "AZURE_SQL_SERVER",
        "AZURE_SQL_DATABASE",
        "AZURE_SQL_USERNAME",
        "AZURE_SQL_PASSWORD",
    ]
    return all(os.getenv(name) for name in required)


# Check whether the external AI service is configured.
def llm_is_configured():
    required = ["LLM_ENDPOINT", "LLM_TOKEN", "LLM_MODEL"]
    return all(os.getenv(name) for name in required)


# Preserve Kartik's Azure SQL connection.
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


# Retrieve sales records from Azure SQL.
def fetch_sales_rows():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT product_name, region, quarter, revenue FROM SalesData"
        )
        rows = cursor.fetchall()

        return [
            {
                "product_name": row.product_name,
                "region": row.region,
                "quarter": row.quarter,
                "revenue": float(row.revenue),
            }
            for row in rows
        ]


# Load our local sample dataset.
def load_sample_data():
    with open(SAMPLE_DATA_PATH, "r", encoding="utf-8-sig") as file:
        return json.load(file)


# Choose Azure SQL or local sample data.
def load_sales_data():
    if not azure_is_configured():
        return load_sample_data(), "sample"

    try:
        return fetch_sales_rows(), "azure"
    except pyodbc.Error:
        raise HTTPException(
            status_code=503,
            detail="Azure SQL is configured but sales data is unavailable."
        )


# Generate an offline, data-derived sales summary.
def generate_rule_based_insight(data):
    if not data:
        return "No sales records are available for analysis."

    product_totals = defaultdict(float)
    region_totals = defaultdict(float)

    for record in data:
        revenue = float(record["revenue"])
        product_totals[record["product_name"]] += revenue
        region_totals[record["region"]] += revenue

    leading_product = max(product_totals, key=product_totals.get)
    leading_region = max(region_totals, key=region_totals.get)
    total_revenue = sum(product_totals.values())

    return (
        f"Total revenue is ${total_revenue:,.0f}. "
        f"{leading_product} leads product sales with "
        f"${product_totals[leading_product]:,.0f}, "
        f"while {leading_region} is the highest-revenue region "
        f"at ${region_totals[leading_region]:,.0f}."
    )


# Preserve Kartik's external LLM insight integration.
def generate_llm_insight(question, data):
    lines = [
        f"{r['product_name']} | {r['region']} | "
        f"{r['quarter']} | ${r['revenue']:,.0f}"
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

        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"].strip()

    except (
        requests.RequestException,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        AttributeError,
    ) as error:
        raise HTTPException(
            status_code=502,
            detail=f"AI insight generation failed: {type(error).__name__}"
        )


# Check whether the backend is running.
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "HoloInsights backend running",
        "azure_configured": azure_is_configured(),
        "llm_configured": llm_is_configured(),
    }


# Test the Azure SQL database connection.
@app.get("/api/test-db")
def test_db():
    if not azure_is_configured():
        raise HTTPException(
            status_code=503,
            detail="Azure SQL credentials are not configured."
        )

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 AS test_value")
            row = cursor.fetchone()

        return {"connection": "success", "result": row.test_value}

    except pyodbc.Error:
        raise HTTPException(
            status_code=503,
            detail="Azure SQL connection failed."
        )


# Return sales records to Unity.
@app.get("/api/sales-data")
def get_sales_data():
    data, source = load_sales_data()

    return {
        "source": source,
        "data": data,
    }


# Generate an AI or offline sales insight.
@app.get("/api/insight")
def get_insight(question: str = "Summarise how sales are performing."):
    data, source = load_sales_data()

    if llm_is_configured():
        insight = generate_llm_insight(question, data)
        insight_type = "llm"
    else:
        insight = generate_rule_based_insight(data)
        insight_type = "rule_based"

    return {
        "question": question,
        "insight": insight,
        "insight_type": insight_type,
        "source": source,
        "data": data,
    }
