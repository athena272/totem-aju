"""Testes de integracao da coleta, sem webcam e sem MediaPipe.

Exercitam o caminho completo -- fonte de quadros, extracao, normalizacao,
reamostragem, gravacao do .npy e indexacao no manifest -- usando os dubles
definidos em ``conftest``. E este teste que demonstra o beneficio pratico de o
recorder depender de ``Protocol`` em vez de bibliotecas concretas.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.conftest import FakeExtractor, FakeFrameSource
from totem_aju.config import SEQUENCE_LENGTH
from totem_aju.data.recorder import SampleRecorder
from totem_aju.errors import CameraUnavailableError, UnknownSignError
from totem_aju.vision.schema import FRAME_VECTOR_SIZE

FRAMES_PER_SAMPLE = 12


def make_recorder(data_root: Path, **kwargs: object) -> SampleRecorder:
    return SampleRecorder(
        source=kwargs.get("source") or FakeFrameSource(),  # type: ignore[arg-type]
        extractor=kwargs.get("extractor") or FakeExtractor(),  # type: ignore[arg-type]
        data_root=data_root,
    )


class TestRecordSample:
    def test_returns_validated_record(self, tmp_path: Path) -> None:
        record = make_recorder(tmp_path).record_sample(
            sign="banheiro", signer_id="ana", n_frames=FRAMES_PER_SAMPLE
        )
        assert record.sign == "banheiro"
        assert record.signer_id == "ana"
        assert record.n_frames == SEQUENCE_LENGTH

    def test_writes_npy_with_canonical_shape(self, tmp_path: Path) -> None:
        record = make_recorder(tmp_path).record_sample(
            sign="praia", signer_id="ana", n_frames=FRAMES_PER_SAMPLE
        )
        saved = np.load(tmp_path / record.relative_path)
        assert saved.shape == (SEQUENCE_LENGTH, FRAME_VECTOR_SIZE)
        assert saved.dtype == np.float32

    def test_relative_path_uses_forward_slashes(self, tmp_path: Path) -> None:
        """Mantem o dataset portavel entre Windows e Linux."""
        record = make_recorder(tmp_path).record_sample(
            sign="praia", signer_id="ana", n_frames=FRAMES_PER_SAMPLE
        )
        assert "\\" not in record.relative_path
        assert record.relative_path.startswith("samples/praia/")

    def test_appends_to_manifest(self, tmp_path: Path) -> None:
        recorder = make_recorder(tmp_path)
        recorder.record_sample(
            sign="onibus", signer_id="ana", n_frames=FRAMES_PER_SAMPLE
        )
        assert len(recorder.manifest.read_all()) == 1

    def test_reads_exactly_the_requested_frames(self, tmp_path: Path) -> None:
        source = FakeFrameSource()
        extractor = FakeExtractor()
        SampleRecorder(
            source=source, extractor=extractor, data_root=tmp_path
        ).record_sample(sign="praia", signer_id="ana", n_frames=FRAMES_PER_SAMPLE)
        assert source.read_calls == FRAMES_PER_SAMPLE
        assert extractor.extract_calls == FRAMES_PER_SAMPLE

    def test_detection_ratio_reflects_undetected_frames(self, tmp_path: Path) -> None:
        recorder = SampleRecorder(
            source=FakeFrameSource(),
            extractor=FakeExtractor(detected=False),
            data_root=tmp_path,
        )
        record = recorder.record_sample(
            sign="praia", signer_id="ana", n_frames=FRAMES_PER_SAMPLE
        )
        assert record.detection_ratio == pytest.approx(0.0)


class TestSampleNaming:
    def test_successive_samples_do_not_overwrite(self, tmp_path: Path) -> None:
        recorder = make_recorder(tmp_path)
        paths = {
            recorder.record_sample(
                sign="praia", signer_id="ana", n_frames=FRAMES_PER_SAMPLE
            ).relative_path
            for _ in range(3)
        }
        assert len(paths) == 3

    def test_index_survives_deleted_sample(self, tmp_path: Path) -> None:
        """Apagar uma amostra ruim nao pode fazer o indice ser reutilizado."""
        recorder = make_recorder(tmp_path)
        first = recorder.record_sample(
            sign="praia", signer_id="ana", n_frames=FRAMES_PER_SAMPLE
        )
        second = recorder.record_sample(
            sign="praia", signer_id="ana", n_frames=FRAMES_PER_SAMPLE
        )
        (tmp_path / first.relative_path).unlink()
        third = recorder.record_sample(
            sign="praia", signer_id="ana", n_frames=FRAMES_PER_SAMPLE
        )
        assert third.relative_path not in {first.relative_path, second.relative_path}

    def test_signers_do_not_collide(self, tmp_path: Path) -> None:
        recorder = make_recorder(tmp_path)
        ana = recorder.record_sample(
            sign="praia", signer_id="ana", n_frames=FRAMES_PER_SAMPLE
        )
        joao = recorder.record_sample(
            sign="praia", signer_id="joao", n_frames=FRAMES_PER_SAMPLE
        )
        assert ana.relative_path != joao.relative_path


class TestRecordSampleFailures:
    def test_unknown_sign_raises_before_touching_the_camera(
        self, tmp_path: Path
    ) -> None:
        source = FakeFrameSource()
        recorder = SampleRecorder(
            source=source, extractor=FakeExtractor(), data_root=tmp_path
        )
        with pytest.raises(UnknownSignError):
            recorder.record_sample(
                sign="inexistente", signer_id="ana", n_frames=FRAMES_PER_SAMPLE
            )
        assert source.read_calls == 0

    def test_non_positive_frames_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="n_frames"):
            make_recorder(tmp_path).record_sample(
                sign="praia", signer_id="ana", n_frames=0
            )

    def test_camera_failure_propagates(self, tmp_path: Path) -> None:
        recorder = SampleRecorder(
            source=FakeFrameSource(max_reads=3),
            extractor=FakeExtractor(),
            data_root=tmp_path,
        )
        with pytest.raises(CameraUnavailableError):
            recorder.record_sample(
                sign="praia", signer_id="ana", n_frames=FRAMES_PER_SAMPLE
            )

    def test_failed_sample_is_not_indexed(self, tmp_path: Path) -> None:
        """Manifest e .npy nao podem divergir."""
        recorder = SampleRecorder(
            source=FakeFrameSource(max_reads=3),
            extractor=FakeExtractor(),
            data_root=tmp_path,
        )
        with pytest.raises(CameraUnavailableError):
            recorder.record_sample(
                sign="praia", signer_id="ana", n_frames=FRAMES_PER_SAMPLE
            )
        assert recorder.manifest.read_all() == []
