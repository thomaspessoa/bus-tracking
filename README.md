# Rizzatti - Sistema de Rastreamento de Ônibus

## Visão Geral

Rizzatti é uma aplicação web de rastreamento de ônibus projetada para gerenciar e monitorar rotas de ônibus e atividades de motoristas. Ela fornece interfaces distintas para administradores e motoristas. Administradores podem visualizar a localização em tempo real de ônibus ativos em um mapa e ver uma lista de viagens ativas. Motoristas podem fazer login, gerenciar suas viagens (iniciar, finalizar) e compartilhar automaticamente sua geolocalização enquanto uma viagem está ativa.

## Funcionalidades Chave

*   **Autenticação Baseada em Papéis:** Login e painéis separados para Administradores e Motoristas.
*   **Painel do Administrador:**
    *   Visualização em mapa em tempo real de todos os ônibus ativos usando Leaflet.js.
    *   Visualização em lista de viagens ativas com detalhes (motorista, detalhes da viagem, horário de início, localização).
*   **Painel do Motorista:**
    *   Iniciar novas viagens com informações de destino e horário.
    *   Finalizar viagens ativas.
    *   Rastreamento automático de geolocalização via navegador enquanto uma viagem está ativa, atualizando o servidor.
*   **Gerenciamento de Viagens:** Criação, ativação e finalização de viagens vinculadas aos motoristas.
*   **Gerenciamento de Sessão:** Sessões de usuário seguras usando Flask-Login.

## Pilha Tecnológica

*   **Backend:** Python, Flask
*   **Banco de Dados:** SQLite (via Flask-SQLAlchemy)
*   **Autenticação:** Flask-Login
*   **Frontend:** HTML, CSS, JavaScript
*   **Mapeamento:** Leaflet.js
*   **Hashing de Senha:** Utilitários de segurança do Werkzeug

## Pré-requisitos

*   Python 3.8 ou mais recente
*   pip (instalador de pacotes Python)
*   Um navegador web moderno com JavaScript habilitado (para geolocalização e exibição do mapa).
*   Git (para clonar o repositório).

## Instruções de Configuração

1.  **Clone o Repositório:**
    ```bash
    git clone <url_do_repositorio>
    cd rizzatti-bus-tracker 
    ```
    (Substitua `<url_do_repositorio>` pela URL real do repositório)

2.  **Crie e Ative um Ambiente Virtual Python:**
    *   No macOS e Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    *   No Windows:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Inicialize o Banco de Dados:**
    O banco de dados (`database/app.db`) e os usuários padrão são criados automaticamente na primeira vez que você executa a aplicação. Se precisar resetar o banco de dados, você pode deletar o diretório `database` e reiniciar a aplicação.

5.  **Execute a Aplicação:**
    ```bash
    python app.py
    ```
    A aplicação estará acessível em `http://localhost:8080` por padrão.

## Rodando os Testes

Para rodar os testes unitários e de integração, navegue até o diretório raiz do projeto e execute:

```bash
python -m unittest discover tests
```
Isso descobrirá e executará todos os testes localizados no diretório `tests`.

## Credenciais Padrão


Este projeto foi desenvolvido como parte de um exercício guiado.
