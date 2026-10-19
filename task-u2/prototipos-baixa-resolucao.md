# Protótipos de baixa resolução — Blog

Os esquemas são conceituais e priorizam hierarquia, estrutura e componentes. Não especificam acabamento visual. O documento de requisitos também os apresenta em conjunto: [Documento de Requisitos](./documento-de-requisitos.md#4-protótipos-de-baixa-resolução).

## Página inicial

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

## Leitura da publicação

```text
+------------------------------------------------------------------+
| [Voltar à lista]                                      [Conta]    |
+------------------------------------------------------------------+
|                         Título da publicação                     |
|                   Autor / informações da publicação              |
|                                                                  |
|  Corpo renderizado: parágrafos, títulos, listas, citações e código|
|                                                                  |
|  [Curtir] [Opção de áudio, se habilitada]                         |
|  [Publicações relacionadas, se habilitadas]                       |
+------------------------------------------------------------------+
```

## Login e cadastro

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

## Minhas publicações

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

## Editor

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
