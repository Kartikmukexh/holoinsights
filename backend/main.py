
import json
import os
from collections import defaultdict
from pathlib import Path

import pyodbc
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).parent / ".env")

app = FastAPI(title="HoloInsights API", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

SAMPLE_DATA_PATH = Path(__file__).parent / "sample_sales.json"


# --------------------------------------------------
# Configuration
# --------------------------------------------------

def azure_is_configured():
    required = [
        "AZURE_SQL_SERVER",
        "AZURE_SQL_DATABASE",
        "AZURE_SQL_USERNAME",
        "AZURE_SQL_PASSWORD",
    ]
    return all(os.getenv(name) for name in required)


def llm_is_configured():
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "gemini":
        return bool(os.getenv("GEMINI_API_KEY"))

    return all(
        os.getenv(name)
        for name in ["LLM_ENDPOINT", "LLM_TOKEN", "LLM_MODEL"]
    )


# --------------------------------------------------
# Azure SQL
# --------------------------------------------------

def get_connection():
    server = os.getenv("AZURE_SQL_SERVER")
    database = os.getenv("AZURE_SQL_DATABASE")
    username = os.getenv("AZURE_SQL_USERNAME")
    password = os.getenv("AZURE_SQL_PASSWORD")

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER=tcp:{server},1433;"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

    return pyodbc.connect(connection_string)


def fetch_sales_rows():
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT product_name, region, quarter, revenue "
            "FROM SalesData"
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


# --------------------------------------------------
# Sample data and data source selection
# --------------------------------------------------

def load_sample_data():
    with open(SAMPLE_DATA_PATH, "r", encoding="utf-8-sig") as file:
        return json.load(file)


def load_sales_data():
    if not azure_is_configured():
        try:
            return load_sample_data(), "sample"
        except (OSError, ValueError) as error:
            raise HTTPException(
                status_code=503,
                detail=f"Sample sales data unavailable: {error}",
            ) from error

    try:
        return fetch_sales_rows(), "azure"
    except pyodbc.Error as error:
        raise HTTPException(
            status_code=503,
            detail="Azure SQL is configured but sales data is unavailable.",
        ) from error


# --------------------------------------------------
# Sales aggregation
# --------------------------------------------------

def build_summary(rows):
    by_quarter = defaultdict(float)

    for row in rows:
        by_quarter[row["quarter"]] += float(row["revenue"])

    quarters = sorted(by_quarter)
    latest = quarters[-1] if quarters else None
    previous = quarters[-2] if len(quarters) > 1 else None

    def region_totals(quarter):
        totals = defaultdict(float)

        for row in rows:
            if row["quarter"] == quarter:
                totals[row["region"]] += float(row["revenue"])

        return dict(totals)

    latest_regions = region_totals(latest) if latest else {}
    previous_regions = region_totals(previous) if previous else {}

    region_stats = []

    for region, revenue in latest_regions.items():
        previous_revenue = previous_regions.get(region)

        change = (
            (revenue - previous_revenue) / previous_revenue * 100
            if previous_revenue
            else None
        )

        region_stats.append(
            {
                "region": region,
                "revenue": revenue,
                "change_pct": change,
            }
        )

    total_latest = by_quarter[latest] if latest else 0.0
    total_previous = by_quarter[previous] if previous else None

    total_change = (
        (total_latest - total_previous) / total_previous * 100
        if total_previous
        else None
    )

    return {
        "latest_quarter": latest,
        "previous_quarter": previous,
        "total_latest": total_latest,
        "total_change_pct": total_change,
        "regions": region_stats,
        "quarters": [
            {"quarter": quarter, "revenue": by_quarter[quarter]}
            for quarter in quarters
        ],
    }


# --------------------------------------------------
# Data-derived fallback insights
# --------------------------------------------------

def format_money(value):
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.1f} million"

    return f"${value:,.0f}"


def format_percent(value):
    return "n/a" if value is None else f"{value:+.0f}%"


def generate_rule_based_insight(question, summary):
    regions = summary["regions"]

    if not regions:
        return "There is no sales data available to analyse."

    text = (question or "").lower()
    latest = summary["latest_quarter"]

    ranked = sorted(
        regions,
        key=lambda region: region["revenue"],
        reverse=True,
    )

    if any(
        word in text
        for word in ("underperform", "worst", "declin", "weak", "lowest")
    ):
        regions_with_change = [
            region
            for region in regions
            if region["change_pct"] is not None
        ]

        if regions_with_change:
            weakest = min(
                regions_with_change,
                key=lambda region: region["change_pct"],
            )

            return (
                f"{weakest['region']} is the region to watch in {latest}: "
                f"revenue of {format_money(weakest['revenue'])}, "
                f"{format_percent(weakest['change_pct'])} "
                "versus the previous quarter."
            )

        weakest = ranked[-1]

        return (
            f"{weakest['region']} has the lowest revenue in {latest} "
            f"at {format_money(weakest['revenue'])}."
        )

    if any(
        word in text
        for word in ("trend", "month", "quarterly", "over time", "growth")
    ):
        quarters = summary["quarters"]

        if len(quarters) < 2:
            return "There is not enough quarterly data to show a trend."

        first = quarters[0]
        last = quarters[-1]

        direction = (
            "risen"
            if last["revenue"] >= first["revenue"]
            else "fallen"
        )

        return (
            f"Revenue has {direction} from "
            f"{format_money(first['revenue'])} in {first['quarter']} "
            f"to {format_money(last['revenue'])} in {last['quarter']}."
        )

    leader = ranked[0]

    return (
        f"Total revenue for {latest} was "
        f"{format_money(summary['total_latest'])} "
        f"({format_percent(summary['total_change_pct'])} "
        "versus the previous quarter). "
        f"{leader['region']} led with "
        f"{format_money(leader['revenue'])}."
    )


# --------------------------------------------------
# LLM integration
# --------------------------------------------------

def build_prompt(question, summary):
    region_lines = [
        (
            f"{region['region']}: "
            f"{format_money(region['revenue'])}, "
            f"{format_percent(region['change_pct'])} "
            "versus the previous quarter"
        )
        for region in summary["regions"]
    ]

    quarter_lines = [
        f"{quarter['quarter']}: {format_money(quarter['revenue'])}"
        for quarter in summary["quarters"]
    ]

    return (
        "You are a business analyst inside a mixed reality dashboard. "
        "Answer the user's question in one or two plain sentences. "
        "Use only the figures provided. Do not invent data. "
        "Do not use Markdown.\n\n"
        f"Latest quarter: {summary['latest_quarter']}\n"
        f"Previous quarter: {summary['previous_quarter']}\n"
        f"Latest revenue: {format_money(summary['total_latest'])}\n"
        f"Quarterly change: "
        f"{format_percent(summary['total_change_pct'])}\n\n"
        "Regions:\n"
        + "\n".join(region_lines)
        + "\n\nQuarterly totals:\n"
        + "\n".join(quarter_lines)
        + f"\n\nQuestion: {question}"
    )


def call_llm(prompt):
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL") or "gemini-2.0-flash"

        response = requests.post(
            (
                "https://generativelanguage.googleapis.com/"
                f"v1beta/models/{model}:generateContent"
            ),
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "contents": [
                    {"parts": [{"text": prompt}]}
                ]
            },
            timeout=20,
        )

        response.raise_for_status()

        return (
            response.json()["candidates"][0]["content"]["parts"][0]["text"]
            .strip()
        )

    if provider != "openai":
        raise ValueError(f"Unsupported LLM provider: {provider}")

    response = requests.post(
        os.getenv("LLM_ENDPOINT"),
        headers={
            "Authorization": f"Bearer {os.getenv('LLM_TOKEN')}",
            "Content-Type": "application/json",
        },
        json={
            "model": os.getenv("LLM_MODEL"),
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 150,
        },
        timeout=20,
    )

    response.raise_for_status()

    return (
        response.json()["choices"][0]["message"]["content"]
        .strip()
    )


# --------------------------------------------------
# API routes
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "HoloInsights backend running",
        "azure_configured": azure_is_configured(),
        "llm_configured": llm_is_configured(),
    }


@app.get("/api/test-db")
def test_db():
    if not azure_is_configured():
        raise HTTPException(
            status_code=503,
            detail="Azure SQL credentials are not configured.",
        )

    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1 AS test_value")
            row = cursor.fetchone()

        return {
            "connection": "success",
            "result": row.test_value,
        }

    except pyodbc.Error as error:
        raise HTTPException(
            status_code=503,
            detail="Azure SQL connection failed.",
        ) from error


@app.get("/api/sales-data")
def get_sales_data():
    data, source = load_sales_data()

    return {
        "source": source,
        "data": data,
    }


@app.get("/api/summary")
def get_summary():
    data, source = load_sales_data()

    return {
        **build_summary(data),
        "source": source,
    }


@app.get("/api/insight")
def get_insight(question: str = "Summarise how sales are performing."):
    data, source = load_sales_data()
    summary = build_summary(data)

    insight_type = "rule_based"

    if llm_is_configured():
        try:
            insight = call_llm(build_prompt(question, summary))

            if not insight:
                raise ValueError("The LLM returned an empty response.")

            insight_type = "llm"

        except (requests.RequestException, ValueError, KeyError,
                IndexError, TypeError, AttributeError, RuntimeError):
            insight = generate_rule_based_insight(question, summary)

    else:
        insight = generate_rule_based_insight(question, summary)

    return {
        "question": question,
        "insight": insight,
        "insight_type": insight_type,
        "source": source,
        "data": data,
        "summary": summary,
    }
