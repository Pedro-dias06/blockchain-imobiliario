import os
import sqlite3
import json
import requests
from bloco import Bloco
from typing import Any, List, Set


class BlockchainForum:
    def __init__(self):
        self.cadeia: List[Bloco] = []
        self.dificuldade: int = 4
        self.nos: Set[str] = set()

        nome_banco = os.environ.get('DB_NAME', 'forum_blockchain.db')
        self.conn = sqlite3.connect(nome_banco, check_same_thread=False)
        self.cursor = self.conn.cursor()

        self._criar_tabela()
        self._carregar_do_banco()

    # ------------------------------------------------------------------
    # Banco de Dados
    # ------------------------------------------------------------------

    def _criar_tabela(self) -> None:
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocos (
                indice INTEGER PRIMARY KEY,
                timestamp TEXT,
                dados TEXT,
                hash_anterior TEXT,
                nonce INTEGER,
                hash TEXT
            )
        ''')
        self.conn.commit()

    def _carregar_do_banco(self) -> None:
        self.cursor.execute("SELECT * FROM blocos ORDER BY indice ASC")
        linhas = self.cursor.fetchall()

        if len(linhas) == 0:
            self._criar_bloco_genese()
        else:
            for linha in linhas:
                dados_transacao = json.loads(linha[2]) if linha[2].startswith('{') else linha[2]
                bloco_recuperado = Bloco(
                    indice=linha[0],
                    timestamp=linha[1],
                    transacao=dados_transacao,
                    hash_anterior=linha[3],
                    nonce=linha[4],
                    hash_existente=linha[5]
                )
                self.cadeia.append(bloco_recuperado)
            print(f"📦 Blockchain carregada do Banco de Dados! Total: {len(self.cadeia)} blocos.")

    def _salvar_bloco_no_banco(self, bloco: Bloco) -> None:
        dados_json = json.dumps(bloco.dados) if isinstance(bloco.dados, dict) else str(bloco.dados)
        self.cursor.execute('''
            INSERT INTO blocos (indice, timestamp, dados, hash_anterior, nonce, hash)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (bloco.indice, bloco.timestamp, dados_json, bloco.hash_anterior, bloco.nonce, bloco.hash))
        self.conn.commit()

    def _criar_bloco_genese(self) -> None:
        print("🌱 Iniciando nova Blockchain (Criando Bloco Gênese)...")
        bloco_genese = Bloco(0, "Bloco Gênese - Fórum Inicializado", "0")
        bloco_genese.minerar_bloco(self.dificuldade)
        self.cadeia.append(bloco_genese)
        self._salvar_bloco_no_banco(bloco_genese)

    # ------------------------------------------------------------------
    # Operações da Cadeia
    # ------------------------------------------------------------------

    def get_ultimo_bloco(self) -> Bloco:
        return self.cadeia[-1]

    def adicionar_bloco(self, transacao: Any) -> Bloco:
        if hasattr(transacao, 'validar_assinatura'):
            if not transacao.validar_assinatura():
                raise ValueError("Transação Rejeitada: Assinatura digital inválida ou falsificada!")

        ultimo_bloco = self.get_ultimo_bloco()
        novo_bloco = Bloco(ultimo_bloco.indice + 1, transacao, ultimo_bloco.hash)
        novo_bloco.minerar_bloco(self.dificuldade)
        self.cadeia.append(novo_bloco)
        self._salvar_bloco_no_banco(novo_bloco)
        return novo_bloco

    def validar_corrente(self) -> bool:
        for i in range(1, len(self.cadeia)):
            bloco_atual = self.cadeia[i]
            bloco_anterior = self.cadeia[i - 1]

            if bloco_atual.hash != bloco_atual.gerar_hash():
                return False
            if bloco_atual.hash_anterior != bloco_anterior.hash:
                return False
        return True

    # ------------------------------------------------------------------
    # Camada P2P
    # ------------------------------------------------------------------

    def conectar_no(self, endereco: str) -> None:
        """Registra o endereço de um nó par (ex: 'http://outro-nó.pythonanywhere.com')."""
        self.nos.add(endereco.rstrip('/'))

    def propagar_novo_bloco(self, bloco: Bloco) -> None:
        """Envia o bloco recém-minerado para todos os nós conhecidos da rede."""
        dados_bloco = {
            "indice": bloco.indice,
            "timestamp": bloco.timestamp,
            "dados": bloco.dados,
            "hash_anterior": bloco.hash_anterior,
            "nonce": bloco.nonce,
            "hash": bloco.hash
        }
        for no in self.nos:
            try:
                requests.post(
                    f"{no}/receber_bloco_p2p",
                    json=dados_bloco,
                    timeout=5
                )
                print(f"📡 Bloco {bloco.indice} propagado para {no}")
            except requests.exceptions.RequestException:
                print(f"⚠️  Nó {no} não respondeu. Propagação continua para os demais.")
