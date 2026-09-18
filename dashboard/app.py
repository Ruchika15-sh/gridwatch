from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.graph_objects as go
from dash import Dash, dash_table, dcc, html

from qa_framework.test_history import TestHistoryStore

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///local_test_history.db")
store = TestHistoryStore(DATABASE_URL)

app = Dash(__name__)
app.title = "GridWatch - Test History"


def build_trend_figure() -> go.Figure:
    runs = list(reversed(store.recent_runs(limit=30)))  # oldest -> newest, left to right
    fig = go.Figure()

    if not runs:
        fig.update_layout(title="No test runs recorded yet")
        return fig

    labels = [f"#{r.id} {r.git_commit} ({r.python_version})" for r in runs]
    fig.add_trace(go.Bar(x=labels, y=[r.passed for r in runs], name="Passed", marker_color="#2ECC71"))
    fig.add_trace(go.Bar(x=labels, y=[r.failed for r in runs], name="Failed", marker_color="#E74C3C"))
    fig.update_layout(
        barmode="stack",
        title="Test results by run",
        xaxis_title="Run (commit / Python version)",
        yaxis_title="Test count",
    )
    return fig


def build_flaky_table():
    flaky = store.flaky_tests(lookback_runs=10)
    data = [{"Test": f["test_name"], "Outcomes seen": ", ".join(f["outcomes_seen"])} for f in flaky]

    if not data:
        return html.P("No flaky tests detected in the last 10 runs.")

    return dash_table.DataTable(
        data=data,
        columns=[{"name": c, "id": c} for c in ["Test", "Outcomes seen"]],
        style_cell={"textAlign": "left", "padding": "8px"},
        style_header={"fontWeight": "bold"},
    )


CARD_STYLE = {
    "background": "#ffffff",
    "borderRadius": "10px",
    "padding": "20px 24px",
    "boxShadow": "0 1px 4px rgba(0,0,0,0.12)",
    "flex": "1",
    "minWidth": "180px",
}

PAGE_STYLE = {
    "fontFamily": "'Segoe UI', sans-serif",
    "background": "#f4f5f7",
    "minHeight": "100vh",
    "padding": "32px",
}

CONTAINER_STYLE = {"maxWidth": "1100px", "margin": "0 auto"}


def stat_card(label: str, value: str, accent: str = "#2c3e50"):
    return html.Div(
        style=CARD_STYLE,
        children=[
            html.Div(label, style={"fontSize": "13px", "color": "#8a8f98", "marginBottom": "8px", "textTransform": "uppercase", "letterSpacing": "0.5px"}),
            html.Div(value, style={"fontSize": "28px", "fontWeight": "700", "color": accent}),
        ],
    )


def build_summary_cards():
    runs = store.recent_runs(limit=100)
    if not runs:
        return html.Div("No test runs recorded yet - run pytest and record_test_run.py to get started.")

    latest = runs[0]
    pass_rate = round((latest.passed / latest.total) * 100, 1) if latest.total else 0
    flaky_count = len(store.flaky_tests(lookback_runs=10))

    latest_accent = "#E74C3C" if latest.failed > 0 else "#2ECC71"
    flaky_accent = "#E67E22" if flaky_count > 0 else "#2ECC71"

    return html.Div(
        style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "28px"},
        children=[
            stat_card("Latest run", f"{latest.passed}/{latest.total} passed", latest_accent),
            stat_card("Pass rate", f"{pass_rate}%", latest_accent),
            stat_card("Runs tracked", str(len(runs)), "#2c3e50"),
            stat_card("Flaky tests", str(flaky_count), flaky_accent),
        ],
    )


def build_layout():
    return html.Div(
        style=PAGE_STYLE,
        children=[
            html.Div(
                style=CONTAINER_STYLE,
                children=[
                    html.H1("GridWatch", style={"marginBottom": "2px"}),
                    html.P("AI-assisted test automation - run history", style={"color": "#8a8f98", "marginTop": 0, "marginBottom": "24px"}),
                    build_summary_cards(),
                    html.Div(
                        style=CARD_STYLE | {"marginBottom": "24px"},
                        children=[dcc.Graph(figure=build_trend_figure())],
                    ),
                    html.Div(
                        style=CARD_STYLE,
                        children=[
                            html.H3("Flaky tests (last 10 runs)", style={"marginTop": 0}),
                            build_flaky_table(),
                        ],
                    ),
                ],
            )
        ],
    )


# A callable, not a static value - Dash re-runs this on every browser
# page load, so new test runs show up on refresh without restarting
# the server.
app.layout = build_layout

if __name__ == "__main__":
    app.run(debug=True, port=8050)