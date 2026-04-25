import hashlib
import json
from datetime import datetime
from typing import Any, Optional

class Bloco:
    def __init__(self, indice: int, transacao: Any, hash_anterior: str, 
                 timestamp: Optional[str] = None, nonce: int = 0, hash_existente: Optional[str] = None):
        
        self.indice = indice 
        self.hash_anterior = hash_anterior

        if hasattr(transacao, 'to_dict'):
            self.dados = transacao.to_dict()
        else:
            self.dados = transacao

        self.timestamp = timestamp if timestamp else str(datetime.now())
        self.nonce = nonce

        self.hash = hash_existente if hash_existente else self.gerar_hash()

    def gerar_hash(self) -> str:
        conteudo = json.dumps({
            "indice": self.indice,
            "timestamp": self.timestamp,
            "dados": self.dados,
            "hash_anterior": self.hash_anterior,
            "nonce": self.nonce
        }, sort_keys=True).encode()

        return hashlib.sha256(conteudo).hexdigest()

    def minerar_bloco(self, dificuldade: int) -> None:
        alvo = "0" * dificuldade
        while self.hash[:dificuldade] != alvo:
            self.nonce += 1
            self.hash = self.gerar_hash()
            
        print(f"Bloco {self.indice} minerado! Nonce: {self.nonce} | Hash: {self.hash}")