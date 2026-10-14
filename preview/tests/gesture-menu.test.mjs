import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { CATEGORY_SIGNS } from "../js/catalog.js";
import {
  MENU_LEVEL,
  createGestureMenu,
  gestureNumberFor,
} from "../js/gesture-menu.js";

const CATEGORY_IDS = ["servico", "transporte", "ponto_turistico", "pergunta"];

function newMenu() {
  return createGestureMenu({
    categoryIds: CATEGORY_IDS,
    topicsByCategory: CATEGORY_SIGNS,
  });
}

describe("nível de categorias", () => {
  it("começa nas categorias", () => {
    const menu = newMenu();
    assert.equal(menu.level, MENU_LEVEL.CATEGORIES);
    assert.equal(menu.optionCount, 4);
  });

  it("1 a 4 dedos escolhem a categoria e entram nos assuntos", () => {
    const menu = newMenu();
    assert.deepEqual(menu.apply(2), { type: "category", categoryId: "transporte" });
    assert.equal(menu.level, MENU_LEVEL.TOPICS);
    assert.equal(menu.categoryId, "transporte");
  });

  it("ignora 0 e 5 dedos com um motivo", () => {
    for (const fingers of [0, 5]) {
      const menu = newMenu();
      const action = menu.apply(fingers);
      assert.equal(action.type, "ignored");
      assert.match(action.reason, /1 a 4 dedos/);
      assert.equal(menu.level, MENU_LEVEL.CATEGORIES);
    }
  });
});

describe("nível de assuntos", () => {
  it("escolhe o assunto pela posição e continua no mesmo nível", () => {
    const menu = newMenu();
    menu.apply(2);
    assert.deepEqual(menu.apply(2), {
      type: "topic",
      categoryId: "transporte",
      topicId: "taxi",
    });
    assert.equal(menu.level, MENU_LEVEL.TOPICS);
  });

  it("punho fechado volta para as categorias", () => {
    const menu = newMenu();
    menu.apply(3);
    assert.deepEqual(menu.apply(0), { type: "back", categoryId: "ponto_turistico" });
    assert.equal(menu.level, MENU_LEVEL.CATEGORIES);
  });

  it("ignora contagem maior que o número de assuntos", () => {
    const menu = newMenu();
    menu.apply(2);
    const action = menu.apply(4);
    assert.equal(action.type, "ignored");
    assert.match(action.reason, /3 assuntos/);
  });

  it("limita a 5 assuntos por gesto mesmo em categorias maiores", () => {
    const menu = newMenu();
    menu.apply(1);
    assert.equal(menu.optionCount, 5);
    assert.equal(menu.apply(5).topicId, "policia");
  });
});

describe("toque e validação", () => {
  it("o toque numa categoria sincroniza o nível", () => {
    const menu = newMenu();
    menu.selectCategoryByTouch("pergunta");
    assert.equal(menu.level, MENU_LEVEL.TOPICS);
    assert.equal(menu.apply(1).topicId, "onde");
  });

  it("toque em categoria desconhecida não muda nada", () => {
    const menu = newMenu();
    menu.selectCategoryByTouch("inexistente");
    assert.equal(menu.level, MENU_LEVEL.CATEGORIES);
  });

  it("rejeita contagens inválidas", () => {
    for (const fingers of [-1, 1.5, null, undefined, "2"]) {
      assert.equal(newMenu().apply(fingers).type, "ignored");
    }
  });
});

describe("gestureNumberFor", () => {
  it("numera a partir de 1 dentro do limite", () => {
    assert.equal(gestureNumberFor(0, 5), 1);
    assert.equal(gestureNumberFor(4, 5), 5);
  });

  it("devolve null para itens só por toque", () => {
    assert.equal(gestureNumberFor(5, 5), null);
  });
});
