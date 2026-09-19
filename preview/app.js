const SIGN_LABELS = {
  ola: "Olá",
  obrigado: "Obrigado",
  sim: "Sim",
  nao: "Não",
  ajuda: "Ajuda",
  repetir: "Repetir",
  onde: "Onde",
  como_chegar: "Como chegar",
  quanto_custa: "Quanto custa",
  que_horas: "Que horas",
  banheiro: "Banheiro",
  comer: "Comer",
  agua: "Água",
  hospital: "Hospital",
  policia: "Polícia",
  dinheiro: "Dinheiro",
  hotel: "Hotel",
  onibus: "Ônibus",
  taxi: "Táxi",
  aeroporto: "Aeroporto",
  praia: "Praia",
  orla: "Orla",
  mercado: "Mercado",
  museu: "Museu",
  igreja: "Igreja",
  centro: "Centro",
};

const CATEGORY_SIGNS = {
  servico: ["banheiro", "comer", "agua", "hospital", "policia", "dinheiro", "hotel"],
  transporte: ["onibus", "taxi", "aeroporto"],
  ponto_turistico: ["praia", "orla", "mercado", "museu", "igreja", "centro"],
  pergunta: ["onde", "como_chegar", "quanto_custa", "que_horas", "ajuda"],
};

const els = {
  categories: document.querySelector("#categories"),
  signs: document.querySelector("#signs"),
  answerLabel: document.querySelector("#answer-label"),
  answerDate: document.querySelector("#answer-date"),
  answerTitle: document.querySelector("#answer-title"),
  answerText: document.querySelector("#answer-text"),
  disclaimer: document.querySelector("#disclaimer"),
};

let knowledge = null;
let activeCategory = null;
let activeSign = null;

function labelFor(sign) {
  return SIGN_LABELS[sign] ?? sign;
}

function formatDate(isoDate) {
  if (!isoDate) return "";
  const [year, month, day] = isoDate.split("-");
  return `Atualizado em ${day}/${month}/${year}`;
}

function setAnswer(signId) {
  const entry = knowledge.responses[signId];
  if (!entry) return;

  activeSign = signId;
  els.answerLabel.textContent = "Resposta";
  els.answerTitle.textContent = entry.title;
  els.answerText.textContent = entry.text;
  els.answerDate.textContent = formatDate(entry.verified_at);

  els.answerText.classList.remove("is-fresh");
  // Force reflow so the highlight animation retriggers.
  void els.answerText.offsetWidth;
  els.answerText.classList.add("is-fresh");

  document.querySelectorAll(".sign").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.sign === signId);
  });
}

function renderSigns(categoryId) {
  const signs = CATEGORY_SIGNS[categoryId] ?? [];
  els.signs.replaceChildren();

  if (signs.length === 0) {
    const empty = document.createElement("p");
    empty.className = "signs__empty";
    empty.textContent = "Nenhum tema nesta categoria.";
    els.signs.append(empty);
    return;
  }

  for (const sign of signs) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "sign";
    button.dataset.sign = sign;
    button.textContent = labelFor(sign);
    button.addEventListener("click", () => setAnswer(sign));
    els.signs.append(button);
  }
}

function selectCategory(categoryId) {
  activeCategory = categoryId;

  document.querySelectorAll(".category").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.category === categoryId);
    button.setAttribute(
      "aria-selected",
      button.dataset.category === categoryId ? "true" : "false",
    );
  });

  renderSigns(categoryId);
}

function renderCategories() {
  els.categories.replaceChildren();

  for (const category of knowledge.categories) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "category";
    button.dataset.category = category.id;
    button.setAttribute("role", "tab");
    button.setAttribute("aria-selected", "false");

    const label = document.createElement("span");
    label.className = "category__label";
    label.textContent = category.label;

    const hint = document.createElement("span");
    hint.className = "category__hint";
    hint.textContent = category.hint;

    button.append(label, hint);
    button.addEventListener("click", () => selectCategory(category.id));
    els.categories.append(button);
  }
}

async function boot() {
  const response = await fetch("./knowledge.json");
  if (!response.ok) {
    throw new Error(`Falha ao carregar knowledge.json (${response.status})`);
  }

  knowledge = await response.json();
  els.disclaimer.textContent = knowledge.meta.disclaimer;

  renderCategories();
  selectCategory(knowledge.categories[0].id);
  setAnswer("ola");
}

boot().catch((error) => {
  els.answerTitle.textContent = "Nao foi possivel carregar o preview";
  els.answerText.textContent =
    "Abra esta pagina por um servidor local (por exemplo: python -m http.server). " +
    "Abrir o arquivo direto no navegador bloqueia o carregamento do knowledge.json.";
  els.answerDate.textContent = "";
  console.error(error);
});
