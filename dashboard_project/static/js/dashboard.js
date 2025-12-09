
import { plotMapChart, plotLineChart } from './plot.js'
import { openInfoModal, openFilterModal } from './modal.js';

// Configurações Variaveis Globais
const API_BASE = "http://0.0.0.0:8002";
let currentOffset = 0;
const LIMIT = 10;
let totalIndicators = 0;


// Evento para inicio das funções ao carregar o DOM
document.addEventListener("DOMContentLoaded", () => {
	initDashboard();
	initApplyFiltersButton();
});

// Monitora o clique no botão de carregar mais 
// ao clicar ele muda a paginação e busca os próximos dados com base no LIMIT definido
document.getElementById("loadMoreBtn").addEventListener("click", async () => {
	currentOffset += LIMIT;
	await initDashboard(currentOffset, true); // append = true
});


// Função para carregar indicadores da API e plotar os charts
async function initDashboard(offset = 0, append = false) {
	// Buscando o chartsContainer do dashboard.html
	const container = document.getElementById("chartsContainer");

	// Se o parametro append for falso significa que os indicadores estão sendo carregados
	if (!append) container.innerHTML = "<h4>Carregando indicadores...</h4>";

	// Busca indicadores com paginação (definida no backend com FASTAPI)
	// Estrutura vinda do backend 
	// {
	//     "indicators": paginated_indicators,
	//     "total": total_count,
	//     "limit": limit,
	//     "offset": offset,
	// }
	const res = await fetch(`${API_BASE}/indicators?limit=${LIMIT}&offset=${offset}`);
	if (!res.ok) throw new Error("Erro ao buscar indicadores");

	// busca os dados json
	const json = await res.json();
	const indicators = json.indicators;
	totalIndicators = json.total;

	if (!append) container.innerHTML = "";

	// Percorre todos os IDs para fazer a requisição dos dados dos indicadores
	for (const id of indicators) {
		// faz a busca do metada.json e data_example dos id do indicador atual
		const indicatorData = await fetchIndicatorData(id);
		// chama a função para criar ou atualizar o card que irá plotar o chart
		createChartCard(indicatorData);
	}

	const btn = document.getElementById("loadMoreBtn");
	if (offset + LIMIT >= totalIndicators) {
		btn.style.display = "none"; // esconde quando não tem mais
	} else {
		btn.style.display = "inline-block"; //mostra se ainda tiver
		btn.disabled = false;
	}
}


// Busca os metadados.json e data_example de um indicador especifico
async function fetchIndicatorData(id) {
	const res = await fetch(`${API_BASE}/indicators/${id}`);
	if (!res.ok) throw new Error("Erro ao buscar indicador " + id);
	return await res.json();
}

// Função para criar ou atualizar o card com os charts
export function createChartCard(data) {
	// Busca a div do chart
	const container = document.getElementById("chartsContainer");
	const chartId = "chart_" + data.metadata.id;

	// Procura card existente pelo ID do indicador
	let card = container.querySelector(`[data-indicator-id="${data.metadata.id}"]`);

	// Se o card existir,  atualiza somente o card-body correto
	if (card) {
		const cardBody = card.querySelector(`[data-chart-id="${chartId}"]`);

		cardBody.innerHTML = `
			<div style="position:absolute; top:10px; right:10px; display:flex; gap:8px;">
				<button class="btn btn-sm btn-info btn-modal-info" data-indicator-id="${data.metadata.id}" title="Informações">
					<i class="bi bi-info-circle"></i>
				</button>
				<button class="btn btn-sm btn-secondary btn-modal-filters" data-indicator-id="${data.metadata.id}" title="Filtros">
					<i class="bi bi-funnel"></i>
				</button>
			</div>

			<h4>${data.metadata.nome}</h4>
			<div id="${chartId}" style="width:100%;height:380px;"></div>
			<small>${data.metadata.ficha.complemento}</small>
		`;

		// Reaplica botões para abrir os modais com informações e filtros
		cardBody.querySelector(".btn-modal-info").addEventListener("click", () => openInfoModal(data.metadata));
		cardBody.querySelector(".btn-modal-filters").addEventListener("click", () => openFilterModal(data.metadata, data.data_example));

	} else {
		// Se o card não existir, criamos um 
		card = document.createElement("div");
		card.className = "card mb-4 shadow-sm";
		card.style.borderRadius = "12px";
		card.dataset.indicatorId = data.metadata.id;

		card.innerHTML = `
			<div class="card-body position-relative" data-chart-id="${chartId}">
				<div style="position:absolute; top:10px; right:10px; display:flex; gap:8px;">
					<button class="btn btn-sm btn-info btn-modal-info" data-indicator-id="${data.metadata.id}" title="Informações">
						<i class="bi bi-info-circle"></i>
					</button>
					<button class="btn btn-sm btn-secondary btn-modal-filters" data-indicator-id="${data.metadata.id}" title="Filtros">
						<i class="bi bi-funnel"></i>
					</button>
				</div>

				<h4>${data.metadata.nome}</h4>
				<div id="${chartId}" style="width:100%;height:380px;"></div>
				<small>${data.metadata.ficha.complemento}</small>
			</div>
		`;

		container.appendChild(card);

		const cardBody = card.querySelector(`[data-chart-id="${chartId}"]`);
		// Eventos dos botões para abrir os modais de informações e filtros
		cardBody.querySelector(".btn-modal-info").addEventListener("click", () => openInfoModal(data.metadata));
		cardBody.querySelector(".btn-modal-filters").addEventListener("click", () => openFilterModal(data.metadata, data.data_example));
	}

	plotChart(chartId, data);
}


// LÓGICA CENTRAL: Identificar tipo de gráfico
function plotChart(chartId, data) {
	const type = detectChartType(data);

	if (type === "line") {
		plotLineChart(chartId, data);
	} else if (type === "map") {
		plotMapChart(chartId, data);
	} else {
		console.warn("Tipo desconhecido:", type);
	}
}

// Detectar tipo — com base no metadata
function detectChartType(data) {
	const metadata = data.metadata || {};
	const example = data.data_example || {};
	const option = example.option_echarts || {};
	const series = option.series || [];

	// 1) metadata.chart_type definido
	if (metadata.chart_type === "line") return "line";
	if (metadata.chart_type === "map") return "map";

	// 2) metadata contém indicadores de mapa
	if (metadata.geojson || metadata.map_type || metadata.tipo_grafico === "map") {
		return "map";
	}

	// 3) NOVA REGRA → visualMap só aparece em mapa temático
	if (option.visualMap) {
		return "map";
	}

	// 4) no data_example → series[].type
	if (series.length > 0) {
		const typeInSeries = series[0].type;

		if (typeInSeries === "line") return "line";
		if (typeInSeries === "map") return "map";
		if (typeInSeries === "bar") return "bar";
		if (typeInSeries === "scatter") return "scatter";
	}

	// 5) Caso especial: séries sem type, mas com "id" + "data" = linha
	if (series.length > 0 && series[0].data) {
		return "line";
	}

	// 6) Fallback final
	console.warn("Chart type não identificado. Usando 'line' como fallback.");
	return "line";
}


// filterApply.js
export function initApplyFiltersButton() {
	// Ativa a chamada da função ao clicar no botão de aplicação de filtros
	// tudo isso de forma dinamica
	document.getElementById("applyFilters").addEventListener("click", async () => {
		const modal = document.getElementById("modalFilters");
		const indicatorId = modal?.dataset?.indicatorId;
		if (!indicatorId) return;

		const modalBody = document.getElementById("modalFiltersBody");
		const selects = modalBody.querySelectorAll("select");

		// Monta os filtros para query params
		const paramsObj = {};
		selects.forEach(sel => {
			const field = sel.dataset.field;
			const values = Array.from(sel.selectedOptions).map(opt => opt.value);
			if (values.length) {
				paramsObj[field] = values;
			}
		});

		if (!Object.keys(paramsObj).length) return;

		const chartEl = document.getElementById("chart_" + indicatorId);
		if (!chartEl) return;

		// Desativa selects e botão pra evitar requisições duplicadas
		const applyButton = document.getElementById("applyFilters");
		applyButton.disabled = true;
		selects.forEach(s => s.disabled = true);

		// Garante posicionamento para overlay
		if (getComputedStyle(chartEl).position === "static") {
			chartEl.style.position = "relative";
		}

		// -----------------------------
		// Loader overlay (com CSS inline para garantir)
		// -----------------------------
		const overlay = document.createElement("div");
		overlay.className = "chart-loader-overlay";
		overlay.style.position = "absolute";
		overlay.style.inset = "0"; // top:0;right:0;bottom:0;left:0;
		overlay.style.display = "flex";
		overlay.style.alignItems = "center";
		overlay.style.justifyContent = "center";
		overlay.style.background = "rgba(255,255,255,0.6)";
		overlay.style.zIndex = "9999";

		// Spinner (simples)
		const spinner = document.createElement("div");
		spinner.style.width = "48px";
		spinner.style.height = "48px";
		spinner.style.border = "6px solid rgba(0,0,0,0.12)";
		spinner.style.borderTop = "6px solid rgba(0,0,0,0.6)";
		spinner.style.borderRadius = "50%";
		spinner.style.animation = "spin 1s linear infinite";

		// Keyframes (adiciona uma tag style se não existir)
		if (!document.getElementById("chart-loader-keyframes")) {
			const styleTag = document.createElement("style");
			styleTag.id = "chart-loader-keyframes";
			styleTag.innerHTML = `
				@keyframes spin { to { transform: rotate(360deg); } }
			`;
			document.head.appendChild(styleTag);
		}

		overlay.appendChild(spinner);
		chartEl.appendChild(overlay);

		try {
			// Monta query string
			const q = [];
			for (const field in paramsObj) {
				paramsObj[field].forEach(v => {
					q.push(`${encodeURIComponent(field)}=${encodeURIComponent(v)}`);
				});
			}
			const queryString = q.join("&");
			const url = `http://localhost:8002/indicators/${indicatorId}/filter?${queryString}`;

			const res = await fetch(url);

			if (!res.ok) {
				// tenta pegar json de erro
				let errText = `${res.status} ${res.statusText}`;
				try {
					const errJson = await res.json();
					errText += ` - ${JSON.stringify(errJson)}`;
				} catch (e) { }
				console.error("Erro na requisição:", errText);
				throw new Error(errText);
			}

			const data = await res.json();

			// Tenta chamar createChartCard de duas formas possíveis:
			// 1) função nomeada importada/declared: createChartCard(data, indicatorId)
			// 2) função global: window.createChartCard(data, indicatorId)
			let called = false;
			try {
				if (typeof createChartCard === "function") {
					createChartCard(data, indicatorId);
					called = true;
				}
			} catch (e) {
				// não faz nada, tenta window abaixo
			}

			if (!called && typeof window !== "undefined" && typeof window.createChartCard === "function") {
				window.createChartCard(data, indicatorId);
				called = true;
			}

			// Se nenhuma existir, faz um fallback: atualiza o conteúdo do card com json
			if (!called) {
				console.warn("createChartCard não encontrada — usando fallback visual.");
				// Mantém a estrutura do card e substitui apenas a área do gráfico:
				// supondo que o chartEl é o container do gráfico, limpamos e inserimos um pre
				chartEl.innerHTML = `<pre style="padding:10px; font-size:13px; white-space:pre-wrap;">${JSON.stringify(data, null, 2)}</pre>`;
			}

		} catch (err) {
			console.error("Erro ao aplicar filtros:", err);
			// Exibe erro no chart (opcional)
			chartEl.querySelectorAll(".chart-error").forEach(n => n.remove());
			const errNode = document.createElement("div");
			errNode.className = "chart-error";
			errNode.style.position = "absolute";
			errNode.style.top = "8px";
			errNode.style.left = "8px";
			errNode.style.background = "rgba(255,0,0,0.08)";
			errNode.style.padding = "6px 8px";
			errNode.style.borderRadius = "4px";
			errNode.style.fontSize = "12px";
			errNode.style.zIndex = "10000";
			errNode.textContent = "Erro ao carregar dados. Veja console.";
			chartEl.appendChild(errNode);
		} finally {
			// Remove overlay e reativa controles
			overlay.remove();
			applyButton.disabled = false;
			selects.forEach(s => s.disabled = false);
		}

		// Fecha modal (depois do fetch)
		const bsModal = bootstrap.Modal.getInstance(modal);
		if (bsModal) bsModal.hide();
	});
}
