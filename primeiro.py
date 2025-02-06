from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

# Conexão com o banco de dados
def connect_to_db():
    return mysql.connector.connect(
        host="localhost", 
        user="root", 
        password="",  
        database="python"  
    )

# Criar tabela (se necessário)
def create_table():
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100),
            email VARCHAR(100)
        );
        """
    )
    connection.commit()
    connection.close()

# Rota para criar um novo usuário
@app.route('/usuarios', methods=['POST'])
def create_user():
    data = request.json
    nome = data.get('nome')
    email = data.get('email')

    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO usuarios (nome, email) VALUES (%s, %s)", (nome, email))
    connection.commit()
    connection.close()

    return jsonify({"message": "Usuário criado com sucesso!"}), 201

# Rota para listar todos os usuários
@app.route('/usuarios', methods=['GET'])
def get_users():
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM usuarios")
    rows = cursor.fetchall()
    connection.close()

    usuarios = [
        {"id": row[0], "nome": row[1], "email": row[2]} for row in rows
    ]
    return jsonify(usuarios)

# Rota para atualizar um usuário
@app.route('/usuarios/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    nome = data.get('nome')
    email = data.get('email')

    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("UPDATE usuarios SET nome = %s, email = %s WHERE id = %s", (nome, email, user_id))
    connection.commit()
    connection.close()

    return jsonify({"message": "Usuário atualizado com sucesso!"})

# Rota para excluir um usuário
@app.route('/usuarios/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
    connection.commit()
    connection.close()

    return jsonify({"message": "Usuário excluído com sucesso!"})

if __name__ == "__main__":
    create_table()
    app.run(debug=True)
