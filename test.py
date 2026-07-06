import sqlite3

# 1. 创建一个纯内存数据库
conn = sqlite3.connect(":memory:")
cursor = conn.cursor()

# 2. 读取并执行 SQL 脚本文件
sql_file = "data\网络结果落库脚本.sql"
try:
    with open(sql_file, "r", encoding="utf-8") as f:
        sql_script = f.read()
    cursor.executescript(sql_script)
    print(f"✅ 成功执行 {sql_file} 脚本！\n")
except FileNotFoundError:
    print(f"❌ 错误：找不到文件 {sql_file}，请确保文件在当前目录下。")
    exit()
except sqlite3.Error as e:
    print(f"❌ 执行 SQL 脚本时发生错误: {e}")
    exit()

# 3. 获取数据库中所有的表名
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# 4. 遍历每个表，打印前 10 行数据
for table_name in tables:
    table_name = table_name[0]
    print(f"📊 正在查看表: 【{table_name}】")

    # 获取表的字段名（列名）
    cursor.execute(f"PRAGMA table_info([{table_name}])")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"字段包含: {columns}")

    # 查询前 10 行数据
    cursor.execute(f"SELECT * FROM [{table_name}] LIMIT 10")
    rows = cursor.fetchall()

    # 打印数据
    if rows:
        for row in rows:
            print(row)
    else:
        print("（该表为空，没有数据）")

    print("-" * 50)

# 5. 关闭内存数据库
conn.close()