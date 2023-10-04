import pandas as pd

df = pd.read_csv("session_data.txt",delimiter="\t")
df.columns = ["hour", "minute", "session_count"]
df.to_csv("/var/www/html/session_count.csv")
print(df)
