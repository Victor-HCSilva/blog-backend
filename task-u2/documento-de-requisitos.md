# Documento de Requisitos — Blog

## Capa

**Instituição:** [Nome da instituição]<br>
**Disciplina:** [Nome da disciplina]<br>
**Unidade:** II Unidade<br>
**Equipe:** [Nome da equipe e integrantes]<br>
**Projeto:** Blog — plataforma de criação e leitura de publicações<br>
**Data:** [Data de entrega]

> O painel MVP não faz parte desta versão do documento, conforme solicitado.

## 1. Introdução

### 1.1 Contexto e motivação

O projeto Blog, identificado na interface como HW, é uma aplicação web de publicação. A proposta é permitir que autores criem e personalizem artigos, salvem seu trabalho como rascunho e o publiquem para leitura pública. Pessoas visitantes podem descobrir e ler publicações; usuários autenticados também podem interagir com o conteúdo e receber recomendações.

O sistema possui uma interface web independente e uma API. Este documento descreve os fluxos identificados no código disponível. Quando uma função parece planejada, mas não está conectada ao aplicativo principal, isso é indicado como ponto a validar, e não como comportamento já entregue.

### 1.2 Objetivo do projeto

Descrever os usuários, os requisitos e os principais fluxos do Blog, de modo que a equipe e as partes interessadas compartilhem uma compreensão do que o software oferece e do que deve ser verificado ou desenvolvido.

### 1.3 Limites e premissas

- A aplicação atende à criação, edição, publicação, descoberta e leitura de publicações.
- A leitura de publicações publicadas é pública; operações de autoria exigem autenticação.
- O usuário autenticado só deve alterar e publicar as próprias publicações.
- A API é a fonte de validação dos dados e de autorização; ocultar uma ação na interface não substitui essa validação.
- Comentários possuem código de rotas e modelos, mas não estão registrados na inicialização da API examinada. Portanto, comentários não são tratados como fluxo disponível neste documento.
- Funcionalidades de áudio e algumas abas de descoberta existem no código, mas sua integração e comportamento completo devem ser testados no ambiente de execução.

## 2. Tecnologias

| Camada | Tecnologia identificada | Utilização |
|---|---|---|
| Interface web | Next.js 16, React 19, TypeScript | Páginas, componentes e navegação do usuário |
| Estilização | Tailwind CSS 4 | Estilos e layout da interface |
| API | Python 3.11 no contêiner, FastAPI | Endpoints HTTP e documentação automática da API |
| Persistência | PostgreSQL 15 no Docker | Banco de dados relacional |
| Acesso a dados | SQLAlchemy 2 assíncrono | Modelos e operações no banco |
| Validação | Pydantic 2 | Validação de requisições e respostas |
| Autenticação | JWT, PyJWT e pwdlib | Token de acesso e verificação de senha |
| Servidor da API | Uvicorn | Execução da aplicação ASGI |
| Infraestrutura de desenvolvimento | Docker Compose | Inicialização dos serviços da API e banco |

O arquivo de composição também define um serviço Redis, mas o código consultado não permite afirmar que ele participa dos fluxos funcionais do Blog. O frontend consulta a URL da API por `NEXT_PUBLIC_HW_API_URL`, usando `http://localhost:8000` como padrão.

## 3. Estórias de usuário

### EU1 — Criar uma publicação

**Estória:** Como autor autenticado, quero criar uma publicação com título e conteúdo para registrar minhas ideias.

**Critérios de aceitação**

1. Dado que estou autenticado, quando informo um título válido e inicio uma publicação, então o sistema cria uma publicação associada à minha conta.
2. A publicação nova deve começar como rascunho e não aparecer na listagem pública.
3. O sistema deve criar um identificador legível (slug) compatível com o formato aceito pela API.
4. Se o slug já estiver em uso, o sistema deve informar que não foi possível criar a publicação por conflito.
5. Se não estou autenticado, o sistema deve solicitar que eu entre antes de criar a publicação.

### EU2 — Ler uma publicação

**Estória:** Como visitante, quero abrir uma publicação publicada para ler seu conteúdo.

**Critérios de aceitação**

1. Dada uma publicação ativa e publicada, quando acesso seu endereço, então vejo título e conteúdo.
2. Uma publicação em rascunho ou inexistente não deve ser apresentada como conteúdo público.
3. A leitura não deve exigir autenticação.
4. A partir da página inicial, devo poder localizar uma publicação pela lista e pela busca disponível na interface.

### EU3 — Editar uma publicação própria

**Estória:** Como autor autenticado, quero editar minhas publicações para corrigir ou atualizar o conteúdo.

**Critérios de aceitação**

1. Posso alterar o título, o conteúdo e opções de apresentação da minha publicação.
2. Posso salvar as alterações e receber confirmação ou mensagem de erro.
3. Não posso editar publicações de outro autor.
4. A API deve validar a propriedade da publicação, mesmo se a solicitação for feita fora da interface.

### EU4 — Publicar uma publicação

**Estória:** Como autor autenticado, quero publicar um rascunho para disponibilizá-lo a leitores.

**Critérios de aceitação**

1. Somente o autor da publicação pode publicá-la.
2. Antes da publicação, as alterações atuais do editor devem ser salvas.
3. Após publicação bem-sucedida, a publicação deve ser marcada como publicada e ficar disponível na listagem e na leitura pública.
4. Se o salvamento ou a publicação falhar, a interface deve informar a falha e não indicar sucesso.

### EU5 — Criar uma conta

**Estória:** Como visitante, quero criar uma conta para poder escrever e gerenciar minhas publicações.

**Critérios de aceitação**

1. O cadastro recebe usuário e senha.
2. O usuário deve ter de 3 a 12 caracteres e a senha de 4 a 15 caracteres, conforme as validações declaradas na API.
3. Se o cadastro for aceito, a interface informa que a conta foi criada e encaminha ao login.
4. Se os dados forem rejeitados pela API, a interface apresenta o erro recebido sem indicar que a conta foi criada.

### EU6 — Entrar no sistema

**Estória:** Como usuário cadastrado, quero entrar para acessar as funções de autoria e personalização.

**Critérios de aceitação**

1. O login envia usuário e senha e, em sucesso, recebe um token de acesso.
2. Credenciais inválidas devem resultar em mensagem de erro.
3. O token é usado nas operações que exigem autenticação.
4. Se o usuário veio de uma rota interna para autenticar-se, após login deve retornar a essa rota, desde que o destino seja local e seguro.

### EU7 — Reagir a uma publicação

**Estória:** Como usuário autenticado, quero curtir ou remover minha curtida de uma publicação para expressar minha reação.

**Critérios de aceitação**

1. Posso registrar uma curtida em uma publicação.
2. Posso remover minha reação existente.
3. A interface atualiza a reação e os totais apresentados após confirmação da API.
4. Usuários sem sessão recebem solicitação para entrar.

### EU8 — Personalizar recomendações

**Estória:** Como usuário autenticado, quero informar meus interesses para receber recomendações de publicações mais relevantes.

**Critérios de aceitação**

1. Posso consultar e atualizar minha lista de interesses.
2. Cada interesse deve conter entre 1 e 50 caracteres e a lista aceita no máximo 30 itens, de acordo com a validação da API.
3. Após salvar, a interface solicita recomendações atualizadas.
4. Se o salvamento ou a atualização falhar, a interface deve informar o problema.

## 4. Protótipos de baixa resolução

Os wireframes abaixo representam estrutura e componentes, não a identidade visual final. São esquemas conceituais baseados nas rotas e componentes existentes.

### 4.1 Página inicial e descoberta

```text
+------------------------------------------------------------------+
| [Conta/Entrar]       [ Buscar publicações... ]     [Minhas pub.] |
|                              HW                                  |
+------------------------------------------------------------------+
|                         Seu conteúdo,                            |
|                           seu jeito!                             |
|             [ Título da nova publicação... ] [ Nova ]            |
+------------------------------------------------------------------+
| [Para você] [Recentes] [Em alta] [Explorar]                      |
| Interesses: [ temas separados por vírgula... ] [Salvar]           |
|                                                                  |
| +-------------------------------+ +----------------------------+ |
| | Imagem / título               | | Imagem / título             | |
| | resumo da publicação          | | resumo da publicação        | |
| | autor                         | | autor                       | |
| | [Abrir]              [Curtir] | | [Abrir]           [Curtir] | |
| +-------------------------------+ +----------------------------+ |
+------------------------------------------------------------------+
```

### 4.2 Leitura de publicação

```text
+------------------------------------------------------------------+
| [Voltar à lista]                                      [Conta]    |
+------------------------------------------------------------------+
|                         Título da publicação                     |
|                   Autor / informações da publicação              |
|                                                                  |
|  Conteúdo: parágrafos, títulos, citações, listas e código        |
|  renderizados conforme os blocos do documento.                    |
|                                                                  |
|  [Curtir] [Ouvir, se disponível]                                  |
|  [Publicações relacionadas, se disponíveis]                       |
+------------------------------------------------------------------+
```

### 4.3 Cadastro e login

```text
+-----------------------------------+
| [ Login ]       [ Cadastro ]      |
|                                   |
| Usuário  [____________________]   |
| Senha    [____________________]   |
|                                   |
|          [ Entrar / Criar conta ] |
| Mensagem de validação ou erro     |
| [Criar uma conta / Já tenho conta]|
+-----------------------------------+
```

### 4.4 Área “Minhas publicações”

```text
+------------------------------------------------------------------+
| HW / autor                         [Voltar à Home]                |
| Minhas publicações                                               |
+------------------------------------------------------------------+
| Rascunhos (N)                                                   |
| [Título] /slug                  [Editar]                         |
|                                                                  |
| Publicadas (N)                                                  |
| [Título] /slug                  [Editar] [Visualizar]             |
+------------------------------------------------------------------+
```

### 4.5 Editor de publicação

```text
+------------------------------------------------------------------+
| [Voltar] [Editar] [Pré-visualizar] [Salvar] [Publicar]           |
| Tema [____] Largura [____] Fonte [____] Tamanho [____]            |
| Fundo [cor] Acento [cor] Sumário [ ] Imagem de capa [_________]   |
+------------------------------------------------------------------+
| Título [____________________________________________________]    |
|                                                                  |
| Tipo de bloco: [Parágrafo] [Título] [Citação] [Lista] [Código]   |
| +--------------------------------------------------------------+ |
| | Conteúdo do bloco                                            | |
| +--------------------------------------------------------------+ |
| [Remover bloco]                                                 |
|                                                                  |
| Prévia do conteúdo renderizado                                   |
+------------------------------------------------------------------+
```

## 5. Diagrama de casos de uso

O diagrama UML está em [diagrama-casos-de-uso.puml](./diagrama-casos-de-uso.puml). Ele pode ser renderizado com PlantUML. Os atores principais são Visitante e Usuário autenticado; Autor é uma especialização do usuário autenticado para destacar os casos de uso de autoria.

## 6. Especificações de casos de uso

### UC01 — Criar conta

| Campo | Especificação |
|---|---|
| **Descrição** | Um visitante registra uma nova conta para usar recursos autenticados. |
| **Resultado desejado** | Conta criada e usuário encaminhado ao login. |
| **Objetivo do usuário** | Habilitar autoria e personalização no sistema. |
| **Participantes/papéis** | Visitante; interface web; API; banco de dados. |
| **Pré-condições** | API disponível; visitante ainda não autenticado. |
| **Regras de negócio** | Usuário entre 3 e 12 caracteres; senha entre 4 e 15 caracteres; senha armazenada de forma protegida pela API. |
| **Cenário principal** | 1. Visitante abre Cadastro. 2. Informa usuário e senha. 3. Envia o formulário. 4. A API valida e cria a conta. 5. A interface informa sucesso e conduz ao login. |
| **Alternativas/exceções** | 2a. Campos ausentes ou fora dos limites: API rejeita; interface apresenta erro. 4a. Usuário já existente ou conflito: API rejeita; interface apresenta a resposta de erro. 4b. API indisponível: cadastro não é confirmado; apresentar falha. |

### UC02 — Autenticar-se

| Campo | Especificação |
|---|---|
| **Descrição** | Um usuário fornece credenciais e recebe token de acesso se forem válidas. |
| **Resultado desejado** | Sessão autenticada disponível para chamadas protegidas. |
| **Objetivo do usuário** | Acessar funções pessoais e de autoria. |
| **Participantes/papéis** | Usuário; interface web; API de autenticação. |
| **Pré-condições** | Conta cadastrada e ativa. |
| **Regras de negócio** | Credenciais inválidas não autenticam; token de acesso tem prazo de expiração configurado na API (15 minutos por padrão no código consultado). |
| **Cenário principal** | 1. Usuário abre Login. 2. Informa credenciais. 3. Envia formulário. 4. API verifica credenciais e emite JWT. 5. Interface guarda o token para chamadas autenticadas e direciona para a página solicitada ou para a Home. |
| **Alternativas/exceções** | 3a. Credenciais inválidas: API rejeita; interface mostra mensagem. 4a. Conta inativa ou API indisponível: acesso não é concedido e o erro deve ser informado. |

### UC03 — Descobrir publicações

| Campo | Especificação |
|---|---|
| **Descrição** | O visitante ou usuário consulta publicações disponíveis e utiliza a busca da página inicial. |
| **Resultado desejado** | Lista de publicações ativas e publicadas apresentada ao leitor. |
| **Objetivo do usuário** | Encontrar conteúdo para ler. |
| **Participantes/papéis** | Visitante ou usuário autenticado; interface; API de publicações. |
| **Pré-condições** | Serviço da API disponível. |
| **Regras de negócio** | A listagem pública retorna publicações ativas e publicadas; rascunhos não são conteúdo público. |
| **Cenário principal** | 1. Usuário abre a Home. 2. Interface solicita publicações públicas à API. 3. Lista é exibida. 4. Usuário digita termo de busca. 5. Interface filtra/seleciona resultados conforme o comportamento implementado. |
| **Alternativas/exceções** | 2a. Falha ao carregar: interface informa erro. 3a. Lista vazia ou busca sem correspondência: interface informa que não há publicações encontradas. |

### UC04 — Ler publicação

| Campo | Especificação |
|---|---|
| **Descrição** | Um leitor abre uma publicação publicada pelo seu slug. |
| **Resultado desejado** | Conteúdo renderizado para leitura. |
| **Objetivo do usuário** | Ler o artigo escolhido. |
| **Participantes/papéis** | Visitante ou usuário autenticado; interface; API. |
| **Pré-condições** | Publicação ativa e publicada; slug conhecido ou selecionado na lista. |
| **Regras de negócio** | Leitura pública não requer login; publicação inexistente, inativa ou não publicada não deve ser exibida publicamente. |
| **Cenário principal** | 1. Leitor seleciona uma publicação. 2. Interface requisita a publicação pelo slug. 3. API retorna título, documento e apresentação. 4. Interface renderiza os blocos para leitura. |
| **Alternativas/exceções** | 2a. Slug não encontrado ou publicação indisponível: API retorna não encontrado; interface informa que a publicação não foi localizada. 2b. Falha de rede: interface deve indicar que não conseguiu carregar. |

### UC05 — Criar publicação

| Campo | Especificação |
|---|---|
| **Descrição** | Um autor autenticado inicia uma publicação, que é criada como rascunho. |
| **Resultado desejado** | Rascunho associado ao autor e editor aberto. |
| **Objetivo do usuário** | Começar a escrever um artigo próprio. |
| **Participantes/papéis** | Autor; interface; API; banco de dados. |
| **Pré-condições** | Autor autenticado com token válido; título informado. |
| **Regras de negócio** | Slug único, minúsculo e formado por grupos alfanuméricos separados por hífen; nova publicação começa não publicada; autor deriva do usuário autenticado, não de um ID escolhido pelo cliente. |
| **Cenário principal** | 1. Autor informa título na Home. 2. Interface gera slug e envia requisição autenticada com documento inicial e apresentação padrão. 3. API valida e cria o rascunho. 4. Interface abre o editor da publicação. |
| **Alternativas/exceções** | 1a. Título vazio ou que não gere slug válido: criação não prossegue. 2a. Sem token: interface pede login. 3a. Slug duplicado ou entrada inválida: API rejeita; interface informa o problema. |

### UC06 — Editar e salvar publicação própria

| Campo | Especificação |
|---|---|
| **Descrição** | O autor altera o título, blocos do documento, imagem de capa e opções de apresentação, e salva as alterações. |
| **Resultado desejado** | Publicação atualizada e confirmação mostrada ao autor. |
| **Objetivo do usuário** | Elaborar ou corrigir o artigo e sua apresentação. |
| **Participantes/papéis** | Autor; interface/editor; API; banco de dados. |
| **Pré-condições** | Autor autenticado; publicação pertencente ao autor e ativa. |
| **Regras de negócio** | Somente o proprietário pode editar; documento e apresentação devem seguir os esquemas aceitos pela API. |
| **Cenário principal** | 1. Autor abre “Minhas publicações” e seleciona Editar. 2. Interface carrega a publicação do autor. 3. Autor edita título, blocos ou apresentação. 4. Seleciona Salvar. 5. API verifica propriedade, valida os dados e persiste alterações. 6. Interface confirma o salvamento. |
| **Alternativas/exceções** | 1a. Publicação não pertence ao usuário ou não existe: acesso negado/não encontrado. 4a. Token inválido/expirado: API rejeita; solicitar novo login. 5a. Dados inválidos ou falha de rede: alterações não são confirmadas; mostrar erro e preservar o rascunho local enquanto a página estiver aberta. |

### UC07 — Publicar publicação própria

| Campo | Especificação |
|---|---|
| **Descrição** | O autor salva as alterações atuais e torna pública sua publicação. |
| **Resultado desejado** | Publicação marcada como publicada e disponível aos leitores. |
| **Objetivo do usuário** | Compartilhar o artigo com o público. |
| **Participantes/papéis** | Autor; interface/editor; API; banco de dados. |
| **Pré-condições** | Autor autenticado e proprietário da publicação. |
| **Regras de negócio** | Somente proprietário pode publicar; a interface tenta salvar antes de solicitar a publicação; apenas publicações ativas e publicadas são exibidas publicamente. |
| **Cenário principal** | 1. Autor seleciona Publicar. 2. Interface salva o estado atual. 3. Após confirmação do salvamento, solicita a publicação à API. 4. API valida propriedade e altera o estado. 5. Interface confirma e a publicação passa a aparecer publicamente. |
| **Alternativas/exceções** | 2a. Salvamento falha: não enviar publicação; informar falha. 3a. API rejeita por autorização ou token: não indicar sucesso; apresentar erro. 3b. Falha de rede: manter estado não confirmado e permitir nova tentativa. |

### UC08 — Reagir a publicação

| Campo | Especificação |
|---|---|
| **Descrição** | Um usuário autenticado registra ou remove uma reação de curtir. |
| **Resultado desejado** | Reação individual persistida e contagens atualizadas. |
| **Objetivo do usuário** | Indicar aprovação do conteúdo. |
| **Participantes/papéis** | Usuário autenticado; interface; API. |
| **Pré-condições** | Usuário autenticado; publicação existente e publicada. |
| **Regras de negócio** | Uma reação por usuário e publicação; a API aceita like, dislike ou remoção da reação. |
| **Cenário principal** | 1. Usuário seleciona Curtir. 2. Interface envia a reação autenticada. 3. API salva a reação e devolve totais. 4. Interface atualiza botão e totais. |
| **Alternativas/exceções** | 1a. Usuário não autenticado: solicitar login. 2a. Erro de API ou rede: preservar estado anterior e informar a falha. |

### UC09 — Atualizar interesses e consultar recomendações

| Campo | Especificação |
|---|---|
| **Descrição** | Um usuário autenticado informa temas de interesse e consulta recomendações personalizadas. |
| **Resultado desejado** | Lista de interesses persistida e recomendações atualizadas. |
| **Objetivo do usuário** | Encontrar publicações alinhadas aos seus interesses e leituras. |
| **Participantes/papéis** | Usuário autenticado; interface; API; mecanismo de recomendação. |
| **Pré-condições** | Usuário autenticado. |
| **Regras de negócio** | Até 30 interesses; cada interesse entre 1 e 50 caracteres; valores vazios não são aceitos; recomendações limitadas pelo parâmetro da API (12 por padrão na interface). |
| **Cenário principal** | 1. Usuário abre a aba Para você. 2. Consulta ou informa interesses separados por vírgulas. 3. Salva preferências. 4. Interface solicita recomendações. 5. Resultados personalizados são apresentados. |
| **Alternativas/exceções** | 2a. Interesse inválido: API rejeita; interface apresenta erro. 3a. Salvamento falha: informar que preferências não foram confirmadas. 4a. Recomendações falham: mostrar erro, sem exibir como atualizado. |

## 7. Análise de riscos

Escala qualitativa usada neste documento: probabilidade e impacto são classificados como Baixo, Médio ou Alto. A classificação deve ser revisada pela equipe; o slide 41 citado na orientação não foi fornecido, portanto não se afirma que esta tabela replica seu modelo.

| ID | Risco | Probabilidade | Impacto | Consequência | Mitigação / resposta |
|---|---|---:|---:|---|---|
| R1 | Descrição do produto divergir do comportamento realmente integrado | Alta | Alto | Entrega acadêmica promete funções que não podem ser demonstradas | Demonstrar os fluxos principais; atualizar requisitos com evidências; marcar lacunas como pendentes de validação |
| R2 | Acesso indevido a rascunhos ou edição/publicação por outro usuário | Média | Alto | Exposição ou alteração não autorizada de conteúdo | Testar autorização na API com usuários distintos e tokens expirados; manter verificação de propriedade no servidor |
| R3 | Perda de alterações durante erro de rede ou falha no salvamento | Média | Alto | Autor perde conteúdo e confiança no sistema | Testar falhas e repetição; apresentar estados claros; considerar salvamento de rascunho local/automático como melhoria futura |
| R4 | Slug duplicado ou inválido impedir criação | Média | Médio | Publicação não pode ser criada pelo fluxo esperado | Exibir erro acionável e permitir ajustar o título/slug; testar caracteres acentuados, pontuação e duplicidade |
| R5 | API ou banco indisponível durante demonstração/uso | Média | Alto | Cadastro, leitura ou edição deixam de funcionar | Verificar serviços antes da demonstração; testar conexão e configuração do ambiente; manter instruções de execução e plano de recuperação |
| R6 | Token expirar durante uma operação | Média | Médio | Requisição protegida falha e usuário pode perder fluxo | Tratar 401/expiração, orientar novo login e testar retorno seguro à página solicitada |
| R7 | Requisitos de comentários serem apresentados como recurso pronto apesar de não estar integrado | Alta | Médio | Escopo da entrega fica inconsistente com o sistema executável | Excluir comentários dos casos de uso entregues até o roteador ser registrado, validado e testado |
| R8 | Acessibilidade ou responsividade insuficiente nos formulários/editor | Média | Médio | Parte dos usuários tem dificuldade de concluir tarefas | Testar navegação por teclado, rótulos, mensagens de erro e tamanhos de tela; corrigir barreiras encontradas |
| R9 | Credenciais/configurações inadequadas em ambiente de execução | Média | Alto | Acesso não autorizado ou indisponibilidade do serviço | Usar segredos fora do código, revisar configuração de produção e validar variáveis de ambiente antes da publicação |

## 8. Itens a validar com a equipe

1. Substituir os campos da capa pelos nomes da equipe, instituição, disciplina e data.
2. Confirmar com uma execução real quais abas de descoberta e opções da página de leitura estão ativas e completas.
3. Definir se comentários fazem parte do escopo futuro e integrar/testar suas rotas antes de documentá-los como função disponível.
4. Conferir a tabela de riscos com o formato exato solicitado em aula, quando o slide 41 estiver disponível.
5. Revisar critérios de aceitação com a professora/equipe e ajustar os limites que forem decisões de produto, não validações já definidas no código.
