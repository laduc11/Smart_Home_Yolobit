import tensorflow as tf
from tensorflow.keras import layers, models
from keras.models import load_model  # TensorFlow is required for Keras to work (version == 2.13.0)
import cv2  # Install opencv-python
import numpy as np
from scipy import spatial
import time


def recognition(s, embedding, threshold):
    for i in range(s.count(',')):
        string = s.split(',')[i]
        class_name = string[:string.index(' ')].replace("\n", "")
        vector = np.fromstring(string[string.index(' ')+3:string.index(']]')].replace("\n", ""), dtype=float, sep=' ')
        similarity = 1 - spatial.distance.cosine(embedding[0], vector)
        print(similarity)
        if similarity >= threshold:
            return class_name, True
    return "false", False


# Load the embedding_layer
embedding_layer = load_model("embedding_layer.h5", compile=False)

# Embedding model
anchor_input = tf.keras.Input(shape=(100,75,3))
anchor_embeddings = embedding_layer(anchor_input)
embedding_model = models.Model(inputs=anchor_input, outputs=anchor_embeddings)

# Face detect with Haar Cascade
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# start = time.time()
pic = cv2.imread('./bach.jpg')  # modify with cv2 capture image

gray = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)
face = face_cascade.detectMultiScale(gray, 1.1, 4)
face = face[np.argmax(face[:, 2])]
face = np.expand_dims(face, 0)
for (x, y, w, h) in face:
    face = pic[y:y + h, x:x + w]
    face = cv2.resize(face, (75, 100))
    face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

embedding = embedding_model.predict(np.expand_dims(np.array(face), axis = 0))
# print(f"embedding time: {time.time() - start}")
s = ""
with open('./image_features.txt', "r") as file:
    for line in file:
        s += line


threshold = 0.9
name, isTrue = recognition(s, embedding, threshold)
print(name)
# print(f"run time: {time.time() - start}")