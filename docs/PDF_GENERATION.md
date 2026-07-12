# Geração de PDFs com PyMuPDF

## Arquitetura

O backend abre os modelos originais com `import pymupdf`, preenche seus widgets
AcroForm, atualiza as aparências e executa
`Document.bake(annots=True, widgets=True)`. O navegador recebe um PDF finalizado:
ele não preenche campos, recalcula aparências nem modifica bytes.

O fluxo central fica em `src/pdf/`:

- `inventory.py`: modelos, páginas, campos essenciais e regras de seleção;
- `mappings.py`: aliases existentes e origem dos dados clínicos;
- `renderer.py`: widgets, radio buttons, coordenadas e overflow;
- `validators.py`: reabertura, páginas, conteúdo e ausência de widgets;
- `storage.py`: escrita temporária única e substituição atômica;
- `generator.py`: interface `generate_pdf(tipo, dados, app_root) -> bytes`.

As funções públicas antigas em `src/utils/pdf_utils.py` permanecem disponíveis para
que rotas e integrações não precisem conhecer detalhes do PyMuPDF.

## Inventário

| Identificador | Modelo | Páginas | Campos | Regra |
|---|---|---:|---:|---|
| `internacao` | `src/static/Internacao.pdf` | 7 | 72 widgets | 5 páginas sem OPME; 7 com OPME |
| `hemocomponente` | `src/static/REQUISIÇÃO HEMOCOMPONENTE.pdf` | 2 | 64 widgets | somente quando há reserva de sangue |

Os retângulos, fontes, tamanhos, alinhamentos e estados dos botões continuam vindo
dos widgets dos próprios modelos. As páginas não são rasterizadas.

## Mapeamentos e novos campos

Para adicionar um alias, inclua-o no builder correspondente em `mappings.py`, sem
alterar o nome gravado no modelo. Nomes são resolvidos nesta ordem: exato,
normalizado sem acento e, apenas para nomes legados corrompidos, similaridade forte
e não ambígua.

Para um novo modelo:

1. adicione o PDF em `src/static/`;
2. cadastre um `PdfDocumentSpec` no inventário;
3. crie o builder de dados preservando os nomes AcroForm;
4. adicione teste de integração parametrizado;
5. declare os campos essenciais que devem bloquear uma saída incompleta.

Mapeamentos por coordenadas usam `mapping_to_rect()`. Para mapas legados cuja
origem fica na parte inferior, use `convert_legacy_coordinates()`, que considera
CropBox e a matriz de rotação da página. Não espalhe conversões pelas regras de
negócio.

## Fontes, overflow e imagens

Widgets mantêm as fontes e aparências incorporadas nos modelos. Conteúdo desenhado
por coordenadas deve usar fonte existente no repositório ou uma fonte PDF padrão
compatível. `insert_text_fitting_box()` reduz progressivamente o tamanho até o
mínimo permitido e lança erro se o texto não couber; falhas não são ignoradas.

Imagens futuras devem ser inseridas com `Page.insert_image()` dentro do retângulo
mapeado, preservando proporção e transparência. Nunca converta o modelo inteiro em
imagem.

## Validação e entrega HTTP

Antes da gravação, campos essenciais são conferidos e suas regiões são renderizadas
para provar que a aparência mudou. Depois do bake, os bytes são reabertos e são
verificados: assinatura PDF, tamanho, páginas, conteúdo não vazio e zero widgets.
Somente então ocorre a gravação atômica no diretório protegido.

As rotas entregam `application/pdf`, `Content-Disposition` inline ou attachment,
`Content-Length` e `Cache-Control: no-store`. O frontend apenas usa links ou iframe;
não há Base64, Blob transformado ou preenchimento em JavaScript.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\generate_pdf_test_artifacts.py
```

Os artefatos fictícios ficam em `test_artifacts/pdf/`. Abra os mesmos arquivos em:

- Chrome;
- Edge;
- Firefox;
- Adobe Acrobat Reader ou visualizador nativo.

Confira nomes, acentos, campos multilinha, radio buttons, páginas e fundo original.
Os bytes não devem ser regenerados ou modificados entre os leitores.

## Motivo da migração

O fluxo anterior atualizava valores AcroForm com PyPDF2, mas não incorporava os
widgets à página e ainda ignorava exceções por página. Assim, a exibição podia
depender das appearance streams e do recálculo particular de Chrome, Edge ou outro
leitor. O bake no backend elimina essa dependência.
