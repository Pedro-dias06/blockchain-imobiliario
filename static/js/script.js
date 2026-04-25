
async function carregarBlockchain() {
    const resposta = await fetch('/cadeia');
    const blocos = await resposta.json();
    
    const divCadeia = document.getElementById('cadeia-blocos');
    divCadeia.innerHTML = '<h2>⛓️ Explorador de Blocos</h2>';

    blocos.forEach((bloco, index) => {
        if (index > 0) {
            divCadeia.innerHTML += `<div class="seta">⬇️</div>`;
        }

        let isGenese = index === 0;
        let conteudo = isGenese ? `<i>${bloco.dados}</i>` : 
            `<b>Imóvel:</b> ${bloco.dados.imovel.matricula}<br>
             <b>Destinatário:</b> ${bloco.dados.chave_pub_destinatario.substring(0,25)}...<br>
             <b>Assinatura:</b> <span style="color:green;">Válida ✅</span>`;

        divCadeia.innerHTML += `
            <div class="bloco ${isGenese ? 'bloco-genese' : ''}">
                <div class="bloco-header">Bloco #${bloco.indice}</div>
                <div class="bloco-body">
                    <p>${conteudo}</p>
                    <small><b>Nonce:</b> ${bloco.dados.nonce || "N/A"}</small><br>
                    <small><b>Hash:</b> <span class="hash">${bloco.hash}</span></small>
                </div>
            </div>
        `;
    });
}

async function gerarChaves() {
    const resposta = await fetch('/gerar_carteira');
    const chaves = await resposta.json();
    document.getElementById('minha_pub').value = chaves.chave_publica;
    document.getElementById('minha_priv').value = chaves.chave_privada;
    alert("Chaves geradas! Guarde sua Chave Privada em segurança.");
}

async function registrarImovel() {
    const matricula = document.getElementById('matricula').value;
    const chave_remetente = document.getElementById('minha_pub').value;
    const chave_destinatario = document.getElementById('chave_destinatario').value;
    const chave_privada = document.getElementById('chave_privada_assinatura').value;

    if(!matricula || !chave_remetente || !chave_destinatario || !chave_privada) {
        alert("Erro: Preencha a matrícula, as chaves e não esqueça de assinar com sua chave privada!");
        return;
    }

    try {
        const resposta = await fetch('/registrar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ matricula, chave_remetente, chave_destinatario, chave_privada })
        });

        const resultado = await resposta.json();
        
        if(resposta.ok) {
            alert("Sucesso! " + resultado.mensagem);
            document.getElementById('matricula').value = '';
            carregarBlockchain();
        } else {
            alert("🚨 ATAQUE BLOQUEADO ou ERRO: " + resultado.erro);
        }
    } catch (erro) {
        alert("Erro na conexão com o Fórum.");
    }
}

carregarBlockchain();