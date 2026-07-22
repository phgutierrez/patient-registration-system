(() => {
  'use strict';

  const app = document.getElementById('surgeryRequestApp');
  if (!app) return;

  const form = app.querySelector('.surgery-form');
  const storageKey =
    `cirurgiaModelos:${app.dataset.specialty}:u${app.dataset.userId}`;
  const clinicalFields = [
    'sinais_sintomas',
    'condicoes_justificativa',
    'resultados_diagnosticos',
    'procedimento_solicitado',
    'codigo_procedimento',
    'tipo_cirurgia',
    'internar_antes',
    'aparelhos_especiais',
    'reserva_sangue',
    'quantidade_sangue',
    'raio_x',
    'reserva_uti',
    'duracao_prevista',
    'evolucao_internacao',
    'prescricao_internacao',
    'exames_preop',
    'opme_items',
    'opme_outro',
  ];

  let editingId = null;
  let modal = null;

  const escapeHtml = value => String(value ?? '').replace(
    /[&<>"']/g,
    char => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    })[char],
  );

  function procedureCodeMap() {
    try {
      return JSON.parse(
        document.getElementById('procedureCodeMap')?.textContent || '{}',
      );
    } catch {
      return {};
    }
  }

  function updateProcedure() {
    const select = document.getElementById('procedimento_select');
    document.getElementById('codigo_sus_input').value =
      procedureCodeMap()[select.value] || '';
  }

  function filterProcedures() {
    const input = document.getElementById('procedureSearch');
    const select = document.getElementById('procedimento_select');
    const term = input.value.trim().toLocaleLowerCase('pt-BR');
    let count = 0;
    [...select.options].forEach((option, index) => {
      const visible = (
        index === 0
        || !term
        || option.text.toLocaleLowerCase('pt-BR').includes(term)
      );
      option.hidden = !visible;
      if (visible && index > 0) count += 1;
    });
    document.getElementById('procedureFilterHint').textContent =
      term ? `${count} procedimento(s) encontrado(s)` : '';
  }

  function updateBlood() {
    const checked = document.getElementById('reserva_sangue_check').checked;
    const group = document.getElementById('bloodQuantityGroup');
    const input = document.getElementById('quantidade_sangue_input');
    group.hidden = !checked;
    input.disabled = !checked;
    if (!checked) input.value = '';
  }

  function updateOpme(event) {
    const boxes = [...form.querySelectorAll('[name="opme_items"]')];
    const notApplicable = boxes.find(
      box => box.value.toLocaleLowerCase('pt-BR') === 'não se aplica',
    );
    if (
      event?.target === notApplicable
      && notApplicable.checked
    ) {
      boxes.forEach(box => {
        if (box !== notApplicable) box.checked = false;
      });
    } else if (
      event?.target?.checked
      && notApplicable
      && event.target !== notApplicable
    ) {
      notApplicable.checked = false;
    }
  }

  function pickClinical(source) {
    const result = {};
    clinicalFields.forEach(name => {
      if (Object.prototype.hasOwnProperty.call(source, name)) {
        result[name] = source[name];
      }
    });

    if (!Array.isArray(result.opme_items) && source.opme) {
      const known = [...form.querySelectorAll('[name="opme_items"]')]
        .map(field => field.value);
      let remaining = String(source.opme);
      result.opme_items = known.filter(value => remaining.includes(value));
      result.opme_items.forEach(value => {
        remaining = remaining.replace(value, ' ');
      });
      const other = remaining
        .replace(/Outro:/gi, ' ')
        .replace(/[|,;]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
      if (
        !result.opme_outro
        && other
        && !/^n[aã]o se aplica$/i.test(other)
      ) {
        result.opme_outro = other;
      }
    }
    return result;
  }

  function loadModels() {
    try {
      const parsed = JSON.parse(localStorage.getItem(storageKey) || '[]');
      if (!Array.isArray(parsed)) return [];
      return parsed.map(model => ({
        ...model,
        version: 2,
        dados: pickClinical(model.dados || {}),
      }));
    } catch (error) {
      console.warn('Modelos clínicos inválidos', error);
      return [];
    }
  }

  function saveModels(models) {
    localStorage.setItem(storageKey, JSON.stringify(models));
  }

  function collectClinical() {
    const data = new FormData(form);
    const result = {};
    clinicalFields.forEach(name => {
      if (name === 'opme_items') {
        result[name] = data.getAll(name);
      } else if (
        ['internar_antes', 'reserva_sangue', 'raio_x', 'reserva_uti']
          .includes(name)
      ) {
        result[name] = data.has(name);
      } else {
        result[name] = data.get(name) || '';
      }
    });
    return result;
  }

  function feedback(message, type = 'success') {
    document.getElementById('modelFeedback').innerHTML =
      `<div class="alert alert-${type} py-2">${escapeHtml(message)}</div>`;
  }

  function renderModels() {
    const term = document.getElementById('modelSearch')
      .value.trim().toLocaleLowerCase('pt-BR');
    const models = loadModels()
      .filter(model => (
        !term
        || model.nome.toLocaleLowerCase('pt-BR').includes(term)
        || String(model.dados.procedimento_solicitado || '')
          .toLocaleLowerCase('pt-BR').includes(term)
      ))
      .sort(
        (first, second) =>
          new Date(second.atualizadoEm || second.dataCriacao || 0)
          - new Date(first.atualizadoEm || first.dataCriacao || 0),
      );
    const list = document.getElementById('modelsList');
    if (!models.length) {
      list.innerHTML =
        '<div class="text-center text-muted py-4">Nenhum modelo encontrado.</div>';
      return;
    }
    list.innerHTML = models.map(model => `
      <article class="model-card">
        <div>
          <strong>${escapeHtml(model.nome)}</strong>
          <small>
            ${escapeHtml(
              model.dados.procedimento_solicitado
              || 'Procedimento não informado',
            )} · ${model.usosCount || 0} uso(s)
          </small>
        </div>
        <div class="btn-group btn-group-sm">
          <button class="btn btn-primary"
                  data-model-apply="${escapeHtml(model.id)}">Aplicar</button>
          <button class="btn btn-outline-secondary"
                  data-model-edit="${escapeHtml(model.id)}">Atualizar</button>
          <button class="btn btn-outline-danger"
                  data-model-delete="${escapeHtml(model.id)}"
                  aria-label="Excluir"><i class="fas fa-trash"></i></button>
        </div>
      </article>
    `).join('');
  }

  function setField(name, value) {
    const fields = [...form.querySelectorAll(`[name="${name}"]`)];
    if (!fields.length) return;
    if (name === 'opme_items') {
      fields.forEach(field => {
        field.checked = Array.isArray(value) && value.includes(field.value);
      });
    } else if (fields[0].type === 'radio') {
      fields.forEach(field => {
        field.checked = field.value === value;
      });
    } else if (fields[0].type === 'checkbox') {
      fields[0].checked = Boolean(value);
    } else {
      fields[0].value = value ?? '';
    }
  }

  function applyFields(model) {
    Object.entries(model.dados).forEach(
      ([name, value]) => setField(name, value),
    );
    updateProcedure();
    updateBlood();
    updateOpme();
  }

  function applyModel(id) {
    const models = loadModels();
    const index = models.findIndex(
      model => String(model.id) === String(id),
    );
    if (index < 0) return;
    applyFields(models[index]);
    models[index].usosCount = (models[index].usosCount || 0) + 1;
    models[index].ultimoUso = new Date().toISOString();
    saveModels(models);
    modal.hide();
    document.getElementById('clinicalSection')
      .scrollIntoView({behavior: 'smooth'});
  }

  function resetEditingState() {
    editingId = null;
    document.getElementById('modelName').value = '';
    document.getElementById('saveAsModelButton').innerHTML =
      '<i class="fas fa-save"></i> Salvar como modelo';
  }

  function persistModel() {
    const name = document.getElementById('modelName').value.trim();
    if (!name) {
      feedback('Informe um nome para o modelo.', 'warning');
      return;
    }
    const models = loadModels();
    const duplicate = models.find(model => (
      model.nome.toLocaleLowerCase('pt-BR')
        === name.toLocaleLowerCase('pt-BR')
      && String(model.id) !== String(editingId)
    ));
    if (duplicate) {
      feedback('Já existe um modelo com esse nome.', 'warning');
      return;
    }

    const now = new Date().toISOString();
    if (editingId) {
      const index = models.findIndex(
        model => String(model.id) === String(editingId),
      );
      if (index < 0) {
        feedback('Modelo não encontrado.', 'danger');
        return;
      }
      models[index] = {
        ...models[index],
        nome: name,
        dados: collectClinical(),
        atualizadoEm: now,
        version: 2,
      };
      feedback(`Modelo "${name}" atualizado.`);
    } else {
      models.push({
        id: `mdl_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
        nome: name,
        dados: collectClinical(),
        dataCriacao: now,
        atualizadoEm: now,
        usosCount: 0,
        version: 2,
      });
      feedback(`Modelo "${name}" salvo.`);
    }
    saveModels(models);
    resetEditingState();
    renderModels();
  }

  function editModel(id) {
    const model = loadModels().find(
      item => String(item.id) === String(id),
    );
    if (!model) return;
    editingId = model.id;
    applyFields(model);
    document.getElementById('modelName').value = model.nome;
    document.getElementById('saveAsModelButton').innerHTML =
      '<i class="fas fa-save"></i> Atualizar modelo';
    modal.hide();
    document.getElementById('clinicalSection')
      .scrollIntoView({behavior: 'smooth'});
  }

  function deleteModel(id) {
    const models = loadModels();
    const model = models.find(item => String(item.id) === String(id));
    if (
      !model
      || !window.confirm(`Excluir o modelo "${model.nome}"?`)
    ) {
      return;
    }
    saveModels(
      models.filter(item => String(item.id) !== String(id)),
    );
    if (String(editingId) === String(id)) resetEditingState();
    feedback('Modelo excluído.');
    renderModels();
  }

  document.addEventListener('DOMContentLoaded', () => {
    modal = bootstrap.Modal.getOrCreateInstance(
      document.getElementById('modelsModal'),
    );
    document.getElementById('procedimento_select')
      .addEventListener('change', updateProcedure);
    document.getElementById('procedureSearch')
      .addEventListener('input', filterProcedures);
    document.getElementById('reserva_sangue_check')
      .addEventListener('change', updateBlood);
    form.querySelectorAll('[name="opme_items"]').forEach(
      box => box.addEventListener('change', updateOpme),
    );

    document.getElementById('openModelsButton')
      .addEventListener('click', () => {
        resetEditingState();
        renderModels();
        modal.show();
      });
    document.getElementById('saveAsModelButton')
      .addEventListener('click', () => {
        if (!editingId) document.getElementById('modelName').value = '';
        renderModels();
        modal.show();
        setTimeout(
          () => document.getElementById('modelName').focus(),
          250,
        );
      });
    document.getElementById('persistModelButton')
      .addEventListener('click', persistModel);
    document.getElementById('modelSearch')
      .addEventListener('input', renderModels);
    document.getElementById('modelsList')
      .addEventListener('click', event => {
        const apply = event.target.closest('[data-model-apply]');
        const edit = event.target.closest('[data-model-edit]');
        const remove = event.target.closest('[data-model-delete]');
        if (apply) applyModel(apply.dataset.modelApply);
        if (edit) editModel(edit.dataset.modelEdit);
        if (remove) deleteModel(remove.dataset.modelDelete);
      });

    const observer = new IntersectionObserver(
      entries => entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        document.querySelectorAll('.section-nav a').forEach(link => {
          link.classList.toggle(
            'active',
            link.getAttribute('href') === `#${entry.target.id}`,
          );
        });
      }),
      {rootMargin: '-25% 0px -65%'},
    );
    document.querySelectorAll('.form-section')
      .forEach(section => observer.observe(section));

    updateProcedure();
    updateBlood();
    updateOpme();

    const firstError = document.querySelector('.is-invalid');
    if (firstError) {
      document.querySelector('.error-summary')?.focus();
      setTimeout(() => firstError.focus(), 150);
    }
  });
})();

