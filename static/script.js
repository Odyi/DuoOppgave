document.addEventListener("DOMContentLoaded", function() {
    if (document.getElementById("quiz-container")) {
        const quizId = document.getElementById("quiz-container").getAttribute("data-quiz-id");
        loadQuiz(quizId);
    }
    if (document.getElementById("scoreboard")) {
        loadScoreboard();
    }
});

function toggleMenu() {
    var menu = document.getElementById("nav-menu");
    if (menu.style.display === "block") {
        menu.style.display = "none";
    } else {
        menu.style.display = "block";
    }
}

let currentQuestionIndex = 0;
let questions = [];
let userAnswers = {};

function loadQuiz(quizId) {
    fetch(`/api/questions/${quizId}`)
        .then(response => response.json())
        .then(data => {
            questions = data;
            showQuestion();
        });
}

function showQuestion() {
    let question = questions[currentQuestionIndex];
    document.getElementById("question-text").textContent = question.question;
    let buttons = document.getElementsByClassName("option");
    for (let i = 0; i < buttons.length; i++) {
        buttons[i].textContent = question["option" + (i + 1)];
        buttons[i].classList.remove("answered");
    }
}

function answer(questionId, choice) {
    userAnswers[questionId] = choice;
    markAnswered(questionId, choice);
}

function markAnswered(questionId, choice) {
    let questionDiv = document.querySelector(`.question[data-question-id='${questionId}']`);
    let buttons = questionDiv.getElementsByClassName("option");
    for (let i = 0; i < buttons.length; i++) {
        buttons[i].classList.remove("answered");
        if (i === choice - 1) {
            buttons[i].classList.add("answered");
        }
    }
}

function nextQuestion() {
    if (currentQuestionIndex < questions.length - 1) {
        currentQuestionIndex++;
        showQuestion();
    } else {
        alert("Ingen flere spørsmål. Send inn din quiz!");
    }
}

function submitQuiz() {
    const quizId = document.getElementById("quiz-container").getAttribute("data-quiz-id");
    fetch(`/submit_quiz/${quizId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ answers: userAnswers })
    })
    .then(response => response.json())
    .then(data => {
        alert("Din poengsum er: " + data.score);
        window.location.href = "/scoreboard";
    });
}