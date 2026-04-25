import rsa
import base64
from datetime import datetime
from typing import Dict, Any

class Imovel:
    def __init__(self, matricula: str, proprietario: str, endereco: str):
        self.matricula = matricula
        self.proprietario = proprietario 
        self.endereco = endereco

    def to_dict(self) -> Dict[str, str]:
        return {
            "matricula": self.matricula,
            "proprietario": self.proprietario,
            "endereco": self.endereco
        }

class Transacao:
    def __init__(self, imovel: Imovel, chave_pub_remetente: str, chave_pub_destinatario: str):
        self.imovel = imovel
        self.chave_pub_remetente = chave_pub_remetente
        self.chave_pub_destinatario = chave_pub_destinatario
        self.data_registro = str(datetime.now())
        self.assinatura = "" 

    def to_dict(self) -> Dict[str, Any]:
        return {
            "imovel": self.imovel.to_dict(),
            "chave_pub_remetente": self.chave_pub_remetente,
            "chave_pub_destinatario": self.chave_pub_destinatario,
            "data_registro": self.data_registro,
            "assinatura": self.assinatura
        }

    def assinar_transacao(self, chave_privada_objeto: rsa.PrivateKey) -> None:
        dados_transacao = f"{self.imovel.matricula}{self.chave_pub_remetente}{self.chave_pub_destinatario}{self.data_registro}"
        assinatura_bytes = rsa.sign(dados_transacao.encode('utf-8'), chave_privada_objeto, 'SHA-256')
        self.assinatura = base64.b64encode(assinatura_bytes).decode('utf-8')

    def validar_assinatura(self) -> bool:
        if self.chave_pub_remetente == "SISTEMA_FORUM":
            return True

        if not self.assinatura:
            return False

        try:
            dados_transacao = f"{self.imovel.matricula}{self.chave_pub_remetente}{self.chave_pub_destinatario}{self.data_registro}"
            
            chave_pub_objeto = rsa.PublicKey.load_pkcs1(self.chave_pub_remetente.encode('utf-8'))
            assinatura_bytes = base64.b64decode(self.assinatura.encode('utf-8'))

            rsa.verify(dados_transacao.encode('utf-8'), assinatura_bytes, chave_pub_objeto)
            return True
        except:
            return False