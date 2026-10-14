"""Script minimo: abre a webcam numa janela. ESC encerra."""

import cv2


def main() -> int:
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Erroo")
        return 1

    while True:
        ret, frame = cap.read()  # le o frame atual

        if not ret:
            print("frame nao foi possivel")
            break

        cv2.imshow("Totem - AJU", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()  # libera a camera e fecha janelas
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
