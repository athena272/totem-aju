"""Helpers compartilhados pelos testes do pacote ``ml``."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from totem_aju.config import MANIFEST_FILENAME, SEQUENCE_LENGTH
from totem_aju.data.manifest import SampleManifest, SampleRecord
from totem_aju.ml.dataset import LabeledSample, LoadedDataset
from totem_aju.vision.schema import FRAME_VECTOR_SIZE
from totem_aju.vocabulary import SIGN_TO_INDEX


def make_sequence(*, fill: float) -> np.ndarray:
    """Tensor ``(32, 225)`` preenchido com ``fill`` (mais ruido leve)."""
    rng = np.random.default_rng(abs(hash(fill)) % (2**32))
    noise = rng.normal(0.0, 0.01, size=(SEQUENCE_LENGTH, FRAME_VECTOR_SIZE))
    return (np.full((SEQUENCE_LENGTH, FRAME_VECTOR_SIZE), fill) + noise).astype(
        np.float32
    )


def make_labeled_sample(
    *,
    sign: str,
    signer_id: str,
    fill: float,
    relative_path: str = "x.npy",
) -> LabeledSample:
    return LabeledSample(
        sequence=make_sequence(fill=fill),
        sign=sign,
        label=SIGN_TO_INDEX[sign],
        signer_id=signer_id,
        relative_path=relative_path,
    )


def make_separable_dataset() -> LoadedDataset:
    """Tres sinais, tres sinalizadores, medias distintas por classe."""
    signs = ("ola", "sim", "nao")
    fills = {"ola": 0.0, "sim": 1.0, "nao": 2.0}
    signers = ("alice", "bruno", "carla")
    samples: list[LabeledSample] = []
    for signer in signers:
        for sign in signs:
            for index in range(4):
                samples.append(
                    make_labeled_sample(
                        sign=sign,
                        signer_id=signer,
                        fill=fills[sign],
                        relative_path=f"{sign}/{signer}_{index:04d}.npy",
                    )
                )
    return LoadedDataset(samples=tuple(samples), data_root=Path("synthetic"))


def write_dataset_on_disk(
    root: Path,
    *,
    signs: tuple[str, ...] = ("ola", "sim"),
    signers: tuple[str, ...] = ("alice", "bruno"),
    reps: int = 2,
) -> Path:
    """Grava um mini-dataset real em ``root`` (manifest + npy)."""
    fills = {sign: float(index) for index, sign in enumerate(signs)}
    manifest = SampleManifest(root / MANIFEST_FILENAME)
    for signer in signers:
        for sign in signs:
            sign_dir = root / "samples" / sign
            sign_dir.mkdir(parents=True, exist_ok=True)
            for index in range(1, reps + 1):
                relative = f"samples/{sign}/{signer}_{index:04d}.npy"
                path = root / relative
                np.save(path, make_sequence(fill=fills[sign]))
                manifest.append(
                    SampleRecord.create(
                        sign=sign,
                        signer_id=signer,
                        relative_path=relative.replace("\\", "/"),
                        n_frames=SEQUENCE_LENGTH,
                        detection_ratio=1.0,
                    )
                )
    return root
