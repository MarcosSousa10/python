from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configuração do JWT
app.config["JWT_SECRET_KEY"] = "sua_chave_secreta"  # Substitua por uma chave secreta segura
jwt = JWTManager(app)

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
            email VARCHAR(100) UNIQUE,
            senha VARCHAR(255)
        );
        """
    )
    connection.commit()
    connection.close()

# Rota para registrar usuário
@app.route('/register/', methods=['POST'])
def register_user():
    data = request.json
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')

    if not nome or not email or not senha:
        return jsonify({"message": "Todos os campos são obrigatórios!"}), 400

    hashed_password = generate_password_hash(senha)

    connection = connect_to_db()
    cursor = connection.cursor()

    # Verificar se o e-mail já está cadastrado
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    if cursor.fetchone():
        connection.close()
        return jsonify({"message": "E-mail já cadastrado."}), 400

    # Inserir novo usuário
    cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)", (nome, email, hashed_password))
    connection.commit()
    connection.close()

    return jsonify({"message": "Usuário registrado com sucesso!"}), 201

# Rota para login e geração de token
@app.route('/login/', methods=['POST'])
def login_user():
    data = request.json
    email = data.get('email')
    senha = data.get('senha')

    if not email or not senha:
        return jsonify({"message": "E-mail e senha são obrigatórios!"}), 400

    connection = connect_to_db()
    cursor = connection.cursor()

    # Verificar se o usuário existe
    cursor.execute("SELECT id, senha FROM usuarios WHERE email = %s", (email,))
    user = cursor.fetchone()
    connection.close()

    if not user or not check_password_hash(user[1], senha):
        return jsonify({"message": "Credenciais inválidas."}), 401

    # Gerar token JWT
    # Gerar token JWT
    token = create_access_token(identity=str(user[0]))  # Passa o ID como string

    # token = create_access_token(identity=user[0])

    return jsonify({"token": token}), 200

# Rota protegida (exemplo)
@app.route('/protected/', methods=['GET'])
@jwt_required()
def protected():
    user_id = get_jwt_identity()
    return jsonify({"message": "Acesso permitido.", "user_id": user_id}), 200

# Rota protegida para listar todos os usuários
@app.route('/usuarios', methods=['GET'])
@jwt_required()
def get_users():
    # Verifica a identidade do usuário (informações do token)
    current_user = get_jwt_identity()
    print("Token payload:", current_user)  # Verifique o que está retornando aqui
    
    # Se current_user não for uma string, converta-o para uma string
    if not isinstance(current_user, str):
        current_user = str(current_user)

    # Conectar ao banco de dados
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id, nome, email FROM usuarios")
    rows = cursor.fetchall()
    connection.close()

    # Formatar a resposta
    usuarios = [{"id": row[0], "nome": row[1], "email": row[2]} for row in rows]
    
    return jsonify(usuarios), 200


@app.route('/usuarios/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    data = request.json
    nome = data.get('nome')
    email = data.get('email')

    if not nome or not email:
        return jsonify({"message": "Nome e e-mail são obrigatórios!"}), 400

    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("UPDATE usuarios SET nome = %s, email = %s WHERE id = %s", (nome, email, user_id))
    connection.commit()
    connection.close()

    return jsonify({"message": "Usuário atualizado com sucesso!"}), 200

# Rota protegida para excluir um usuário
@app.route('/usuarios/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
    connection.commit()
    connection.close()

    return jsonify({"message": "Usuário excluído com sucesso!"}), 200

if __name__ == "__main__":
    create_table()
    app.run(debug=True)
