// Navegação do menu por dedos, sem DOM: recebe uma contagem confirmada e
// devolve a ação correspondente ao nível atual.

export const MENU_LEVEL = Object.freeze({
  CATEGORIES: "categories",
  TOPICS: "topics",
});

export const BACK_FINGERS = 0;
export const MAX_GESTURE_CATEGORIES = 4;
export const MAX_GESTURE_TOPICS = 5;

/** Número do gesto para o item na posição `index`, ou null se só por toque. */
export function gestureNumberFor(index, limit) {
  return index >= 0 && index < limit ? index + 1 : null;
}

function plural(count, singular, pluralForm) {
  return `${count} ${count === 1 ? singular : pluralForm}`;
}

export function createGestureMenu({ categoryIds, topicsByCategory }) {
  const gestureCategories = categoryIds.slice(0, MAX_GESTURE_CATEGORIES);
  let level = MENU_LEVEL.CATEGORIES;
  let categoryId = null;

  function gestureTopicsOf(id) {
    return (topicsByCategory[id] ?? []).slice(0, MAX_GESTURE_TOPICS);
  }

  function enterCategory(id) {
    level = MENU_LEVEL.TOPICS;
    categoryId = id;
  }

  function applyOnCategories(fingers) {
    if (fingers >= 1 && fingers <= gestureCategories.length) {
      const id = gestureCategories[fingers - 1];
      enterCategory(id);
      return { type: "category", categoryId: id };
    }
    return {
      type: "ignored",
      reason: `Mostre de 1 a ${gestureCategories.length} dedos para escolher a categoria.`,
    };
  }

  function applyOnTopics(fingers) {
    if (fingers === BACK_FINGERS) {
      const previous = categoryId;
      level = MENU_LEVEL.CATEGORIES;
      return { type: "back", categoryId: previous };
    }

    const topics = gestureTopicsOf(categoryId);
    if (fingers >= 1 && fingers <= topics.length) {
      return { type: "topic", categoryId, topicId: topics[fingers - 1] };
    }
    return {
      type: "ignored",
      reason:
        `Esta categoria tem ${plural(topics.length, "assunto", "assuntos")} por gesto. ` +
        "Use menos dedos ou o punho fechado para voltar.",
    };
  }

  return {
    get level() {
      return level;
    },

    get categoryId() {
      return categoryId;
    },

    /** Quantidade de opções que o nível atual aceita por gesto. */
    get optionCount() {
      return level === MENU_LEVEL.CATEGORIES
        ? gestureCategories.length
        : gestureTopicsOf(categoryId).length;
    },

    /** Mantém o menu em sincronia quando a categoria é escolhida por toque. */
    selectCategoryByTouch(id) {
      if (categoryIds.includes(id)) enterCategory(id);
    },

    apply(fingers) {
      if (!Number.isInteger(fingers) || fingers < 0) {
        return { type: "ignored", reason: "Contagem de dedos inválida." };
      }
      return level === MENU_LEVEL.CATEGORIES
        ? applyOnCategories(fingers)
        : applyOnTopics(fingers);
    },
  };
}
