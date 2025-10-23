# Ethekwini WS-7761 Dashboard

This Streamlit app visualizes the contents of the provided Excel workbook (`Ethekwini WS-7761 07 Oct 2025.xlsx`). It integrates all sheets and provides:

- KPIs (total tasks, completed, in progress, overdue)
- Progress, Priority and Bucket charts
- Timeline (Start -> Due)
- Overdue tasks table
- Export current sheet view to CSV

## How to run locally

1. Create a virtual environment (recommended)
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud / Streamlit Sharing

1. Create a new GitHub repository and push the contents of this folder.
2. On [streamlit.io/cloud](https://streamlit.io/cloud), connect your GitHub repo and deploy.
3. Make sure the Excel file (`Ethekwini WS-7761 07 Oct 2025.xlsx`) is included in the repository root or change `load_data` path in `app.py`.

--