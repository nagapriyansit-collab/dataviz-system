# 📊 DataViz Explorer

A simple, professional Data Visualization web app built with Python (Flask + Plotly).
Perfect for a fresher data scientist to explore any CSV dataset visually!

## 🚀 How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the server
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

## ✨ Features

- **Drag & Drop CSV Upload** — just drop any `.csv` file
- **Instant Dataset Overview** — rows, columns, missing values, duplicates
- **Auto-Generated Charts** — smart charts chosen based on your data
- **Custom Chart Builder** — choose from 8 chart types:
  - Histogram
  - Scatter Plot
  - Bar Chart
  - Box Plot
  - Violin Plot
  - Pie Chart
  - Line Chart
  - Correlation Heatmap
- **Interactive Plotly Charts** — zoom, hover, download

## 📁 Project Structure

```
dataviz_app/
├── app.py              # Flask backend
├── requirements.txt    # Python dependencies
├── sample_data.csv     # Test dataset (employees)
├── uploads/            # Uploaded CSVs stored here
└── templates/
    └── index.html      # Single-page frontend
```

## 🧪 Test with sample data

Use `sample_data.csv` included in this folder — it contains employee records
with numeric, categorical, and mixed columns — great for testing all chart types!
