import { CATEGORY_SIGNS, labelFor } from "./js/catalog.js";
import { startGestureFeed } from "./js/gesture-feed.js";
import {
  MAX_GESTURE_CATEGORIES,
  MAX_GESTURE_TOPICS,
  MENU_LEVEL,
  createGestureMenu,
  gestureNumberFor,
} from "./js/gesture-menu.js";

const GESTURE_STATE_URL = "./gesture_state.json";
const NOTICE_DURATION_MS = 4000;

const els = {
  guide: document.querySelector(".panel--guide"),
  categories: document.querySelector("#categories"),
  signs: document.querySelector("#signs"),
  gestureLevel: document.querySelector("#gesture-level"),
  answerLabel: document.querySelector("#answer-label"),
  answerDate: document.querySelector("#answer-date"),
  answerTitle: document.querySelector("#answer-title"),
  answerText: document.querySelector("#answer-text"),
  disclaimer: document.querySelector("#disclaimer"),
  status: document.querySelector("#status"),
  statusText: document.querySelector("#status-text"),
  statusProgress: document.querySelector("#status-progress-fill"),
  statusNotice: document.querySelector("#status-notice"),
  openVlibras: document.querySelector("#open-vlibras"),
};

let knowledge = null;
let activeCategory = null;
let activeSign = null;
let gestureMenu = null;
let noticeTimer = null;

function formatDate(isoDate) {
  if (!isoDate) return "";
  const [year, month, day] = isoDate.split("-");
  return `Atualizado em ${day}/${month}/${year}`;
}

function categoryLabel(categoryId) {
  return knowledge.categories.find((c) => c.id === categoryId)?.label ?? categoryId;
}

function setStatus(kind, text, { progress = 0, detail = "" } = {}) {
  els.status.dataset.state = kind;
  els.statusText.textContent = text;
  els.statusText.title = detail;
  els.statusProgress.style.transform = `scaleX(${progress})`;
}

function showNotice(text) {
  els.statusNotice.textContent = text;
  window.clearTimeout(noticeTimer);
  noticeTimer = window.setTimeout(() => {
    els.statusNotice.textContent = "";
  }, NOTICE_DURATION_MS);
}

function createGestureBadge(number) {
  const badge = document.createElement("span");
  badge.className = "gesture-badge";
  badge.textContent = String(number);
  return badge;
}

function setAnswer(signId, { fromGesture = false } = {}) {
  const entry = knowledge.responses[signId];
  if (!entry) return;

  activeSign = signId;
  els.answerLabel.textContent = fromGesture ? "Escolhido por gesto" : "Resposta";
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

  signs.forEach((sign, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "sign";
    button.dataset.sign = sign;

    const number = gestureNumberFor(index, MAX_GESTURE_TOPICS);
    if (number !== null) button.append(createGestureBadge(number));

    const label = document.createElement("span");
    label.textContent = labelFor(sign);
    button.append(label);

    button.classList.toggle("is-active", sign === activeSign);
    button.addEventListener("click", () => setAnswer(sign));
    els.signs.append(button);
  });
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

function renderGestureLevel() {
  const { level, optionCount } = gestureMenu;
  els.guide.dataset.gestureLevel = level;
  els.gestureLevel.textContent =
    level === MENU_LEVEL.CATEGORIES
      ? `Gestos: mostre de 1 a ${optionCount} dedos para escolher a categoria.`
      : `Gestos: 1 a ${optionCount} dedos escolhem o assunto · punho fechado volta.`;
}

function selectCategoryByTouch(categoryId) {
  gestureMenu.selectCategoryByTouch(categoryId);
  selectCategory(categoryId);
  renderGestureLevel();
}

function renderCategories() {
  els.categories.replaceChildren();

  knowledge.categories.forEach((category, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "category";
    button.dataset.category = category.id;
    button.setAttribute("role", "tab");
    button.setAttribute("aria-selected", "false");

    const number = gestureNumberFor(index, MAX_GESTURE_CATEGORIES);
    if (number !== null) button.append(createGestureBadge(number));

    const label = document.createElement("span");
    label.className = "category__label";
    label.textContent = category.label;

    const hint = document.createElement("span");
    hint.className = "category__hint";
    hint.textContent = category.hint;

    button.append(label, hint);
    button.addEventListener("click", () => selectCategoryByTouch(category.id));
    els.categories.append(button);
  });
}

function handleGestureSelection(fingers) {
  const action = gestureMenu.apply(fingers);

  switch (action.type) {
    case "category":
      selectCategory(action.categoryId);
      showNotice(`${categoryLabel(action.categoryId)} · agora escolha o assunto`);
      break;
    case "topic":
      setAnswer(action.topicId, { fromGesture: true });
      showNotice(`Gesto · ${labelFor(action.topicId)}`);
      break;
    case "back":
      showNotice("Voltou para as categorias");
      break;
    default:
      showNotice(action.reason);
  }

  renderGestureLevel();
}

function findVlibrasAccessButton() {
  return (
    document.querySelector("[vw-access-button]") ||
    document.querySelector("div[vw] .access-button") ||
    document.querySelector(".vw-access-button") ||
    document.querySelector("div[vw] img")
  );
}

function openVlibrasForAnswer() {
  els.answerText.classList.add("is-fresh");
  els.answerText.focus({ preventScroll: false });
  els.answerText.scrollIntoView({ behavior: "smooth", block: "center" });

  const access = findVlibrasAccessButton();
  if (access) {
    access.click();
  }

  showNotice("VLibras · se o avatar pedir, toque no texto da resposta");
}

function bindVlibrasCta() {
  if (!els.openVlibras) return;
  els.openVlibras.addEventListener("click", openVlibrasForAnswer);
}

async function loadKnowledge() {
  const response = await fetch("./knowledge.json");
  if (!response.ok) {
    throw new Error(`Falha ao carregar knowledge.json (${response.status})`);
  }
  return response.json();
}

async function boot() {
  setStatus("loading", "Carregando conteúdo…");
  knowledge = await loadKnowledge();
  els.disclaimer.textContent = knowledge.meta.disclaimer;

  gestureMenu = createGestureMenu({
    categoryIds: knowledge.categories.map((category) => category.id),
    topicsByCategory: CATEGORY_SIGNS,
  });

  renderCategories();
  selectCategory(knowledge.categories[0].id);
  renderGestureLevel();
  setAnswer("ola");
  bindVlibrasCta();

  setStatus("loading", "Procurando a câmera de gestos…");
  startGestureFeed({
    url: GESTURE_STATE_URL,
    onState: ({ kind, text, progress, detail }) =>
      setStatus(kind, text, { progress, detail }),
    onSelection: handleGestureSelection,
  });
}

boot().catch((error) => {
  setStatus("error", "Não foi possível carregar o conteúdo");
  els.answerTitle.textContent = "Não foi possível carregar o preview";
  els.answerText.textContent =
    "Abra esta página por um servidor local (por exemplo: python -m http.server). " +
    "Abrir o arquivo direto no navegador bloqueia o carregamento do knowledge.json.";
  els.answerDate.textContent = "";
  console.error(error);
});
