import pandas as pd
import sqlite3

# Подключение к SQLite
conn = sqlite3.connect("fraud_monitoring.db")

# Чтение таблицы
query = "SELECT * FROM transactions"

df = pd.read_sql(query, conn)

# Экспорт в CSV
df.to_csv("transactions.csv", index=False)

print("CSV exported successfully")
print(df.head())