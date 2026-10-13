import os
import pyodbc
from collections import defaultdict

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="HoloInsights API", version="1.1.0")
app = FastAPI(title="HoloInsights backend")

SAMPLE_DATA_PATH = Path(__file__).parent / "sample_sales.json"
# The browser prototype (Live Server / file://) calls this API from another origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


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

# --------------------------------------------------------------------------
# Data layer (Azure SQL)
# --------------------------------------------------------------------------
def get_connection():
    import pyodbc  # imported lazily so the module loads without the ODBC driver

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


def load_rows_or_503():
    try:
        return fetch_sales_rows()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {e}")


# --------------------------------------------------------------------------
# Aggregation + deterministic (non-LLM) insight
# --------------------------------------------------------------------------
def build_summary(rows):
    """Aggregate raw SalesData rows into the shapes the dashboard needs."""
    by_quarter = defaultdict(float)
    for r in rows:
        by_quarter[r["quarter"]] += r["revenue"]
    quarters = sorted(by_quarter)
    latest = quarters[-1] if quarters else None
    previous = quarters[-2] if len(quarters) > 1 else None

    def region_totals(quarter):
        totals = defaultdict(float)
        for r in rows:
            if r["quarter"] == quarter:
                totals[r["region"]] += r["revenue"]
        return dict(totals)

    latest_regions = region_totals(latest) if latest else {}
    prev_regions = region_totals(previous) if previous else {}

    region_stats = []
    for region, value in latest_regions.items():
        prev = prev_regions.get(region)
        change = ((value - prev) / prev * 100) if prev else None
        region_stats.append({"region": region, "revenue": value, "change_pct": change})

    total_latest = by_quarter[latest] if latest else 0.0
    total_prev = by_quarter[previous] if previous else None
    total_change = (
        (total_latest - total_prev) / total_prev * 100 if total_prev else None
    )

    return {
        "latest_quarter": latest,
        "previous_quarter": previous,
        "total_latest": total_latest,
        "total_change_pct": total_change,
        "regions": region_stats,
        "quarters": [{"quarter": q, "revenue": by_quarter[q]} for q in quarters],
    }


def _money(v):
    return f"${v / 1e6:.1f} million" if abs(v) >= 1e6 else f"${v:,.0f}"


def _pct(v):
    return "n/a" if v is None else f"{v:+.0f}%"


def fallback_insight(question, summary):
    """Plain data-driven answer used when no LLM is reachable. Not AI-generated."""
    regions = summary["regions"]
    if not regions:
        return "There is no sales data to analyse yet."
    q = (question or "").lower()
    latest = summary["latest_quarter"]
    ranked = sorted(regions, key=lambda r: r["revenue"], reverse=True)

    if any(w in q for w in ("underperform", "worst", "declin", "weak", "lowest")):
        with_change = [r for r in regions if r["change_pct"] is not None]
        worst = min(with_change, key=lambda r: r["change_pct"]) if with_change else ranked[-1]
        if worst["change_pct"] is not None:
            return (
                f"{worst['region']} is the region to watch in {latest}: revenue of "
                f"{_money(worst['revenue'])}, {_pct(worst['change_pct'])} versus the previous quarter."
            )
        return f"{worst['region']} is the lowest region in {latest} at {_money(worst['revenue'])}."

    if any(w in q for w in ("trend", "month", "quarterly", "over time", "growth")):
        qs = summary["quarters"]
        if len(qs) < 2:
            return f"Only one quarter of data ({qs[0]['quarter']}) is available, so no trend yet."
        first, last = qs[0], qs[-1]
        direction = "risen" if last["revenue"] >= first["revenue"] else "fallen"
        return (
            f"Revenue has {direction} from {_money(first['revenue'])} in {first['quarter']} "
            f"to {_money(last['revenue'])} in {last['quarter']} across {len(qs)} quarters."
        )

    top = ranked[0]
    return (
        f"Total revenue for {latest} was {_money(summary['total_latest'])} "
        f"({_pct(summary['total_change_pct'])} versus the previous quarter). "
        f"{top['region']} led with {_money(top['revenue'])}."
    )


# --------------------------------------------------------------------------
# LLM call (provider switchable via LLM_PROVIDER = openai | gemini)
# --------------------------------------------------------------------------
def call_llm(prompt):
    provider = (os.getenv("LLM_PROVIDER") or "openai").lower()

    if provider == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL") or "gemini-2.0-flash"
        if not key:
            raise RuntimeError("GEMINI_API_KEY not set")
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=20,
        )
        if r.status_code != 200:
            raise RuntimeError(f"Gemini returned {r.status_code}: {r.text[:200]}")
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

    # OpenAI-compatible chat/completions (GitHub Models, Azure OpenAI, OpenAI)
    endpoint = os.getenv("LLM_ENDPOINT")
    if not endpoint:
        raise RuntimeError("LLM_ENDPOINT not set")
    r = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {os.getenv('LLM_TOKEN')}",
            "Content-Type": "application/json",
        },
        json={
            "model": os.getenv("LLM_MODEL"),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 150,
        },
        timeout=20,
    )
    if r.status_code != 200:
        raise RuntimeError(f"LLM returned {r.status_code}: {r.text[:200]}")
    try:
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        raise RuntimeError(f"Unexpected LLM response: {r.text[:200]!r}")


def build_prompt(question, rows, summary):
    # Pre-computed figures keep the AI consistent with the dashboard cards.
    region_lines = [
        f"{r['region']}: {_money(r['revenue'])} in {summary['latest_quarter']}, "
        f"{_pct(r['change_pct'])} vs {summary['previous_quarter']}"
        for r in summary["regions"]
    ]
    quarter_lines = [f"{q['quarter']}: {_money(q['revenue'])}" for q in summary["quarters"]]
    return (
        "You are a business analyst inside a mixed reality dashboard. "
        "Answer the question in one or two plain sentences with specific numbers. No markdown.\n"
        "Rules: 'this quarter' or 'performance' means the latest quarter. "
        "'Underperforming' means the region with the weakest change versus the previous quarter. "
        "'Trend' means the quarterly totals. Use only the figures below.\n\n"
        f"Latest quarter: {summary['latest_quarter']}, total {_money(summary['total_latest'])}, "
        f"{_pct(summary['total_change_pct'])} vs {summary['previous_quarter']}\n"
        "Regions (latest quarter):\n" + "\n".join(region_lines)
        + "\nQuarterly totals:\n" + "\n".join(quarter_lines)
        + f"\n\nQuestion: {question}"
    )


# Load our local sample dataset.
def load_sample_data():
    with open(SAMPLE_DATA_PATH, "r", encoding="utf-8-sig") as file:
        return json.load(file)
# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "HoloInsights backend running"}


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
@app.get("/api/sales-data")
def get_sales_data():
    return {"data": load_rows_or_503()}


@app.get("/api/summary")
def get_summary():
    return build_summary(load_rows_or_503())


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
@app.get("/api/insight")
def get_insight(question: str = "Summarise how sales are performing."):
    rows = load_rows_or_503()
    summary = build_summary(rows)

    source, note = "llm", None
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
        insight = call_llm(build_prompt(question, rows, summary))
        if not insight:
            raise RuntimeError("empty LLM response")
    except Exception as e:
        # Never fail the demo because the LLM is unreachable: answer from the data.
        insight = fallback_insight(question, summary)
        source, note = "fallback", str(e)


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
    return {
        "question": question,
        "insight": insight,
        "source": source,  # "llm" = AI generated, "fallback" = computed from SQL data
        "note": note,
        "summary": summary,
    }
