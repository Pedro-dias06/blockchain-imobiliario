// =====================================================================
// Explorador de Blocos
// =====================================================================

async function carregarBlockchain() {
    const divCadeia = document.getElementById('cadeia-blocos');
    divCadeia.innerHTML = '<p class="carregando">Carregando blocos...</p>';

    const resposta = await fetch('/cadeia');
    const blocos = await resposta.json();

    divCadeia.innerHTML = '';

    blocos.forEach((bloco, index) => {
        if (index > 0) {
            divCadeia.innerHTML += `<div class="seta">⬇</div>`;
        }

        const isGenese = index === 0;
        let conteudo;

        if (isGenese) {
            conteudo = `<em>${bloco.dados}</em>`;
        } else {
            const dest = bloco.dados.chave_pub_destinatario
                ? bloco.dados.chave_pub_destinatario.replace(/\n/g, '').substring(27, 55) + '...'
                : 'N/A';
            const assinaturaOk = bloco.dados.assinatura && bloco.dados.assinatura.length > 0;
            conteudo = `
                <div class="dado-linha"><span class="dado-label">Imóvel</span> ${bloco.dados.imovel.matricula}</div>
                <div class="dado-linha"><span class="dado-label">Destinatário</span> <span class="mono">${dest}</span></div>
                <div class="dado-linha"><span class="dado-label">Registrado em</span> ${bloco.dados.data_registro || 'N/A'}</div>
                <div class="dado-linha"><span class="dado-label">Assinatura RSA</span>
                    ${assinaturaOk
                        ? '<span class="badge badge-ok">Válida ✅</span>'
                        : '<span class="badge badge-warn">Ausente ⚠️</span>'}
                </div>`;
        }

        divCadeia.innerHTML += `
            <div class="bloco ${isGenese ? 'bloco-genese' : ''}">
                <div class="bloco-header">
                    <span>Bloco #${bloco.indice}</span>
                    <span class="bloco-ts">${bloco.timestamp ? bloco.timestamp.substring(0, 19) : ''}</span>
                </div>
                <div class="bloco-body">
                    ${conteudo}
                    <div class="bloco-rodape">
                        <small><b>Nonce:</b> ${bloco.nonce}</small>
                        <small><b>Hash anterior:</b> <span class="hash">${bloco.hash_anterior.substring(0, 16)}…</span></small>
                        <small><b>Hash:</b> <span class="hash">${bloco.hash}</span></small>
                    </div>
                </div>
            </div>`;
    });
}

async function validarCadeia() {
    const div = document.getElementById('status-validacao');
    div.innerHTML = '<p class="carregando">Validando...</p>';

    const resposta = await fetch('/validar');
    const resultado = await resposta.json();

    div.innerHTML = `<div class="status-banner ${resultado.valida ? 'banner-ok' : 'banner-erro'}">
        ${resultado.mensagem}
    </div>`;
}


// =====================================================================
// Carteira
// =====================================================================

async function gerarChaves() {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '⏳ Gerando...';

    const resposta = await fetch('/gerar_carteira');
    const chaves = await resposta.json();

    document.getElementById('minha_pub').value = chaves.chave_publica;
    document.getElementById('minha_priv').value = chaves.chave_privada;

    btn.disabled = false;
    btn.textContent = '🔑 Gerar Novas Chaves';

    mostrarToast('✅ Par de chaves RSA gerado! Guarde sua chave privada.', 'ok');
}


// =====================================================================
// Transações
// =====================================================================

async function registrarImovel() {
    const matricula = document.getElementById('matricula').value.trim();
    const chave_remetente = document.getElementById('minha_pub').value.trim();
    const chave_destinatario = document.getElementById('chave_destinatario').value.trim();
    const chave_privada = document.getElementById('chave_privada_assinatura').value.trim();

    if (!matricula || !chave_remetente || !chave_destinatario || !chave_privada) {
        mostrarToast('⚠️ Preencha todos os campos antes de assinar.', 'warn');
        return;
    }

    mostrarToast('⛏️ Minerando bloco… Aguarde.', 'info');

    try {
        const resposta = await fetch('/registrar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ matricula, chave_remetente, chave_destinatario, chave_privada })
        });

        const resultado = await resposta.json();

        if (resposta.ok) {
            mostrarToast(`✅ ${resultado.mensagem} (Bloco #${resultado.bloco_indice})`, 'ok');
            document.getElementById('matricula').value = '';
            carregarBlockchain();
        } else {
            mostrarToast(`🚨 ${resultado.erro}`, 'erro');
        }
    } catch {
        mostrarToast('❌ Erro na conexão com o servidor.', 'erro');
    }
}


// =====================================================================
// Rede P2P
// =====================================================================

async function conectarNo() {
    const endereco = document.getElementById('endereco_no').value.trim();
    if (!endereco) {
        mostrarToast('⚠️ Informe o endereço do nó.', 'warn');
        return;
    }

    const resposta = await fetch('/conectar_nos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nos: [endereco] })
    });

    const resultado = await resposta.json();

    if (resposta.ok) {
        document.getElementById('endereco_no').value = '';
        mostrarToast(`🔗 ${resultado.mensagem}`, 'ok');
        atualizarListaNos(resultado.nos_ativos);
    } else {
        mostrarToast(`❌ ${resultado.erro}`, 'erro');
    }
}

async function carregarNos() {
    const resposta = await fetch('/nos');
    const resultado = await resposta.json();
    atualizarListaNos(resultado.nos);
}

function atualizarListaNos(nos) {
    const div = document.getElementById('lista-nos');
    if (!nos || nos.length === 0) {
        div.innerHTML = '<p class="sem-dados">Nenhum nó conectado.</p>';
        return;
    }
    div.innerHTML = nos.map(no =>
        `<div class="no-item">🟢 <span class="mono">${no}</span></div>`
    ).join('');
}


// =====================================================================
// Toast de notificações
// =====================================================================

function mostrarToast(mensagem, tipo = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${tipo}`;
    toast.textContent = mensagem;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('toast-visivel'), 10);
    setTimeout(() => {
        toast.classList.remove('toast-visivel');
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}


// =====================================================================
// Init
// =====================================================================

carregarBlockchain();
carregarNos();
