document.addEventListener("DOMContentLoaded", function() {
    if (document.getElementById("quiz-container")) {
        loadQuiz();
    }
    if (document.getElementById("scoreboard")) {
        loadScoreboard();
    }
});

let currentQuestionIndex = 0;
let questions = [];

function loadQuiz() {
    fetch("/api/questions")
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
    }
}

function answer(choice) {
    let correct = questions[currentQuestionIndex].correct_option;
    if (choice === correct) {
        alert("Riktig!");
    } else {
        alert("Feil!");
    }
}

function nextQuestion() {
    if (currentQuestionIndex < questions.length - 1) {
        currentQuestionIndex++;
        showQuestion();
    } else {
        alert("Quiz ferdig!");
        window.location.href = "/scoreboard";
    }
}