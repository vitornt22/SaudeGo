// GRÁFICO DE LINHA
export function plotLineChart(chartId, data) {
	const dom = document.getElementById(chartId);
	const chart = echarts.init(dom);

	const x = data.data_example.option_echarts.xAxis.data;
	const series = data.data_example.option_echarts.series;

	const option = {
		tooltip: { trigger: "axis" },

		xAxis: {
			type: "category",
			data: x
		},

		yAxis: { type: "value" },

		series: series.map(s => ({
			...s,
			type: "line",
			smooth: true,
			symbol: "circle"
		}))
	};

	chart.setOption(option);
}


// GRÁFICO DE MAPA (GOIÁS)
export async function plotMapChart(chartId, data) {
	try {
		const dom = document.getElementById(chartId);
		const chart = echarts.init(dom);

		// ============================
		// 1) DEFINIR MAPA COM BASE NO METADATA
		// ============================
		let mapName = "GO_reg"; // fallback

		if (data.metadata) {
			const metaText = JSON.stringify(data.metadata).toLowerCase();

			if (metaText.includes("município") || metaText.includes("municipio")) {
				mapName = "GO_mun";
			} else if (metaText.includes("macroregiao") || metaText.includes("macro-região") || metaText.includes("macro região")) {
				mapName = "GO_mac";
			} else if (
				metaText.includes("região de saúde") ||
				metaText.includes("regiao de saude") ||
				metaText.includes("regiao de saúde")
			) {
				mapName = "GO_reg";
			}
		}

		// ============================
		// 2) Buscar mapa da API
		// ============================
		const geo = await fetch(`http://localhost:8002/maps/${mapName}`)
			.then(res => res.json());

		echarts.registerMap("goias", geo);

		// ============================
		// 3) Extrair dados
		// ============================
		const seriesData =
			data.data_example?.option_echarts?.series?.[0]?.data || [];

		if (!seriesData.length) {
			console.error("Nenhum dado encontrado para o mapa");
			return;
		}

		const visualMapData =
			data.data_example?.option_echarts?.visualMap || {
				min: Math.min(...seriesData.map(d => d.value)),
				max: Math.max(...seriesData.map(d => d.value))
			};

		// ============================
		// 4) Configurar gráfico
		// ============================
		const option = {
			tooltip: { trigger: "item" },

			visualMap: {
				left: "left",
				min: visualMapData.min,
				max: visualMapData.max,
				text: ["Alto", "Baixo"],
				calculable: true
			},

			series: [
				{
					type: "map",
					map: "goias",
					roam: true,
					emphasis: { label: { show: true } },
					data: seriesData
				}
			]
		};

		chart.setOption(option);

	} catch (err) {
		console.error("ERRO AO PLOTAR MAPA:", err);
	}
}

// Detectar tipo — com base no metadata
export function detectChartType(data) {
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


// LÓGICA CENTRAL: Identificar tipo de gráfico
export function plotChart(chartId, data) {
	const type = detectChartType(data);

	if (type === "line") {
		plotLineChart(chartId, data);
	} else if (type === "map") {
		plotMapChart(chartId, data);
	} else {
		console.warn("Tipo desconhecido:", type);
	}
}
