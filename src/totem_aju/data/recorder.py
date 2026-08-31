"""Orquestracao da coleta: quadros -> landmarks normalizados -> disco.

Recebe as dependencias por construtor (``FrameSource`` e ``LandmarkExtractor``,
ambos ``Protocol``), portanto nao conhece OpenCV nem MediaPipe e pode ser
exercitado integralmente em teste com implementacoes sinteticas.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from totem_aju.config import (
    MANIFEST_FILENAME,
    SAMPLES_DIRNAME,
    SEQUENCE_LENGTH,
)
from totem_aju.data.manifest import SampleManifest, SampleRecord
from totem_aju.vision.camera import FrameSource
from totem_aju.vision.extractor import LandmarkExtractor
from totem_aju.vision.normalization import normalize_frame
from totem_aju.vision.sequence import SequenceBuffer
from totem_aju.vocabulary import ensure_known_sign


class SampleRecorder:
    """Grava amostras de sinais em disco e as indexa no manifest."""

    def __init__(
        self,
        *,
        source: FrameSource,
        extractor: LandmarkExtractor,
        data_root: Path,
        sequence_length: int = SEQUENCE_LENGTH,
    ) -> None:
        self._source = source
        self._extractor = extractor
        self._data_root = data_root
        self._sequence_length = sequence_length
        self._manifest = SampleManifest(data_root / MANIFEST_FILENAME)

    @property
    def manifest(self) -> SampleManifest:
        return self._manifest

    def record_sample(
        self, *, sign: str, signer_id: str, n_frames: int
    ) -> SampleRecord:
        """Captura ``n_frames`` quadros e persiste uma amostra do sinal.

        Args:
            sign: rotulo do sinal, validado contra o vocabulario.
            signer_id: identificador de quem esta sinalizando.
            n_frames: quantos quadros capturar antes de reamostrar.

        Raises:
            UnknownSignError: se o sinal nao pertencer ao vocabulario.
            CameraUnavailableError: se a fonte parar de entregar quadros.
            ValueError: se ``n_frames`` nao for positivo.
        """
        ensure_known_sign(sign)
        if n_frames <= 0:
            raise ValueError(f"'n_frames' deve ser positivo, recebido {n_frames}.")

        buffer = SequenceBuffer(
            max_frames=n_frames, sequence_length=self._sequence_length
        )
        for _ in range(n_frames):
            frame = self._source.read()
            buffer.append(normalize_frame(self._extractor.extract(frame)))

        sequence = buffer.to_array()
        relative_path = self._persist_sequence(sign, signer_id, sequence)
        record = SampleRecord.create(
            sign=sign,
            signer_id=signer_id,
            relative_path=relative_path,
            n_frames=int(sequence.shape[0]),
            detection_ratio=buffer.detection_ratio,
        )
        self._manifest.append(record)
        return record

    def _persist_sequence(self, sign: str, signer_id: str, sequence: np.ndarray) -> str:
        """Salva o array e devolve o caminho relativo a raiz do dataset.

        O nome do arquivo e sequencial por sinal e sinalizador, o que evita
        colisao entre integrantes da equipe gravando em paralelo e mantem o
        dataset legivel na inspecao manual.
        """
        directory = self._data_root / SAMPLES_DIRNAME / sign
        directory.mkdir(parents=True, exist_ok=True)
        index = self._next_index(directory, signer_id)
        filename = f"{signer_id}_{index:04d}.npy"
        np.save(directory / filename, sequence)
        return f"{SAMPLES_DIRNAME}/{sign}/{filename}"

    @staticmethod
    def _next_index(directory: Path, signer_id: str) -> int:
        """Proximo indice livre, derivado do maior indice existente.

        Usa o maximo em vez da contagem: se uma amostra ruim for apagada
        manualmente, a contagem reutilizaria um indice e sobrescreveria um
        arquivo valido.
        """
        highest = 0
        for path in directory.glob(f"{signer_id}_*.npy"):
            suffix = path.stem.removeprefix(f"{signer_id}_")
            if suffix.isdigit():
                highest = max(highest, int(suffix))
        return highest + 1
