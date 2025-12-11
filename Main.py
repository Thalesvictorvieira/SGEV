import psycopg2

conecao = psycopg2.connect(
    host="localhost",
    database ="SERVER SGEV",
    user="postgres",
    password="1234"
)

cursor = conecao.cursor()

cursor.execute("SELECT * FROM produtos;")
dados = cursor.fetchall()

for linha in dados:
    print(linha)
