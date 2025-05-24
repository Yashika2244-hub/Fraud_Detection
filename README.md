# Fraud Detection and Prevention Platform
A full-stack analytics solution to identify and prevent financial fraud using SQL, Python, Power BI, and Streamlit.

🔍 Project Overview
This project simulates a real-world financial fraud detection system. It is designed to help financial institutions monitor suspicious transactions, identify high-risk merchants and users, and take proactive steps using real-time alerts and data insights.

The platform integrates multiple tools to offer an end-to-end solution — from raw data to interactive dashboards and web deployment.

🎯 Objective
Detect and analyze fraudulent transactions

Provide user- and merchant-level fraud insights

Visualize fraud trends and anomalies

Enable real-time decision-making via dashboards and alerts

🛠️ Tools & Technologies
Tool	Purpose
Python (Jupyter)	Anomaly detection, EDA, and fraud pattern analysis
MySQL	Data extraction, joins, and aggregation across tables
Power BI	Interactive dashboards, card brand analysis, decomposition tree
Excel	Pre-processing and financial reporting
Streamlit	Web app deployment for real-time fraud insights

📊 Key Features
✅ Anomaly Detection: Highlights unusual spikes or transaction patterns

🧠 Explainable Analysis: Transparent, rule-based fraud logic without ML

🔍 Decomposition Tree (Power BI): Drill down into fraud drivers (card brand, amount range, etc.)

💬 Chatbot (Prototype): Basic Q&A fraud assistant embedded in the dashboard



🚦 How It Works
Data Cleaning: Used Python to prepare user, card, merchant, and transaction datasets.

ETL Process: Loaded and merged data in MySQL with optimized joins.

Fraud Detection: Applied rule-based logic in Python to flag anomalies.

Dashboarding: Created a multi-page Power BI report with slicers, visual KPIs, and decomposition trees.

Web App: Deployed the dashboard and SQL outputs using Streamlit for easy access and demonstration.

🖥️ Streamlit Deployment
🔗 App URL: [https://frauddetection-ksq7xedbyxxevf5kq9svwa.streamlit.app/]
🌐 This web app allows users to:

View merged transaction data

Navigate through different fraud analysis pages

Access dashboards and sql queries via simple UI

📌 Results & Insights
Identified high-risk merchants based on cresit score and fraud frequency

Detected anomalous transactions with large amounts outside normal thresholds

Enabled breakdown of fraud drivers (region, card type, user age group, etc.)

