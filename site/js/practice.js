(function () {
  "use strict";

  const bank = window.POM_QUESTION_BANK;
  if (!bank) {
    document.body.innerHTML =
      "<p>Practice question bank could not be loaded.</p>";
    return;
  }

  const STORAGE_KEY = "pom-practice-completed-v1";
  const typeLabels = { sba: "SBA", vsaq: "VSAQ", saq: "SAQ" };
  const levelLabels = {
    recall: "Recall",
    understanding: "Understanding",
    application: "Application",
    inference: "Inference",
  };

  const elements = {
    setup: document.getElementById("practice-setup"),
    completionGrid: document.getElementById("completion-grid"),
    topic: document.getElementById("practice-topic"),
    availability: document.getElementById("topic-availability"),
    count: document.getElementById("question-count"),
    start: document.getElementById("start-practice"),
    session: document.getElementById("practice-session"),
    results: document.getElementById("practice-results"),
    sessionLabel: document.getElementById("session-label"),
    progressLabel: document.getElementById("progress-label"),
    progressBar: document.getElementById("progress-bar"),
    scorePill: document.getElementById("score-pill"),
    typeBadge: document.getElementById("question-type-badge"),
    levelBadge: document.getElementById("question-level-badge"),
    source: document.getElementById("question-source"),
    question: document.getElementById("question-text"),
    answerArea: document.getElementById("answer-area"),
    feedback: document.getElementById("answer-feedback"),
    submit: document.getElementById("submit-answer"),
    next: document.getElementById("next-question"),
    quit: document.getElementById("quit-practice"),
    newSession: document.getElementById("new-session"),
    resultScore: document.getElementById("result-score"),
    resultPercent: document.getElementById("result-percent"),
    resultsTitle: document.getElementById("results-title"),
    resultsSummary: document.getElementById("results-summary"),
  };

  const state = {
    questions: [],
    currentIndex: 0,
    score: 0,
    answered: 0,
    type: "sba",
    topicName: "",
    awaitingSelfMark: false,
  };
  const completed = loadCompletion();

  function loadCompletion() {
    const progress = {};
    bank.topics.forEach((topic) => {
      progress[topic.id] = { sba: [], vsaq: [], saq: [] };
    });

    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (!saved || typeof saved !== "object") return progress;
      bank.topics.forEach((topic) => {
        Object.keys(typeLabels).forEach((type) => {
          if (Array.isArray(saved[topic.id]?.[type])) {
            progress[topic.id][type] = [
              ...new Set(saved[topic.id][type].filter(String)),
            ];
          }
        });
      });
    } catch (_error) {
      // Storage can be unavailable in private browsing.
    }
    return progress;
  }

  function saveCompletion() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(completed));
    } catch (_error) {
      // Keep in-memory progress when persistent storage is unavailable.
    }
  }

  function questionId(question, type) {
    const value = `${question.topicId}|${type}|${question.lecture}|${question.q}`;
    let hash = 2166136261;
    for (let index = 0; index < value.length; index += 1) {
      hash ^= value.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return (hash >>> 0).toString(36);
  }

  function completionCount(topicId, type) {
    if (topicId === "all") {
      return bank.topics.reduce(
        (total, topic) => total + completed[topic.id][type].length,
        0,
      );
    }
    return completed[topicId][type].length;
  }

  function recordCurrentQuestionCompleted() {
    const question = state.questions[state.currentIndex];
    const values = completed[question.topicId][state.type];
    const id = questionId(question, state.type);
    if (!values.includes(id)) {
      values.push(id);
      saveCompletion();
      renderCompletion();
    }
  }

  function renderCompletion() {
    elements.completionGrid.replaceChildren();

    bank.topics.forEach((topic) => {
      const card = document.createElement("section");
      card.className = "completion-topic";
      const heading = document.createElement("h3");
      heading.textContent = topic.name;
      card.appendChild(heading);

      Object.keys(typeLabels).forEach((type) => {
        const total = bank.questions[topic.id][type].length;
        const done = Math.min(completionCount(topic.id, type), total);
        const row = document.createElement("div");
        row.className = "completion-row";

        const label = document.createElement("span");
        label.textContent = typeLabels[type];
        const count = document.createElement("strong");
        count.textContent = `${done.toLocaleString()} / ${total.toLocaleString()}`;
        const bar = document.createElement("div");
        bar.className = "completion-bar";
        const fill = document.createElement("span");
        fill.style.width = total ? `${(done / total) * 100}%` : "0%";
        bar.appendChild(fill);
        row.append(label, count, bar);
        card.appendChild(row);
      });
      elements.completionGrid.appendChild(card);
    });
  }

  function shuffle(values) {
    const result = values.slice();
    for (let index = result.length - 1; index > 0; index -= 1) {
      const swapIndex = Math.floor(Math.random() * (index + 1));
      [result[index], result[swapIndex]] = [
        result[swapIndex],
        result[index],
      ];
    }
    return result;
  }

  function selectedType() {
    return document.querySelector(
      'input[name="question-type"]:checked',
    ).value;
  }

  function populateTopics() {
    const allOption = document.createElement("option");
    allOption.value = "all";
    allOption.textContent = "All available topics";
    elements.topic.appendChild(allOption);

    bank.topics.forEach((topic) => {
      const option = document.createElement("option");
      option.value = topic.id;
      option.textContent = topic.name;
      elements.topic.appendChild(option);
    });
  }

  function questionsFor(topicId, type) {
    if (topicId !== "all") {
      const topic = bank.topics.find((item) => item.id === topicId);
      return (bank.questions[topicId][type] || []).map((question) => ({
        ...question,
        topicId,
        topicName: topic.name,
      }));
    }

    return bank.topics.flatMap((topic) =>
      (bank.questions[topic.id][type] || []).map((question) => ({
        ...question,
        topicId: topic.id,
        topicName: topic.name,
      })),
    );
  }

  /** Prefer a balanced mix of cognitive levels when sampling. */
  function sampleBalanced(pool, count) {
    if (pool.length <= count) return shuffle(pool);
    const byLevel = {};
    pool.forEach((q) => {
      const level = q.level || "recall";
      if (!byLevel[level]) byLevel[level] = [];
      byLevel[level].push(q);
    });
    Object.keys(byLevel).forEach((level) => {
      byLevel[level] = shuffle(byLevel[level]);
    });
    const levels = shuffle(Object.keys(byLevel));
    const picked = [];
    let i = 0;
    while (picked.length < count) {
      const level = levels[i % levels.length];
      if (byLevel[level] && byLevel[level].length) {
        picked.push(byLevel[level].pop());
      }
      i += 1;
      if (i > count * 8) break;
    }
    // Fill any shortfall from remaining pool
    if (picked.length < count) {
      const used = new Set(picked);
      const rest = shuffle(pool.filter((q) => !used.has(q)));
      picked.push(...rest.slice(0, count - picked.length));
    }
    return shuffle(picked);
  }

  function updateAvailability() {
    const type = selectedType();
    const available = questionsFor(elements.topic.value, type).length;
    const done = Math.min(
      completionCount(elements.topic.value, type),
      available,
    );
    const typeName = type.toUpperCase();
    elements.availability.textContent =
      `${done.toLocaleString()} of ${available.toLocaleString()} ${typeName} questions completed`;
    const maximum = Math.min(50, available);
    elements.count.max = String(Math.max(1, maximum));
    if (Number(elements.count.value) > maximum && maximum > 0) {
      elements.count.value = String(maximum);
    }
    if (Number(elements.count.value) < 1 && maximum > 0) {
      elements.count.value = "1";
    }
    elements.start.disabled = available === 0;
  }

  function startSession() {
    const topicId = elements.topic.value;
    state.type = selectedType();
    const pool = questionsFor(topicId, state.type);
    const requested = Math.max(1, Number(elements.count.value) || 1);
    const topic =
      topicId === "all"
        ? { name: "All topics" }
        : bank.topics.find((item) => item.id === topicId);

    state.questions = sampleBalanced(pool, Math.min(requested, pool.length)).map(
      (question) => ({
        ...question,
        shuffledOptions:
          state.type === "sba" ? shuffle(question.options) : undefined,
      }),
    );
    state.currentIndex = 0;
    state.score = 0;
    state.answered = 0;
    state.topicName = topic.name;
    state.awaitingSelfMark = false;

    elements.setup.hidden = true;
    elements.results.hidden = true;
    elements.session.hidden = false;
    elements.sessionLabel.textContent = `${topic.name} · ${state.type.toUpperCase()}`;
    renderQuestion();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function renderQuestion() {
    const current = state.questions[state.currentIndex];
    const position = state.currentIndex + 1;
    const total = state.questions.length;

    elements.progressLabel.textContent = `Question ${position} of ${total}`;
    elements.progressBar.style.width = `${(position / total) * 100}%`;
    elements.scorePill.textContent = `Score: ${state.score}`;
    elements.typeBadge.textContent = state.type.toUpperCase();
    const level = current.level || "recall";
    elements.levelBadge.textContent = levelLabels[level] || level;
    elements.levelBadge.dataset.level = level;
    elements.source.textContent = `${current.topicName} · ${current.lecture}`;
    elements.question.textContent = current.q;
    elements.answerArea.replaceChildren();
    elements.feedback.replaceChildren();
    elements.feedback.hidden = true;
    elements.submit.hidden = false;
    elements.submit.disabled = false;
    elements.submit.textContent =
      state.type === "saq" ? "Show model answer" : "Submit answer";
    elements.next.hidden = true;
    state.awaitingSelfMark = false;

    if (state.type === "sba") renderSba(current);
    if (state.type === "vsaq") renderVsaq();
    if (state.type === "saq") renderSaq();
  }

  function renderSba(current) {
    const fieldset = document.createElement("fieldset");
    fieldset.className = "sba-options";
    fieldset.setAttribute("aria-label", "Answer options");

    current.shuffledOptions.forEach((option, index) => {
      const label = document.createElement("label");
      label.className = "sba-option";

      const input = document.createElement("input");
      input.type = "radio";
      input.name = "sba-answer";
      input.value = option;

      const letter = document.createElement("span");
      letter.className = "option-letter";
      letter.textContent = String.fromCharCode(65 + index);

      const text = document.createElement("span");
      text.textContent = option;

      label.append(input, letter, text);
      fieldset.appendChild(label);
    });
    elements.answerArea.appendChild(fieldset);
  }

  function renderVsaq() {
    const label = document.createElement("label");
    label.className = "answer-input-label";
    label.setAttribute("for", "vsaq-answer");
    label.textContent = "Your answer (maximum four words)";

    const input = document.createElement("input");
    input.id = "vsaq-answer";
    input.className = "practice-text-input";
    input.type = "text";
    input.maxLength = 60;
    input.autocomplete = "off";
    input.placeholder = "Type up to four words";
    input.addEventListener("input", enforceFourWords);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") submitAnswer();
    });

    const counter = document.createElement("span");
    counter.id = "vsaq-word-count";
    counter.className = "word-count";
    counter.textContent = "0 / 4 words";

    elements.answerArea.append(label, input, counter);
    setTimeout(() => input.focus(), 0);
  }

  function enforceFourWords(event) {
    const words = event.target.value.trim().split(/\s+/).filter(Boolean);
    if (words.length > 4) {
      event.target.value = words.slice(0, 4).join(" ");
    }
    const count = event.target.value.trim()
      ? event.target.value.trim().split(/\s+/).length
      : 0;
    document.getElementById("vsaq-word-count").textContent =
      `${count} / 4 words`;
  }

  function renderSaq() {
    const label = document.createElement("label");
    label.className = "answer-input-label";
    label.setAttribute("for", "saq-answer");
    label.textContent = "Write a structured answer in multiple sentences";

    const textarea = document.createElement("textarea");
    textarea.id = "saq-answer";
    textarea.className = "practice-textarea";
    textarea.rows = 8;
    textarea.placeholder =
      "Explain your answer, including the key mechanisms or clinical points…";

    elements.answerArea.append(label, textarea);
    setTimeout(() => textarea.focus(), 0);
  }

  function normalizeAnswer(value) {
    return value
      .toLocaleLowerCase()
      .replace(/[^a-z0-9]+/g, " ")
      .trim()
      .replace(/\s+/g, " ");
  }

  function vsaqMatches(userValue, accepted) {
    const user = normalizeAnswer(userValue);
    const answers = Array.isArray(accepted) ? accepted : [accepted];
    return answers.some((answer) => normalizeAnswer(answer) === user);
  }

  function submitAnswer() {
    const current = state.questions[state.currentIndex];

    if (state.type === "sba") {
      const selected = document.querySelector(
        'input[name="sba-answer"]:checked',
      );
      if (!selected) {
        showPrompt("Choose an answer before submitting.");
        return;
      }
      const correct = selected.value === current.a;
      markSbaOptions(current.a);
      completeAutomaticQuestion(correct, current.a);
      return;
    }

    if (state.type === "vsaq") {
      const input = document.getElementById("vsaq-answer");
      if (!input.value.trim()) {
        showPrompt("Enter an answer before submitting.");
        return;
      }
      const correct = vsaqMatches(input.value, current.a);
      input.disabled = true;
      const model = Array.isArray(current.a) ? current.a[0] : current.a;
      completeAutomaticQuestion(correct, model);
      return;
    }

    const textarea = document.getElementById("saq-answer");
    if (!textarea.value.trim()) {
      showPrompt("Write your answer before revealing the model answer.");
      return;
    }
    textarea.disabled = true;
    showSaqModelAnswer(current.a);
  }

  function markSbaOptions(correctAnswer) {
    document.querySelectorAll(".sba-option").forEach((label) => {
      const input = label.querySelector("input");
      input.disabled = true;
      if (input.value === correctAnswer) label.classList.add("is-correct");
      if (input.checked && input.value !== correctAnswer) {
        label.classList.add("is-incorrect");
      }
    });
  }

  function completeAutomaticQuestion(correct, modelAnswer) {
    state.answered += 1;
    if (correct) state.score += 1;
    recordCurrentQuestionCompleted();
    elements.scorePill.textContent = `Score: ${state.score}`;

    elements.feedback.replaceChildren();
    elements.feedback.className =
      `answer-feedback ${correct ? "feedback-correct" : "feedback-incorrect"}`;

    const heading = document.createElement("strong");
    heading.textContent = correct ? "Correct" : "Not quite";
    const answer = document.createElement("p");
    answer.textContent = `Model answer: ${modelAnswer}`;
    elements.feedback.append(heading, answer);

    const explanation = state.questions[state.currentIndex].explanation;
    if (explanation) {
      const why = document.createElement("p");
      why.textContent = explanation;
      elements.feedback.appendChild(why);
    }

    elements.feedback.hidden = false;
    elements.submit.hidden = true;
    elements.next.hidden = false;
    elements.next.textContent =
      state.currentIndex === state.questions.length - 1
        ? "View results"
        : "Next question";
  }

  function showSaqModelAnswer(modelAnswer) {
    elements.feedback.replaceChildren();
    elements.feedback.className = "answer-feedback feedback-model";

    const heading = document.createElement("strong");
    heading.textContent = "Model answer";
    const answer = document.createElement("p");
    answer.textContent = modelAnswer;
    const prompt = document.createElement("p");
    prompt.className = "self-mark-prompt";
    prompt.textContent =
      "Did your answer cover the important points in the model answer?";

    const controls = document.createElement("div");
    controls.className = "self-mark-controls";
    const review = document.createElement("button");
    review.type = "button";
    review.className = "practice-secondary";
    review.dataset.selfMark = "review";
    review.textContent = "Needs review";
    const correct = document.createElement("button");
    correct.type = "button";
    correct.className = "practice-primary";
    correct.dataset.selfMark = "correct";
    correct.textContent = "Covered the key points";
    controls.append(review, correct);

    elements.feedback.append(heading, answer, prompt, controls);
    elements.feedback.hidden = false;
    elements.submit.hidden = true;
    state.awaitingSelfMark = true;
  }

  function applySelfMark(mark) {
    if (!state.awaitingSelfMark) return;
    state.awaitingSelfMark = false;
    state.answered += 1;
    if (mark === "correct") state.score += 1;
    recordCurrentQuestionCompleted();
    elements.scorePill.textContent = `Score: ${state.score}`;
    document.querySelectorAll("[data-self-mark]").forEach((button) => {
      button.disabled = true;
    });
    elements.next.hidden = false;
    elements.next.textContent =
      state.currentIndex === state.questions.length - 1
        ? "View results"
        : "Next question";
  }

  function showPrompt(message) {
    elements.feedback.className = "answer-feedback feedback-prompt";
    elements.feedback.textContent = message;
    elements.feedback.hidden = false;
  }

  function nextQuestion() {
    if (state.currentIndex >= state.questions.length - 1) {
      showResults(false);
      return;
    }
    state.currentIndex += 1;
    elements.submit.textContent = "Submit answer";
    renderQuestion();
    document
      .querySelector(".practice-status")
      .scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function showResults(endedEarly) {
    elements.session.hidden = true;
    elements.results.hidden = false;
    const denominator = endedEarly ? state.answered : state.questions.length;
    const percent = denominator
      ? Math.round((state.score / denominator) * 100)
      : 0;

    elements.resultsTitle.textContent = endedEarly
      ? "Session ended"
      : "Practice complete";
    elements.resultScore.textContent = `${state.score}/${denominator}`;
    elements.resultPercent.textContent = `${percent}%`;
    elements.resultsSummary.textContent =
      state.type === "saq"
        ? "SAQs are self-marked against the model answer."
        : `You completed ${denominator} ${state.type.toUpperCase()} questions from ${state.topicName}.`;
    elements.results.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function resetToSetup() {
    elements.results.hidden = true;
    elements.session.hidden = true;
    elements.setup.hidden = false;
    elements.submit.textContent = "Submit answer";
    renderCompletion();
    updateAvailability();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  elements.topic.addEventListener("change", updateAvailability);
  elements.count.addEventListener("input", updateAvailability);
  document.querySelectorAll('input[name="question-type"]').forEach((input) => {
    input.addEventListener("change", updateAvailability);
  });
  elements.start.addEventListener("click", startSession);
  elements.submit.addEventListener("click", submitAnswer);
  elements.next.addEventListener("click", nextQuestion);
  elements.quit.addEventListener("click", () => showResults(true));
  elements.newSession.addEventListener("click", resetToSetup);
  elements.feedback.addEventListener("click", (event) => {
    const button = event.target.closest("[data-self-mark]");
    if (button) applySelfMark(button.dataset.selfMark);
  });

  populateTopics();
  renderCompletion();
  updateAvailability();
})();
