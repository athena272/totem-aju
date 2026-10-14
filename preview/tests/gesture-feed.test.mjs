import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  FEED_KIND,
  STALE_AFTER_MS,
  createGestureFeed,
  describeGestureState,
} from "../js/gesture-feed.js";

const NOW = 1_000_000;

function state(overrides = {}) {
  return {
    status: "tracking",
    updated_at_ms: NOW,
    fingers: 2,
    progress: 0.5,
    awaiting_release: false,
    selection: null,
    message: null,
    ...overrides,
  };
}

describe("describeGestureState", () => {
  it("sem arquivo, a câmera está desligada", () => {
    const described = describeGestureState(null, NOW);
    assert.equal(described.kind, FEED_KIND.OFFLINE);
    assert.match(described.text, /use o toque/);
  });

  it("starting mostra carregamento mesmo sem atualizações recentes", () => {
    const old = state({ status: "starting", updated_at_ms: NOW - 10_000 });
    assert.equal(describeGestureState(old, NOW).kind, FEED_KIND.STARTING);
  });

  it("estado parado há mais que o limite fica sem resposta", () => {
    const old = state({ updated_at_ms: NOW - STALE_AFTER_MS - 1 });
    assert.equal(describeGestureState(old, NOW).kind, FEED_KIND.STALE);
  });

  it("sem mão, procura a mão", () => {
    const described = describeGestureState(state({ status: "no_hand", fingers: null }), NOW);
    assert.equal(described.kind, FEED_KIND.SEARCHING);
  });

  it("com mão, mostra o progresso de segurar", () => {
    const described = describeGestureState(state(), NOW);
    assert.equal(described.kind, FEED_KIND.HOLDING);
    assert.equal(described.progress, 0.5);
    assert.match(described.text, /2 dedos/);
  });

  it("depois de escolher, pede para abaixar a mão", () => {
    const described = describeGestureState(state({ awaiting_release: true }), NOW);
    assert.equal(described.kind, FEED_KIND.CHOSEN);
    assert.equal(described.progress, 1);
  });

  it("punho fechado tem texto próprio", () => {
    const described = describeGestureState(state({ fingers: 0 }), NOW);
    assert.match(described.text, /punho fechado/);
  });

  it("erro traz a mensagem como detalhe", () => {
    const described = describeGestureState(
      state({ status: "error", message: "câmera ocupada" }),
      NOW,
    );
    assert.equal(described.kind, FEED_KIND.ERROR);
    assert.equal(described.detail, "câmera ocupada");
  });

  it("stopped vale mesmo se for antigo", () => {
    const old = state({ status: "stopped", updated_at_ms: 0 });
    assert.equal(describeGestureState(old, NOW).kind, FEED_KIND.STOPPED);
  });
});

function jsonResponse(body) {
  return { ok: true, json: async () => body };
}

function scriptedFetch(responses) {
  const queue = [...responses];
  return async () => {
    const next = queue.shift();
    if (next instanceof Error) throw next;
    return next;
  };
}

function newFeed(responses) {
  const states = [];
  const selections = [];
  const feed = createGestureFeed({
    url: "./gesture_state.json",
    fetchImpl: scriptedFetch(responses),
    now: () => NOW,
    onState: (described) => states.push(described),
    onSelection: (fingers) => selections.push(fingers),
  });
  return { feed, states, selections };
}

const selection = (fingers, eventId) => ({ fingers, event_id: eventId, at_ms: NOW });

describe("createGestureFeed", () => {
  it("404 e falha de rede contam como desligada", async () => {
    const { feed, states } = newFeed([{ ok: false }, new Error("rede")]);
    assert.equal(await feed.pollOnce(), false);
    assert.equal(await feed.pollOnce(), false);
    assert.deepEqual(
      states.map((s) => s.kind),
      [FEED_KIND.OFFLINE, FEED_KIND.OFFLINE],
    );
  });

  it("não reaplica a escolha que já estava no arquivo ao abrir a página", async () => {
    const { feed, selections } = newFeed([
      jsonResponse(state({ selection: selection(3, 10) })),
      jsonResponse(state({ selection: selection(3, 10) })),
    ]);
    await feed.pollOnce();
    await feed.pollOnce();
    assert.deepEqual(selections, []);
  });

  it("entrega cada nova escolha uma única vez", async () => {
    const { feed, selections } = newFeed([
      jsonResponse(state()),
      jsonResponse(state({ selection: selection(2, 11) })),
      jsonResponse(state({ selection: selection(2, 11) })),
      jsonResponse(state({ selection: selection(0, 12) })),
    ]);
    for (let i = 0; i < 4; i += 1) await feed.pollOnce();
    assert.deepEqual(selections, [2, 0]);
  });

  it("a primeira leitura com a câmera ligada define a referência", async () => {
    const { feed, selections } = newFeed([
      { ok: false },
      jsonResponse(state({ status: "starting" })),
      jsonResponse(state({ selection: selection(1, 20) })),
    ]);
    for (let i = 0; i < 3; i += 1) await feed.pollOnce();
    assert.deepEqual(selections, [1]);
  });

  it("JSON ilegível mantém o último estado exibido", async () => {
    const broken = { ok: true, json: async () => { throw new SyntaxError("parcial"); } };
    const { feed, states } = newFeed([jsonResponse(state()), broken]);
    await feed.pollOnce();
    assert.equal(await feed.pollOnce(), true);
    assert.equal(states.length, 1);
  });
});
