"""Indice persistente das amostras coletadas.

Formato JSON Lines (uma amostra por linha, append-only). A escolha e
deliberada: a coleta e um processo longo e frequentemente interrompido com
Ctrl+C, e um JSON unico corrompido perderia o dataset inteiro. Com JSONL,
perde-se no maximo a ultima linha.

Este modulo nao sabe o que e um landmark: lida apenas com metadados de amostra.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from totem_aju.vocabulary import ensure_known_sign

MANIFEST_ENCODING = "utf-8"


@dataclass(frozen=True, slots=True)
class SampleRecord:
    """Metadados de uma unica amostra gravada.

    Attributes:
        sign: rotulo do sinal, validado contra o vocabulario.
        signer_id: identificador de quem sinalizou. **Obrigatorio**: sem ele a
            divisao treino/teste por pessoa e impossivel, e a acuracia
            relatada ficaria inflada por vazamento de dados.
        relative_path: caminho do ``.npy``, relativo a raiz do dataset, para
            que o dataset permaneca portavel entre maquinas.
        n_frames: numero de quadros apos reamostragem.
        detection_ratio: fracao de quadros com mao detectada; indicador de
            qualidade da amostra.
        recorded_at: instante da gravacao, em ISO 8601 UTC.
    """

    sign: str
    signer_id: str
    relative_path: str
    n_frames: int
    detection_ratio: float
    recorded_at: str

    @classmethod
    def create(
        cls,
        *,
        sign: str,
        signer_id: str,
        relative_path: str,
        n_frames: int,
        detection_ratio: float,
    ) -> SampleRecord:
        """Cria um registro validado, com timestamp do momento atual.

        Raises:
            UnknownSignError: se ``sign`` nao pertencer ao vocabulario.
            ValueError: se ``signer_id`` estiver vazio.
        """
        if not signer_id.strip():
            raise ValueError(
                "'signer_id' e obrigatorio: sem ele a divisao treino/teste "
                "por sinalizador se torna impossivel."
            )
        return cls(
            sign=ensure_known_sign(sign),
            signer_id=signer_id.strip(),
            relative_path=relative_path,
            n_frames=n_frames,
            detection_ratio=round(detection_ratio, 4),
            recorded_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )

    def to_json(self) -> str:
        """Serializa em uma unica linha JSON."""
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json(cls, line: str) -> SampleRecord:
        """Desserializa uma linha do manifest.

        Raises:
            ValueError: se a linha nao contiver os campos esperados.
        """
        data: dict[str, Any] = json.loads(line)
        try:
            return cls(
                sign=data["sign"],
                signer_id=data["signer_id"],
                relative_path=data["relative_path"],
                n_frames=int(data["n_frames"]),
                detection_ratio=float(data["detection_ratio"]),
                recorded_at=data["recorded_at"],
            )
        except KeyError as exc:
            raise ValueError(
                f"Linha de manifest sem o campo obrigatorio {exc}."
            ) from exc


class SampleManifest:
    """Acesso de leitura e escrita ao arquivo de manifest."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def append(self, record: SampleRecord) -> None:
        """Acrescenta um registro ao fim do arquivo, criando-o se necessario."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding=MANIFEST_ENCODING) as handle:
            handle.write(f"{record.to_json()}\n")

    def read_all(self) -> list[SampleRecord]:
        """Le todos os registros. Devolve lista vazia se o arquivo nao existe.

        Linhas em branco sao ignoradas, tolerando uma escrita interrompida.
        """
        if not self._path.exists():
            return []
        with self._path.open(encoding=MANIFEST_ENCODING) as handle:
            return [SampleRecord.from_json(line) for line in handle if line.strip()]

    def count_by_sign(self) -> dict[str, int]:
        """Conta amostras por sinal, para acompanhar o progresso da coleta."""
        counts: dict[str, int] = {}
        for record in self.read_all():
            counts[record.sign] = counts.get(record.sign, 0) + 1
        return counts

    def count_for(self, sign: str, signer_id: str) -> int:
        """Conta amostras de um sinal para um sinalizador especifico."""
        return sum(
            1
            for record in self.read_all()
            if record.sign == sign and record.signer_id == signer_id
        )

    def signers(self) -> set[str]:
        """Conjunto de sinalizadores presentes no dataset."""
        return {record.signer_id for record in self.read_all()}
