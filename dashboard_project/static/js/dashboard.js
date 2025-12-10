
import { plotChart } from './plot.js'
import { openInfoModal, openFilterModal } from './modal.js';
import { createLoader, showChartError } from './utils.js';

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

// Controle de paginação dos indicadores
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

	// Define se haverá o botão de carregar mais indicadores ou não
	const btn = document.getElementById("loadMoreBtn");
	// Se o limite chegou ao total de indicadores, esconde o botão 
	if (offset + LIMIT >= totalIndicators) {
		btn.style.display = "none";
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

		// Adiciona o card ao elemento
		container.appendChild(card);


		const cardBody = card.querySelector(`[data-chart-id="${chartId}"]`);
		// Eventos dos botões para abrir os modais de informações e filtros
		cardBody.querySelector(".btn-modal-info").addEventListener("click", () => openInfoModal(data.metadata));
		cardBody.querySelector(".btn-modal-filters").addEventListener("click", () => openFilterModal(data.metadata, data.data_example));
	}

	// chama a função para plotar o chart
	plotChart(chartId, data);
}

// Função para realizar filtragem dinamica dos charts
export function initApplyFiltersButton() {
	// Ativa a chamada da função ao clicar no botão de aplicação de filtros
	document.getElementById("applyFilters").addEventListener("click", async () => {
		// Seleciona o modalFilters no base.html
		const modal = document.getElementById("modalFilters");
		// Seleciona o ID do indicador contigo na tag dataset
		const indicatorId = modal?.dataset?.indicatorId;

		if (!indicatorId) return;

		// Seleciona a elemento que corresponde ao corpo do MODAL
		const modalBody = document.getElementById("modalFiltersBody");

		// seleciona todos os selects dentro do modal de filtragem
		const selects = modalBody.querySelectorAll("select");

		// coleta os filtros escolhidos
		const paramsObj = {};
		selects.forEach(sel => {
			// Busca o campo field com o padrão definido no openFilterModal - nome_option_{id} 
			const field = sel.dataset.field;
			const values = Array.from(sel.selectedOptions).map(opt => opt.value);
			// se existir valores, seta adicona essa chave/valor ao paramsOBJ
			if (values.length) {
				// {nome_option_11: 10} - EXEMPLO
				paramsObj[field] = values;
			}
		});

		// Se os parametros forem vazios a função acaba
		if (!Object.keys(paramsObj).length) return;

		// busca o elemento o card que receberá a atualização do chart 
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

		let overlay = createLoader(chartEl);

		await applyFiltersRequest({
			indicatorId,
			paramsObj,
			chartEl,
			overlay,
			applyButton,
			selects,
		});

		// Fecha modal (depois do fetch)
		const bsModal = bootstrap.Modal.getInstance(modal);
		if (bsModal) bsModal.hide();
	});
}


// Função para montar a query para filtragem de dados
async function applyFiltersRequest({ indicatorId, paramsObj, chartEl, overlay, applyButton, selects, }) {
	try {
		// Monta query string
		const q = [];
		for (const field in paramsObj) {
			paramsObj[field].forEach(v => {
				q.push(`${encodeURIComponent(field)}=${encodeURIComponent(v)}`);
			});
		}

		const queryString = q.join("&");
		// após montar a query assume a forma de 

		const url = `http://localhost:8002/indicators/${indicatorId}/filter?${queryString}`;
		// indicators/1299/filter?nome_option_f3=Centro%20Oeste&nome_option_f1=Abadi%C3%A2nia

		const res = await fetch(url);

		if (!res.ok) {
			let errText = `${res.status} ${res.statusText}`;
			try {
				const errJson = await res.json();
				errText += ` - ${JSON.stringify(errJson)}`;
			} catch (e) { }
			console.error("Erro na requisição:", errText);
			throw new Error(errText);
		}

		const data = await res.json();

		createChartCard(data, indicatorId);


	} catch (err) {
		showChartError(chartEl);
	} finally {
		overlay.remove();
		applyButton.disabled = false;
		selects.forEach(s => s.disabled = false);
	}

}


