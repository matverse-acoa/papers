# Deploy com Testes e Rastreamento

Módulo de deploy automatizado para o repositório `matverse-acoa/papers`, com validação
rigorosa, testes automatizados e rastreamento criptográfico completo.

## 📋 Funcionalidades

- ✅ **Testes automatizados**: LaTeX, Python, segurança básica
- 🔐 **Rastreamento criptográfico**: SHA3-512, assinatura Ed25519, trace ID único
- 🧪 **Validação Ω-Gate**: Integração com core MatVerse para decisão de admissibilidade
- 📤 **Publicação multi-plataforma**: Zenodo, GitHub, ORCID
- 📊 **Relatório detalhado**: Logs estruturados em JSON para auditoria
- 🚀 **Pipeline completo**: Do teste ao deploy com rollback automático em falhas

## 🚀 Uso rápido

```bash
# 1. Instalar dependências
pip install -r requirements-deploy.txt

# 2. Configurar variáveis de ambiente
export ZENODO_TOKEN="seu_token_aqui"
export ZENODO_SANDBOX="true"  # use sandbox.zenodo.org para testes
export MATVERSE_CORE_URL="https://core.matverse.acoa.io"

# 3. Executar deploy
python deploy_with_tests_and_tracing.py
```

## ⚙️ Configuração

### Variáveis de ambiente

| Variável | Descrição | Padrão |
| --- | --- | --- |
| `ZENODO_TOKEN` | Token da API Zenodo | Obrigatório para Zenodo |
| `ZENODO_SANDBOX` | Usar sandbox do Zenodo | `true` |
| `MATVERSE_CORE_URL` | URL do core MatVerse | `https://core.matverse.acoa.io` |
| `ENABLE_ZENODO` | Habilitar publicação Zenodo | `true` |
| `ENABLE_GITHUB_PUSH` | Habilitar push para GitHub | `true` |
| `REQUIRE_OMEGA_GATE` | Exigir validação Ω-Gate | `true` |

### Variáveis de ambiente (publishers)

| Variável | Descrição | Padrão |
| --- | --- | --- |
| `MATVERSE_ZENODO_TOKEN` | Token da API do Zenodo (executor v2) | Obrigatório para Zenodo |
| `MATVERSE_ZENODO_SANDBOX` | Usar sandbox do Zenodo | `true` |
| `MATVERSE_ZENODO_TITLE` | Título do depósito | Data atual |
| `MATVERSE_ZENODO_DESCRIPTION` | Descrição do depósito | Texto padrão |
| `MATVERSE_ZENODO_KEYWORDS` | Palavras-chave (CSV) | vazio |
| `MATVERSE_ZENODO_COMMUNITIES` | Comunidades Zenodo (CSV) | vazio |
| `MATVERSE_ZENODO_CREATORS` | JSON com autores | usa `MATVERSE_ZENODO_AUTHOR` |
| `MATVERSE_ZENODO_AUTHOR` | Autor fallback | `MatVerse Team` |

### Configuração via código

```python
from deploy_with_tests_and_tracing import DeployConfig

config = DeployConfig(
    enable_zenodo=True,
    enable_github_push=True,
    enable_orcid_update=False,
    require_omega_gate=True,
    test_timeout=300,
)
```

## 📊 Pipeline de execução

1. Coleta de arquivos: Identifica todos os arquivos para deploy.
2. Geração de manifesto: Calcula hashes SHA3-512 e assina.
3. Execução de testes:
   - Compilação LaTeX de todos os `.tex`.
   - Testes Python (sintaxe e unitários).
   - Scan básico de segurança.
4. Validação Ω-Gate: Envia para core MatVerse para decisão.
5. Publicação (se todos os passos anteriores passarem):
   - Zenodo: cria deposition, upload, publica com DOI.
   - GitHub: commit e push automático.
   - ORCID: atualização de perfil (opcional).
6. Geração de relatório: JSON completo com todos os dados.

## 🔒 Segurança e rastreabilidade

- Trace ID único: Identificador único para cada execução.
- Assinatura criptográfica: Ed25519 para todos os manifestos.
- Hashes imutáveis: SHA3-512 de todos os arquivos.
- Logs estruturados: Armazenados em `deploy_reports/`.
- Auditoria completa: Qualquer execução pode ser reproduzida e verificada.

## 📁 Estrutura de saída

```text
deploy_reports/
└── deploy_{trace_id}.json
    ├── trace_id: ID único do deploy
    ├── start_time/end_time: Timestamps UTC
    ├── steps: Resultados de cada passo
    ├── manifest: Hashes e assinaturas
    └── success: Status final
```

## 🛠️ Extensibilidade

### Adicionar novos testes

```python
class CustomTestRunner(TestRunner):
    def run_custom_test(self) -> tuple[bool, str]:
        return True, "Teste customizado passou"
```

### Adicionar novos publishers

```python
class CustomPublisher:
    def publish(self, files: list[Path], manifest: dict) -> dict:
        return {"success": True, "message": "Publicado"}
```

## 🚨 Tratamento de erros

- Falha em testes: Pipeline interrompido, relatório gerado.
- Falha Ω-Gate: Deploy bloqueado, motivo registrado.
- Falha de publicação: Rollback parcial quando possível.
- Timeout: Configurável por teste/passo.

## 📈 Monitoramento

- Logs em tempo real no console.
- Arquivo `deploy_trace.log` detalhado.
- Relatório JSON estruturado.
- Integração com sistemas de observabilidade via stdout estruturado.

## 🔄 Integração CI/CD

```yaml
name: MatVerse Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
      - name: Install dependencies
        run: pip install -r tools/exocortex_executor/requirements-deploy.txt
      - name: Run Deploy
        env:
          ZENODO_TOKEN: ${{ secrets.ZENODO_TOKEN }}
          MATVERSE_CORE_URL: ${{ secrets.MATVERSE_CORE_URL }}
        run: python tools/exocortex_executor/deploy_with_tests_and_tracing.py
```

## 📄 Licença

MIT License - veja LICENSE para detalhes.

## 🤝 Contribuições

- Fork o repositório.
- Crie uma branch para sua feature.
- Commit suas mudanças.
- Push para a branch.
- Abra um Pull Request.

MatVerse ACOA Research Collective • https://github.com/matverse-acoa
