import os
import cv2
import sys
import re
import numpy as np
import pytesseract
from navec import Navec
from slovnet import NER
from pdf2image import convert_from_path
from matplotlib import pyplot as plt
from PIL import Image
from PyPDF2 import PdfFileMerger

class FileProcessing(object):
    '''
    Класс обработки *.pdf файла:
    1. Преобразование страниц файла в jpeg
    2. Обезличивание данных на изображениях
    3. Сохранение полученных изображений
    '''
    
    def __init__(self, full_path_pdf):
        self.full_path = full_path_pdf
        self.poppler_path = r'poppler-0.68.0\bin'
        
    def pdf2jpg(self):
        '''
        Конвертация *.pdf-файлов в *.jpeg постранично
        Возвращает полученные изображения списком
        
        *.pdf --> *.jpeg
        '''
        
        return convert_from_path(self.full_path, 200, poppler_path=self.poppler_path, fmt='png', thread_count=2)
    
    def textExtract(self, processed_image):
        '''
        Извлечение текста из изображения
        Возвращает текст
        
        image --> text
        '''
        
        return re.sub('\n', ' ', pytesseract.image_to_string(processed_image, lang='rus'))
    
    def imagePreproc(self, image):
        '''
        Предобработка изображения (преобразование в другую цветовую кодировку и использование бинарного трешхолда, 
        для улучшения качества парсинага текста)
        Возвращает обработанное изображение
        
        image --> image
        '''

        # im_gray = cv2.imread(img_rgb, cv2.IMREAD_GRAYSCALE)
        img_rgb = cv2.cvtColor(np.array(image), cv2.IMREAD_GRAYSCALE)

        ret, threshold_image = cv2.threshold(img_rgb, 180,255, cv2.THRESH_BINARY)

        return threshold_image
    
    def tagChoosing(self, markup, tag = 'PER'):
        '''
        Извлечение текста для заданной разметки(по умолчанию 'PER' - ФИО текста)
        Возвращает список токенов, которым присвоен данных тэг
        
        murkup --> list of tokens
        '''
        
        return [markup.text[i.start:i.stop] for i in markup.spans if i.type == tag]
    
    def wordOccurences(self, data, persons):
        splited_pers = []

        for i in persons:
            splited_pers += i.split()

        word_occurences = []
        for target_words in splited_pers:
            for i, word in enumerate(data["text"]):
                if word == target_words:
                    word_occurences.append(i)
        return word_occurences
    
        return [[i for i, word in enumerate(data["text"]) if word == target_words] for target_words in persons]
    
    def imageSaver(self, image_loc, data, word_occurences, page):
        for occ in word_occurences:
            w = data["width"][occ]
            h = data["height"][occ]
            x = data["left"][occ]
            y = data["top"][occ]

            p1 = (x, y)
            p2 = (x + w, y + h)

            ROI = image_loc[y:y+h, x:x+w]
            blur = cv2.GaussianBlur(ROI, (35,35), 0) 
            image_loc[y:y+h, x:x+w] = blur

        name = str('.'.join(self.full_path.split('.')[:-1])).split('\\')[-1]
        plt.imsave('output\\' + name + '__' + str(page) + '.jpeg', image_loc)
    
        
    def fit(self):
        print()
        pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
        navec = Navec.load('navec_news_v1_1B_250K_300d_100q.tar')
        
        ner = NER.load('slovnet_ner_news_v1.tar')
        ner.navec(navec)
        
        ext = self.full_path.split('.')[-1]
        images = []
        if (ext == 'jpg' or ext == 'jpeg'):
            images.append(Image.open(self.full_path))
        else: 
            images = self.pdf2jpg()
            
        print('processing...')
        for page in range(len(images)):
            processed_image = self.imagePreproc(images[page])
            text = self.textExtract(processed_image)
            markup = ner(text)
            pers_tokens = self.tagChoosing(markup)
            data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT, lang='rus')
            word_occurences = self.wordOccurences(data, pers_tokens)
            self.imageSaver(processed_image, data, word_occurences, page)
        print('file succesfully processed!')
        print('saved in ' + '\\output\\')

def main():
    os.chdir(os.getcwd())
    pathPDF = sys.argv[1]
    fp = FileProcessing(pathPDF)
    fp.fit()

main()
