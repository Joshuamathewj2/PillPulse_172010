import cv2
import math
import numpy as np

def createKernel(kernelSize, sigma, theta):
    assert kernelSize % 2 # must be odd size
    halfSize = kernelSize // 2
    
    kernel = np.zeros([kernelSize, kernelSize])
    sigmaX = sigma
    sigmaY = sigma * theta
    
    for i in range(kernelSize):
        for j in range(kernelSize):
            x = i - halfSize
            y = j - halfSize
            
            expTerm = np.exp(-x**2 / (2 * sigmaX) - y**2 / (2 * sigmaY))
            xTerm = (x**2 - sigmaX**2) / (2 * math.pi * sigmaX**5 * sigmaY)
            yTerm = (y**2 - sigmaY**2) / (2 * math.pi * sigmaY**5 * sigmaX)
            
            kernel[i, j] = (xTerm + yTerm) * expTerm

    kernel = kernel / np.sum(kernel)
    return kernel

def wordSegmentation(imgRGB, img, kernelSize=25, sigma=11, theta=7, minArea=0):
    kernel = createKernel(kernelSize, sigma, theta)
    imgFiltered = cv2.filter2D(img, -1, kernel, borderType=cv2.BORDER_REPLICATE).astype(np.uint8)
    imgThres = cv2.adaptiveThreshold(
        imgFiltered, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    imgThres = 255 - imgThres

    if cv2.__version__.startswith('3.'):
        (_, components, _) = cv2.findContours(imgThres, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    else:
        (components, _) = cv2.findContours(imgThres, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    res = []
    for c in components:
        if cv2.contourArea(c) < minArea:
            continue
        currBox = cv2.boundingRect(c)
        (x, y, w, h) = currBox
        currImg = imgRGB[y:y+h, x:x+w]
        res.append((currBox, currImg))

    return sorted(res, key=lambda entry:entry[0][0])

def prepareImg(img, height):
    assert img.ndim in (2, 3)
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h = img.shape[0]
    factor = height / h
    return cv2.resize(img, dsize=None, fx=factor, fy=factor)

def xyz(img, height):
    assert img.ndim in (2, 3)
    h = img.shape[0]
    factor = height / h
    return cv2.resize(img, dsize=None, fx=factor, fy=factor)

def preprocess_prescription(img_bytes):
    # Decode image
    nparr = np.frombuffer(img_bytes, np.uint8)
    img_color = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_gray = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

    if img_color is None or img_gray is None:
        raise ValueError("Invalid image content")

    preProcess = cv2.medianBlur(img_gray, 5)
    Gaussian = cv2.adaptiveThreshold(preProcess, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    img = prepareImg(Gaussian, 1000)
    imgRGB = xyz(img_color, 1000)
    
    res = wordSegmentation(imgRGB, img, kernelSize=25, sigma=11, theta=7, minArea=100)
    
    test_array = []
    if len(res) == 0:
        gray_word = img_gray
        new_array = cv2.resize(gray_word, (160, 80))
        new_array = new_array.reshape(new_array.shape + (1,))
        test_array.append(new_array)
    else:
        for (wordBox, wordImg) in res:
            gray_word = cv2.cvtColor(wordImg, cv2.COLOR_BGR2GRAY)
            new_array = cv2.resize(gray_word, (160, 80))
            new_array = new_array.reshape(new_array.shape + (1,))
            test_array.append(new_array)
        
    test_array = np.array(test_array)
    test_array = test_array / 255.0
    
    return test_array
