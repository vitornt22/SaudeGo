console.log("dashboard.js carregado");

// URL da API FastAPI
const API_BASE = "http://0.0.0.0:8002";

/* ============================================================
	1. Função principal — inicia dashboard
============================================================ */
async function initDashboard() {
	try {
		// 1. Buscar lista de indicadores
		const resp = await fetch(`${API_BASE}/indicators`);
		const data = await resp.json();

		const ids = data.indicators; // ["1299", "4445", ...]
		console.log("Indicadores encontrados:", ids);

		// 2. Para cada ID, criar card + buscar dados
		for (let id of ids) {
			createLoaderCard(id); // mostra loader

			try {
				const respInd = await fetch(`${API_BASE}/indicators/${id}`);
				const indData = await respInd.json();

				// O gráfico correto fica AQUI:
				const option = indData.data_example.option_echarts;

				updateCardWithChart(id, option, indData.metadata.nome);

			} catch (e) {
				console.error("Erro ao buscar dados do indicador", id, e);
				showErrorInCard(id);
			}
		}

	} catch (e) {
		console.error("Erro ao carregar lista de indicadores", e);
	}
}

/* ============================================================
	2. Card inicial com loader
============================================================ */
function createLoaderCard(id) {
	const container = document.getElementById("chartsContainer");

	const card = document.createElement("div");
	card.id = `card-${id}`;
	card.className = "indicator-card card p-3 mb-4 shadow-sm";

	card.innerHTML = `
        <h4 class="mb-3">Indicador ${id}</h4>
        <div class="loader text-center py-4">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2">Carregando dados...</p>
        </div>
        <div id="chart-${id}" style="width:100%; height:350px;"></div>
    `;

	container.appendChild(card);
}

/* ============================================================
	3. Atualiza card com o gráfico ECharts
============================================================ */
function updateCardWithChart(id, option, title) {
	const card = document.getElementById(`card-${id}`);

	// muda título
	card.querySelector("h4").innerText = title || `Indicador ${id}`;

	// remove loader
	const loader = card.querySelector(".loader");
	if (loader) loader.remove();

	// inicia echarts
	const chartDom = document.getElementById(`chart-${id}`);
	const chart = echarts.init(chartDom);

	chart.setOption(option);
}

/* ============================================================
	4. Exibir erro no card caso falhe
============================================================ */
function showErrorInCard(id) {
	const card = document.getElementById(`card-${id}`);
	const loader = card.querySelector(".loader");

	if (loader) loader.innerHTML = `
        <p class="text-danger">Erro ao carregar indicador ${id}</p>
    `;
}

/* ============================================================
	5. Inicialização automática
============================================================ */
initDashboard();
