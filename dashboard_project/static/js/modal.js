
// Função para abrir modal de informações
export function openInfoModal(metadata) {
	const modalBody = document.getElementById("modalInfoBody");
	modalBody.innerHTML = `
		<h5><strong>${metadata.nome}</strong></strong></h5>
		<br><br>
		${metadata.ficha.resumo ? `<h5><strong>Resumo</strong></h5><p>${metadata.ficha.resumo}</p>` : ''}
		${metadata.ficha.formula_ficha ? `<h5><strong>Fórmula</strong></h5><p>${metadata.ficha.formula_ficha}</p>` : ''}
		${metadata.ficha.limitacoes ? `<h5><strong>Limitações</strong></h5><p>${metadata.ficha.limitacoes}</p>` : ''}
		${metadata.ficha.referencias ? `<h5><strong>Referências</strong></h5><p>${metadata.ficha.referencias}</p>` : ''}
		${metadata.ficha.complemento ? `<h5><strong>Complemento</strong></h5><small class="text-muted">${metadata.ficha.complemento}</small>` : ''}

	`;
	const modal = new bootstrap.Modal(document.getElementById("modalInfo"));
	modal.show();
}

// Função para abrir modal de filtros
export function openFilterModal(metadata) {
	const modalBody = document.getElementById("modalFiltersBody");
	modalBody.innerHTML = ""; // Limpar antes

	if (metadata.filtros && metadata.filtros.length) {
		metadata.filtros.forEach(filtro => {
			// Cria label
			const label = document.createElement("label");
			label.textContent = filtro.nome_filtro;
			label.className = "form-label";

			// Cria select multi
			const select = document.createElement("select");
			select.className = "form-select mb-1";
			select.name = filtro.nome;

			// AQUI  ALTERAÇÃO:
			select.dataset.field = `nome_option_f${filtro.id_filtro}`;

			select.multiple = true; // obrigatório para Choices.js

			// Adiciona opções
			filtro.options.forEach(opt => {
				const option = document.createElement("option");
				option.value = opt.nome_option;
				option.textContent = opt.label || opt.nome_option;
				select.appendChild(option);
			});

			// Cria small com descrição do filtro
			if (filtro.descricao) {
				const small = document.createElement("small");
				small.className = "text-muted d-block mb-3";
				small.textContent = filtro.descricao;

				modalBody.appendChild(label);
				modalBody.appendChild(select);
				modalBody.appendChild(small);
			} else {
				modalBody.appendChild(label);
				modalBody.appendChild(select);
			}

			// Inicializa Choices.js
			new Choices(select, {
				removeItemButton: true,
				searchEnabled: true,
				placeholder: true,
				placeholderValue: 'Selecione...',
				itemSelectText: '',
			});
		});
	} else {
		modalBody.innerHTML = "<p>Nenhum filtro disponível para este indicador.</p>";
	}

	// Exibe modal
	const modal = document.getElementById("modalFilters");
	modal.dataset.indicatorId = metadata.id;
	const bsModal = new bootstrap.Modal(modal);
	bsModal.show();
}

