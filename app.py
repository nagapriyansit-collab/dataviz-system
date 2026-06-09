"""
DataViz Explorer - A simple data visualization web app
Built by a fresher data scientist :)
"""

import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "dataviz_secret_key_2024"

# Config
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --------------- helpers ---------------

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_df(filename):
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    return pd.read_csv(path)


def get_col_types(df):
    numeric = df.select_dtypes(include="number").columns.tolist()
    categorical = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime = df.select_dtypes(include=["datetime"]).columns.tolist()
    return {"numeric": numeric, "categorical": categorical, "datetime": datetime}


def summary_stats(df):
    stats = {}
    stats["rows"] = int(df.shape[0])
    stats["cols"] = int(df.shape[1])
    stats["missing"] = int(df.isnull().sum().sum())
    stats["missing_pct"] = round(stats["missing"] / (stats["rows"] * stats["cols"]) * 100, 2)
    stats["duplicates"] = int(df.duplicated().sum())
    col_types = get_col_types(df)
    stats["num_numeric"] = len(col_types["numeric"])
    stats["num_categorical"] = len(col_types["categorical"])

    # Per-column info
    col_info = []
    for col in df.columns:
        info = {
            "name": col,
            "dtype": str(df[col].dtype),
            "missing": int(df[col].isnull().sum()),
            "unique": int(df[col].nunique()),
        }
        if col in col_types["numeric"]:
            info["mean"] = round(float(df[col].mean()), 3) if not df[col].isnull().all() else None
            info["std"] = round(float(df[col].std()), 3) if not df[col].isnull().all() else None
            info["min"] = round(float(df[col].min()), 3) if not df[col].isnull().all() else None
            info["max"] = round(float(df[col].max()), 3) if not df[col].isnull().all() else None
        col_info.append(info)

    stats["columns"] = col_info
    return stats


# --------------- routes ---------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only CSV files are allowed"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        df = pd.read_csv(filepath)
        session["filename"] = filename
        stats = summary_stats(df)
        col_types = get_col_types(df)

        # Preview — first 8 rows
        preview = df.head(8).fillna("").to_dict(orient="records")
        headers = df.columns.tolist()

        return jsonify({
            "success": True,
            "filename": filename,
            "stats": stats,
            "col_types": col_types,
            "preview": preview,
            "headers": headers,
        })
    except Exception as e:
        return jsonify({"error": f"Could not read CSV: {str(e)}"}), 500


@app.route("/visualize", methods=["POST"])
def visualize():
    data = request.get_json()
    filename = session.get("filename") or data.get("filename")
    if not filename:
        return jsonify({"error": "No file uploaded"}), 400

    df = load_df(filename)
    chart_type = data.get("chart_type", "histogram")
    x_col = data.get("x_col")
    y_col = data.get("y_col")
    color_col = data.get("color_col")

    try:
        fig = None
        color_arg = color_col if color_col and color_col != "None" else None

        if chart_type == "histogram":
            fig = px.histogram(df, x=x_col, color=color_arg,
                               title=f"Distribution of {x_col}",
                               template="plotly_dark",
                               color_discrete_sequence=px.colors.sequential.Plasma)

        elif chart_type == "scatter":
            if not y_col:
                return jsonify({"error": "Scatter plot needs Y column"}), 400
            fig = px.scatter(df, x=x_col, y=y_col, color=color_arg,
                             title=f"{x_col} vs {y_col}",
                             template="plotly_dark",
                             color_discrete_sequence=px.colors.qualitative.Bold)

        elif chart_type == "bar":
            if y_col:
                bar_df = df.groupby(x_col)[y_col].mean().reset_index()
                fig = px.bar(bar_df, x=x_col, y=y_col,
                             title=f"Average {y_col} by {x_col}",
                             template="plotly_dark",
                             color=y_col,
                             color_continuous_scale="Viridis")
            else:
                vc = df[x_col].value_counts().reset_index()
                vc.columns = [x_col, "count"]
                fig = px.bar(vc, x=x_col, y="count",
                             title=f"Count of {x_col}",
                             template="plotly_dark",
                             color="count",
                             color_continuous_scale="Plasma")

        elif chart_type == "box":
            fig = px.box(df, x=color_arg, y=x_col,
                         title=f"Box Plot of {x_col}",
                         template="plotly_dark",
                         color=color_arg,
                         color_discrete_sequence=px.colors.qualitative.Vivid)

        elif chart_type == "pie":
            vc = df[x_col].value_counts().reset_index()
            vc.columns = [x_col, "count"]
            fig = px.pie(vc, names=x_col, values="count",
                         title=f"Pie Chart of {x_col}",
                         template="plotly_dark",
                         color_discrete_sequence=px.colors.qualitative.Bold)

        elif chart_type == "line":
            if not y_col:
                return jsonify({"error": "Line chart needs Y column"}), 400
            fig = px.line(df, x=x_col, y=y_col, color=color_arg,
                          title=f"{y_col} over {x_col}",
                          template="plotly_dark",
                          color_discrete_sequence=px.colors.qualitative.Plotly)

        elif chart_type == "heatmap":
            num_cols = df.select_dtypes(include="number").columns.tolist()
            if len(num_cols) < 2:
                return jsonify({"error": "Need at least 2 numeric columns for heatmap"}), 400
            corr = df[num_cols].corr()
            fig = go.Figure(data=go.Heatmap(
                z=corr.values,
                x=corr.columns.tolist(),
                y=corr.index.tolist(),
                colorscale="RdBu",
                zmid=0,
            ))
            fig.update_layout(title="Correlation Heatmap", template="plotly_dark")

        elif chart_type == "violin":
            fig = px.violin(df, x=color_arg, y=x_col, box=True,
                            title=f"Violin Plot of {x_col}",
                            template="plotly_dark",
                            color=color_arg,
                            color_discrete_sequence=px.colors.qualitative.Pastel)

        if fig is None:
            return jsonify({"error": "Unknown chart type"}), 400

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,15,25,0.6)",
            font=dict(family="IBM Plex Mono, monospace", color="#e0e0ff"),
            margin=dict(l=40, r=40, t=60, b=40),
        )

        graphJSON = json.dumps(fig, cls=PlotlyJSONEncoder)
        return jsonify({"success": True, "plot": graphJSON})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/auto_charts", methods=["POST"])
def auto_charts():
    """Auto-generate 4 smart charts based on the dataset."""
    data = request.get_json()
    filename = session.get("filename") or data.get("filename")
    if not filename:
        return jsonify({"error": "No file uploaded"}), 400

    df = load_df(filename)
    col_types = get_col_types(df)
    charts = []

    num_cols = col_types["numeric"]
    cat_cols = col_types["categorical"]

    # 1. Histogram of first numeric col
    if num_cols:
        col = num_cols[0]
        fig = px.histogram(df, x=col, title=f"Distribution of {col}",
                           template="plotly_dark",
                           color_discrete_sequence=["#7B61FF"])
        _style(fig)
        charts.append({"title": f"Distribution — {col}", "plot": json.dumps(fig, cls=PlotlyJSONEncoder)})

    # 2. Scatter of first two numeric cols
    if len(num_cols) >= 2:
        fig = px.scatter(df, x=num_cols[0], y=num_cols[1],
                         color=cat_cols[0] if cat_cols else None,
                         title=f"{num_cols[0]} vs {num_cols[1]}",
                         template="plotly_dark",
                         color_discrete_sequence=px.colors.qualitative.Bold)
        _style(fig)
        charts.append({"title": f"Scatter — {num_cols[0]} × {num_cols[1]}", "plot": json.dumps(fig, cls=PlotlyJSONEncoder)})

    # 3. Bar / value counts of first categorical col
    if cat_cols:
        vc = df[cat_cols[0]].value_counts().head(12).reset_index()
        vc.columns = [cat_cols[0], "count"]
        fig = px.bar(vc, x=cat_cols[0], y="count",
                     title=f"Top values in {cat_cols[0]}",
                     template="plotly_dark",
                     color="count",
                     color_continuous_scale="Plasma")
        _style(fig)
        charts.append({"title": f"Counts — {cat_cols[0]}", "plot": json.dumps(fig, cls=PlotlyJSONEncoder)})

    # 4. Correlation heatmap
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        fig = go.Figure(data=go.Heatmap(
            z=corr.values, x=corr.columns.tolist(), y=corr.index.tolist(),
            colorscale="RdBu", zmid=0,
        ))
        fig.update_layout(title="Correlation Heatmap", template="plotly_dark")
        _style(fig)
        charts.append({"title": "Correlation Heatmap", "plot": json.dumps(fig, cls=PlotlyJSONEncoder)})

    return jsonify({"success": True, "charts": charts})


def _style(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,15,25,0.6)",
        font=dict(family="IBM Plex Mono, monospace", color="#e0e0ff"),
        margin=dict(l=40, r=40, t=60, b=40),
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
