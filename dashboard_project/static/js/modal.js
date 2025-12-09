
// Função para abrir modal de informações
export function openInfoModal(metadata) {
	// Abre o modal e organiza as informações do metadata.json
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
export function openFilterModal(metadata, appliedData) {
	const modalBody = document.getElementById("modalFiltersBody");
	modalBody.innerHTML = ""; // Limpar antes de colocar os filtros dinamicamente

	// 1. Mapear os filtros aplicados (id_filtro -> [valor_da_opcao_em_string, ...])
	// Nessa parte a função percorrer o APPLYED_FILTERS do data_example e adiciona
	// todas as opções pré selecionadas para seus respectivos id
	// A lógica é relacionar os ids selecionados com os filtros do metadata.json
	// e adicionar ao formulário quando for aberto...
	const appliedOptionsMap = new Map();
	if (appliedData && appliedData.applyed_filters && appliedData.applyed_filters.length) {
		appliedData.applyed_filters.forEach(filter => {
			// CONVERTE para String. Isso transforma 2025.0 em "2025"
			const optionsToSelect = filter.id_option.map(id => String(id));
			appliedOptionsMap.set(filter.id_filtro, optionsToSelect);
		});
	}

	// Se existem filtros que podem ser aplicados
	if (metadata.filtros && metadata.filtros.length) {
		metadata.filtros.forEach(filtro => {
			// Busca as opções aplicadas para o filtro atual( procura na lista de filtros adicionado)
			// diretamente do applyed_filters
			const selectedValues = appliedOptionsMap.get(filtro.id_filtro) || [];

			// Criação de Label e Select 
			const label = document.createElement("label");
			label.textContent = filtro.nome_filtro;
			label.className = "form-label";

			const select = document.createElement("select");
			select.className = "form-select mb-1";
			select.name = filtro.nome;
			// Essa lógica foi percebida analizando o raw_data.json
			select.dataset.field = `nome_option_f${filtro.id_filtro}`;
			select.multiple = true;

			// Percorre os filtros aplicaveis no metadata.json
			filtro.options.forEach(opt => {
				// busca os options
				const option = document.createElement("option");
				const optionValue = String(opt.nome_option);

				option.value = optionValue;
				option.textContent = opt.label || opt.nome_option;
				select.appendChild(option);
			});

			// Se houver descrição adiciona
			if (filtro.descricao) {
				const small = document.createElement("small");
				small.className = "text-muted d-block mb-3";
				small.textContent = filtro.descricao;
				modalBody.appendChild(small);
			}
			// Adiciona label e o select
			modalBody.appendChild(label);
			modalBody.appendChild(select);

			// Inicializa Choices.js
			const choicesInstance = new Choices(select, {
				removeItemButton: true,
				searchEnabled: true,
				placeholder: true,
				placeholderValue: 'Selecione...',
				itemSelectText: '',
			});

			// Se houver filtros aplicados, adiciona os valores aos selects
			if (selectedValues.length > 0) {
				// selectedValues é um array de strings (ex: ["2025"])
				choicesInstance.setChoiceByValue(selectedValues);
			}

		});
	} else {
		// Se não houver filtros para serem aplicados 
		modalBody.innerHTML = "<p>Nenhum filtro disponível para este indicador.</p>";
	}

	// Exibe modal de filtros 
	const modal = document.getElementById("modalFilters");
	modal.dataset.indicatorId = metadata.id;
	const bsModal = new bootstrap.Modal(modal);
	bsModal.show();
}