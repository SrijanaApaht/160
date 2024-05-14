document.getElementsByClassName("new-test-form")[0].addEventListener("submit", updateForm);

function updateForm(event) {
    event.preventDefault();
    let form = document.getElementsByClassName("new-test-form")[0];
    let numQuestions = document.getElementById("num_questions").value;
    document.getElementsByClassName("form-info-questions")[0].style.display = "none";
    for (let i = 0; i < numQuestions; i++) {
        let newLabel = document.createElement("p");
        newLabel.textContent = "Enter question " + (i + 1);
        newLabel.classList.add("new-test-question");
        let newQuestion = document.createElement("input");
        newQuestion.type = "text";
        newQuestion.setAttribute("required", "");
        newQuestion.setAttribute("autocomplete", "off");
        newQuestion.name = `question-${i + 1}`;
        form.appendChild(newLabel);
        form.appendChild(newQuestion); 
    }
    form.removeEventListener("submit", updateForm);
    form.setAttribute("method", "POST");
    let newSubmit = document.createElement("input");
    newSubmit.type = "submit";
    newSubmit.value = "Create";
    form.appendChild(newSubmit);
}

