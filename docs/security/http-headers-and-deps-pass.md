# Segunda Passada: Headers HTTP e Dependências Vulneráveis

Esta passada traduz o endurecimento de navegador e a atualização de dependências em um pacote pronto para implementação e validação.

## Estado atual resumido

- Headers de segurança foram centralizados em um hook global de resposta.
- `Cache-Control: no-store` passou a ser aplicado em respostas autenticadas, JSON com dados clínicos e PDFs protegidos.
- CSP foi introduzida em modo `Report-Only` para evitar quebrar templates ainda dependentes de inline JS/CSS.
- `Strict-Transport-Security` continua desligado por padrão e deve ser habilitado apenas atrás de HTTPS real.
- Dependências de maior prioridade foram revisadas com base no PyPI oficial em **3 de abril de 2026**.

## Baseline de headers

| Header | Valor base | Observação |
|---|---|---|
| `X-Frame-Options` | `DENY` | Bloqueia clickjacking por framing do app |
| `X-Content-Type-Options` | `nosniff` | Evita MIME sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Reduz vazamento de contexto em navegação cruzada |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Nega APIs sensíveis não usadas |
| `Cross-Origin-Opener-Policy` | `same-origin` | Isola contexto de navegação |
| `Cross-Origin-Resource-Policy` | `same-origin` | Restringe consumo cross-origin de recursos |
| `Cache-Control` | `no-store` | Obrigatório para páginas autenticadas, JSON clínico e PDFs protegidos |
| `Content-Security-Policy-Report-Only` | política compatível com o app atual | Passo intermediário antes da CSP enforcement |

## Política CSP inicial

A política inicial adotada nesta passada é compatibilidade-first:

```text
default-src 'self';
frame-ancestors 'none';
object-src 'none';
base-uri 'self';
form-action 'self';
img-src 'self' data:;
font-src 'self' https: data:;
frame-src 'self' https://docs.google.com;
script-src 'self' 'unsafe-inline';
style-src 'self' 'unsafe-inline' https:;
connect-src 'self' https://docs.google.com https://calendar.google.com
```

### Estratégia de rollout da CSP

1. Manter `Content-Security-Policy-Report-Only` nesta fase.
2. Levantar violações reais em templates e integrações.
3. Remover inline JS/CSS de forma incremental.
4. Só depois migrar para CSP enforcement.

## Estratégia de HSTS

- Não habilitar `Strict-Transport-Security` em localhost, LAN HTTP pura ou qualquer ambiente sem TLS confiável.
- Habilitar via flag (`SECURITY_HSTS_ENABLED=true`) apenas quando:
  - o tráfego externo já entrar por HTTPS real,
  - existir proxy/balanceador confiável,
  - e o time de implantação souber exatamente quais domínios receberão a política.

## Dependências priorizadas

| Pacote | Antes | Alvo adotado | Fonte oficial | Observação |
|---|---|---|---|---|
| `Werkzeug` | `3.1.3` | `3.1.8` | PyPI oficial, release em **2 abr 2026** | Substitui o alvo `3.1.7` do plano por já haver release mais recente no dia da implementação |
| `requests` | `2.32.4` | `2.33.1` | PyPI oficial, release em **30 mar 2026** | Exige `Python >=3.10`, então scripts/docs precisam refletir esse piso |

## Impacto de compatibilidade

- A atualização para `requests 2.33.1` eleva o piso de instalação do projeto para **Python 3.10+**.
- O repositório precisa manter documentação, scripts de setup e ambiente CI alinhados com esse requisito.

## Verificações obrigatórias desta passada

### Dependências

```bash
./.venv311/bin/python -m pip_audit -r requirements.txt --no-deps --disable-pip
./.venv311/bin/python -m compileall src server.py init_db.py setup_init_data.py
```

### Smoke tests funcionais

- Login com senha correta/incorreta.
- Acesso à agenda autenticada.
- Fluxo de integração com Google Forms quando configurado.
- Download/view de PDF protegido.
- Rotas protegidas de paciente/cirurgia com escopo por especialidade.

### Conferência de headers

- `/`
- `/agenda`
- uma rota protegida de paciente autenticada
- uma rota protegida de PDF autenticada

Verificar presença de:

- `X-Frame-Options`
- `X-Content-Type-Options`
- `Referrer-Policy`
- `Permissions-Policy`
- `Cross-Origin-Opener-Policy`
- `Cross-Origin-Resource-Policy`
- `Content-Security-Policy-Report-Only`
- `Cache-Control: no-store` nas superfícies clínicas/autenticadas

## Próximos passos recomendados

- Remover inline JS/CSS dos templates para preparar enforcement de CSP.
- Revisar `shutdown`/rotas operacionais em conjunto com a passada `V-014`.
- Levar `pip-audit` e smoke checks para CI (`V-015`).
