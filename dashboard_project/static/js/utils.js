export function createLoader(target) {
	// Loader overlay
	const overlay = document.createElement("div");
	overlay.className = "chart-loader-overlay";
	overlay.style.position = "absolute";
	overlay.style.inset = "0";
	overlay.style.display = "flex";
	overlay.style.alignItems = "center";
	overlay.style.justifyContent = "center";
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
	target.appendChild(overlay);

	return overlay;
}

export function showChartError(chartEl) {
	// Remove erros anteriores
	chartEl.querySelectorAll(".chart-error").forEach(n => n.remove());

	// Cria o aviso de erro
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

	// Insere no card do gráfico
	chartEl.appendChild(errNode);
}