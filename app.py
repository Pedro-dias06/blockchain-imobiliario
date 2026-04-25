from flask import Flask, render_template, request, jsonify
from modelos import Imovel, Transacao
from blockchain import BlockchainForum
import rsa

app = Flask(__name__)
meu_forum = BlockchainForum()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gerar_carteira', methods=['GET'])
def gerar_carteira():
    pub, priv = rsa.newkeys(512)
    return jsonify({
        "chave_publica": pub.save_pkcs1().decode('utf-8'),
        "chave_privada": priv.save_pkcs1().decode('utf-8')
    }), 200

@app.route('/registrar', methods=['POST'])
def registrar_imovel():
    dados = request.get_json()
    
    matricula = dados.get('matricula')
    chave_remetente = dados.get('chave_remetente')
    chave_destinatario = dados.get('chave_destinatario')
    chave_privada = dados.get('chave_privada')
    
    if not matricula or not chave_remetente or not chave_destinatario or not chave_privada:
        return jsonify({"erro": "Todos os campos e chaves são obrigatórios!"}), 400
    
    try:
        novo_imovel = Imovel(matricula, chave_remetente, "Endereço Registrado no BD")
        nova_transacao = Transacao(novo_imovel, chave_remetente, chave_destinatario)
        
        priv_key_obj = rsa.PrivateKey.load_pkcs1(chave_privada.encode('utf-8'))
        nova_transacao.assinar_transacao(priv_key_obj)
        
        bloco_gerado = meu_forum.adicionar_bloco(nova_transacao)
        
        return jsonify({
            "mensagem": "Transação Assinada e Bloco Minerado com Sucesso!",
            "bloco_indice": bloco_gerado.indice,
            "hash": bloco_gerado.hash
        }), 201

    except ValueError as e:
        return jsonify({"erro": str(e)}), 403 
    except Exception as e:
        return jsonify({"erro": "Erro na formatação da chave criptográfica."}), 400

@app.route('/cadeia', methods=['GET'])
def ver_cadeia():
    lista_blocos = []
    for bloco in meu_forum.cadeia:
        lista_blocos.append({
            "indice": bloco.indice,
            "dados": bloco.dados,
            "hash": bloco.hash,
            "hash_anterior": bloco.hash_anterior
        })
    return jsonify(lista_blocos), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)