from flask import Flask, render_template, request,jsonify

from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string

app = Flask(__name__)

# Configuração do JWT
app.config["JWT_SECRET_KEY"] = "teste"  
jwt = JWTManager(app)
def connect_to_db():
    return mysql.connector.connect(
        host="localhost", 
        user="root", 
        password="",  
        database="python"
    )

def create_table():
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            senha VARCHAR(255),
            email_verificado BOOLEAN DEFAULT FALSE,
            token_verificacao VARCHAR(255)
        );
        """
    )
    connection.commit()
    connection.close()


def send_email(to_email, subject, body):
    # Configurações do servidor SMTP
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "marcospegodesousa10@gmail.com"  
    smtp_password = "ydzprxplbjmeyedl" 

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Conectar ao servidor SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Iniciar criptografia TLS
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())  # Enviar o e-mail
        server.quit()  # Fechar a conexão com o servidor
        print(f'E-mail enviado para {to_email}')
    except Exception as e:
        print(f"Erro ao enviar o e-mail: {str(e)}")



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

    # Gerar token de verificação único
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=20))

    # Inserir novo usuário com token de verificação
    cursor.execute("INSERT INTO usuarios (nome, email, senha, token_verificacao) VALUES (%s, %s, %s, %s)",
                   (nome, email, hashed_password, token))
    connection.commit()
    connection.close()

    # Enviar email com link de verificação
    verification_link = f'http://localhost:5000/verify/{token}'  # Substitua pela URL do seu servidor
    send_email(email, "Verifique seu e-mail", f'Clique no link para verificar seu e-mail: {verification_link}')

    return jsonify({"message": "Usuário registrado com sucesso! Verifique seu e-mail para confirmar sua conta."}), 201

# Rota para verificar o e-mail do usuário
@app.route('/verify/<token>', methods=['GET'])
def verify_email(token):
    connection = connect_to_db()
    cursor = connection.cursor()

    # Verificar o token de verificação
    cursor.execute("SELECT id FROM usuarios WHERE token_verificacao = %s", (token,))
    user = cursor.fetchone()
    
    if not user:
        return render_template('verification_result.html', message="Token de verificação inválido!", success=False)

    # Atualizar o status do e-mail para verificado
    cursor.execute("UPDATE usuarios SET email_verificado = TRUE WHERE token_verificacao = %s", (token,))
    connection.commit()
    connection.close()

    return render_template('verification_result.html', message="E-mail verificado com sucesso! Agora você pode fazer login.", success=True)

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

    # Verificar se o usuário existe e se o e-mail foi verificado
    cursor.execute("SELECT id, senha, email_verificado FROM usuarios WHERE email = %s", (email,))
    user = cursor.fetchone()
    connection.close()

    if not user:
        return jsonify({"message": "Usuário não encontrado."}), 401

    if not check_password_hash(user[1], senha):
        return jsonify({"message": "Credenciais inválidas."}), 401

    if not user[2]:
        return jsonify({"message": "Por favor, verifique seu e-mail antes de fazer login."}), 400

    # Gerar token JWT
    token = create_access_token(identity=str(user[0]))  # Passa o ID como string

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

    return jsonify({"message": "Usuário excluído com sucesso!"}), 200# Outras rotas...
if __name__ == "__main__":
    create_table()
    app.run(debug=True)
