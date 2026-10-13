import os
from collections import defaultdict

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="HoloInsights backend")

# The browser prototype (Live Server / file://) calls this API from another origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


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


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
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
    return {"data": load_rows_or_503()}


@app.get("/api/summary")
def get_summary():
    return build_summary(load_rows_or_503())


@app.get("/api/insight")
def get_insight(question: str = "Summarise how sales are performing."):
    rows = load_rows_or_503()
    summary = build_summary(rows)

    source, note = "llm", None
    try:
        insight = call_llm(build_prompt(question, rows, summary))
        if not insight:
            raise RuntimeError("empty LLM response")
    except Exception as e:
        # Never fail the demo because the LLM is unreachable: answer from the data.
        insight = fallback_insight(question, summary)
        source, note = "fallback", str(e)

    return {
        "question": question,
        "insight": insight,
        "source": source,  # "llm" = AI generated, "fallback" = computed from SQL data
        "note": note,
        "summary": summary,
    }
