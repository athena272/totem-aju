import cv2

cap=cv2.VideoCapture(0)

if not cap.isOpened():
    print("Erroo")
    exit()

while True:
    ret, frame = cap.read() #le o frame atual

    if not ret:
        print("frame nao foi possivel")
        break

    cv2.imshow("tortaLety", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break
    
cap.release() #libera a camera e fecha janelas
cv2.destroyAllWindows()
