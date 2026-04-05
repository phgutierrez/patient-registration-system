# Guia Curto de Bootstrap Admin

Este guia cobre a criação segura do primeiro administrador via variáveis `ADMIN_BOOTSTRAP_*`.
O objetivo é permitir a primeira entrada sem recriar o problema de credenciais padrão previsíveis.

## Variáveis disponíveis

| Variável | Obrigatória? | Uso |
|---|---|---|
| `ADMIN_BOOTSTRAP_USERNAME` | Sim, na primeira subida sem admins | Login do primeiro administrador |
| `ADMIN_BOOTSTRAP_PASSWORD` | Sim, na primeira subida sem admins | Senha inicial forte do primeiro administrador |
| `ADMIN_BOOTSTRAP_FULL_NAME` | Opcional | Nome completo exibido na interface |
| `ADMIN_BOOTSTRAP_SPECIALTY` | Opcional | Especialidade vinculada ao admin bootstrap; padrão `ortopedia` |

## Comportamento do sistema

- O bootstrap só roda quando **não existe nenhum usuário admin** no banco.
- Se já houver um admin cadastrado, as variáveis `ADMIN_BOOTSTRAP_*` são ignoradas.
- O usuário criado via bootstrap entra com `must_change_password=true`.
- No primeiro login, o sistema obriga a troca de senha antes de liberar o dashboard.

## Sequência segura de primeira implantação

1. Copie `.env.example` para `.env`.
2. Preencha pelo menos:

```properties
ADMIN_BOOTSTRAP_USERNAME=admin.local
ADMIN_BOOTSTRAP_PASSWORD=use-uma-senha-forte-e-unica
ADMIN_BOOTSTRAP_FULL_NAME=Administrador do Sistema
ADMIN_BOOTSTRAP_SPECIALTY=ortopedia
```

3. Ajuste `SERVER_HOST`, `DESKTOP_MODE` e integrações opcionais conforme o ambiente.
4. Em produção, defina também um `SECRET_KEY` forte e estável.
5. Inicie o sistema e faça o primeiro login com o usuário bootstrap.
6. Troque a senha quando o sistema solicitar.
7. Crie os demais usuários pela interface administrativa.
8. Remova ou esvazie `ADMIN_BOOTSTRAP_PASSWORD` após confirmar que existe ao menos um admin persistido.

## Quando limpar as variáveis

Após o primeiro acesso bem-sucedido e a criação/validação de um admin persistido:

- remova `ADMIN_BOOTSTRAP_PASSWORD` do `.env`, ou
- deixe todas as `ADMIN_BOOTSTRAP_*` vazias.

Isso reduz o risco de exposição operacional em servidor, suporte remoto e cópia de arquivos de configuração.

## Expectativa de primeiro login

- Informar usuário e senha bootstrap.
- Ser redirecionado para a tela de troca obrigatória de senha.
- Definir nova senha forte.
- Prosseguir para o dashboard.

## Mínimo esperado para produção

- `SECRET_KEY` forte e estável configurada fora de placeholders.
- `SESSION_COOKIE_SECURE=true` quando houver HTTPS real.
- `SECURITY_HSTS_ENABLED=true` apenas atrás de TLS confiável.
- `ADMIN_BOOTSTRAP_PASSWORD` removida depois da criação inicial.
- `.env` armazenado com permissão restrita no host.

## Rotação recomendada após o bootstrap

- Valide o primeiro login.
- Troque imediatamente a senha bootstrap.
- Crie um segundo admin operacional, se fizer sentido para contingência.
- Remova o segredo bootstrap do ambiente.
- Registre internamente quem executou a implantação e quando.
