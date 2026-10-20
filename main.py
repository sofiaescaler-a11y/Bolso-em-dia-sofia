from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from datetime import datetime
import fdb

# importamos a biblioteca os, que permite trabalhar com arquivos  e pastas do computador.
# Vamos utilizá-la para descobrir a extensão da imagem escolhida e definir em qual pasta ela será salva.
import os

# importa 'uuid4' para gerar nomes únicos para as imagens
# assim, dois arquivos com o mesmo nome não vão se sobrescrever
from uuid import uuid4

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='Static', template_folder='Templates', static_url_path='/static')

app.config['SECRET_KEY'] = 'chave_secreta_bolso_em_dia'

host = "localhost"
database = r"C:\Users\User\Downloads\bolso-em-dia-main (3)\bolso-em-dia-main\BANCO.FDB"
user = "sysdba"
password = "sysdba"


con = fdb.connect(host=host, database=database, user=user, password=password)

def validar_senha(senha):
    min_caractere = False
    min_upper = False
    min_lower = False
    min_num = False
    min_caractere_esp = False

    if len(senha) >= 8:
        min_caractere = True

    for caractere in senha:

        if caractere.isalpha() and caractere == caractere.upper():
            min_upper = True

        if caractere.isalpha() and caractere == caractere.lower():
            min_lower = True

        if caractere.isdigit():
            min_num = True

        if not caractere.isalpha() and not caractere.isdigit():
            min_caractere_esp = True

    if min_caractere == True and min_upper == True and min_lower == True and min_num == True and min_caractere_esp == True:
        validacao = True
        return validacao

    else:
        validacao = False
        return validacao

def buscar_dados(id_usuario):
    cursor = con.cursor()

    try:
        cursor.execute("""SELECT NOME_COMPLETO, EMAIL, DATA_NASCIMENTO, TELEFONE, CPF, SENHA, VALOR_DIARIA, ADICIONAL, MIN_PACOTES, FOTO_PERFIL FROM USUARIO WHERE ID_USUARIO = ?""", (id_usuario,))
        usuario = cursor.fetchone()
        return usuario

    finally:
        cursor.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pagina_cadastro')
def pagina_cadastro():
    return render_template('cadastro.html')

@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():

    nome = request.form['nome'].strip()

    if not nome:
        flash('O campo "Nome" não pode ficar vazio!', 'error')
        return redirect(url_for('pagina_cadastro'))

    email = request.form['email'].strip()

    if not email:
        flash('O campo "E-mail" não pode ficar vazio!', 'error')
        return redirect(url_for('pagina_cadastro'))

    data_nasc = request.form['data_nasc']
    telefone = request.form['telefone'].strip().replace("(","").replace(")","").replace("-","")

    if not telefone:
        flash('O campo "Telefone" não pode ficar vazio!', 'error')
        return redirect(url_for('pagina_cadastro'))

    cpf = request.form['cpf'].strip().replace(".","").replace("-","")

    if not cpf:
        flash('O campo "CPF" não pode ficar vazio!', 'error')
        return redirect(url_for('pagina_cadastro'))

    senha = request.form['senha']
    confirmar = request.form['confirmar']

    cursor = con.cursor()

    try:
        cursor.execute("""SELECT 1 FROM USUARIO 
                          WHERE upper(EMAIL) = ? OR TELEFONE = ? OR CPF = ?""", (email.upper(), telefone, cpf,))

        if cursor.fetchone():
            flash('E-mail, telefone ou CPF já está sendo usado por outro usuário', 'error')
            return redirect(url_for('pagina_cadastro'))

        if confirmar != senha:
            flash('Confirmação de senha não corresponde à senha', 'error')
            return redirect(url_for('pagina_cadastro'))

        if validar_senha(senha) == True:
            senha_cripto = generate_password_hash(senha)

            session['cadastro'] = {
                'nome': nome,
                'email': email,
                'data_nasc': data_nasc,
                'telefone': telefone,
                'cpf': cpf,
                'senha': senha_cripto
            }

            return render_template('cadastro_info.html')

        else:
            flash('Senha não atende aos requisitos!', 'error')
            return redirect(url_for('pagina_cadastro'))

    except Exception as e:
        flash(f'Ocorreu um erro: {e}', 'error')
        return redirect(url_for('pagina_cadastro'))

    finally:
        cursor.close()

@app.route('/cadastrar_informacoes', methods=['POST'])
def cadastrar_informacoes():

    valor_diaria = float(request.form['valor_diaria'])
    adicional = float(request.form['adicional'])
    min_pacotes = int(request.form['min_pacotes'])

    if valor_diaria < 0 or adicional < 0 or min_pacotes < 0:
        flash('Os valores não podem ser negativos!', 'error')
        return redirect(url_for('pagina_cadastro'))

    dados = session['cadastro']
    cursor = con.cursor()
    try:
        cursor.execute("""INSERT INTO USUARIO (
                        NOME_COMPLETO, EMAIL, DATA_NASCIMENTO,
                        TELEFONE, CPF, SENHA, STATUS, TENTATIVAS,
                        VALOR_DIARIA, ADICIONAL, MIN_PACOTES
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 1, 0, ?, ?, ?)""", (dados['nome'],
                                                                    dados['email'],
                                                                    dados['data_nasc'],
                                                                    dados['telefone'],
                                                                    dados['cpf'],
                                                                    dados['senha'],
                                                                    valor_diaria,
                                                                    adicional,
                                                                    min_pacotes))
        cursor.execute("""SELECT ID_USUARIO FROM USUARIO WHERE CPF = ?""", (dados['cpf'],))

        id_usuario = cursor.fetchone()[0]

        cursor.execute("""INSERT INTO HISTORICO_SENHA (ID_USUARIO, SENHA) VALUES(?,?)""", (id_usuario, dados['senha'],))

        con.commit()

        session.pop('cadastro', None)

        return render_template('final_cadastro.html')

    except Exception as e:
        con.rollback()
        flash(f'Ocorreu um erro: {e}', 'error')
        return redirect(url_for('pagina_cadastro'))

    finally:
        cursor.close()

@app.route('/pagina_login')
def pagina_login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():

    login = request.form['login']
    senha = request.form['senha']

    cursor = con.cursor()

    try:

        if len(login) > 15:
            cursor.execute("""SELECT ID_USUARIO, SENHA, COALESCE(STATUS, 1), COALESCE(TENTATIVAS, 0) FROM USUARIO WHERE upper(EMAIL) = ?""", (login.upper(),))
        else:
            cursor.execute("""SELECT ID_USUARIO, SENHA, COALESCE(STATUS, 1), COALESCE(TENTATIVAS, 0) FROM USUARIO WHERE upper(EMAIL) = ? OR CPF = ? OR TELEFONE = ?""", (login.upper(), login, login,))

        usuario = cursor.fetchone()

        if usuario:

            if usuario[2] == 1:

                id_usuario = usuario[0]
                senha_banco = usuario[1]

                if check_password_hash(senha_banco, senha):

                    cursor.execute("""UPDATE USUARIO SET TENTATIVAS = 0 WHERE ID_USUARIO = ?""", (id_usuario, ))

                    con.commit()

                    session['id_usuario'] = id_usuario

                    return redirect(url_for('dashboard'))


                else:
                    cursor.execute("""UPDATE USUARIO SET TENTATIVAS = COALESCE(TENTATIVAS, 0) + 1 WHERE ID_USUARIO = ?""", (id_usuario,))

                    cursor.execute("""SELECT TENTATIVAS FROM USUARIO WHERE ID_USUARIO = ?""", (id_usuario,))
                    erros = cursor.fetchone()[0]

                    con.commit()

                    if erros == 3:
                        cursor.execute("""UPDATE USUARIO SET STATUS = 0 WHERE ID_USUARIO = ?""", (id_usuario,))
                        con.commit()

                        flash('USUÁRIO BLOQUEADO: 3 tentativas falhas', 'error')
                        return redirect(url_for('pagina_login'))

                    flash('Senha incorreta!', 'error')
                    return redirect(url_for('pagina_login'))

            else:
                flash('Usuário inativo!', 'error')
                return redirect(url_for('pagina_login'))

        else:
            flash('E-mail, telefone ou CPF não cadastrado!', 'error')
            return redirect(url_for('pagina_login'))

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro: {e}", "error")
        return redirect(url_for('pagina_login'))

    finally:
        cursor.close()

@app.route('/logout')
def logout():
    if 'id_usuario' not in session:
        return redirect(url_for('pagina_login'))

    session.pop('id_usuario', None)
    flash('Sessão encerrada. Faça login novamente.')
    return redirect(url_for('pagina_login'))

@app.route('/dashboard')
def dashboard():

    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']

    cursor = con.cursor()

    try:
        usuario = buscar_dados(id_usuario)

        valor_diaria = float(usuario[6] or 0)
        adicional = float(usuario[7] or 0)
        min_pacotes = int(usuario[8] or 0)

        ano_atual = datetime.now().year
        ano_anterior = ano_atual - 1

        ganho_ano = 0
        despesas_ano = 0

        ganho_anterior = 0
        despesas_anterior = 0

        dias_trabalhados_ano = 0
        dias_trabalhados_anterior = 0

        pacotes_ano = 0
        pacotes_anterior = 0

        ganhos_mensais = [0] * 12
        despesas_mensais = [0] * 12

        cursor.execute("""SELECT DATA_TRABALHO, PACOTES_COLETADOS FROM DIA_TRABALHADO WHERE ID_USUARIO = ? AND STATUS = 1""", (id_usuario,))
        dias_trabalhados = cursor.fetchall()

        for dia in dias_trabalhados:
            data_trabalho = dia[0]
            pacotes = dia[1] or 0

            if data_trabalho.year == ano_atual:
                dias_trabalhados_ano += 1
                pacotes_ano += pacotes

            elif data_trabalho.year == ano_anterior:
                dias_trabalhados_anterior += 1
                pacotes_anterior += pacotes

        cursor.execute("""SELECT DATA_MOVIMENTACAO, VALOR, TIPO FROM MOVIMENTACAO WHERE ID_USUARIO = ? AND STATUS = 1""", (id_usuario,))
        movimentacoes = cursor.fetchall()

        for movimentacao in movimentacoes:
            data_movimentacao = movimentacao[0]
            valor = float(movimentacao[1] or 0)
            tipo = movimentacao[2]

            if data_movimentacao.year == ano_atual:

                if tipo == 1:
                    despesas_ano += valor

                    mes = data_movimentacao.month - 1
                    despesas_mensais[mes] += valor

                elif tipo == 2:
                    ganho_ano += valor

                    mes = data_movimentacao.month - 1
                    ganhos_mensais[mes] += valor

            elif data_movimentacao.year == ano_anterior:

                if tipo == 1:
                    despesas_anterior += valor

                elif tipo == 2:
                    ganho_anterior += valor


        saldo_atual = ganho_ano - despesas_ano
        saldo_anterior = ganho_anterior - despesas_anterior


        if dias_trabalhados_ano > 0:
            media_ganho_dia = ganho_ano / dias_trabalhados_ano
        else:
            media_ganho_dia = 0

        if dias_trabalhados_anterior > 0:
            media_ganho_dia_anterior = ganho_anterior / dias_trabalhados_anterior
        else:
            media_ganho_dia_anterior = 0


        if ganho_anterior > 0:
            ganho_percentual = round(abs((ganho_ano - ganho_anterior) / ganho_anterior * 100))
        else:
            ganho_percentual = 0

        if despesas_anterior > 0:
            despesas_percentual = round(abs((despesas_ano - despesas_anterior) / despesas_anterior * 100))
        else:
            despesas_percentual = 0

        if saldo_anterior != 0:
            saldo_percentual = round(abs((saldo_atual - saldo_anterior) / saldo_anterior * 100))
        else:
            saldo_percentual = 0

        if dias_trabalhados_anterior > 0:
            dias_percentual = round(abs((dias_trabalhados_ano - dias_trabalhados_anterior) / dias_trabalhados_anterior * 100))
        else:
            dias_percentual = 0

        if pacotes_anterior > 0:
            pacotes_percentual = round(abs((pacotes_ano - pacotes_anterior) / pacotes_anterior * 100))
        else:
            pacotes_percentual = 0

        if media_ganho_dia_anterior > 0:
            media_percentual = round(abs((media_ganho_dia - media_ganho_dia_anterior) / media_ganho_dia_anterior * 100))
        else:
            media_percentual = 0


        ganho_subiu = ganho_ano > ganho_anterior
        despesas_subiram = despesas_ano > despesas_anterior
        saldo_subiu = saldo_atual > saldo_anterior

        dias_subiram = dias_trabalhados_ano > dias_trabalhados_anterior
        pacotes_subiram = pacotes_ano > pacotes_anterior
        media_subiu = media_ganho_dia > media_ganho_dia_anterior

        saldo_negativo = saldo_atual < 0


        mes_atual = datetime.now().month
        saldo_mes_atual = ganhos_mensais[mes_atual - 1] - despesas_mensais[mes_atual - 1]

        if mes_atual > 1:
            saldo_mes_anterior = ganhos_mensais[mes_atual - 2] - despesas_mensais[mes_atual - 2]
        else:
            saldo_mes_anterior = 0

        if saldo_mes_anterior != 0:
            projecao_percentual = round(abs((saldo_mes_atual - saldo_mes_anterior) / saldo_mes_anterior * 100))
        else:
            projecao_percentual = 0

        projecao_subiu = saldo_mes_atual > saldo_mes_anterior

        saldo_projetado_mensal = saldo_atual / mes_atual
        saldo_projetado_anual = saldo_projetado_mensal * 12


        return render_template(
            'dashboard.html',

            usuario=usuario,
            ano_atual=ano_atual,

            ganho_ano=ganho_ano,
            despesas_ano=despesas_ano,
            saldo_atual=saldo_atual,

            ganho_percentual=ganho_percentual,
            despesas_percentual=despesas_percentual,
            saldo_percentual=saldo_percentual,

            ganho_subiu=ganho_subiu,
            despesas_subiram=despesas_subiram,
            saldo_subiu=saldo_subiu,
            saldo_negativo=saldo_negativo,

            ganhos_mensais=ganhos_mensais,

            dias_trabalhados_ano=dias_trabalhados_ano,
            pacotes_ano=pacotes_ano,
            media_ganho_dia=media_ganho_dia,

            dias_percentual=dias_percentual,
            pacotes_percentual=pacotes_percentual,
            media_percentual=media_percentual,

            dias_subiram=dias_subiram,
            pacotes_subiram=pacotes_subiram,
            media_subiu=media_subiu,

            saldo_projetado_mensal=saldo_projetado_mensal,
            saldo_projetado_anual=saldo_projetado_anual,

            projecao_percentual=projecao_percentual,
            projecao_subiu=projecao_subiu
        )

    except Exception as e:
        flash(f'Ocorreu um erro: {e}', 'error')
        return redirect(url_for('pagina_login'))

    finally:
        cursor.close()

@app.route('/relatorio')
def relatorio():
    return render_template('relatorios.html')

@app.route('/perfil', methods=['GET'])
def perfil():
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']

    cursor = con.cursor()

    try:
        usuario = buscar_dados(id_usuario)

        return render_template('perfil.html', usuario=usuario)

    except Exception as e:
        con.rollback()
        flash(f'Ocorreu um erro: {e}', 'error')
        return redirect(url_for('dashboard'))

    finally:
        cursor.close()

@app.route('/editar_usuario', methods=['GET','POST'])
def editar_usuario():

    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']

    cursor = con.cursor()

    try:
        usuario = buscar_dados(id_usuario)

        if request.method == 'POST':
            nome = request.form['nome'].strip()

            if not nome:
                flash('O nome não pode ficar vazio!', 'error')
                return redirect(url_for('pagina_cadastro'))

            email = request.form['email']
            data_nasc = request.form['data_nasc']
            telefone = request.form['telefone']
            cpf = request.form['cpf']
            senha_nova = request.form['senha']
            valor_diaria = float(request.form['valor_diaria'])
            adicional = float(request.form['adicional'])
            min_pacotes = int(request.form['min_pacotes'])

            if valor_diaria < 0 or adicional < 0 or min_pacotes < 0:
                flash('Os valores não podem ser negativos!', 'error')
                return redirect(url_for('pagina_cadastro'))

            cursor.execute("""SELECT 1 FROM USUARIO WHERE (upper(EMAIL) = ? OR TELEFONE = ? OR CPF = ?) AND ID_USUARIO <> ? """, (email.upper(), telefone, cpf, id_usuario))

            if cursor.fetchone():
                flash('E-mail, telefone ou CPF já está sendo usado por outro usuário', 'error')
                return redirect(url_for('editar_usuario'))

            cursor.execute("""SELECT FIRST 3 SENHA FROM HISTORICO_SENHA WHERE ID_USUARIO = ? ORDER BY DATA_ALTERACAO DESC""", (id_usuario,))
            senhas_antigas = cursor.fetchall()

            if senha_nova:

                for senha_antiga in senhas_antigas:
                    if check_password_hash(senha_antiga[0], senha_nova):

                        flash('A nova senha não pode ser igual às últimas 3 senhas!', 'error')
                        return redirect(url_for('editar_usuario'))

                if validar_senha(senha_nova):
                    senha_cripto = generate_password_hash(senha_nova)

                else:
                    flash('Senha não atende aos requisitos!', 'error')
                    return redirect(url_for('editar_usuario'))

            else:
                senha_cripto = usuario[5]


            # utilizamos request.files para pegar o arquivo enviado pelo formulário HTML.
            # o nome 'foto' precisa ser igual ao atributo name do input no HTML.
            # usamos .get() para buscar esse arquivo sem gerar um erro caso o usuário não tenha enviado nenhuma imagem.
            foto = request.files.get('foto')

            # verificamos se existe um arquivo e se ele possui um nome.
            # isso é necessário porque o usuário pode editar o perfil sem querer alterar a foto, mudando apenas o nome ou o e-mail.
            if foto and foto.filename:

                # utilizamos os.path.splitext() para separar o nome do arquivo da sua extensão.
                # O [1] pega somente a extensão.
                # por exemplo, se a imagem for chamada minha_foto.jpg, a variável extensao receberá somente '.jpg'.
                # o .lower() transforma as letras em minúsculas,evitando problemas com extensões como '.JPG' ou '.PNG'.
                extensao = os.path.splitext(foto.filename)[1].lower()

                # verificamos se a extensão da imagem é permitida.
                # caso não seja JPG, JPEG, PNG ou WEBP, mostramos uma mensagem e devolvemos o usuário para a página de edição.
                # essa é uma verificação básica pela extensão do nome do arquivo.
                if extensao not in ('.jpg', '.jpeg', '.png', '.webp'):
                    flash('Escolha uma imagem JPG, PNG ou WEBP.', 'error')
                    return redirect(url_for('editar_usuario'))

                # criamos um nome único para a imagem utilizando o ID do usuário.
                # utilizamos uuid4() para gerar um identificador aleatório, evitando que imagens diferentes sejam salvas com o mesmo nome.
                # o .hex transforma esse identificador em uma sequência de letras e números.
                # por fim, acrescentamos a extensão para manter o formato original da imagem.
                nome_foto = f'perfil_{id_usuario}_{uuid4().hex}{extensao}'

                # utilizamos foto.save() para salvar a imagem no computador.
                # app.static_folder indica a pasta Static do projeto.
                # os.path.join() junta o caminho da pasta com o nome da imagem.
                # assim, o arquivo será salvo dentro de Static/Uploads.
                foto.save(os.path.join(app.static_folder, 'Uploads', nome_foto))

                # depois de salvar a imagem na pasta, precisamos registrar o nome dela no banco de dados.
                # utilizamos UPDATE porque estamos alterando os dados de um usuário que já existe.
                # FOTO_PERFIL é a coluna que recebe o nome da imagem.
                # ID_USUARIO identifica qual usuário terá sua foto atualizada.
                cursor.execute(
                    "UPDATE USUARIO SET FOTO_PERFIL = ? WHERE ID_USUARIO = ?",
                    (nome_foto, id_usuario)
                )

            # agora, atualizamos todos os dados do usuário no banco de dados
            cursor.execute("""UPDATE USUARIO SET NOME_COMPLETO = ?, EMAIL = ?, DATA_NASCIMENTO = ?, TELEFONE = ?, CPF = ?, SENHA = ?, VALOR_DIARIA = ?, ADICIONAL = ?, MIN_PACOTES = ? WHERE ID_USUARIO = ?""",(nome, email, data_nasc, telefone, cpf, senha_cripto, valor_diaria, adicional, min_pacotes, id_usuario,))

            if senha_nova:
                cursor.execute("""INSERT INTO HISTORICO_SENHA (ID_USUARIO, SENHA) VALUES (?, ?)""",(id_usuario, senha_cripto,))

            con.commit()

            flash('Usuário editado com sucesso!', 'success')
            return redirect(url_for('perfil'))

        else:
            return render_template("editar.html", usuario=usuario)

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro: {e}", "error")
        return redirect(url_for('dashboard'))

    finally:
        cursor.close()



@app.route('/todas_categorias', methods=['GET'])
def todas_categorias():
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']

    cursor = con.cursor()

    try:
        usuario = buscar_dados(id_usuario)

        cursor.execute(""" SELECT ID_CATEGORIA, NOME_CATEGORIA, TIPO, COR, ICONE, STATUS FROM CATEGORIA WHERE ID_CATEGORIA IN(1,2)
        UNION
        SELECT ID_CATEGORIA, NOME_CATEGORIA, TIPO, COR, ICONE, STATUS FROM CATEGORIA WHERE ID_USUARIO = ?""", (id_usuario, ))
        categorias = cursor.fetchall()

        return render_template("categorias.html", categoria=categorias, usuario=usuario)

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro: {e}", "error")
        return redirect(url_for('todas_categorias'))

    finally:
        cursor.close()


@app.route('/nova_categoria')
def nova_categoria():
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']
    usuario = buscar_dados(id_usuario)
    return render_template("nova_categoria.html", usuario=usuario)


@app.route('/cadastrar_categoria', methods=['POST'])
def cadastrar_categoria():
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']

    nome_categoria = request.form['nome_categoria'].strip()
    tipo = int(request.form['tipo'])
    cor = request.form['cor'].replace("#","")
    icone = request.form['icone']

    if not nome_categoria:
        flash('O campo "Nome Categoria" não pode ser vazio!', 'error')
        return redirect(url_for('nova_categoria'))

    cursor = con.cursor()

    try:
        cursor.execute("""SELECT 1 FROM CATEGORIA WHERE upper(NOME_CATEGORIA) = ? AND ID_USUARIO = ?""", (nome_categoria.upper(), id_usuario))
        if cursor.fetchone():
            flash('Essa categoria já existe!', 'error')
            return redirect(url_for('nova_categoria'))

        cursor.execute("""INSERT INTO CATEGORIA (NOME_CATEGORIA, TIPO, COR, ICONE, ID_USUARIO, STATUS) VALUES (?,?,?,?,?,1)""", (nome_categoria, tipo, cor, icone, id_usuario ))

        con.commit()
        flash('Categoria cadastrado com sucesso!', 'success')
        return redirect(url_for('todas_categorias'))

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro: {e}", "error")
        return redirect(url_for('nova_categoria'))

    finally:
        cursor.close()


@app.route('/editar_categoria/<int:id>', methods=['GET','POST'])
def editar_categoria(id):
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']

    cursor = con.cursor()

    try:
        usuario = buscar_dados(id_usuario)

        cursor.execute("""SELECT NOME_CATEGORIA, TIPO, COR, ICONE, STATUS FROM CATEGORIA WHERE ID_USUARIO = ? AND ID_CATEGORIA = ?""", (id_usuario, id))
        categoria = cursor.fetchone()

        if not categoria:
            flash('Categoria não encontrada!', 'error')
            return redirect(url_for('todas_categorias'))

        if categoria[4] == 0:
            flash('Não é possível editar uma categoria inativada!', 'error')
            return redirect(url_for('todas_categorias'))

        if request.method == 'POST':
            nome_categoria = request.form['nome_categoria'].strip()

            if not nome_categoria:
                flash('O campo "Nome Categoria" não pode ser vazio!', 'error')
                return redirect(url_for('editar_categoria', id=id))

            tipo = int(request.form['tipo'])
            cor = request.form['cor']
            icone = request.form['icone']

            cursor.execute("""SELECT 1 FROM CATEGORIA WHERE upper(NOME_CATEGORIA) = ? AND ID_USUARIO = ? AND ID_CATEGORIA <> ?""", (nome_categoria.upper(), id_usuario, id))
            if cursor.fetchone():
                flash('Essa categoria já existe!', 'error')
                return redirect(url_for('editar_categoria', id=id))

            cursor.execute("""UPDATE CATEGORIA SET NOME_CATEGORIA = ?, TIPO = ?, COR = ?, ICONE = ? WHERE ID_CATEGORIA = ? AND ID_USUARIO = ?""", (nome_categoria, tipo, cor, icone, id, id_usuario))
            con.commit()
            flash('Categoria editado com sucesso!', 'success')
            return redirect(url_for('todas_categorias'))

        else:
            return render_template("editar_categoria.html",categoria=categoria, usuario=usuario)

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro: {e}", "error")
        return redirect(url_for('todas_categorias'))

    finally:
        cursor.close()

@app.route('/inativar_categoria/<int:id>', methods=['POST'])
def inativar_categoria(id):
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']
    ativar = int(request.form['ativar'])

    if ativar == 1:
        mensagem = 'ativada'
    else:
        mensagem = 'inativada'

    cursor = con.cursor()

    try:
        cursor.execute("""SELECT 1 FROM CATEGORIA WHERE ID_USUARIO = ? AND ID_CATEGORIA = ?""", (id_usuario, id))
        if not cursor.fetchone():
            flash('Categoria não encontrada!', 'error')
            return redirect(url_for('todas_categorias'))

        cursor.execute("""UPDATE CATEGORIA SET STATUS = ? WHERE ID_USUARIO = ? AND ID_CATEGORIA = ?""", (ativar, id_usuario, id))
        con.commit()
        flash(f'Categoria { mensagem } com sucesso!', 'success')
        return redirect(url_for('todas_categorias'))

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro: {e}", "error")
        return redirect(url_for('todas_categorias'))

    finally:
        cursor.close()


@app.route('/servico_extra')
def servico_extra():
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']
    usuario = buscar_dados(id_usuario)
    return render_template("servico_extra.html", usuario=usuario)


@app.route('/cadastrar_servico_extra', methods=['POST'])
def cadastrar_servico_extra():
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']

    servico_realizado = request.form['servico_realizado'].strip()
    valor = float(request.form['valor'])
    data = request.form['data']
    descricao = request.form['descricao'].strip()

    if not servico_realizado:
        flash('O campo "Serviço Realizado" não pode ser vazio!', 'error')
        return redirect(url_for('servico_extra'))

    if valor <= 0:
        flash('O campo "Valor Recebido" deve ser maior que zero!', 'error')
        return redirect(url_for('servico_extra'))

    if not valor:
        flash('O campo "Valor Recebido" não pode ser vazio!', 'error')
        return redirect(url_for('servico_extra'))

    cursor = con.cursor()

    try:
        cursor.execute("""INSERT INTO SERVICO_EXTRA (SERVICO_REALIZADO, VALOR, DATA_SERVICO, DESCRICAO, ID_USUARIO, STATUS) VALUES (?, ?, ?, ?, ?, 1)""", (servico_realizado, valor, data, descricao, id_usuario))
        con.commit()
        flash('Serviço cadastrado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro: {e}", "error")
        return redirect(url_for('servico_extra'))

    finally:
        cursor.close()


@app.route('/excluir_servico_extra/<int:id>', methods=['POST'])
def excluir_servico_extra(id):
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))
    id_usuario = session['id_usuario']
    cursor = con.cursor()
    try:
        cursor.execute("""SELECT DATA_SERVICO FROM SERVICO_EXTRA WHERE ID_USUARIO = ? AND ID_SERVICO_EXTRA = ?""", (id_usuario, id, ))
        data_banco = cursor.fetchone()
        data_atual = datetime.now().date()

        if not data_banco:
            flash('Registro não encontrado!', 'error')
            return redirect(url_for('rendimentos'))

        if data_banco[0] < data_atual:
            flash('Não é possível excluir registros retroativos!', 'error')
            return redirect(url_for('rendimentos'))

        cursor.execute("""DELETE FROM SERVICO_EXTRA WHERE ID_USUARIO = ? AND ID_SERVICO_EXTRA = ?""", (id_usuario, id, ))
        con.commit()
        flash('Registro excluido com sucesso!', 'success')
        return redirect(url_for('rendimentos'))

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro: {e}", "error")
        return redirect(url_for('rendimentos'))

    finally:
        cursor.close()


@app.route('/editar_servico_extra/<int:id>', methods=['GET','POST'])
def editar_servico_extra(id):
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']

    cursor = con.cursor()

    try:
        usuario = buscar_dados(id_usuario)

        cursor.execute("""SELECT SERVICO_REALIZADO, VALOR, DATA_SERVICO, DESCRICAO, ID_USUARIO, STATUS FROM SERVICO_EXTRA WHERE ID_USUARIO = ? AND ID_SERVICO_EXTRA = ?""", (id_usuario, id, ))
        servico = cursor.fetchone()

        if not servico:
            flash('Serviço extra não encontrado!', 'error')
            return redirect(url_for('rendimentos'))

        if servico[5] == 0:
            flash('Um registro inativado não pode ser editado.', 'error')
            return redirect(url_for('rendimentos'))

        data_atual = datetime.now().date()

        if servico[2] < data_atual:
            flash('Não é possível editar registros retroativos!', 'error')
            return redirect(url_for('rendimentos'))

        if request.method == 'POST':
            servico_realizado = request.form['servico_realizado'].strip()
            valor = float(request.form['valor'])
            data_servico = request.form['data_servico']
            descricao = request.form['descricao'].strip()

            # transforma em AAAA-MM-DD para conferir se não ta sendo alterada para uma data passada
            if data_servico < data_atual.strftime('%Y-%m-%d'):
                flash('Não é possível alterar para uma data retroativa!', 'error')
                return redirect(url_for('editar_servico_extra', id=id))

            if not servico_realizado:
                flash('O campo "Serviço Realizado" não pode ser vazio!', 'error')
                return redirect(url_for('editar_servico_extra', id=id))

            if valor <= 0:
                flash('O campo "Valor Recebido" deve ser maior que zero!', 'error')
                return redirect(url_for('editar_servico_extra', id=id))

            cursor.execute("""UPDATE SERVICO_EXTRA SET SERVICO_REALIZADO = ?, VALOR = ?, DATA_SERVICO = ?, DESCRICAO = ? WHERE ID_USUARIO = ? AND ID_SERVICO_EXTRA = ?""", (servico_realizado, valor, data_servico, descricao, id_usuario, id))
            con.commit()
            flash('Registro editado com sucesso!', 'success')
            return redirect(url_for('rendimentos'))

        else:
            return render_template('editar_servico_extra.html', servico=servico, usuario=usuario)

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro: {e}", "error")
        return redirect(url_for('editar_servico_extra', id=id))

    finally:
        cursor.close()

@app.route('/inativar_servico_extra/<int:id>', methods=['POST'])
def inativar_servico_extra(id):
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']
    ativar = int(request.form['ativar'])

    if ativar == 1:
        mensagem = 'ativado'
    else:
        mensagem = 'inativado'

    cursor = con.cursor()

    try:
        cursor.execute("""SELECT 1 FROM SERVICO_EXTRA WHERE ID_USUARIO = ? AND ID_SERVICO_EXTRA = ?""", (id_usuario, id))
        if not cursor.fetchone():
            flash('Registro não encontrado!', 'error')
            return redirect(url_for('rendimentos'))

        cursor.execute("""UPDATE SERVICO_EXTRA SET STATUS = ? WHERE ID_USUARIO = ? AND ID_SERVICO_EXTRA = ?""", (ativar, id_usuario, id))
        con.commit()
        flash(f'Serviço extra { mensagem } com sucesso!', 'success')
        return redirect(url_for('rendimentos'))

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro: {e}", "error")
        return redirect(url_for('rendimentos'))

    finally:
        cursor.close()


@app.route('/dia_trabalhado')
def dia_trabalhado():
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']
    usuario = buscar_dados(id_usuario)
    return render_template("dia_trabalhado.html", usuario=usuario)


def calcular_valor_total(pacotes, valor_diaria, adicional, min_pacotes):
    valor_total = valor_diaria

    if pacotes > min_pacotes:
        pacotes_excedentes = pacotes - min_pacotes
        valor_adicional = pacotes_excedentes * adicional
        valor_total = valor_total + valor_adicional

    return valor_total


@app.route('/cadastrar_dia_trabalhado', methods=['POST'])
def cadastrar_dia_trabalhado():
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']

    data = request.form['data']
    pacotes_coletados = int(request.form['pacotes_coletados'])

    if pacotes_coletados <= 0:
        flash('A quantidade de pacotes deve ser maior que zero!', 'error')
        return redirect(url_for('dia_trabalhado'))

    data_atual = datetime.now().date()

    if data < data_atual.strftime('%Y-%m-%d'):
        flash('Não é possível cadastrar um dia trabalhado com data retroativa!', 'error')
        return redirect(url_for('dia_trabalhado'))

    cursor = con.cursor()

    try:
        cursor.execute("""SELECT VALOR_DIARIA, ADICIONAL, MIN_PACOTES FROM USUARIO WHERE ID_USUARIO = ?""", (id_usuario,))

        dados_usuario = cursor.fetchone()

        if not dados_usuario:
            flash('Usuário não encontrado!', 'error')
            return redirect(url_for('dia_trabalhado'))

        valor_diaria = dados_usuario[0]
        adicional = dados_usuario[1]
        min_pacotes = dados_usuario[2]

        valor_total = calcular_valor_total(
            pacotes_coletados,
            valor_diaria,
            adicional,
            min_pacotes
        )

        cursor.execute("""INSERT INTO DIA_TRABALHADO (DATA_TRABALHO, PACOTES_COLETADOS, VALOR_TOTAL, ID_USUARIO, STATUS) VALUES (?, ?, ?, ?, 1)""", (data, pacotes_coletados, valor_total, id_usuario))
        con.commit()
        flash('Dia trabalhado registrado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro: {e}", "error")
        return redirect(url_for('dia_trabalhado'))

    finally:
        cursor.close()


@app.route('/inativar_dia_trabalhado/<int:id>', methods=['POST'])
def inativar_dia_trabalhado(id):
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']
    ativar = int(request.form['ativar'])

    if ativar == 1:
        mensagem = 'ativado'
    else:
        mensagem = 'inativado'

    cursor = con.cursor()

    try:
        cursor.execute("""SELECT 1 FROM DIA_TRABALHADO WHERE ID_USUARIO = ? AND ID_DIA_TRABALHADO = ?""",(id_usuario, id))
        if not cursor.fetchone():
            flash('Registro não encontrado!', 'error')
            return redirect(url_for('rendimentos'))

        cursor.execute("""UPDATE DIA_TRABALHADO SET STATUS = ? WHERE ID_USUARIO = ? AND ID_DIA_TRABALHADO = ?""", (ativar, id_usuario, id))
        con.commit()
        flash(f'Dia trabalhado { mensagem } com sucesso!', 'success')
        return redirect(url_for('rendimentos'))

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro: {e}", "error")
        return redirect(url_for('rendimentos'))

    finally:
        cursor.close()

@app.route('/editar_dia_trabalhado/<int:id>', methods=['GET','POST'])
def editar_dia_trabalhado(id):
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']

    cursor = con.cursor()

    try:
        usuario = buscar_dados(id_usuario)

        cursor.execute("""SELECT DATA_TRABALHO, PACOTES_COLETADOS, ID_USUARIO, STATUS FROM DIA_TRABALHADO WHERE ID_USUARIO = ? AND ID_DIA_TRABALHADO = ?""", (id_usuario, id, ))
        dia_trabalhado = cursor.fetchone()

        if not dia_trabalhado:
            flash('Registro não encontrado!', 'error')
            return redirect(url_for('rendimentos'))

        if dia_trabalhado[3] == 0:
            flash('Um registro inativado não pode ser editado.', 'error')
            return redirect(url_for('rendimentos'))

        data_atual = datetime.now().date()

        if dia_trabalhado[0] < data_atual:
            flash('Não é possível editar registros retroativos!', 'error')
            return redirect(url_for('rendimentos'))

        if request.method == 'POST':
            data = request.form['data']
            pacotes_coletados = int(request.form['pacotes_coletados'])

            if pacotes_coletados <= 0:
                flash('O campo "Pacotes coletados" deve ser maior que zero!', 'error')
                return redirect(url_for('editar_dia_trabalhado', id=id))

            # transforma em AAAA-MM-DD para conferir se não ta sendo alterada para uma data passada
            if data < data_atual.strftime('%Y-%m-%d'):
                flash('Não é possível alterar para uma data retroativa!', 'error')
                return redirect(url_for('editar_dia_trabalhado', id=id))

            cursor.execute("""UPDATE DIA_TRABALHADO SET DATA_TRABALHO = ?, PACOTES_COLETADOS = ? WHERE ID_USUARIO = ? AND ID_DIA_TRABALHADO = ?""", (data, pacotes_coletados, id_usuario, id))
            con.commit()
            flash('Registro editado com sucesso!', 'success')
            return redirect(url_for('rendimentos'))

        else:
            return render_template('editar_dia_trabalhado.html', dia_trabalhado=dia_trabalhado, usuario=usuario, id=id)

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro: {e}", "error")
        return redirect(url_for('rendimentos'))

    finally:
        cursor.close()

@app.route('/excluir_dia_trabalhado/<int:id>', methods=['POST'])
def excluir_dia_trabalhado(id):
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))
    id_usuario = session['id_usuario']
    cursor = con.cursor()
    try:
        cursor.execute("""SELECT DATA_TRABALHO FROM DIA_TRABALHADO WHERE ID_USUARIO = ? AND ID_DIA_TRABALHADO = ?""", (id_usuario, id, ))
        data_banco = cursor.fetchone()

        if not data_banco:
            flash('Registro não encontrado!', 'error')
            return redirect(url_for('rendimentos'))

        data_atual = datetime.now().date()

        if data_banco[0] < data_atual:
            flash('Não é possível excluir registros retroativos!', 'error')
            return redirect(url_for('rendimentos'))

        cursor.execute("""DELETE FROM DIA_TRABALHADO WHERE ID_USUARIO = ? AND ID_DIA_TRABALHADO = ?""", (id_usuario, id, ))
        con.commit()
        flash('Registro excluido com sucesso!', 'success')
        return redirect(url_for('rendimentos'))

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro: {e}", "error")
        return redirect(url_for('rendimentos'))

    finally:
        cursor.close()

@app.route('/movimentacao')
def movimentacao():

    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']
    cursor = con.cursor()

    try:
        usuario = buscar_dados(id_usuario)

        cursor.execute("""SELECT ID_CATEGORIA, NOME_CATEGORIA, TIPO, COR, ICONE, STATUS FROM CATEGORIA WHERE STATUS = 1 AND (ID_CATEGORIA IN (1, 2) OR ID_USUARIO = ?) ORDER BY NOME_CATEGORIA""", (id_usuario,))
        categorias = cursor.fetchall()

        return render_template("movimentacao.html", usuario=usuario, categorias=categorias)

    except Exception as e:
        flash(f'Ocorreu um erro: {e}', 'error')
        return redirect(url_for('dashboard'))

    finally:
        cursor.close()

@app.route('/cadastrar_movimentacao', methods=['POST'])
def cadastrar_movimentacao():

    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']

    valor = float(request.form['valor'])
    tipo = int(request.form['tipo'])
    data = request.form['data']
    categoria = int(request.form['categoria'])
    descricao = request.form['descricao'].strip()

    if valor <= 0:
        flash('O valor deve ser maior que zero!', 'error')
        return redirect(url_for('movimentacao'))

    if not data:
        flash('Informe a data da movimentação!', 'error')
        return redirect(url_for('movimentacao'))

    if not valor:
        flash('O campo "Valor" não pode ser vazio!', 'error')
        return redirect(url_for('movimentacao'))

    if not descricao:
        flash('Informe a descrição da movimentação!', 'error')
        return redirect(url_for('movimentacao'))

    if tipo not in [1, 2]:
        flash('Tipo de movimentação inválido!', 'error')
        return redirect(url_for('movimentacao'))

    cursor = con.cursor()

    try:
        cursor.execute("""SELECT ID_CATEGORIA FROM CATEGORIA WHERE ID_CATEGORIA = ? AND STATUS = 1 AND ID_CATEGORIA IN(1, 2)
                    UNION
                    SELECT ID_CATEGORIA FROM CATEGORIA WHERE ID_CATEGORIA = ? AND ID_USUARIO = ? AND STATUS = 1""",
                    (categoria, categoria, id_usuario))

        if not cursor.fetchone():
            flash('Categoria inválida!', 'error')
            return redirect(url_for('movimentacao'))

        cursor.execute("""INSERT INTO MOVIMENTACAO (VALOR, TIPO, DATA_MOVIMENTACAO, DESCRICAO, ID_CATEGORIA, ID_USUARIO, STATUS) VALUES (?, ?, ?, ?, ?, ?, 1)""", (valor, tipo, data, descricao, categoria, id_usuario))
        con.commit()
        flash('Movimentação cadastrada com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        con.rollback()
        flash(f'Ocorreu um erro: {e}', 'error')
        return redirect(url_for('movimentacao'))

    finally:
        cursor.close()



@app.route('/inativar_movimentacao/<int:id>', methods=['POST'])
def inativar_movimentacao(id):
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']
    cursor = con.cursor()

    try:
        cursor.execute("""SELECT TIPO, DATA_MOVIMENTACAO FROM MOVIMENTACAO WHERE ID_USUARIO = ? AND ID_MOVIMENTACAO = ? AND STATUS = 1""", (id_usuario, id))

        movimentacao = cursor.fetchone()

        if not movimentacao:
            flash('Movimentação não encontrada!', 'error')
            return redirect(url_for('dashboard'))

        tipo = movimentacao[0]
        data_atual = datetime.now().date()

        if movimentacao[1] >= data_atual:
            flash('Só é possível inativar movimentações de datas passadas!', 'error')

            if tipo == 1:
                return redirect(url_for('despesas'))
            else:
                return redirect(url_for('rendimentos'))

        cursor.execute("""UPDATE MOVIMENTACAO SET STATUS = 0 WHERE ID_USUARIO = ? AND ID_MOVIMENTACAO = ?""", (id_usuario, id))
        con.commit()
        flash('Movimentação inativada com sucesso!', 'success')

        if tipo == 1:
            return redirect(url_for('despesas'))
        else:
            return redirect(url_for('rendimentos'))

    except Exception as e:
        con.rollback()
        flash(f'Ocorreu um erro: {e}', 'error')
        return redirect(url_for('dashboard'))

    finally:
        cursor.close()


@app.route('/excluir_movimentacao/<int:id>', methods=['POST'])
def excluir_movimentacao(id):
    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']
    cursor = con.cursor()

    try:
        cursor.execute("""SELECT TIPO, DATA_MOVIMENTACAO FROM MOVIMENTACAO WHERE ID_USUARIO = ? AND ID_MOVIMENTACAO = ? AND STATUS = 1""", (id_usuario, id))
        movimentacao = cursor.fetchone()

        if not movimentacao:
            flash('Movimentação não encontrada!', 'error')
            return redirect(url_for('dashboard'))

        tipo = movimentacao[0]
        data_atual = datetime.now().date()

        if movimentacao[1] < data_atual:
            flash(
                'Não é possível excluir movimentações de datas passadas!','error')
            if tipo == 2:
                return redirect(url_for('rendimentos'))
            else:
                return redirect(url_for('despesas'))

        cursor.execute("""DELETE FROM MOVIMENTACAO WHERE ID_USUARIO = ? AND ID_MOVIMENTACAO = ?""", (id_usuario, id))
        con.commit()
        flash('Movimentação excluída com sucesso!', 'success')

        if tipo == 2:
            return redirect(url_for('rendimentos'))
        else:
            return redirect(url_for('despesas'))

    except Exception as e:
        con.rollback()
        flash(f'Ocorreu um erro: {e}', 'error')
        return redirect(url_for('dashboard'))

    finally:
        cursor.close()

@app.route('/editar_movimentacao/<int:id>', methods=['GET', 'POST'])
def editar_movimentacao(id):

    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']
    cursor = con.cursor()

    try:
        usuario = buscar_dados(id_usuario)

        cursor.execute("""SELECT VALOR, TIPO, DATA_MOVIMENTACAO, DESCRICAO, ID_CATEGORIA, STATUS FROM MOVIMENTACAO WHERE ID_USUARIO = ? AND ID_MOVIMENTACAO = ?""", (id_usuario, id))
        movimentacao = cursor.fetchone()

        if not movimentacao:
            flash('Movimentação não encontrada!', 'error')
            return redirect(url_for('dashboard'))

        if movimentacao[5] == 0:
            flash('Uma movimentação inativada não pode ser editada.', 'error')
            return redirect(url_for('dashboard'))

        data_atual = str(datetime.now().date())

        if str(movimentacao[2]) < data_atual:
            flash('Não é possível editar movimentações de datas passadas!', 'error')
            return redirect(url_for('dashboard'))

        cursor.execute("""SELECT ID_CATEGORIA, NOME_CATEGORIA, TIPO, COR, ICONE, STATUS FROM CATEGORIA WHERE ID_CATEGORIA IN (1, 2) AND STATUS = 1 UNION SELECT ID_CATEGORIA, NOME_CATEGORIA, TIPO, COR, ICONE, STATUS FROM CATEGORIA WHERE ID_USUARIO = ? AND STATUS = 1 ORDER BY NOME_CATEGORIA""", (id_usuario,))
        categorias = cursor.fetchall()

        if request.method == 'POST':
            valor = float(request.form['valor'])
            tipo = int(request.form['tipo'])
            data = request.form['data']
            categoria = int(request.form['categoria'])
            descricao = request.form['descricao'].strip()

            if valor <= 0:
                flash('O valor deve ser maior que zero!', 'error')
                return redirect(url_for('editar_movimentacao', id=id))

            if not data:
                flash('Informe a data da movimentação!', 'error')
                return redirect(url_for('editar_movimentacao', id=id))

            if not descricao:
                flash('Informe a descrição da movimentação!', 'error')
                return redirect(url_for('editar_movimentacao', id=id))

            if tipo not in [1, 2]:
                flash('Tipo de movimentação inválido!', 'error')
                return redirect(url_for('editar_movimentacao', id=id))

            if data < data_atual:
                flash('Não é possível alterar para uma data passada!', 'error')
                return redirect(url_for('editar_movimentacao', id=id))

            cursor.execute("""SELECT ID_CATEGORIA FROM CATEGORIA WHERE ID_CATEGORIA = ? AND TIPO = ? AND STATUS = 1 AND ID_CATEGORIA IN (1, 2) UNION SELECT ID_CATEGORIA FROM CATEGORIA WHERE ID_CATEGORIA = ? AND ID_USUARIO = ? AND TIPO = ? AND STATUS = 1""", (categoria, tipo, categoria, id_usuario, tipo))

            if not cursor.fetchone():
                flash('Categoria inválida para esse tipo de movimentação!', 'error')
                return redirect(url_for('editar_movimentacao', id=id))

            cursor.execute("""UPDATE MOVIMENTACAO SET VALOR = ?, TIPO = ?, DATA_MOVIMENTACAO = ?, DESCRICAO = ?, ID_CATEGORIA = ? WHERE ID_USUARIO = ? AND ID_MOVIMENTACAO = ?""", (valor, tipo, data, descricao, categoria, id_usuario, id))

            con.commit()
            flash('Movimentação editada com sucesso!', 'success')
            return redirect(url_for('dashboard'))

        else:
            return render_template('editar_movimentacao.html', movimentacao=movimentacao, categorias=categorias, usuario=usuario, id=id)

    except Exception as e:
        con.rollback()
        flash(f'Ocorreu um erro: {e}', 'error')
        return redirect(url_for('dashboard'))

    finally:
        cursor.close()



@app.route('/despesas')
def despesas():

    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']
    cursor = con.cursor()

    try:
        usuario = buscar_dados(id_usuario)

        cursor.execute("""SELECT M.ID_MOVIMENTACAO, M.DATA_MOVIMENTACAO, C.NOME_CATEGORIA, M.DESCRICAO, M.VALOR, M.STATUS
            FROM MOVIMENTACAO M
            LEFT JOIN CATEGORIA C ON C.ID_CATEGORIA = M.ID_CATEGORIA
            WHERE M.ID_USUARIO = ? AND M.TIPO = 1 AND M.STATUS = 1
            ORDER BY M.DATA_MOVIMENTACAO DESC""", (id_usuario,))
        despesas = cursor.fetchall()

        cursor.execute("""SELECT cast(COALESCE(SUM(VALOR), 0) as double precision) FROM MOVIMENTACAO WHERE ID_USUARIO = ? AND TIPO = 1 AND STATUS = 1""", (id_usuario,))
        total_despesas = cursor.fetchone()[0]

        cursor.execute("""SELECT cast(COALESCE(SUM(VALOR), 0) as double precision) FROM MOVIMENTACAO 
            WHERE ID_USUARIO = ? AND TIPO = 1 AND STATUS = 1 
            AND EXTRACT(MONTH FROM DATA_MOVIMENTACAO) = ? AND EXTRACT(YEAR FROM DATA_MOVIMENTACAO) = ?""", (id_usuario, datetime.now().month, datetime.now().year))
        despesas_mes = cursor.fetchone()[0]

        cursor.execute("""SELECT COUNT(*) FROM MOVIMENTACAO WHERE ID_USUARIO = ? AND TIPO = 1 AND STATUS = 1""", (id_usuario,))
        quantidade_despesas = cursor.fetchone()[0]

        return render_template(
            'despesas.html',
            usuario=usuario,
            despesas=despesas,
            total_despesas=total_despesas,
            despesas_mes=despesas_mes,
            quantidade_despesas=quantidade_despesas
        )

    except Exception as e:
        con.rollback()
        flash(f'Ocorreu um erro: {e}', 'error')
        return redirect(url_for('dashboard'))

    finally:
        cursor.close()


@app.route('/rendimentos')
def rendimentos():

    if 'id_usuario' not in session:
        flash('É necessário realizar o login', 'error')
        return redirect(url_for('pagina_login'))

    id_usuario = session['id_usuario']
    cursor = con.cursor()

    try:
        usuario = buscar_dados(id_usuario)
        rendimentos = []

        # Receitas
        cursor.execute("""SELECT M.ID_MOVIMENTACAO, M.DATA_MOVIMENTACAO,
            COALESCE(C.NOME_CATEGORIA, 'Receita'), M.DESCRICAO, M.VALOR
            FROM MOVIMENTACAO M
            LEFT JOIN CATEGORIA C ON C.ID_CATEGORIA = M.ID_CATEGORIA
            WHERE M.ID_USUARIO = ? AND M.TIPO = 2 AND M.STATUS = 1 AND (C.NOME_CATEGORIA IS NULL OR C.NOME_CATEGORIA <> 'Dia Trabalhado')""",
            (id_usuario,))

        for r in cursor.fetchall():
            rendimentos.append({
                'id': r[0],
                'data': r[1],
                'categoria': r[2],
                'descricao': r[3],
                'valor': r[4],
                'tipo': 'movimentacao'
            })

        # Dias trabalhados
        cursor.execute("""SELECT ID_DIA_TRABALHADO, DATA_TRABALHO,
            VALOR_TOTAL
            FROM DIA_TRABALHADO
            WHERE ID_USUARIO = ? AND STATUS = 1""",
            (id_usuario,))

        for d in cursor.fetchall():
            rendimentos.append({
                'id': d[0],
                'data': d[1],
                'categoria': 'Dia Trabalhado',
                'descricao': 'Receita cadastrada pelo Dia Trabalhado',
                'valor': d[2],
                'tipo': 'dia_trabalhado'
            })

        # Serviços extras
        cursor.execute("""SELECT ID_SERVICO_EXTRA, DATA_SERVICO,
            DESCRICAO, VALOR
            FROM SERVICO_EXTRA
            WHERE ID_USUARIO = ? AND STATUS = 1""",
            (id_usuario,))

        for s in cursor.fetchall():
            rendimentos.append({
                'id': s[0],
                'data': s[1],
                'categoria': 'Serviço Extra',
                'descricao': s[2],
                'valor': s[3],
                'tipo': 'servico_extra'
            })

        rendimentos.sort(
            key=lambda r: r['data'],
            reverse=True
        )

        return render_template(
            'rendimentos.html',
            usuario=usuario,
            rendimentos=rendimentos
        )

    except Exception as e:
        con.rollback()
        flash(f'Ocorreu um erro: {e}', 'error')
        return redirect(url_for('dashboard'))

    finally:
        cursor.close()



if __name__ == "__main__":
    app.run(debug=True)