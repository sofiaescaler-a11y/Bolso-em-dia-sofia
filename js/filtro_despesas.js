// Busca os campos de pesquisa, filtros, botões de período e ordenação.
var buscarDespesa = document.querySelector("#buscar-despesa")
var filtroMes = document.querySelector("#filtro-mes")
var filtroCategoria = document.querySelector("#filtro-categoria")

var periodoTodas = document.querySelector("#periodo-todas")
var periodoMes = document.querySelector("#periodo-mes")
var periodoTresMeses = document.querySelector("#periodo-tres-meses")

var ordenarData = document.querySelector("#ordenar-data")
var ordenarValor = document.querySelector("#ordenar-valor")

// Busca todas as linhas da tabela que representam despesas.
var itens = document.querySelectorAll(".item-despesa")

// Define os valores iniciais do período e da ordenação.
var periodoSelecionado = "todas"
var ordemData = "desc"
var ordemValor = "desc"


// Adiciona ao filtro as categorias encontradas nas despesas, sem repetir opções.
itens.forEach(function (item) {

    var nomeCategoria = item.dataset.categoria
    var opcoes = filtroCategoria.querySelectorAll("option")
    var categoriaExiste = false

    // Verifica se a categoria já existe entre as opções do filtro.
    opcoes.forEach(function (opcao) {
        if (opcao.value == nomeCategoria) {
            categoriaExiste = true
        }
    })

    // Se a categoria ainda não existir, cria e adiciona uma nova opção.
    if (categoriaExiste == false) {
        var novaOpcao = document.createElement("option")

        novaOpcao.value = nomeCategoria
        novaOpcao.textContent = nomeCategoria

        filtroCategoria.appendChild(novaOpcao)
    }
})


// Filtra as despesas pela descrição, mês, categoria e período selecionado.
function filtrarDespesas() {

    // Pega os valores dos filtros e transforma a pesquisa em letras minúsculas.
    var valorBusca = buscarDespesa.value.toLowerCase()
    var valorMes = filtroMes.value
    var valorCategoria = filtroCategoria.value

    // Obtém o mês e o ano atuais para filtrar as despesas por período.
    var hoje = new Date()
    var mesAtual = hoje.getMonth() + 1
    var anoAtual = hoje.getFullYear()

    // Percorre cada despesa para verificar se ela atende aos filtros.
    itens.forEach(function (item) {

        // Pega a descrição, a categoria e a data da despesa atual.
        var descricao = item.dataset.descricao.toLowerCase()
        var categoria = item.dataset.categoria
        var data = item.dataset.data

        // Separa a data em ano, mês e dia usando o hífen como separador.
        var partesData = data.split("-")

        // Converte o ano e o mês da despesa em números.
        var anoDespesa = Number(partesData[0])
        var mesDespesa = Number(partesData[1])

        // Verifica se a descrição contém o texto digitado na pesquisa.
        var mostrarBusca = descricao.includes(valorBusca)

        // Verifica se a despesa pertence ao mês selecionado ou se todos foram escolhidos. if ternario
        var mostrarMes = valorMes == "todos" || mesDespesa == valorMes

        // Verifica se a categoria corresponde à selecionada ou se todas foram escolhidas.
        var mostrarCategoria = valorCategoria == "todos" || categoria == valorCategoria

        // Por padrão, permite a despesa no filtro de período.
        var mostrarPeriodo = true

        // Se o período escolhido for o mês atual, compara o mês e o ano da despesa.
        if (periodoSelecionado == "mes") {
            mostrarPeriodo = mesDespesa == mesAtual && anoDespesa == anoAtual
        }

        // Se o período escolhido for os últimos três meses, calcula a diferença entre os meses.
        if (periodoSelecionado == "tres-meses") {
            var numeroMesAtual = anoAtual * 12 + mesAtual
            var numeroMesDespesa = anoDespesa * 12 + mesDespesa
            var diferencaMeses = numeroMesAtual - numeroMesDespesa

            // Permite despesas do mês atual e dos dois meses anteriores.
            mostrarPeriodo = diferencaMeses >= 0 && diferencaMeses <= 2
        }

        // Exibe a despesa se ela atender a todos os filtros; caso contrário, oculta.
        if (mostrarBusca && mostrarMes && mostrarCategoria && mostrarPeriodo) {
            item.style.display = ""
        } else {
            item.style.display = "none"
        }
    })
}


// Atualiza os resultados enquanto o usuário digita na pesquisa.
buscarDespesa.addEventListener("input", function () {
    filtrarDespesas()
})


// Atualiza os resultados quando o mês selecionado mudar.
filtroMes.addEventListener("change", function () {
    filtrarDespesas()
})


// Atualiza os resultados quando a categoria selecionada mudar.
filtroCategoria.addEventListener("change", function () {
    filtrarDespesas()
})


// Seleciona todas as despesas, independentemente do período.
periodoTodas.addEventListener("click", function () {

    periodoSelecionado = "todas"

    // Destaca o botão "Todas" e remove o destaque dos outros períodos.
    periodoTodas.classList.add("ativo")
    periodoMes.classList.remove("ativo")
    periodoTresMeses.classList.remove("ativo")

    filtrarDespesas()
})


// Filtra as despesas do mês e ano atuais.
periodoMes.addEventListener("click", function () {

    periodoSelecionado = "mes"

    // Destaca o botão "Este mês" e remove o destaque dos outros períodos.
    periodoTodas.classList.remove("ativo")
    periodoMes.classList.add("ativo")
    periodoTresMeses.classList.remove("ativo")

    filtrarDespesas()
})


// Filtra as despesas do mês atual e dos dois meses anteriores.
periodoTresMeses.addEventListener("click", function () {

    periodoSelecionado = "tres-meses"

    // Destaca o botão dos últimos três meses e remove o destaque dos outros períodos.
    periodoTodas.classList.remove("ativo")
    periodoMes.classList.remove("ativo")
    periodoTresMeses.classList.add("ativo")

    filtrarDespesas()
})


// Ordena as despesas pela data, alternando entre crescente e decrescente.
ordenarData.addEventListener("click", function () {

    var tabela = document.querySelector("#tabela-despesa")
    var linhas = document.querySelectorAll(".item-despesa")

    // Converte a coleção de linhas em um array para poder usar o sort().
    var listaLinhas = Array.from(linhas)

    // Compara as datas de duas linhas para definir a ordem.
    listaLinhas.sort(function (linha1, linha2) {

        var data1 = linha1.dataset.data
        var data2 = linha2.dataset.data

        if (ordemData == "asc") {
            // Ordena da data mais antiga para a mais recente.
            return data1.localeCompare(data2)
        } else {
            // Ordena da data mais recente para a mais antiga.
            return data2.localeCompare(data1)
        }
    })

    // Reorganiza as linhas da tabela conforme a nova ordem.
    listaLinhas.forEach(function (linha) {
        tabela.appendChild(linha)
    })

    // Inverte o sentido da ordenação para o próximo clique.
    if (ordemData == "desc") {
        ordemData = "asc"
    } else {
        ordemData = "desc"
    }
})


// Ordena as despesas pelo valor, alternando entre crescente e decrescente.
ordenarValor.addEventListener("click", function () {

    var tabela = document.querySelector("#tabela-despesa")
    var linhas = document.querySelectorAll(".item-despesa")

    // Converte a coleção de linhas em um array para poder usar o sort().
    var listaLinhas = Array.from(linhas)

    // Compara os valores de duas despesas para definir a ordem.
    listaLinhas.sort(function (linha1, linha2) {

        // Converte os valores obtidos do HTML em números para compará-los corretamente.
        var valor1 = Number(linha1.dataset.valor)
        var valor2 = Number(linha2.dataset.valor)

        if (ordemValor == "asc") {
            // Ordena do menor valor para o maior.
            return valor1 - valor2
        } else {
            // Ordena do maior valor para o menor.
            return valor2 - valor1
        }
    })

    // Reorganiza as linhas da tabela conforme a nova ordem.
    listaLinhas.forEach(function (linha) {
        tabela.appendChild(linha)
    })

    // Inverte o sentido da ordenação para o próximo clique.
    if (ordemValor == "desc") {
        ordemValor = "asc"
    } else {
        ordemValor = "desc"
    }
})
