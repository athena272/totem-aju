// Leitura do estado publicado pelo totem-menu (preview/gesture_state.json).

export const FEED_KIND = Object.freeze({
  OFFLINE: "offline",
  STARTING: "starting",
  SEARCHING: "searching",
  HOLDING: "holding",
  CHOSEN: "chosen",
  STALE: "stale",
  STOPPED: "stopped",
  ERROR: "error",
});

// Sem atualização por mais que isso, o processo da câmera provavelmente travou.
export const STALE_AFTER_MS = 3000;
// Carregar o MediaPipe leva alguns segundos sem nenhuma gravação nova.
export const STARTING_TIMEOUT_MS = 60000;

const TOUCH_HINT = "use o toque";

function fingersText(count) {
  if (count === 0) return "o punho fechado";
  return `${count} ${count === 1 ? "dedo" : "dedos"}`;
}

function capitalize(text) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/**
 * Traduz o JSON publicado em algo exibível. `state` nulo significa que o
 * arquivo não existe ou não pôde ser lido (câmera desligada).
 */
export function describeGestureState(state, nowMs) {
  if (!state) {
    return {
      kind: FEED_KIND.OFFLINE,
      text: `Câmera de gestos desligada · ${TOUCH_HINT}`,
      progress: 0,
    };
  }

  if (state.status === "stopped") {
    return {
      kind: FEED_KIND.STOPPED,
      text: `Câmera de gestos encerrada · ${TOUCH_HINT}`,
      progress: 0,
    };
  }

  if (state.status === "error") {
    return {
      kind: FEED_KIND.ERROR,
      text: `Câmera de gestos com problema · ${TOUCH_HINT}`,
      detail: state.message ?? "",
      progress: 0,
    };
  }

  const age = nowMs - (state.updated_at_ms ?? 0);
  const timeout = state.status === "starting" ? STARTING_TIMEOUT_MS : STALE_AFTER_MS;
  if (age > timeout) {
    return {
      kind: FEED_KIND.STALE,
      text: `Câmera de gestos sem resposta · ${TOUCH_HINT}`,
      progress: 0,
    };
  }

  if (state.status === "starting") {
    return {
      kind: FEED_KIND.STARTING,
      text: "Iniciando câmera de gestos…",
      progress: 0,
    };
  }

  if (state.status === "tracking" && Number.isInteger(state.fingers)) {
    if (state.awaiting_release) {
      return {
        kind: FEED_KIND.CHOSEN,
        text: `${capitalize(fingersText(state.fingers))} reconhecido · abaixe a mão para repetir`,
        progress: 1,
      };
    }
    return {
      kind: FEED_KIND.HOLDING,
      text: `Segure ${fingersText(state.fingers)} sem mexer…`,
      progress: Math.min(Math.max(state.progress ?? 0, 0), 1),
    };
  }

  return {
    kind: FEED_KIND.SEARCHING,
    text: "Procurando sua mão…",
    progress: 0,
  };
}

/**
 * Busca o estado uma vez por chamada a `pollOnce`. Cada escolha (`event_id`)
 * é entregue a `onSelection` uma única vez. A escolha que já estava no arquivo
 * na primeira leitura é ignorada, para não reaplicar uma escolha antiga quando
 * a página é recarregada.
 */
export function createGestureFeed({
  url,
  onState,
  onSelection,
  fetchImpl = (...args) => fetch(...args),
  now = () => Date.now(),
}) {
  let lastEventId;
  let hasBaseline = false;

  async function readState() {
    let response;
    try {
      response = await fetchImpl(`${url}?ts=${now()}`, { cache: "no-store" });
    } catch {
      return { ok: true, state: null };
    }
    if (!response.ok) return { ok: true, state: null };

    try {
      return { ok: true, state: await response.json() };
    } catch {
      // JSON ilegível: mantém o último estado em vez de piscar "desligada".
      return { ok: false, state: null };
    }
  }

  function handleSelection(selection) {
    const eventId = selection?.event_id ?? null;
    if (!hasBaseline) {
      hasBaseline = true;
      lastEventId = eventId;
      return;
    }
    if (eventId === null || eventId === lastEventId) return;

    lastEventId = eventId;
    onSelection(selection.fingers);
  }

  return {
    /** Devolve true se a câmera de gestos estava publicando. */
    async pollOnce() {
      const { ok, state } = await readState();
      if (!ok) return true;

      onState(describeGestureState(state, now()));
      if (state) handleSelection(state.selection);
      return state !== null;
    },
  };
}

/** Faz polling contínuo, mais espaçado enquanto a câmera estiver desligada. */
export function startGestureFeed({
  onlineIntervalMs = 250,
  offlineIntervalMs = 1000,
  ...options
}) {
  const feed = createGestureFeed(options);
  let timer = null;
  let stopped = false;

  async function loop() {
    const online = await feed.pollOnce();
    if (stopped) return;
    timer = setTimeout(loop, online ? onlineIntervalMs : offlineIntervalMs);
  }

  loop();
  return () => {
    stopped = true;
    clearTimeout(timer);
  };
}
