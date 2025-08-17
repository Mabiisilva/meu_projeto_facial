import face_recognition
import cv2 # OpenCV para exibir a imagem (opcional, mas útil)
import os # Para construir o caminho do arquivo

# Define o caminho para a pasta de imagens
IMAGENS_DIR = 'imagens'
NOME_IMAGEM = 'foto_teste.png' # Altere para o nome da sua imagem de teste

# Constrói o caminho completo para a imagem
caminho_completo_imagem = os.path.join(IMAGENS_DIR, NOME_IMAGEM)

try:
    # Carrega a imagem para um array numpy
    print(f"Carregando imagem: {caminho_completo_imagem}")
    image = face_recognition.load_image_file(caminho_completo_imagem)

    # Encontra todos os rostos na imagem
    # (top, right, bottom, left)
    face_locations = face_recognition.face_locations(image)

    print(f"Encontradas {len(face_locations)} faces nesta imagem.")

    # Opcional: Desenhar retângulos ao redor dos rostos e exibir a imagem
    if len(face_locations) > 0 and cv2:
        # Converte a imagem de RGB (face_recognition) para BGR (OpenCV)
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        for top, right, bottom, left in face_locations:
            # Desenha um retângulo ao redor do rosto
            cv2.rectangle(image_bgr, (left, top), (right, bottom), (0, 255, 0), 2) # Verde, espessura 2

        # Redimensiona a imagem para caber na tela se for muito grande
        max_dim = 800
        h, w = image_bgr.shape[:2]
        if h > max_dim or w > max_dim:
            scaling_factor = max_dim / max(h, w)
            image_bgr = cv2.resize(image_bgr, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)

        cv2.imshow('Faces Encontradas', image_bgr)
        cv2.waitKey(0) # Espera uma tecla ser pressionada
        cv2.destroyAllWindows() # Fecha a janela
    elif len(face_locations) > 0:
        print("Para visualizar, instale o OpenCV: pip install opencv-python")

except FileNotFoundError:
    print(f"ERRO: Imagem '{caminho_completo_imagem}' não encontrada. Verifique o nome e o caminho.")
except Exception as e:
    print(f"Ocorreu um erro: {e}")