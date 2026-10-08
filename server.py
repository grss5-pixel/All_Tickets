import http.server
import socketserver
import json
import uuid
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

# ==============================================================================
# 1. DOMÍNIO, BANCO DE DADOS EM MEMÓRIA & CREDENCIAIS DE TESTE (SEÇÃO 1 & 2)
# ==============================================================================

class UserRole:
    PUBLICO = "PUBLICO"
    EMPRESA = "EMPRESA"
    ADMIN = "ADMIN"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Credenciais Criptografadas dos Perfis de Teste
PASS_ADMIN = hash_password("admin123")
PASS_EMPRESA = hash_password("empresa123")
PASS_PUBLICO = hash_password("user123")

ADMIN_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
COMPANY_ID = "b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22"
PUBLIC_ID = "c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33"
DEFAULT_EVENT_ID = "e3a8910d-2b4a-4f51-b883-92f701b918a2"

db = {
    "users": {
        ADMIN_ID: {"id": ADMIN_ID, "name": "Leonardo Medeiros", "email": "admin@alltickets.com", "pass_hash": PASS_ADMIN, "role": UserRole.ADMIN},
        COMPANY_ID: {"id": COMPANY_ID, "name": "Mariana Produções", "email": "empresa@mariana.com", "pass_hash": PASS_EMPRESA, "role": UserRole.EMPRESA},
        PUBLIC_ID: {"id": PUBLIC_ID, "name": "Isadora Fernandes", "email": "isadora@email.com", "pass_hash": PASS_PUBLICO, "role": UserRole.PUBLICO}
    },
    "events": {
        DEFAULT_EVENT_ID: {
            "id": DEFAULT_EVENT_ID,
            "company_id": COMPANY_ID,
            "company_name": "Mariana Produções",
            "title": "Maceió Summer Sounds 2026",
            "category": "Shows e Festivais",
            "price": 100.00,
            "stock": 10,
            "likes_count": 18,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    },
    "tickets": {},
    "tickets_by_hash": {},
    "financial_transactions": {},
    "company_requests": {
        "REQ-101": {
            "id": "REQ-101",
            "user_id": PUBLIC_ID,
            "company_name": "Isadora Eventos Culturais",
            "cnpj": "12.345.678/0001-90",
            "email": "isadora@email.com",
            "description": "Produção de Peças Teatrais e Festivais",
            "status": "PENDENTE",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    },
    "sessions": {} # token -> user_id
}

# ==============================================================================
# 2. FRONTEND HTML5 + JS ES6 (DESIGN DARK ESTON TEMPLATE INSPIRATION)
# ==============================================================================

HTML_PAGE = """<!DOCTYPE html>
<html lang="pt-BR" data-bs-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>All Tickets. — Movie Studio & Event Platform</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #0d0d0f;
      --card-bg: #16161a;
      --card-border: #24242c;
      --accent-red: #ff2a4b;
      --accent-red-hover: #d91d3a;
      --text-muted: #8e8e9e;
    }
    body {
      background-color: var(--bg-dark);
      color: #f1f1f5;
      font-family: 'Plus Jakarta Sans', sans-serif;
      padding-bottom: 60px;
    }
    .navbar {
      background-color: rgba(13, 13, 15, 0.9) !important;
      backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--card-border);
    }
    .brand-logo {
      font-weight: 800;
      font-size: 1.6rem;
      letter-spacing: -0.5px;
      color: #ffffff;
    }
    .brand-dot {
      color: var(--accent-red);
    }
    .hero-banner {
      background: linear-gradient(180deg, rgba(22, 22, 26, 0.4) 0%, rgba(13, 13, 15, 1) 100%),
                  radial-gradient(circle at top right, rgba(255, 42, 75, 0.15), transparent 40%);
      border-radius: 20px;
      padding: 50px 40px;
      margin-bottom: 40px;
      border: 1px solid var(--card-border);
    }
    .hero-title {
      font-size: 2.8rem;
      font-weight: 800;
      letter-spacing: -1px;
      line-height: 1.1;
    }
    .btn-eston {
      background-color: var(--accent-red);
      color: #ffffff;
      font-weight: 700;
      border: none;
      padding: 10px 24px;
      border-radius: 8px;
      transition: all 0.2s ease;
    }
    .btn-eston:hover {
      background-color: var(--accent-red-hover);
      color: #ffffff;
      transform: translateY(-2px);
    }
    .card-eston {
      background-color: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      overflow: hidden;
      transition: all 0.25s cubic-bezier(0.165, 0.84, 0.44, 1);
    }
    .card-eston:hover {
      transform: translateY(-6px);
      border-color: rgba(255, 42, 75, 0.4);
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.5);
    }
    .nav-pills .nav-link {
      color: var(--text-muted);
      font-weight: 600;
      border-radius: 8px;
      padding: 8px 18px;
    }
    .nav-pills .nav-link.active {
      background-color: var(--accent-red);
      color: #ffffff;
    }
    .badge-category {
      background-color: rgba(255, 42, 75, 0.12);
      color: var(--accent-red);
      border: 1px solid rgba(255, 42, 75, 0.3);
      font-weight: 700;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .qr-badge {
      font-family: monospace;
      font-size: 1rem;
      background: #0d0d0f;
      color: #00ff88;
      border: 1px dashed #00ff88;
      padding: 6px 12px;
      border-radius: 6px;
    }
    .modal-content {
      background-color: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
    }
  </style>
</head>
<body>

  <!-- NAVBAR ESTON STYLE -->
  <nav class="navbar navbar-expand-lg navbar-dark sticky-top">
    <div class="container">
      <a class="navbar-brand brand-logo" href="#">All Tickets<span class="brand-dot">.</span></a>
      
      <div class="d-flex align-items-center gap-3 ms-auto" id="authNavArea">
        <!-- Preenchido dinamicamente via JS -->
      </div>
    </div>
  </nav>

  <div class="container my-4">

    <!-- HERO BANNER ESTON INSPIRATION -->
    <div class="hero-banner">
      <div class="row align-items-center">
        <div class="col-lg-8">
          <span class="badge badge-category mb-3">Live Experiences & Digital Distribution</span>
          <h1 class="hero-title mb-3">Makes & Distributes <br><span style="color: var(--accent-red);">Ticket Experiences.</span></h1>
          <p class="text-secondary lead fs-6 mb-0">Plataforma centralizada para venda de ingressos, emissão de voucher criptográfico e validação na portaria em tempo real.</p>
        </div>
      </div>
    </div>

    <!-- NAVEGAÇÃO DE ABAS PROTEGIDA POR RBAC -->
    <ul class="nav nav-pills mb-4 gap-2" id="mainTabs">
      <li class="nav-item">
        <button class="nav-link active" onclick="switchTab('public')">🎉 Feed de Eventos</button>
      </li>
      <li class="nav-item d-none" id="tabProducer">
        <button class="nav-link" onclick="switchTab('company')">📊 Painel do Produtor</button>
      </li>
      <li class="nav-item d-none" id="tabAdmin">
        <button class="nav-link" onclick="switchTab('admin')">⚙️ Painel Admin Global</button>
      </li>
    </ul>

    <!-- VISÃO 1: FEED PÚBLICO -->
    <div id="view-public" class="tab-content">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h3 class="fw-bold m-0">Próximos Eventos</h3>
      </div>

      <div class="row g-4" id="eventsGrid"></div>

      <!-- CARTEIRA DIGITAL -->
      <div class="mt-5 d-none" id="walletSection">
        <h4 class="fw-bold mb-3">💼 Minha Carteira Digital de Ingressos</h4>
        <div class="list-group" id="userWallet"></div>
      </div>
    </div>

    <!-- VISÃO 2: PAINEL DO PRODUTOR (EMPRESA) -->
    <div id="view-company" class="tab-content d-none">
      <h3 class="fw-bold mb-4">Painel do Produtor de Eventos</h3>
      <div class="row g-4">
        <div class="col-lg-6">
          <div class="card card-eston p-4">
            <h5 class="fw-bold mb-3 text-white">➕ Publicar Novo Evento</h5>
            <form onsubmit="handleCreateEvent(event)">
              <div class="mb-3">
                <label class="form-label text-secondary small fw-semibold">Título do Evento</label>
                <input type="text" id="evTitle" class="form-control bg-dark text-white border-secondary" required placeholder="Ex: Festival Rock Maceió">
              </div>
              <div class="mb-3">
                <label class="form-label text-secondary small fw-semibold">Categoria</label>
                <select id="evCategory" class="form-select bg-dark text-white border-secondary">
                  <option value="Shows e Festivais">Shows e Festivais</option>
                  <option value="Teatro e Cultura">Teatro e Cultura</option>
                  <option value="Festas e Nightlife">Festas e Nightlife</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label text-secondary small fw-semibold">Preço por Ingresso (R$)</label>
                <input type="number" id="evPrice" class="form-control bg-dark text-white border-secondary" step="0.01" required placeholder="100.00">
              </div>
              <div class="mb-4">
                <label class="form-label text-secondary small fw-semibold">Estoque Inicial</label>
                <input type="number" id="evStock" class="form-control bg-dark text-white border-secondary" required placeholder="50">
              </div>
              <button type="submit" class="btn btn-eston w-100">Publicar Evento</button>
            </form>
          </div>
        </div>

        <div class="col-lg-6">
          <div class="card card-eston p-4">
            <h5 class="fw-bold mb-3 text-white">🔍 Validador de Portaria (Antifraude)</h5>
            <p class="text-secondary small">Insira o código Hash único impresso no bilhete para autorizar a entrada e queimar o ingresso.</p>
            <div class="input-group mb-3">
              <input type="text" id="qrInput" class="form-control bg-dark text-white border-secondary" placeholder="Ex: QR-A9F82B10C4">
              <button class="btn btn-success fw-bold" onclick="handleValidateTicket()">Validar Entrada</button>
            </div>
            <div id="validationResult"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- VISÃO 3: PAINEL ADMINISTRATIVO GLOBAL -->
    <div id="view-admin" class="tab-content d-none">
      <h3 class="fw-bold mb-4">Painel do Administrador All Tickets</h3>
      
      <!-- DASHBOARD FINANCEIRO GLOBAL -->
      <div class="row g-4 mb-4">
        <div class="col-md-6">
          <div class="card card-eston p-4 text-center">
            <span class="text-secondary small fw-bold">VOLUME TOTAL TRANSACIONADO</span>
            <h2 class="fw-800 text-white mt-2" id="adminTotalVolume">R$ 0,00</h2>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card card-eston p-4 text-center">
            <span class="text-secondary small fw-bold">COMISSÃO DA PLATAFORMA (20%)</span>
            <h2 class="fw-800 mt-2" style="color: var(--accent-red);" id="adminPlatformShare">R$ 0,00</h2>
          </div>
        </div>
      </div>

      <div class="card card-eston p-4 mb-4">
        <h5 class="fw-bold mb-3 text-white">📋 Solicitações de Parceria Empresarial Pendentes</h5>
        <div id="adminRequestsList"></div>
      </div>

      <div class="card card-eston p-4">
        <h5 class="fw-bold mb-3 text-white">👥 Gestão de Usuários e Promoção de Papéis (RN-05)</h5>
        <div id="adminUsersList"></div>
      </div>
    </div>

  </div>

  <!-- MODAL DE LOGIN -->
  <div class="modal fade" id="loginModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content p-3">
        <div class="modal-header border-0">
          <h4 class="modal-title fw-bold text-white">Entrar na Conta<span class="brand-dot">.</span></h4>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <form onsubmit="handleLogin(event)">
            <div class="mb-3">
              <label class="form-label text-secondary small">E-mail de Acesso</label>
              <input type="email" id="loginEmail" class="form-control bg-dark text-white border-secondary" required>
            </div>
            <div class="mb-4">
              <label class="form-label text-secondary small">Senha</label>
              <input type="password" id="loginPassword" class="form-control bg-dark text-white border-secondary" required>
            </div>
            <button type="submit" class="btn btn-eston w-100 mb-3">Autenticar no Sistema</button>
          </form>

          <p class="text-center text-secondary small mb-3">
            Não tem uma conta? <a href="#" class="text-white fw-bold text-decoration-none" onclick="closeModal('loginModal'); openModal('registerModal');">Criar Conta</a>
          </p>

          <hr class="border-secondary my-4">
          <p class="text-secondary small fw-bold text-center mb-3">ACESSO RÁPIDO PARA TESTES DOS 3 PERFIS:</p>
          <div class="d-grid gap-2">
            <button class="btn btn-outline-warning btn-sm" onclick="quickLogin('admin@alltickets.com', 'admin123')">👑 Logar como Admin (Total Access)</button>
            <button class="btn btn-outline-info btn-sm" onclick="quickLogin('empresa@mariana.com', 'empresa123')">🏢 Logar como Empresa (Produtor Aprovado)</button>
            <button class="btn btn-outline-light btn-sm" onclick="quickLogin('isadora@email.com', 'user123')">👤 Logar como Público (Comprador)</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- MODAL DE CRIAR CONTA (CADASTRO) -->
  <div class="modal fade" id="registerModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content p-3">
        <div class="modal-header border-0">
          <h4 class="modal-title fw-bold text-white">Criar Nova Conta<span class="brand-dot">.</span></h4>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <form onsubmit="handleRegister(event)">
            <div class="mb-3">
              <label class="form-label text-secondary small">Nome Completo</label>
              <input type="text" id="regName" class="form-control bg-dark text-white border-secondary" required>
            </div>
            <div class="mb-3">
              <label class="form-label text-secondary small">E-mail</label>
              <input type="email" id="regEmail" class="form-control bg-dark text-white border-secondary" required>
            </div>
            <div class="mb-4">
              <label class="form-label text-secondary small">Senha</label>
              <input type="password" id="regPassword" class="form-control bg-dark text-white border-secondary" required>
            </div>
            <button type="submit" class="btn btn-eston w-100">Finalizar Cadastro</button>
          </form>
          <p class="text-center text-secondary small mt-3 mb-0">
            Já tem uma conta? <a href="#" class="text-white fw-bold text-decoration-none" onclick="closeModal('registerModal'); openModal('loginModal');">Entrar aqui</a>
          </p>
        </div>
      </div>
    </div>
  </div>

  <!-- MODAL SOLICITAR PARCERIA EMPRESARIAL -->
  <div class="modal fade" id="requestModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content p-3">
        <div class="modal-header border-0">
          <h4 class="modal-title fw-bold text-white">Solicitar Parceria Empresarial</h4>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <p class="text-secondary small mb-3">Após enviar, a proposta passará por análise do Administrador. Uma vez aprovada, sua conta será promovida para Produtor de Eventos.</p>
          <form onsubmit="handleSendRequest(event)">
            <div class="mb-3">
              <label class="form-label text-secondary small">Razão Social / Nome Fantasia da Empresa</label>
              <input type="text" id="reqName" class="form-control bg-dark text-white border-secondary" required>
            </div>
            <div class="mb-3">
              <label class="form-label text-secondary small">CNPJ</label>
              <input type="text" id="reqCnpj" class="form-control bg-dark text-white border-secondary" placeholder="00.000.000/0001-00" required>
            </div>
            <div class="mb-4">
              <label class="form-label text-secondary small">Descrição da Empresa & Proposta de Eventos</label>
              <textarea id="reqDesc" class="form-control bg-dark text-white border-secondary" rows="3" required></textarea>
            </div>
            <button type="submit" class="btn btn-eston w-100">Enviar Solicitação para o Admin</button>
          </form>
        </div>
      </div>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    let sessionToken = localStorage.getItem('token') || null;
    let currentUser = null;

    async function init() {
      if (sessionToken) {
        await fetchCurrentUser();
      } else {
        renderAuthUI();
      }
      loadEvents();
    }

    async function fetchCurrentUser() {
      try {
        const res = await fetch('/api/v1/auth/me', {
          headers: { 'Authorization': `Bearer ${sessionToken}` }
        });
        if (res.ok) {
          currentUser = await res.json();
          renderAuthUI();
          loadWallet();
          if (currentUser.role === 'ADMIN') loadAdminData();
        } else {
          logout();
        }
      } catch (err) {
        logout();
      }
    }

    function renderAuthUI() {
      const authArea = document.getElementById('authNavArea');
      const tabProducer = document.getElementById('tabProducer');
      const tabAdmin = document.getElementById('tabAdmin');
      const walletSec = document.getElementById('walletSection');

      if (currentUser) {
        let badgeColor = currentUser.role === 'ADMIN' ? 'bg-warning text-dark' : currentUser.role === 'EMPRESA' ? 'bg-info text-dark' : 'bg-secondary';
        
        let partnerOption = currentUser.role === 'PUBLICO' 
          ? `<button class="btn btn-outline-light btn-sm rounded-2 me-2" onclick="checkPartnerStatus()">🤝 Seja um Produtor</button>` 
          : '';

        authArea.innerHTML = `
          ${partnerOption}
          <span class="small fw-bold text-white me-2">${currentUser.name} <span class="badge ${badgeColor}">${currentUser.role}</span></span>
          <button class="btn btn-outline-danger btn-sm rounded-2" onclick="logout()">Sair</button>
        `;

        walletSec.classList.remove('d-none');

        // REGRAS DE VISIBILIDADE RBAC (CB-03)
        if (currentUser.role === 'EMPRESA') {
          tabProducer.classList.remove('d-none');
          tabAdmin.classList.add('d-none');
        } else if (currentUser.role === 'ADMIN') {
          tabProducer.classList.remove('d-none');
          tabAdmin.classList.remove('d-none');
        } else {
          // Usuários Compradores (PUBLICO) NÃO veem abas de Produtor e Admin
          tabProducer.classList.add('d-none');
          tabAdmin.classList.add('d-none');
        }
      } else {
        authArea.innerHTML = `
          <button class="btn btn-outline-light btn-sm rounded-2" onclick="openModal('loginModal')">Entrar</button>
          <button class="btn btn-eston btn-sm" onclick="openModal('registerModal')">Criar Conta</button>
        `;
        tabProducer.classList.add('d-none');
        tabAdmin.classList.add('d-none');
        walletSec.classList.add('d-none');
      }
    }

    async function handleLogin(e) {
      e.preventDefault();
      const email = document.getElementById('loginEmail').value;
      const pass = document.getElementById('loginPassword').value;

      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password: pass })
      });

      const data = await res.json();
      if (!res.ok) {
        alert(`Erro: ${data.error}`);
        return;
      }

      sessionToken = data.token;
      localStorage.setItem('token', sessionToken);
      currentUser = data.user;

      closeModal('loginModal');
      renderAuthUI();
      loadWallet();
      if (currentUser.role === 'ADMIN') loadAdminData();
      alert(`👋 Bem-vindo(a), ${currentUser.name}!`);
    }

    async function handleRegister(e) {
      e.preventDefault();
      const name = document.getElementById('regName').value;
      const email = document.getElementById('regEmail').value;
      const pass = document.getElementById('regPassword').value;

      const res = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password: pass })
      });

      const data = await res.json();
      if (!res.ok) {
        alert(`Erro: ${data.error}`);
        return;
      }

      sessionToken = data.token;
      localStorage.setItem('token', sessionToken);
      currentUser = data.user;

      closeModal('registerModal');
      renderAuthUI();
      alert(`🎉 Conta criada com sucesso! Bem-vindo(a), ${currentUser.name}.`);
    }

    function quickLogin(email, pass) {
      document.getElementById('loginEmail').value = email;
      document.getElementById('loginPassword').value = pass;
      handleLogin(new Event('submit'));
    }

    function logout() {
      sessionToken = null;
      currentUser = null;
      localStorage.removeItem('token');
      renderAuthUI();
      switchTab('public');
    }

    function switchTab(tab) {
      document.querySelectorAll('.tab-content').forEach(el => el.classList.add('d-none'));
      document.querySelectorAll('#mainTabs .nav-link').forEach(el => el.classList.remove('active'));
      document.getElementById(`view-${tab}`).classList.remove('d-none');
      event.target.classList.add('active');
    }

    async function loadEvents() {
      const res = await fetch('/api/v1/events');
      const events = await res.json();
      const grid = document.getElementById('eventsGrid');

      grid.innerHTML = events.map(ev => `
        <div class="col-md-4">
          <div class="card card-eston h-100">
            <div class="card-body p-4 d-flex flex-column">
              <div>
                <span class="badge badge-category mb-2">${ev.category}</span>
                <h5 class="fw-bold text-white mb-1">${ev.title}</h5>
                <p class="text-secondary small mb-3">Por: ${ev.company_name}</p>
              </div>
              <div class="mt-auto">
                <div class="d-flex justify-content-between align-items-baseline mb-3">
                  <span class="fs-4 fw-bold text-white">R$ ${ev.price.toFixed(2)}</span>
                  <span class="small text-secondary">Estoque: <strong>${ev.stock}</strong></span>
                </div>
                <button class="btn btn-eston w-100" onclick="buyTicket('${ev.id}')" ${ev.stock <= 0 ? 'disabled' : ''}>
                  ${ev.stock > 0 ? 'Comprar Ingresso' : 'Esgotado'}
                </button>
              </div>
            </div>
          </div>
        </div>
      `).join('');
    }

    async function buyTicket(eventId) {
      if (!currentUser) {
        alert('🔒 Faça login para realizar a compra!');
        openModal('loginModal');
        return;
      }

      const res = await fetch(`/api/v1/events/${eventId}/purchase`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${sessionToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ payment_method: 'PIX' })
      });

      const data = await res.json();
      if (!res.ok) {
        alert(`Erro (${res.status}): ${data.error}`);
        return;
      }

      // MENSAGEM LIMPA PARA O COMPRADOR (SEM INFORMAÇÃO DE SPLIT INTERNO DE 80%/20%)
      alert(`🎉 Compra Concluída com Sucesso!\n\n` +
            `Evento: ${data.ticket.event_title}\n` +
            `Seu ingresso foi emitido e salvo na sua Carteira Digital.\n` +
            `Código Hash Criptográfico: ${data.ticket.qr_hash}`);

      loadEvents();
      loadWallet();
      if (currentUser.role === 'ADMIN') loadAdminData();
    }

    async function loadWallet() {
      if (!currentUser) return;
      const res = await fetch('/api/v1/tickets', {
        headers: { 'Authorization': `Bearer ${sessionToken}` }
      });
      const tickets = await res.json();
      const wallet = document.getElementById('userWallet');

      if (tickets.length === 0) {
        wallet.innerHTML = '<div class="list-group-item bg-dark text-secondary border-secondary">Nenhum ingresso comprado ainda.</div>';
        return;
      }

      wallet.innerHTML = tickets.map(t => `
        <div class="list-group-item bg-dark border-secondary text-white d-flex justify-content-between align-items-center p-3">
          <div>
            <h6 class="fw-bold mb-1">${t.event_title}</h6>
            <small class="text-secondary">Emitido em: ${new Date(t.created_at).toLocaleString()}</small>
          </div>
          <div>
            <span class="qr-badge">${t.qr_hash}</span>
            <span class="badge ${t.is_used ? 'bg-danger' : 'bg-success'} ms-2">
              ${t.is_used ? 'UTILIZADO' : 'VÁLIDO'}
            </span>
          </div>
        </div>
      `).join('');
    }

    async function handleCreateEvent(e) {
      e.preventDefault();
      const payload = {
        title: document.getElementById('evTitle').value,
        category: document.getElementById('evCategory').value,
        price: parseFloat(document.getElementById('evPrice').value),
        stock: parseInt(document.getElementById('evStock').value)
      };

      const res = await fetch('/api/v1/events', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${sessionToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) {
        alert(`Erro (${res.status}): ${data.error}`);
        return;
      }

      alert('✅ Evento cadastrado com sucesso!');
      loadEvents();
    }

    async function handleValidateTicket() {
      const hash = document.getElementById('qrInput').value.trim();
      const resultDiv = document.getElementById('validationResult');

      const res = await fetch('/api/v1/tickets/validate', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${sessionToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ qr_hash: hash })
      });

      const data = await res.json();
      if (!res.ok) {
        resultDiv.innerHTML = `<div class="alert alert-danger mb-0">${data.error}</div>`;
      } else {
        resultDiv.innerHTML = `<div class="alert alert-success mb-0">✅ ${data.message}<br><small>Evento: ${data.event_title}</small></div>`;
        loadWallet();
      }
    }

    async function checkPartnerStatus() {
      const res = await fetch('/api/v1/company-requests/my-status', {
        headers: { 'Authorization': `Bearer ${sessionToken}` }
      });
      const data = await res.json();

      if (data.status === 'PENDENTE') {
        alert(`⌛ Sua solicitação de parceria para "${data.request.company_name}" está em análise pelo Administrador. Você poderá publicar eventos assim que for aprovado!`);
      } else if (data.status === 'REJEITADO') {
        alert('❌ Sua solicitação anterior foi rejeitada pelo Administrador. Você pode enviar uma nova proposta.');
        openModal('requestModal');
      } else {
        openModal('requestModal');
      }
    }

    async function handleSendRequest(e) {
      e.preventDefault();
      const payload = {
        company_name: document.getElementById('reqName').value,
        cnpj: document.getElementById('reqCnpj').value,
        description: document.getElementById('reqDesc').value
      };

      const res = await fetch('/api/v1/company-requests', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${sessionToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (res.ok) {
        alert('✅ Solicitação enviada com sucesso! Aguarde a aprovação do Administrador no painel.');
        closeModal('requestModal');
      } else {
        alert(`Erro: ${data.error}`);
      }
    }

    async function loadAdminData() {
      // Financeiro Global (Admin Only)
      const resFin = await fetch('/api/v1/admin/stats', {
        headers: { 'Authorization': `Bearer ${sessionToken}` }
      });
      if (resFin.ok) {
        const fin = await resFin.json();
        document.getElementById('adminTotalVolume').innerText = `R$ ${fin.total_volume.toFixed(2)}`;
        document.getElementById('adminPlatformShare').innerText = `R$ ${fin.platform_share.toFixed(2)}`;
      }

      // Lista de Solicitações
      const resReq = await fetch('/api/v1/company-requests', {
        headers: { 'Authorization': `Bearer ${sessionToken}` }
      });
      if (resReq.ok) {
        const reqs = await resReq.json();
        const list = document.getElementById('adminRequestsList');
        if (reqs.length === 0) {
          list.innerHTML = '<p class="text-secondary small m-0">Nenhuma solicitação pendente.</p>';
        } else {
          list.innerHTML = reqs.map(r => `
            <div class="d-flex justify-content-between align-items-center border-bottom border-secondary py-3">
              <div>
                <strong class="text-white">${r.company_name}</strong> (CNPJ: ${r.cnpj})<br>
                <small class="text-secondary">${r.description} | Status: <span class="badge bg-warning text-dark">${r.status}</span></small>
              </div>
              <div>
                ${r.status === 'PENDENTE' ? `
                  <button class="btn btn-sm btn-success fw-bold" onclick="approveRequest('${r.id}', 'APROVADO')">Aprovar & Promover</button>
                  <button class="btn btn-sm btn-outline-danger" onclick="approveRequest('${r.id}', 'REJEITADO')">Rejeitar</button>
                ` : `<span class="badge bg-secondary">${r.status}</span>`}
              </div>
            </div>
          `).join('');
        }
      }

      // Lista de Usuários
      const resUsers = await fetch('/api/v1/admin/users', {
        headers: { 'Authorization': `Bearer ${sessionToken}` }
      });
      if (resUsers.ok) {
        const users = await resUsers.json();
        const list = document.getElementById('adminUsersList');
        list.innerHTML = users.map(u => `
          <div class="d-flex justify-content-between align-items-center border-bottom border-secondary py-2">
            <div>
              <strong class="text-white">${u.name}</strong> (${u.email})<br>
              <small class="text-secondary">Papel Atual: <span class="badge bg-secondary">${u.role}</span></small>
            </div>
            <div>
              <select class="form-select form-select-sm bg-dark text-white border-secondary d-inline-block w-auto" onchange="promoteUser('${u.id}', this.value)">
                <option value="PUBLICO" ${u.role === 'PUBLICO' ? 'selected' : ''}>PÚBLICO</option>
                <option value="EMPRESA" ${u.role === 'EMPRESA' ? 'selected' : ''}>EMPRESA</option>
                <option value="ADMIN" ${u.role === 'ADMIN' ? 'selected' : ''}>ADMIN</option>
              </select>
            </div>
          </div>
        `).join('');
      }
    }

    async function approveRequest(reqId, status) {
      const res = await fetch(`/api/v1/company-requests/${reqId}`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${sessionToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      if (res.ok) {
        alert(`Solicitação ${status} com sucesso!`);
        fetchCurrentUser();
        loadAdminData();
      }
    }

    async function promoteUser(userId, newRole) {
      const res = await fetch(`/api/v1/admin/users/${userId}/role`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${sessionToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: newRole })
      });
      if (res.ok) {
        alert(`Papel do usuário atualizado para ${newRole}!`);
        loadAdminData();
      }
    }

    function openModal(id) {
      new bootstrap.Modal(document.getElementById(id)).show();
    }
    function closeModal(id) {
      const el = document.getElementById(id);
      const modal = bootstrap.Modal.getInstance(el);
      if (modal) modal.hide();
    }

    init();
  </script>
</body>
</html>
"""

# ==============================================================================
# 3. HANDLER HTTP E TRATAMENTO DAS ROTAS DA API REST (SEÇÃO 4 & 5)
# ==============================================================================

class AllTicketsRequestHandler(http.server.BaseHTTPRequestHandler):

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def send_html(self, html_content):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def get_auth_user(self):
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            user_id = db["sessions"].get(token)
            if user_id in db["users"]:
                return db["users"][user_id]
        return None

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, OPTIONS')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        user = self.get_auth_user()

        if path == "/" or path == "/index.html":
            self.send_html(HTML_PAGE)

        elif path == "/api/v1/auth/me":
            if not user:
                return self.send_json({"error": "Não autenticado."}, 401)
            return self.send_json(user)

        elif path == "/api/v1/events":
            self.send_json(list(db["events"].values()))

        elif path == "/api/v1/tickets":
            if not user:
                return self.send_json({"error": "Não autenticado."}, 401)
            tickets = list(db["tickets"].values())
            if user["role"] != UserRole.ADMIN:
                tickets = [t for t in tickets if t["user_id"] == user["id"]]
            self.send_json(tickets)

        elif path == "/api/v1/company-requests/my-status":
            if not user:
                return self.send_json({"error": "Não autenticado."}, 401)
            found_req = None
            for r in db["company_requests"].values():
                if r["user_id"] == user["id"]:
                    found_req = r
                    break
            if found_req:
                return self.send_json({"status": found_req["status"], "request": found_req})
            return self.send_json({"status": "NONE"})

        elif path == "/api/v1/company-requests":
            if not user or user["role"] != UserRole.ADMIN:
                return self.send_json({"error": "Acesso negado. Requer perfil ADMIN."}, 403)
            self.send_json(list(db["company_requests"].values()))

        elif path == "/api/v1/admin/stats":
            if not user or user["role"] != UserRole.ADMIN:
                return self.send_json({"error": "Acesso negado. Requer perfil ADMIN."}, 403)
            txs = list(db["financial_transactions"].values())
            total_vol = sum(t["total_amount"] for t in txs)
            platform = sum(t["platform_share_20"] for t in txs)
            self.send_json({"total_volume": total_vol, "platform_share": platform})

        elif path == "/api/v1/admin/users":
            if not user or user["role"] != UserRole.ADMIN:
                return self.send_json({"error": "Acesso negado. Requer perfil ADMIN."}, 403)
            self.send_json(list(db["users"].values()))

        else:
            self.send_json({"error": "Rota não encontrada"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length > 0 else b'{}'
        data = json.loads(body.decode('utf-8')) if body else {}

        user = self.get_auth_user()

        # ITEM 1: REGISTRO DE NOVOS USUÁRIOS (CRIAR CONTA)
        if path == "/api/v1/auth/register":
            name = data.get("name", "").strip()
            email = data.get("email", "").strip().lower()
            password = data.get("password", "").strip()

            if not name or not email or not password:
                return self.send_json({"error": "Todos os campos são obrigatórios."}, 400)

            # Verificar duplicação de e-mail
            for u in db["users"].values():
                if u["email"].lower() == email:
                    return self.send_json({"error": "Este e-mail já está cadastrado."}, 400)

            new_user_id = str(uuid.uuid4())
            new_user = {
                "id": new_user_id,
                "name": name,
                "email": email,
                "pass_hash": hash_password(password),
                "role": UserRole.PUBLICO
            }
            db["users"][new_user_id] = new_user

            token = str(uuid.uuid4())
            db["sessions"][token] = new_user_id
            return self.send_json({"token": token, "user": new_user}, 201)

        # LOGIN COM CRIPTOGRAFIA SHA-256
        elif path == "/api/v1/auth/login":
            email = data.get("email", "").strip().lower()
            pass_raw = data.get("password", "").strip()
            pass_hash = hash_password(pass_raw)

            found = None
            for u in db["users"].values():
                if u["email"].lower() == email and u["pass_hash"] == pass_hash:
                    found = u
                    break

            if not found:
                return self.send_json({"error": "E-mail ou senha incorretos."}, 401)

            token = str(uuid.uuid4())
            db["sessions"][token] = found["id"]
            return self.send_json({"token": token, "user": found})

        # 4.1 Cadastrar Novo Evento (Restrito a EMPRESA/ADMIN)
        elif path == "/api/v1/events":
            if not user or user["role"] not in [UserRole.EMPRESA, UserRole.ADMIN]:
                return self.send_json({"error": "Usuário não possui permissão de EMPRESA para criar eventos."}, 403)

            price = data.get("price")
            stock = data.get("stock")
            if price is None or stock is None or float(price) < 0 or int(stock) < 0:
                return self.send_json({"error": "Dados inválidos ou preço/estoque negativos."}, 422)

            new_id = str(uuid.uuid4())
            new_event = {
                "id": new_id,
                "company_id": user["id"],
                "company_name": user["name"],
                "title": data.get("title", "Novo Evento"),
                "category": data.get("category", "Shows e Festivais"),
                "price": float(price),
                "stock": int(stock),
                "likes_count": 0,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            db["events"][new_id] = new_event
            return self.send_json(new_event, 201)

        # 4.2 Comprar Ingresso (Checkout & Split Financeiro 80/20)
        elif path.startswith("/api/v1/events/") and path.endswith("/purchase"):
            if not user:
                return self.send_json({"error": "Você precisa estar logado para comprar ingressos."}, 401)

            event_id = path.split("/")[4]
            event = db["events"].get(event_id)
            if not event:
                return self.send_json({"error": "Evento não encontrado."}, 404)

            # CB-01 / RN-02: Controle de Estoque
            if event["stock"] <= 0:
                return self.send_json({"error": "Ingressos esgotados para este evento"}, 400)

            event["stock"] -= 1

            # RN-03: QR Hash SHA-256
            ticket_id = str(uuid.uuid4())
            raw_seed = f"{ticket_id}-{user['id']}-{event_id}-{datetime.now(timezone.utc).timestamp()}"
            qr_hash = f"QR-{hashlib.sha256(raw_seed.encode()).hexdigest()[:10].upper()}"

            ticket = {
                "id": ticket_id,
                "user_id": user["id"],
                "event_id": event_id,
                "event_title": event["title"],
                "qr_hash": qr_hash,
                "is_used": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            db["tickets"][ticket_id] = ticket
            db["tickets_by_hash"][qr_hash] = ticket

            # RN-01: Split 80% Produtor / 20% Plataforma (Gravado no BD Interno)
            total = float(event["price"])
            company_share = round(total * 0.80, 2)
            platform_share = round(total * 0.20, 2)

            tx_id = str(uuid.uuid4())
            db["financial_transactions"][tx_id] = {
                "id": tx_id,
                "ticket_id": ticket_id,
                "total_amount": total,
                "platform_share_20": platform_share,
                "company_share_80": company_share,
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            return self.send_json({
                "ticket": ticket,
                "financial_split": {
                    "total_amount": total,
                    "company_share_80": company_share,
                    "platform_share_20": platform_share
                }
            }, 201)

        # 4.3 Validar Ingresso na Portaria
        elif path == "/api/v1/tickets/validate":
            qr_hash = data.get("qr_hash")
            ticket = db["tickets_by_hash"].get(qr_hash)

            # CB-04: Hash Inexistente
            if not ticket:
                return self.send_json({"error": "Código Hash inexistente ou inválido."}, 404)

            # CB-02 / RN-04: Reuso de Ingresso (Antifraude)
            if ticket["is_used"]:
                return self.send_json({"error": "ALERTA: Ingresso já utilizado anteriormente na portaria"}, 400)

            ticket["is_used"] = True
            ticket["validated_at"] = datetime.now(timezone.utc).isoformat()

            return self.send_json({
                "status": "VALIDATED",
                "message": "Entrada liberada com sucesso!",
                "event_title": ticket["event_title"],
                "validated_at": ticket["validated_at"]
            }, 200)

        # ITEM 2: Solicitação de Parceria Empresarial
        elif path == "/api/v1/company-requests":
            if not user:
                return self.send_json({"error": "Você precisa estar autenticado."}, 401)

            # Verificar se já tem pendência
            for r in db["company_requests"].values():
                if r["user_id"] == user["id"] and r["status"] == "PENDENTE":
                    return self.send_json({"error": "Você já possui uma solicitação de parceria pendente em análise."}, 400)

            req_id = f"REQ-{len(db['company_requests']) + 101}"
            req = {
                "id": req_id,
                "user_id": user["id"],
                "company_name": data.get("company_name", ""),
                "cnpj": data.get("cnpj", ""),
                "email": user["email"],
                "description": data.get("description", ""),
                "status": "PENDENTE",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            db["company_requests"][req_id] = req
            return self.send_json(req, 201)

        else:
            self.send_json({"error": "Rota não encontrada"}, 404)

    def do_PATCH(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length > 0 else b'{}'
        data = json.loads(body.decode('utf-8')) if body else {}

        user = self.get_auth_user()

        # RN-05: Aprovação de Parceria Empresarial pelo Admin
        if path.startswith("/api/v1/company-requests/"):
            if not user or user["role"] != UserRole.ADMIN:
                return self.send_json({"error": "Acesso negado. Requer perfil ADMIN."}, 403)

            req_id = path.split("/")[4]
            req = db["company_requests"].get(req_id)
            if not req:
                return self.send_json({"error": "Solicitação não encontrada"}, 404)

            status = data.get("status", "APROVADO")
            req["status"] = status

            # PROMOÇÃO DE PAPEL PARA EMPRESA (ITEM 2)
            if status == "APROVADO" and req["user_id"] in db["users"]:
                db["users"][req["user_id"]]["role"] = UserRole.EMPRESA

            return self.send_json({"message": f"Solicitação {status} com sucesso!", "request": req}, 200)

        # RN-05: Promoção / Alteração de Permissão de Usuário pelo Admin
        elif path.startswith("/api/v1/admin/users/") and path.endswith("/role"):
            if not user or user["role"] != UserRole.ADMIN:
                return self.send_json({"error": "Acesso negado. Requer perfil ADMIN."}, 403)

            target_user_id = path.split("/")[5]
            target_user = db["users"].get(target_user_id)
            if not target_user:
                return self.send_json({"error": "Usuário não encontrado"}, 404)

            new_role = data.get("role")
            if new_role in [UserRole.PUBLICO, UserRole.EMPRESA, UserRole.ADMIN]:
                target_user["role"] = new_role
                return self.send_json(target_user, 200)
            else:
                return self.send_json({"error": "Papel inválido"}, 400)

# ==============================================================================
# 4. INICIALIZAÇÃO DO SERVIDOR (PORTA 8000)
# ==============================================================================

if __name__ == "__main__":
    PORT = 8000
    with socketserver.TCPServer(("", PORT), AllTicketsRequestHandler) as httpd:
        print(f"🚀 Servidor All Tickets rodando em http://localhost:{PORT}")
        print("💡 Teste o fluxo completo no navegador. Use os botões de Login Rápido ou o novo formulário de Criar Conta.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor encerrado.")