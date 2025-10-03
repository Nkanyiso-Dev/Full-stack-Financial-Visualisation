# 📊 Finance Dashboard

A full-stack application that lets users upload an Excel file with **monthly financial data**, stores it in **MySQL**, and displays it in a **table** and **bar chart**.

---

## ⚙️ Features
- Upload `.xlsx` Excel files
- Parse & store records in MySQL
- Retrieve data via REST API
- Display in dashboard (table + Chart.js bar chart)

---

## 🗄️ Database Setup
```bash
mysql -u root -p < backend/db_setup.sql
