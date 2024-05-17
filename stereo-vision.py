'''
Nombre del archivo: stereo-vision.py 

Descripcion:    

Autor(es):  Jonathan Ariel Valadez Saldaña

Fecha de creación: 17/Mayo/2024

Ejemplo de uso:   python stereo-vision.py --l_img left-image.png --r_img right-image.png
'''

# Declaramos los parámetros de calibración, mismos dados por el documento de la tarea 11
calibration_params = {
    "baseline": 94.926,
    "rectified_fx": 648.52,
    "rectified_fy": 648.52,
    "rectified_height": 720,
    "rectified_cx": 635.709,
    "rectified_cy": 370.88,
    "rectified_width": 1280
}

# Los asignamos a su respectiva variable
baseline, fx, fy, h, cx, cy, w = calibration_params.values()

num_pixels = 30

import cv2
import argparse
import matplotlib.pyplot as plt


def parser_user_data() -> argparse.Namespace:
    """
    Descripción:    Función que recibe la información de entrada por el usuario
    
    Parámetros:     Ninguno

    Regresa:        args(argparse) objeto con la información o datos recibidos 
    """
    parser = argparse.ArgumentParser(description='Reconstrucción 3D usando visión estereo.')
    parser.add_argument('--l_img', required=True, 
                        help='Introducir el nombre del archivo de la imagen izquierda')
    parser.add_argument('--r_img', required=True,
                        help='Introducir el nombre del archivo de la imagen derecha')
    args = parser.parse_args()
    return args


def load_images(filename_imgL: str, filename_imgR: str):
    """
    Descripción:    carga dos archivos (imagen y video) desde la ruta especificada
    
    Parámetros:     filename_imgL(str): ruta del archivo de la imagen izquierda
                    filename_imgR(str): ruta del archivo de la imagen derecha

    Regresa:        imagen izquierda y derecha siendo los archivos cargados
    """
    imgL = cv2.imread(filename_imgL)
    imgR = cv2.imread(filename_imgR)

    if imgL is None:
        print("Error: No se pudo cargar la imagen izquierda:", filename_imgL)
        exit()
    if imgR is None:
        print("Error: No se pudo cargar la imagen derecha:", filename_imgR)
        exit()

    return imgL, imgR


def select_30pixels_left(event, x, y, flags, param):
    """
    Descripción:    captura las coordenadas de los puntos seleccionados en la imagen izquierda
    
    Parámetros:     
    - event: tipo de evento de mouse (por ejemplo, cv2.EVENT_LBUTTONDOWN)
    - x: coordenada x del cursor del mouse en la imagen
    - y: coordenada y del cursor del mouse en la imagen
    - flags: indicadores de estado adicionales del evento (no utilizado en esta función)
    - param: parámetro adicional (no utilizado en esta función)

    Regresa:        selected_pixels_left, lista donde se guardan las coordenadas X y Y de los puntos
    """
    global pixel_counterL, selected_pixels_left, imgL
    # Detectar los clic's izquierdos del mouse y que el contador de puntos sea menor a 30
    if event == cv2.EVENT_LBUTTONDOWN and pixel_counterL < num_pixels:

        selected_pixels_left.append((x, y))
        print(f"Punto izquierdo seleccionado #{pixel_counterL + 1}:", (x, y))

        # Dibujar un punto en el pixel seleccionado
        cv2.circle(imgL, (x, y), 3, (0, 255, 0), -1)  # Dibujar un punto verde de radio = 3
        cv2.imshow('Imagen Rectificada Izquierda', imgL)
        pixel_counterL += 1

        # Verificar si ya se han seleccionado 30 puntos, y si es así, desactivar el seguimiento de eventos de mouse
        if pixel_counterL == num_pixels:
            try:
                cv2.setMouseCallback('Imagen Rectificada Izquierda', None)
                #print()  # Imprimir una línea en blanco para separar los puntos seleccionados izquierdos y derechos
            except TypeError:
                pass  # Manejar la excepción sin hacer nada
    
    return selected_pixels_left



def select_30pixels_right(event, x, y, flags, param):
    """
    Descripción:    captura las coordenadas de los puntos seleccionados en la imagen derecha
    
    Parámetros:     
    - event: tipo de evento de mouse (por ejemplo, cv2.EVENT_LBUTTONDOWN)
    - x: coordenada x del cursor del mouse en la imagen
    - y: coordenada y del cursor del mouse en la imagen
    - flags: indicadores de estado adicionales del evento (no utilizado en esta función)
    - param: parámetro adicional (no utilizado en esta función)   

    Regresa:        selected_pixels_right, lista donde se guardan las coordenadas X y Y de los puntos
    """
    global pixel_counterR, selected_pixels_right, imgR
    # Detectar los clic's izquierdos del mouse y que el contador de puntos sea menor a 30
    if event == cv2.EVENT_LBUTTONDOWN and pixel_counterR < num_pixels:

        # Utilizar la misma coordenada Y que se seleccionó en la imagen izquierda
        y = selected_pixels_left[pixel_counterR][1]

        selected_pixels_right.append((x, y))
        print(f"Punto derecho seleccionado #{pixel_counterR + 1}:", (x, y))

        # Dibujar un punto en el pixel seleccionado
        cv2.circle(imgR, (x, y), 3, (0, 255, 0), -1)  # Dibujar un punto verde de radio = 3
        cv2.imshow('Imagen Rectificada Derecha', imgR)
        pixel_counterR += 1

        # Verificar si ya se han seleccionado 30 puntos, y si es así, desactivar el seguimiento de eventos de mouse
        if pixel_counterR == num_pixels:
            try:
                cv2.setMouseCallback('Imagen Rectificada Derecha', None)
                #print()  # Imprimir una línea en blanco para hacer separación en la terminal
            except TypeError:
                pass  # Manejar la excepción sin hacer nada

    return selected_pixels_right

def compute_coords_respect_center(pL, pR):
    """
    Descripción:    calcula nuevamente las coordenadas de los puntos de la imagen  
                    de la izquierda y derecha, pero esta vez con respecto al centro 
                    de cada imagen. No se requiere de volver a capturar las coordenadas,
                    sino que con las mismas se hace una calibración usando Cx y Cy
    
    Parámetros:     pL: coordenadas de los puntos de la imagen izquierda
                    pR: coordenadas de los puntos de la imagen derecha

    Regresa:        coords_cL: calibración de las coordenadas de la imagen izquierda
                    coords_cR: calibración de las coordenadas de la imagen derecha
    """
    coords_cL = []
    coords_cR = []

    print(" ")

    for i, pointL in enumerate(pL):
        # Coordenadas imagen izquierda
        u_cL = pointL[0] - cx      # Coordenada uL respecto al centro
        v_cL = pointL[1] - cy      # Coordenada vL respecto al centro
        coords_cL.append((u_cL, v_cL))
        print(f"Coordenada cL #{i + 1} en imagen izquierda: ({u_cL:.3f}, {v_cL:.3f})")

    print(" ")

    for i, pointR in enumerate(pR):
        # Coordenadas imagen derecha
        u_cR = pointR[0] - cx      # Coordenada uR respecto al centro
        v_cR = pointR[1] - cy      # Coordenada vR respecto al centro
        coords_cR.append((u_cR, v_cR))
        print(f"Coordenada cR #{i + 1} en imagen derecha: ({u_cR:.3f}, {v_cR:.3f})")

    print(" ")

    return coords_cL, coords_cR

print(" ")

def compute_disparity_and_XYZ(coords_cL, coords_cR):
    """
    Descripción:    calcula la disparidad de los puntos de la imagen de la izquierda
                    y derecha, así como la obtención de las coordenadas X, Y y Z 
                    usando esta misma disparidad y algunos parámetros de calibración
    
    Parámetros:     coords_cL: coordenadas respecto al centro de la imagen izquierda
                    coords_cR: coordenadas respecto al centro de la imagen derecha

    Regresa:        coord_final: coordenadas 3D (x, y, z) de los puntos seleccionados
                                 de ambas imágenes
    """
    coord_final = []
    for i in range(len(coords_cL)):
        ucL, vcL = coords_cL[i]
        ucR, _ = coords_cR[i]      # No necesitamos vcR en esta función
        dU = ucL - ucR             # Disparidad U entre imagen izquierda y derecha
        Z = fx * (baseline / dU)   # Profundidad Z (plano 3D)
        X = ucL * (Z / fx)         # Coordenada X (plano 3D)
        Y = vcL * (Z / fy)         # Coordenada Y (plano 3D)
        coord_final.append((round(X, 3), round(Y, 3), round(Z, 3)))
        print(f"Coordenada final #{i + 1}: ({X:.3f}, {Y:.3f}, {Z:.3f})")

    return coord_final


def visualize_3D(xyz):
    """
    Descripción: Función para visualizar las coordenadas 3D en una figura matplotlib 3D.

    Parámetros:
        xyz (list): Lista de coordenadas tridimensionales (X, Y, Z).

    Regresa: Nada
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Extraemos las coordenadas X, Y, Z
    X = [coord[0] for coord in xyz]
    Y = [coord[1] for coord in xyz]
    Z = [coord[2] for coord in xyz]

    # Dividimos cada valor por 1000 para convertirlos de mm a m
    #X = [x / 1000 for x in Xmm]
    #Y = [y / 1000 for y in Ymm]
    #Z = [z / 1000 for z in Zmm]

    # Graficamos los puntos en 3D
    ax.scatter(X, Z, Y, c='b', marker='o')

    ax.set_xlabel('X')
    ax.set_ylabel('Z')
    ax.set_zlabel('Y')

    # Invierte la orientación del eje Y
    ax.invert_yaxis()

    plt.axis('equal')
    plt.show()



def close_windows():
    """
    Descripción: Funcion que cierra las ventanas una vez se haya frenado el procesamiento de las mismas

    Parámetros: Ninguno

    Regresa: Nada
    """
    # Cerramos todas las ventanas
    cv2.destroyAllWindows()


def run_pipeline():
    """
    Descripción: Funcion que se encarga se ejecutar las demás funciones

    Parámetros: Ninguno

    Regresa: Nada
    """
    # Captura del argumento
    args = parser_user_data()

    # Cargamos las imágenes de entrada
    global imgL, imgR
    imgL, imgR = load_images(args.l_img, args.r_img)

    # Variables para almacenar y contar los puntos seleccionados por el usuario

    # Las hacemos globales para que las funciones dentro del run_pipeline, puedan acceder a ellas
    global selected_pixels_left, selected_pixels_right, pixel_counterL, pixel_counterR
    selected_pixels_left = []
    selected_pixels_right = []
    pixel_counterL = 0
    pixel_counterR = 0

    # Vinculamos las funciones de manejo de eventos de mouse con las ventanas de las imágenes

    # Abrimos una ventana para cada una de las imágenes
    cv2.imshow('Imagen Rectificada Izquierda', imgL)
    cv2.imshow('Imagen Rectificada Derecha', imgR)

    # Mandamos a llamar las funciones para tales ventanas
    cv2.setMouseCallback('Imagen Rectificada Izquierda', select_30pixels_left)
    print(" ")
    cv2.setMouseCallback('Imagen Rectificada Derecha', select_30pixels_right)

    # Ejecutamos el bucle hasta que se seleccionen los 30 puntos en ambas imágenes
    while pixel_counterL < num_pixels or pixel_counterR < num_pixels:
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    # Una vez que se hayan seleccionado los puntos necesarios, procedemos con el procesamiento
    if pixel_counterL >= num_pixels and pixel_counterR >= num_pixels:
        # Una vez dibujados los puntos y obtenido sus coordenadas respecto al origen, 
        # vamos a calcularlas ahora con respecto al centro de la imagen
        coords_cL, coords_cR = compute_coords_respect_center(selected_pixels_left, selected_pixels_right)

        # Hacemos el cálculo de la disparidad y Z
        xyz = compute_disparity_and_XYZ(coords_cL, coords_cR)

    # Llamamos a la función para visualizar las coordenadas 3D
    visualize_3D(xyz)
    
    close_windows()

if __name__ == "__main__":
    run_pipeline()