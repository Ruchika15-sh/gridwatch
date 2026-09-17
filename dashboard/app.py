"""
dashboard/app.py

A small Dash app visualizing GridWatch's test run history:
  - pass/fail trend across recent runs
  - a table of currently flaky tests

Run with:
    export DATABASE_URL=postgresql://user:pass@host/dbname   # or sqlite:///local.db
    python dashboard/app.py
Then open http://localhost:8050
"""

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


def build_layout():
    return html.Div(
        style={"fontFamily": "sans-serif", "maxWidth": "1000px", "margin": "0 auto", "padding": "24px"},
        children=[
            html.H1("GridWatch - Test History"),
            dcc.Graph(figure=build_trend_figure()),
            html.H2("Flaky tests (last 10 runs)"),
            build_flaky_table(),
        ],
    )


# A callable, not a static value - Dash re-runs this on every browser
# page load, so new test runs show up on refresh without restarting
# the server.
app.layout = build_layout

if __name__ == "__main__":
    app.run(debug=True, port=8050)