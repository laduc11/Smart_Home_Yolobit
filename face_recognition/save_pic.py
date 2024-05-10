import tensorflow as tf
from tensorflow.keras import layers, models
from keras.models import load_model 

import os
import numpy as np
import cv2
import matplotlib.pyplot as plt


embedding_layer = load_model("embedding_layer.h5", compile=False)
anchor_input = tf.keras.Input(shape=(100,75,3))
anchor_embeddings = embedding_layer(anchor_input)
embedding_model = models.Model(inputs=anchor_input, outputs=anchor_embeddings)

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')


# Hàm để lấy danh sách các file trong một thư mục
def get_file_list(folder_path):
    file_list = []
    for file in os.listdir(folder_path):
        if file.endswith('.jpg') or file.endswith('.png') or file.endswith('.jpeg'):
            file_list.append(file)
    return file_list


with open("image_features.txt", "w") as file:
    for file_name in get_file_list('./data'):
        pic = cv2.imread('./data/'+file_name)
        gray = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)
        face = face_cascade.detectMultiScale(gray, 1.1, 4)
        face = face[np.argmax(face[:, 2])]
        face = np.expand_dims(face, 0)

        for (x, y, w, h) in face:
            face = pic[y:y + h, x:x + w]
            face = cv2.resize(face, (75, 100))
            face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
        
        embedding = embedding_model.predict(np.expand_dims(np.array(face), axis = 0))
        file.write(file_name.split('.')[0] + " ")
        file.write(np.array2string(embedding) + ',')
        file.write('\n')