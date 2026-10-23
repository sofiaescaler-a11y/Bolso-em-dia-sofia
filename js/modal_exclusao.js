// busca todos os elementos HTML que possuem a classe abrir-modal-exclusao
var botoesExcluir = document.querySelectorAll(".abrir-modal-exclusao")
var modalExclusao = document.querySelector("#modal-exclusao")
var cancelarExclusao = document.querySelector("#cancelar-exclusao")
var formExclusao = document.querySelector("#form-exclusao")

// percorre todos os botões de excluir e cria uma função que recebe um botão por vez
botoesExcluir.forEach(function (botao) {

    // quando o evento clique ocorrer...
    botao.addEventListener("click", function () {

        // Define para qual rota o formulário será enviado, usando o endereço do botão de excluir clicado
        formExclusao.action = botao.dataset.url
        // muda o modal de exclusão de 'None' para 'Flex', tornando possível aparecer na tela
        modalExclusao.style.display = "flex"
    })
})

// se o usuário cancelar a exclusão, o modal continua 'None'
cancelarExclusao.addEventListener("click", function () {
    modalExclusao.style.display = "none"
})