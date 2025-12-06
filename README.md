![Logo Indra](img/INDRAGROUP_LOGO.png)
***
# Teste Técnico
## Programador Full Stack Pleno (Python/Django)

### Introdução
Este teste é direcionado para profissionais que desejam atuar como Programador Full Stack Pleno (Python/Django) na Indra Group. 

O processo seletivo prevê a contratação de 1 profissional para atuação em projetos de Desenvolvimento Full-Stack na [Secretaria de Estado da Saúde de Goiás](https://www.saude.go.gov.br/).

### Contextualização
Exite atualmente, uma aplicação chamada [Saúde GO 360](https://360.saude.go.gov.br/frontend/). Essa aplicação, construída em Django, busca exibir os diversos indicadores utilizados pela SES-GO em uma plataforma única, interativa e personalizável para cada usuário. Ela funciona consumindo de uma API desenvolvida internamente, que agrega os metadados e dados de tais indicadores.

Ou seja, existe esse ambiente composto por uma aplicação django que exibe os indicadores retornados por uma API. Esses produtos são de extrema importância para a gestão atual, e é necessário que ele siga evoluindo sendo melhorado.

## Objetivo
Planejar e implementar uma arquitetura que permita a consulta dinâmica aos dados presentes nos arquivos de dados disponíveis. A solução deve prover uma interface que exiba os dados e metadados dos indicadores, possibilitando a aplicação de filtros em tempo de execução da página.

A arquitetura deverá contar com dois serviços:

1. Uma API servindo os metadados e dados presentes na pasta `data`;
2. Uma aplicação Django que é um dashboard que mostre os gráficos dos JSONs, inclusive aplicando filtros, usando eCharts.

É necessário que essa aplicação esteja pronta para ser executada, contando com os arquivos para configuração de ambiente execução utilizando Dockers.

### Dados Disponíveis
Na pasta `data` deste repositório há 5 pastas referentes à 5 Indicadores. Dentro de cada pasta, existem os seguintes arquivos:

* `metadata.json`: que traz um conjunto de metadados referentes ao Indicador;
* `data_example.json`: que traz um exemplo dos dados agregados para plotar o Indicador;
* `raw_data.csv`: que traz os dados brutos, de maneira que seja possível a aplicação dos filtros.

Além disso, existe a pasta `maps`, que contêm arquivos GeoJSON para o plot de mapas, caso nescessário. 

### Restrições Técnicas
- Todas as ferramentas e tecnologias utilizadas na arquitetura devem ser de código aberto (open source);
- A solução deve ser executada localmente, em ambiente on-premise, utilizando Dockers;
- Não é permitido o uso de serviços em nuvem (AWS, Azure, GCP, etc).

### Observações Adicionais
- Considere que o volume de indicadores pode crescer para a casa de milhares;
- Considere que o volume de dados em cada indicador pode crescer para a casa de centenas de milhões de registros;
- Cada consulta não deve levar mais do que poucos segundos para ser processada;
- Além do código, é importante apresentar a documentação da arquitetura (diagramas e texto).

## Prazo
O teste deve ser entregue até o dia 10/12/2025.

## Entrega
Todos os artefatos produzidos deverão ser organizados em um repositório público no GitHub vinculado à sua conta pessoal.

Ao final do prazo de entrega do teste, envie o link do repositório com todos os entregáveis para o e-mail [wsmarques@minsait.com](mailto:wsmarques@minsait.com). 

Após o recebimento, caso o resultado seja satisfatório, entraremos em contato para agendar uma reunião (última fase do processo seletivo)
