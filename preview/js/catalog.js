export const SIGN_LABELS = Object.freeze({
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
});

// A ordem define o número do gesto: o primeiro assunto é 1 dedo, e assim por diante.
export const CATEGORY_SIGNS = Object.freeze({
  servico: ["banheiro", "comer", "agua", "hospital", "policia", "dinheiro", "hotel"],
  transporte: ["onibus", "taxi", "aeroporto"],
  ponto_turistico: ["praia", "orla", "mercado", "museu", "igreja", "centro"],
  pergunta: ["onde", "como_chegar", "quanto_custa", "que_horas", "ajuda"],
});

export function labelFor(sign) {
  return SIGN_LABELS[sign] ?? sign;
}
