import numpy as np
import cv2
import math
import random
import base64

def img_to_gray(npimg):
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.resize(img, (512, 512), interpolation=cv2.INTER_AREA)
    _, img = cv2.imencode('.jpg', img)
    return base64.b64encode(img).decode('utf-8')

def img_to_histogram(npimg):
    img = cv2.cvtColor(cv2.imdecode(np.frombuffer(base64.b64decode(npimg), np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([img], [0], None, [256], [0, 256])
    hist_img = np.zeros((512, 512, 3), dtype=np.uint8)
    cv2.normalize(hist, hist, 0, 512, cv2.NORM_MINMAX)

    bin_width = 512 // 256
    for x in range(256):
        cv2.rectangle(hist_img, (x * bin_width, 512), ((x + 1) * bin_width, 512 - int(hist[x])), (255, 255, 255), -1)
    _, hist_img_encoded = cv2.imencode('.jpg', hist_img)
    return base64.b64encode(hist_img_encoded).decode('utf-8')

def img_to_gaussion_noise(npimg_base64):
    #Base64解碼轉為numpy array
    npimg = np.frombuffer(base64.b64decode(npimg_base64), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_GRAYSCALE)
    gaussion_noise_img = np.copy(img)
    sigma = 50
    
    for x in range(gaussion_noise_img.shape[0]):
        for y in range(gaussion_noise_img.shape[1]):
            r = random.random()
            phi = random.random()
            z1 = sigma * math.cos(2 * math.pi * phi) * (-2 * math.log(r)) ** 0.5
            f1 = gaussion_noise_img[x, y] + z1
            if f1 < 0:
                gaussion_noise_img[x, y] = 0
            elif f1 > 255:
                gaussion_noise_img[x, y] = 255
            else:
                gaussion_noise_img[x, y] = f1

    _, gaussion_noise_img_encoded = cv2.imencode('.jpg', gaussion_noise_img)
    return base64.b64encode(gaussion_noise_img_encoded).decode('utf-8')

def img_to_haar_wavelet(npimg_base64):
    npimg = np.frombuffer(base64.b64decode(npimg_base64), np.uint8) #將Base64解碼轉為numpy
    img = cv2.imdecode(npimg, cv2.IMREAD_GRAYSCALE) #轉灰階

    level = 1
    decompose = 1
    levelused = 1
    rows, cols = img.shape
    tmp = np.zeros((rows, cols), dtype=np.int64)
    wav = np.zeros((rows, cols), dtype=np.int64)

    while decompose <= level:
        width = rows // levelused
        height = cols // levelused
        for i in range(int(width)):
            for j in range(height // 2):
                tmp_val1 = int((img[i, 2 * j] // 2 + img[i, 2 * j + 1]) // 2)
                tmp[i, j] = np.clip(tmp_val1, 0, 255)

                tmp_val2 = int(np.int64(img[i, 2 * j]) - np.int64(img[i, 2 * j + 1]))
                tmp[i, j + int(height // 2)] = np.clip(tmp_val2, 0, 255)

        for i in range(int(width // 2)):
            for j in range(int(height)):
                wav_val1 = int(tmp[2 * i, j] + tmp[2 * i + 1, j])
                wav[i, j] = np.clip(wav_val1, 0, 255)

                wav_val2 = int((tmp[2 * i, j] - tmp[2 * i + 1, j]) // 2)
                wav[i + int(width // 2), j] = np.clip(wav_val2, 0, 255)
        img = wav
        decompose += 1
        levelused *= 2
    _, haar_wavelet_img_encoded = cv2.imencode('.jpg', img)
    return base64.b64encode(haar_wavelet_img_encoded).decode('utf-8')

def img_to_histogram_equalization(npimg_base64):
    npimg = np.frombuffer(base64.b64decode(npimg_base64), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_GRAYSCALE)
    for_histogramequalization_img = cv2.resize(img, (512, 512), interpolation=cv2.INTER_AREA)
    arrayH = []
    dictarrayH = {}
    arrayHC = []
    Hmin = 0

    for i in range(256):
        dictarrayH[i] = 0

    for x in range(512):
        for y in range(512):
            arrayH.append(for_histogramequalization_img[x][y])
    for i in arrayH:
        dictarrayH[i] += 1

    addall = 0
    for i in dictarrayH:
        addall += dictarrayH[i]
        arrayHC.append(addall)
    for i in arrayHC:
        if i != 0:
            Hmin = i
            break
    for x in range(512):
        for y in range(512):
            for_histogramequalization_img[x][y] = round((arrayHC[for_histogramequalization_img[x][y]] - Hmin) / (262144 - Hmin) * 255)

    _, hist_eq_img_encoded = cv2.imencode('.jpg', for_histogramequalization_img)
    return base64.b64encode(hist_eq_img_encoded).decode('utf-8')