"""Testes do manifest de amostras."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from totem_aju.data.manifest import SampleManifest, SampleRecord
from totem_aju.errors import UnknownSignError


def make_record(
    *, sign: str = "banheiro", signer_id: str = "joao", path: str = "a.npy"
) -> SampleRecord:
    return SampleRecord.create(
        sign=sign,
        signer_id=signer_id,
        relative_path=path,
        n_frames=32,
        detection_ratio=0.875,
    )


class TestSampleRecordCreate:
    def test_validates_sign_against_vocabulary(self) -> None:
        with pytest.raises(UnknownSignError):
            make_record(sign="sinal_inexistente")

    def test_rejects_empty_signer_id(self) -> None:
        """Sem sinalizador, a divisao treino/teste por pessoa e impossivel."""
        with pytest.raises(ValueError, match="signer_id"):
            make_record(signer_id="   ")

    def test_strips_signer_id(self) -> None:
        assert make_record(signer_id="  maria  ").signer_id == "maria"

    def test_sets_timestamp(self) -> None:
        assert make_record().recorded_at

    def test_rounds_detection_ratio(self) -> None:
        record = SampleRecord.create(
            sign="praia",
            signer_id="ana",
            relative_path="b.npy",
            n_frames=32,
            detection_ratio=0.123456789,
        )
        assert record.detection_ratio == 0.1235


class TestSampleRecordSerialization:
    def test_round_trip_preserves_all_fields(self) -> None:
        original = make_record()
        assert SampleRecord.from_json(original.to_json()) == original

    def test_to_json_is_a_single_line(self) -> None:
        """Requisito do formato JSON Lines."""
        assert "\n" not in make_record().to_json()

    def test_from_json_rejects_missing_field(self) -> None:
        incomplete = json.dumps({"sign": "praia", "signer_id": "ana"})
        with pytest.raises(ValueError, match="obrigatorio"):
            SampleRecord.from_json(incomplete)


class TestSampleManifest:
    def test_read_all_on_missing_file_returns_empty(self, tmp_path: Path) -> None:
        manifest = SampleManifest(tmp_path / "ausente.jsonl")
        assert manifest.read_all() == []

    def test_append_creates_parent_directories(self, tmp_path: Path) -> None:
        manifest = SampleManifest(tmp_path / "nested" / "deep" / "m.jsonl")
        manifest.append(make_record())
        assert manifest.path.exists()

    def test_append_then_read_round_trip(self, tmp_path: Path) -> None:
        manifest = SampleManifest(tmp_path / "m.jsonl")
        records = [
            make_record(sign="praia", path="1.npy"),
            make_record(sign="onibus", path="2.npy"),
        ]
        for record in records:
            manifest.append(record)
        assert manifest.read_all() == records

    def test_append_does_not_overwrite(self, tmp_path: Path) -> None:
        manifest = SampleManifest(tmp_path / "m.jsonl")
        manifest.append(make_record(path="1.npy"))
        manifest.append(make_record(path="2.npy"))
        assert len(manifest.read_all()) == 2

    def test_blank_lines_are_ignored(self, tmp_path: Path) -> None:
        """Tolerancia a uma escrita interrompida por Ctrl+C."""
        path = tmp_path / "m.jsonl"
        record = make_record()
        path.write_text(f"{record.to_json()}\n\n", encoding="utf-8")
        assert SampleManifest(path).read_all() == [record]

    def test_count_by_sign(self, tmp_path: Path) -> None:
        manifest = SampleManifest(tmp_path / "m.jsonl")
        manifest.append(make_record(sign="praia", path="1.npy"))
        manifest.append(make_record(sign="praia", path="2.npy"))
        manifest.append(make_record(sign="onibus", path="3.npy"))
        assert manifest.count_by_sign() == {"praia": 2, "onibus": 1}

    def test_count_for_filters_by_sign_and_signer(self, tmp_path: Path) -> None:
        manifest = SampleManifest(tmp_path / "m.jsonl")
        manifest.append(make_record(sign="praia", signer_id="ana", path="1.npy"))
        manifest.append(make_record(sign="praia", signer_id="ana", path="2.npy"))
        manifest.append(make_record(sign="praia", signer_id="joao", path="3.npy"))
        manifest.append(make_record(sign="onibus", signer_id="ana", path="4.npy"))
        assert manifest.count_for("praia", "ana") == 2

    def test_signers_returns_unique_ids(self, tmp_path: Path) -> None:
        manifest = SampleManifest(tmp_path / "m.jsonl")
        manifest.append(make_record(signer_id="ana", path="1.npy"))
        manifest.append(make_record(signer_id="joao", path="2.npy"))
        manifest.append(make_record(signer_id="ana", path="3.npy"))
        assert manifest.signers() == {"ana", "joao"}
