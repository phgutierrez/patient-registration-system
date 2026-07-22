(() => {
  'use strict';

  const app = document.getElementById('patientNewApp');
  if (!app) return;

  const form = document.getElementById('patientForm');
  const searchButton = document.getElementById('btnBuscaAccess');
  const searchResult = document.getElementById('searchResult');
  const errorSummary = document.getElementById('formErrorSummary');
  const saveButton = document.getElementById('savePatientButton');
  const fields = [
    ['prontuario', 'Prontuário'], ['nome', 'Nome do paciente'],
    ['data_nascimento', 'Data de nascimento'], ['sexo_m', 'Sexo'],
    ['nome_mae', 'Nome da mãe'], ['cns', 'CNS'], ['cidade', 'Cidade'],
    ['contato', 'Contato'], ['diagnostico', 'Diagnóstico'], ['cid', 'CID'],
  ];

  function groupFor(element) {
    return element?.closest('.field-group') || element?.closest('.lookup-controls');
  }

  function setInvalid(element, invalid) {
    if (!element) return;
    element.classList.toggle('is-invalid', invalid);
    groupFor(element)?.classList.toggle('is-invalid', invalid);
    element.setAttribute('aria-invalid', invalid ? 'true' : 'false');
  }

  function parseBrazilianDate(value) {
    const match = String(value || '').match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (!match) return null;
    const day = Number(match[1]);
    const month = Number(match[2]);
    const year = Number(match[3]);
    const parsed = new Date(year, month - 1, day);
    if (year < 1900 || parsed > new Date() || parsed.getFullYear() !== year || parsed.getMonth() !== month - 1 || parsed.getDate() !== day) return null;
    return parsed;
  }

  function updateAge() {
    const input = document.getElementById('data_nascimento');
    const output = document.getElementById('idade');
    const birth = parseBrazilianDate(input.value);
    output.value = '';
    if (!birth) return;
    const today = new Date();
    let years = today.getFullYear() - birth.getFullYear();
    let months = today.getMonth() - birth.getMonth();
    if (today.getDate() < birth.getDate()) months -= 1;
    if (months < 0) { years -= 1; months += 12; }
    output.value = `${years}a ${months}m`;
  }

  function formatBirthInput(input) {
    const digits = input.value.replace(/\D/g, '').slice(0, 8);
    input.value = [digits.slice(0, 2), digits.slice(2, 4), digits.slice(4, 8)].filter(Boolean).join('/');
    updateAge();
  }

  function formatPhone(input) {
    const digits = input.value.replace(/\D/g, '').slice(0, 11);
    if (!digits) { input.value = ''; return; }
    if (digits.length <= 2) { input.value = `(${digits}`; return; }
    const area = digits.slice(0, 2);
    const local = digits.slice(2);
    const split = local.length > 8 ? 5 : 4;
    input.value = `(${area})${local.slice(0, split)}${local.length > split ? `-${local.slice(split)}` : ''}`;
  }

  function normalizeKey(value) {
    return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]/gi, '').toLowerCase();
  }

  function getValue(data, aliases) {
    if (!data) return null;
    for (const alias of aliases) {
      if (data[alias] !== undefined && data[alias] !== null) return data[alias];
      const normalized = normalizeKey(alias);
      const key = Object.keys(data).find((candidate) => normalizeKey(candidate) === normalized);
      if (key && data[key] !== null) return data[key];
    }
    return null;
  }

  function assignValue(id, value, eventName = 'input') {
    if (value === null || value === undefined || value === '') return;
    const input = document.getElementById(id);
    if (!input) return;
    input.value = String(value);
    input.dispatchEvent(new Event(eventName, { bubbles: true }));
  }

  function formatAccessDate(value) {
    const raw = String(value || '').trim();
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(raw)) return raw;
    const iso = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (iso) return `${iso[3]}/${iso[2]}/${iso[1]}`;
    const parsed = new Date(raw);
    if (Number.isNaN(parsed.getTime())) return '';
    return `${String(parsed.getDate()).padStart(2, '0')}/${String(parsed.getMonth() + 1).padStart(2, '0')}/${parsed.getFullYear()}`;
  }

  function fillFromAccess(data) {
    assignValue('nome', getValue(data, ['nome', 'nome do paciente', 'nome paciente']));
    assignValue('data_nascimento', formatAccessDate(getValue(data, ['data_nascimento', 'data nascimento', 'datanascimento'])));
    assignValue('nome_mae', getValue(data, ['nome_mae', 'nome da mãe', 'nome da mae', 'nome mae', 'nomemae']));
    assignValue('cns', getValue(data, ['cns', 'NºCartSUS', 'nº cart sus', 'ncartsus']));
    assignValue('endereco', getValue(data, ['endereco', 'endereço']));
    assignValue('cidade', getValue(data, ['cidade', 'Municip', 'municipio']));
    assignValue('contato', getValue(data, ['contato', 'Telefone', 'telefone', 'fone']));

    const sex = String(getValue(data, ['sexo', 'SEXO', 'genero']) || '').toUpperCase();
    const radio = sex.includes('FEM') || sex === 'F' ? document.getElementById('sexo_f') :
      (sex.includes('MAS') || sex === 'M' ? document.getElementById('sexo_m') : null);
    if (radio) {
      radio.checked = true;
      radio.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }

  function renderSearchResult(type, message, hint = '', retry = false) {
    searchResult.replaceChildren();
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    const content = document.createElement('div');
    content.className = 'search-result-content';
    const icon = document.createElement('i');
    icon.className = type === 'success' ? 'fas fa-circle-check' : type === 'danger' ? 'fas fa-triangle-exclamation' : 'fas fa-circle-info';
    const copy = document.createElement('div');
    const strong = document.createElement('strong');
    strong.textContent = message;
    copy.appendChild(strong);
    if (hint) {
      const small = document.createElement('small');
      small.textContent = hint;
      copy.appendChild(small);
    }
    if (retry) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'btn btn-sm btn-outline-danger retry-access';
      button.innerHTML = '<i class="fas fa-rotate-right"></i> Tentar novamente';
      button.addEventListener('click', searchAccess);
      copy.appendChild(button);
    }
    content.append(icon, copy);
    alert.appendChild(content);
    searchResult.appendChild(alert);
  }

  function setSearching(searching) {
    searchButton.disabled = searching;
    searchButton.innerHTML = searching ? '<i class="fas fa-spinner fa-spin"></i><span>Buscando…</span>' : '<i class="fas fa-search"></i><span>Buscar</span>';
  }

  async function searchAccess() {
    const recordInput = document.getElementById('prontuario');
    const record = recordInput.value.trim();
    if (!record) {
      setInvalid(recordInput, true);
      renderSearchResult('warning', 'Informe o prontuário antes de buscar.');
      recordInput.focus();
      return;
    }

    setInvalid(recordInput, false);
    setSearching(true);
    searchResult.replaceChildren();
    try {
      const response = await fetch(`${app.dataset.accessUrl}?prontuario=${encodeURIComponent(record)}`, { headers: { Accept: 'application/json' } });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok && payload.code !== 'PATIENT_NOT_FOUND') throw Object.assign(new Error(payload.message || `Falha na busca (HTTP ${response.status}).`), { payload });
      if (payload.found) {
        fillFromAccess(payload.data);
        renderSearchResult('success', 'Paciente encontrado. Os dados disponíveis foram preenchidos.', payload.source === 'memory_cache' ? 'Resultado obtido do cache local.' : 'Revise os dados antes de cadastrar.');
      } else {
        renderSearchResult('info', payload.message || 'Prontuário não localizado no banco do CPAM.', payload.hint || 'Confira o número ou preencha o cadastro manualmente.');
      }
    } catch (error) {
      const details = error.payload || {};
      renderSearchResult('danger', details.message || error.message, details.hint || 'Você pode preencher o cadastro manualmente e tentar novamente depois.', true);
    } finally {
      setSearching(false);
    }
  }

  function validateField(id) {
    if (id === 'sexo_m') {
      const radio = document.getElementById('sexo_m');
      const invalid = !form.querySelector('input[name="sexo"]:checked');
      setInvalid(radio, invalid);
      document.querySelector('.sex-field')?.classList.toggle('is-invalid', invalid);
      return !invalid;
    }
    const input = document.getElementById(id);
    if (!input) return true;
    let valid = input.checkValidity();
    if (id === 'data_nascimento') valid = Boolean(parseBrazilianDate(input.value));
    setInvalid(input, !valid);
    return valid;
  }

  function validateForm() {
    const invalid = fields.filter(([id]) => !validateField(id));
    const list = errorSummary.querySelector('ul');
    list.replaceChildren();
    invalid.forEach(([id, label]) => {
      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = `#${id}`;
      link.textContent = label;
      link.addEventListener('click', (event) => {
        event.preventDefault();
        document.getElementById(id)?.focus();
      });
      item.appendChild(link);
      list.appendChild(item);
    });
    errorSummary.classList.toggle('d-none', invalid.length === 0);
    if (invalid.length) {
      errorSummary.focus();
      document.getElementById(invalid[0][0])?.focus({ preventScroll: true });
      errorSummary.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    return invalid.length === 0;
  }

  document.getElementById('data_nascimento').addEventListener('input', (event) => formatBirthInput(event.target));
  document.getElementById('cns').addEventListener('input', (event) => { event.target.value = event.target.value.replace(/\D/g, '').slice(0, 15); });
  document.getElementById('contato').addEventListener('input', (event) => formatPhone(event.target));
  document.getElementById('cid').addEventListener('input', (event) => { event.target.value = event.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 4); });
  document.getElementById('prontuario').addEventListener('keydown', (event) => { if (event.key === 'Enter') { event.preventDefault(); searchAccess(); } });
  searchButton.addEventListener('click', searchAccess);
  window.buscarPacienteAccess = searchAccess;

  fields.forEach(([id]) => {
    const input = document.getElementById(id);
    if (!input) return;
    const eventName = id === 'sexo_m' ? 'change' : 'input';
    input.addEventListener(eventName, () => {
      if (id === 'sexo_m') validateField(id);
      else if (input.value.trim() === '' || input.checkValidity()) setInvalid(input, false);
    });
  });
  document.getElementById('sexo_f').addEventListener('change', () => validateField('sexo_m'));

  const nameInput = document.getElementById('nome');
  const nameNotice = document.getElementById('nameExists');
  nameInput.addEventListener('input', () => nameNotice.classList.add('d-none'));
  nameInput.addEventListener('blur', async () => {
    const name = nameInput.value.trim();
    nameNotice.classList.add('d-none');
    if (!name) return;
    try {
      const response = await fetch(`${app.dataset.nameCheckUrl}?name=${encodeURIComponent(name)}`, { headers: { Accept: 'application/json' } });
      if (!response.ok) return;
      const payload = await response.json();
      nameNotice.classList.toggle('d-none', !payload.exists);
    } catch (_) {
      nameNotice.classList.add('d-none');
    }
  });

  form.addEventListener('submit', (event) => {
    if (!validateForm()) {
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    saveButton.disabled = true;
    saveButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cadastrando…';
  });

  formatBirthInput(document.getElementById('data_nascimento'));
  formatPhone(document.getElementById('contato'));
})();
