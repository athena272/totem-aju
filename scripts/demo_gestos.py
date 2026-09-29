"""Script de demonstração: integra as heurísticas 3D com a webcam do Totem Aju."""

import cv2
from totem_aju.vision.camera import OpenCVCamera
from totem_aju.vision.heuristics import (
    avaliar_dedos,
    reconhecer_gesto,
    reconhecer_sinal_vocabulario,
)
from totem_aju.vision.mediapipe_extractor import MediaPipeHolisticExtractor
from totem_aju.vision.smoothing import TemporalGestureFilter


def main() -> None:
    filtro = TemporalGestureFilter()

    with OpenCVCamera() as camera, MediaPipeHolisticExtractor() as extractor:
        print("A iniciar demonstração do Totem Aju (Pressione 'q' para sair)...")

        while True:
            try:
                frame = camera.read()
            except Exception:
                break

            frame = cv2.flip(frame, 1)
            landmarks = extractor.extract(frame)

            maos = []
            if landmarks.right_hand_detected:
                maos.append(("Mão Direita", landmarks.right_hand, "right"))
            if landmarks.left_hand_detected:
                maos.append(("Mão Esquerda", landmarks.left_hand, "left"))

            for label, hand_lm, key in maos:
                lm_suavizado = filtro.suavizar_landmarks(key, hand_lm)
                fingers_raw, _ = avaliar_dedos(lm_suavizado)
                fingers = filtro.dedos_estaveis(key, fingers_raw)

                gesto_raw = reconhecer_gesto(fingers, lm_suavizado)
                gesto = filtro.gesto_estavel(key, gesto_raw)
                sinal_oficial = reconhecer_sinal_vocabulario(gesto)

                y_pos = 50 if key == "right" else 100
                texto = f"{label}: {gesto}"
                if sinal_oficial:
                    texto += f" -> [Vocabulário: {sinal_oficial}]"

                cv2.putText(
                    frame,
                    texto,
                    (30, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

            cv2.imshow("Totem Aju - Validação de Gestos", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()