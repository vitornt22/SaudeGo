# README: Dashboard de Indicadores Estatísticos

Este projeto consiste em uma arquitetura de visualização de dados desagregados. O sistema é dividido em dois serviços principais: um _backend_ robusto para processamento de dados e um _frontend_ dinâmico para apresentação de gráficos.

### A arquitetura se baseia

1.  **Backend (FastAPI/Pandas):** Motor de processamento de dados e aplicação de filtros nos arquivos `raw_data.csv`.
2.  **Frontend (Django/JS/ECharts):** Interface que gerencia a interação do usuário e a visualização dos dados processados.
3.  **Arquivos Estáticos:** Os dados de origem (CSV, GeoJSON e Metadados JSON) são a fonte única de informação, sem uso de banco de dados tradicional.

---

### Como Rodar a Aplicação com Docker

A aplicação é orquestrada através do Docker Compose, que gerencia e conecta os dois serviços principais (FastAPI e Django).

#### Pré-requisitos

Certifique-se de ter o **Docker** e o **Docker Compose** instalados em sua máquina.

#### Instruções

1.  **Clonar o Repositório:**

    ```bash
    git clone git@github.com:vitornt22/SaudeGo.git

    ```

2.  **Construir e Iniciar os Contêineres:**
    Execute o comando a seguir na pasta raiz do projeto, onde o `docker-compose.yml` está localizado:
    ```bash
    docker compose up --build
    ```
    O comando `--build` garante que as imagens dos serviços sejam construídas ou atualizadas antes de iniciar.

#### Acesso aos Serviços

Após a conclusão da inicialização (que pode levar alguns minutos na primeira execução), você pode acessar os serviços nos seguintes URLs:

| Serviço                   | URL                                          |
| :------------------------ | :------------------------------------------- |
| **Frontend (Dashboard)**  | [http://0.0.0.0:8004/](http://0.0.0.0:8004/) |
| **Backend (API FastAPI)** | [http://0.0.0.0:8002/](http://0.0.0.0:8002/) |

---

### 📚 Documentação Detalhada da Estrutura

Para entender em profundidade a arquitetura e a lógica de processamento de dados e visualização, consulte os relatórios detalhados localizados nesta mesma pasta:

- **Estrutura do Backend:** [BACKEND_REPORT.md](BACKEND_REPORT.md)
- **Estrutura do Frontend:** [FRONTEND_REPORT.md](FRONTEND_REPORT.md)
