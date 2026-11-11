(() => {
    'use strict';
    // Validação da edição de paciente (antes inline em patient/edit.html).
    function init() {
        const form = document.getElementById('patientEditForm') || document.querySelector('.main-content form');
        if (!form) return;
        const fields = [
            { id: 'nome', feedback: 'nome-feedback' },
            { id: 'prontuario', feedback: 'prontuario-feedback' },
            { id: 'data_nascimento', feedback: 'data_nascimento-feedback' },
            { id: 'sexo_m', feedback: 'sexo-feedback', radio: true },
            { id: 'sexo_f', feedback: 'sexo-feedback', radio: true },
            { id: 'cns', feedback: 'cns-feedback' },
            { id: 'nome_mae', feedback: 'nome_mae-feedback' },
            { id: 'endereco', feedback: 'endereco-feedback' },
            { id: 'cidade', feedback: 'cidade-feedback' },
            { id: 'estado', feedback: 'estado-feedback' },
            { id: 'contato', feedback: 'contato-feedback' },
            { id: 'diagnostico', feedback: 'diagnostico-feedback' },
            { id: 'cid', feedback: 'cid-feedback' }
        ];

        // Limpa mensagens ao carregar
        fields.forEach(f => {
            document.getElementById(f.feedback).style.display = 'none';
            const el = document.getElementById(f.id);
            if (el) el.classList.remove('is-invalid');
        });

        // Função para mostrar/ocultar feedback customizado
        function showFeedback(field, show) {
            const feedback = document.getElementById(field.feedback);
            const el = document.getElementById(field.id);
            if (show) {
                if (el) el.classList.add('is-invalid');
                if (feedback) feedback.style.display = 'block';
            } else {
                if (el) el.classList.remove('is-invalid');
                if (feedback) feedback.style.display = 'none';
            }
        }

        // Validação individual
        fields.forEach(field => {
            const el = document.getElementById(field.id);
            if (!el) return;
            if (field.radio) {
                el.addEventListener('change', function () {
                    const checked = document.querySelector('input[name="sexo"]:checked');
                    showFeedback(field, !checked);
                });
            } else {
                el.addEventListener('blur', function () {
                    if (el.value.trim() === '') {
                        showFeedback(field, false);
                    } else if (!el.checkValidity()) {
                        showFeedback(field, true);
                    } else {
                        showFeedback(field, false);
                    }
                });
                el.addEventListener('input', function () {
                    if (el.value.trim() === '' || el.checkValidity()) {
                        showFeedback(field, false);
                    }
                });
            }
        });

        // Validação no submit
        form.addEventListener('submit', function (event) {
            let isValid = true;
            fields.forEach(field => {
                const el = document.getElementById(field.id);
                if (!el) return;
                if (field.radio) {
                    const checked = document.querySelector('input[name="sexo"]:checked');
                    if (!checked) {
                        showFeedback(field, true);
                        isValid = false;
                    } else {
                        showFeedback(field, false);
                    }
                } else {
                    if (el.value.trim() === '' || !el.checkValidity()) {
                        showFeedback(field, true);
                        isValid = false;
                    } else {
                        showFeedback(field, false);
                    }
                }
            });
            if (!isValid) {
                event.preventDefault();
                event.stopPropagation();
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init, { once: true });
    } else {
        init();
    }
})();

(() => {
  'use strict';
  // Máscaras de preenchimento (mesmas regras do cadastro novo) e proteção
  // contra duplo envio na edição de paciente.
  function onInput(id, format) {
    const input = document.getElementById(id);
    if (!input) return;
    input.addEventListener('input', () => { input.value = format(input.value); });
  }

  function formatPhone(value) {
    const digits = value.replace(/\D/g, '').slice(0, 11);
    if (!digits) return '';
    if (digits.length <= 2) return `(${digits}`;
    const area = digits.slice(0, 2);
    const local = digits.slice(2);
    const split = local.length > 8 ? 5 : 4;
    return `(${area})${local.slice(0, split)}${local.length > split ? `-${local.slice(split)}` : ''}`;
  }

  function init() {
    const form = document.getElementById('patientEditForm');
    if (!form) return;
    onInput('cns', value => value.replace(/\D/g, '').slice(0, 15));
    onInput('contato', formatPhone);
    onInput('cid', value => value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 4));
    onInput('estado', value => value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 2));
    form.addEventListener('submit', event => {
      if (event.defaultPrevented) return;
      if (form.dataset.submitting === '1') { event.preventDefault(); return; }
      form.dataset.submitting = '1';
      form.querySelectorAll('[type="submit"]').forEach(button => button.classList.add('disabled'));
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
