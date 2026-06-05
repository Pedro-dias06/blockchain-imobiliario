import os
from flask import Flask, render_template, request, jsonify
from modelos import Imovel, Transacao
from blockchain import BlockchainForum
from bloco import Bloco
import rsa

app = Flask(__name__)
meu_forum = BlockchainForum()


# ------------------------------------------------------------------
# Interface Web
# ------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


# ------------------------------------------------------------------
# Carteira
# ------------------------------------------------------------------

@app.route('/gerar_carteira', methods=['GET'])
def gerar_carteira():
    pub, priv = rsa.newkeys(512)
    return jsonify({
        "chave_publica": pub.save_pkcs1().decode('utf-8'),
        "chave_privada": priv.save_pkcs1().decode('utf-8')
    }), 200


# ------------------------------------------------------------------
# Transações
# ------------------------------------------------------------------

@app.route('/registrar', methods=['POST'])
def registrar_imovel():
    dados = request.get_json()

    matricula = dados.get('matricula')
    chave_remetente = dados.get('chave_remetente')
    chave_destinatario = dados.get('chave_destinatario')
    chave_privada = dados.get('chave_privada')

    if not all([matricula, chave_remetente, chave_destinatario, chave_privada]):
        return jsonify({"erro": "Todos os campos e chaves são obrigatórios!"}), 400

    try:
        novo_imovel = Imovel(matricula, chave_remetente, "Endereço Registrado no BD")
        nova_transacao = Transacao(novo_imovel, chave_remetente, chave_destinatario)

        priv_key_obj = rsa.PrivateKey.load_pkcs1(chave_privada.encode('utf-8'))
        nova_transacao.assinar_transacao(priv_key_obj)

        bloco_gerado = meu_forum.adicionar_bloco(nova_transacao)

        # Propaga o novo bloco para todos os nós P2P conhecidos
        meu_forum.propagar_novo_bloco(bloco_gerado)

        return jsonify({
            "mensagem": "Transação assinada e bloco minerado com sucesso!",
            "bloco_indice": bloco_gerado.indice,
            "hash": bloco_gerado.hash
        }), 201

    except ValueError as e:
        return jsonify({"erro": str(e)}), 403
    except Exception:
        return jsonify({"erro": "Erro na formatação da chave criptográfica."}), 400


# ------------------------------------------------------------------
# Explorador de Blocos
# ------------------------------------------------------------------

@app.route('/cadeia', methods=['GET'])
def ver_cadeia():
    lista_blocos = []
    for bloco in meu_forum.cadeia:
        lista_blocos.append({
            "indice": bloco.indice,
            "timestamp": bloco.timestamp,
            "dados": bloco.dados,
            "hash": bloco.hash,
            "hash_anterior": bloco.hash_anterior,
            "nonce": bloco.nonce
        })
    return jsonify(lista_blocos), 200


@app.route('/validar', methods=['GET'])
def validar_cadeia():
    valida = meu_forum.validar_corrente()
    return jsonify({
        "valida": valida,
        "mensagem": "✅ Blockchain íntegra." if valida else "🚨 Blockchain corrompida!"
    }), 200


# ------------------------------------------------------------------
# Camada P2P
# ------------------------------------------------------------------

@app.route('/nos', methods=['GET'])
def listar_nos():
    return jsonify({"nos": list(meu_forum.nos)}), 200


@app.route('/conectar_nos', methods=['POST'])
def conectar_nos():
    dados = request.get_json()
    novos_nos = dados.get('nos', [])

    if not novos_nos:
        return jsonify({"erro": "Informe ao menos um endereço de nó."}), 400

    for no in novos_nos:
        meu_forum.conectar_no(no)

    return jsonify({
        "mensagem": f"{len(novos_nos)} nó(s) conectado(s) com sucesso.",
        "nos_ativos": list(meu_forum.nos)
    }), 200


@app.route('/receber_bloco_p2p', methods=['POST'])
def receber_bloco_p2p():
    dados = request.get_json()

    campos_obrigatorios = ['indice', 'timestamp', 'dados', 'hash_anterior', 'nonce', 'hash']
    if not all(c in dados for c in campos_obrigatorios):
        return jsonify({"erro": "Dados do bloco incompletos."}), 400

    ultimo = meu_forum.get_ultimo_bloco()

    # Verificação 1: índice deve ser o próximo da sequência
    if dados['indice'] != ultimo.indice + 1:
        return jsonify({
            "erro": f"Índice inválido. Esperado {ultimo.indice + 1}, recebido {dados['indice']}."
        }), 409

    # Verificação 2: hash_anterior deve bater com o hash do último bloco local
    if dados['hash_anterior'] != ultimo.hash:
        return jsonify({"erro": "hash_anterior não corresponde ao último bloco local."}), 409

    # Verificação 3: integridade do hash do bloco recebido
    bloco_recebido = Bloco(
        indice=dados['indice'],
        transacao=dados['dados'],
        hash_anterior=dados['hash_anterior'],
        timestamp=dados['timestamp'],
        nonce=dados['nonce'],
        hash_existente=dados['hash']
    )

    if bloco_recebido.hash != bloco_recebido.gerar_hash():
        return jsonify({"erro": "Hash do bloco inválido. Bloco rejeitado."}), 400

    meu_forum.cadeia.append(bloco_recebido)
    meu_forum._salvar_bloco_no_banco(bloco_recebido)

    return jsonify({
        "mensagem": f"Bloco #{bloco_recebido.indice} recebido e adicionado à cadeia."
    }), 201


if __name__ == '__main__':
    porta = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=porta)
