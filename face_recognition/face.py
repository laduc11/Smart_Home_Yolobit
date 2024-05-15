import tensorflow as tf
from tensorflow.keras import layers, models
from keras.models import load_model  # TensorFlow is required for Keras to work (version == 2.13.0)
import cv2  # Install opencv-python
import numpy as np
from scipy import spatial
# import time


def recognize(pic=None, threshold=0.9):
    if pic is None:
        return "unknown", False

    gray = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)
    face = face_cascade.detectMultiScale(gray, 1.1, 4)
    face = np.array(face)
    if len(face) == 0:
        return "unknown", False
    face = face[np.argmax(face[:, 2])]
    face = np.expand_dims(face, 0)
    for (x, y, w, h) in face:
        face = pic[y:y + h, x:x + w]
        face = cv2.resize(face, (75, 100))
        face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

    embedding = embedding_model.predict(np.expand_dims(np.array(face), axis=0))
    s = ""
    with open('face_recognition/image_features.txt', "r") as file:
        for line in file:
            s += line

    similar_face = []
    # convert (string) s to (np.ndarray) vector
    for i in range(s.count(',')):
        string = s.split(',')[i]
        class_name = string[:string.index(' ')].replace("\n", "")
        vector = np.fromstring(string[string.index(' ') + 3:string.index(']]')].replace("\n", ""), dtype=float, sep=' ')
        similarity = 1 - spatial.distance.cosine(embedding[0], vector)
        if similarity >= threshold:
            similar_face.append((class_name, similarity))
            print("class name: {}, similarity value: {}".format(class_name, similarity))

    if len(similar_face) != 0:
        sorted_similar_face = sorted(similar_face, key=lambda node: node[1], reverse=True)
        return sorted_similar_face[0][0], True
    return "unknown", False


# Load the embedding_layer
embedding_layer = load_model("face_recognition/embedding_layer.h5", compile=False)

# Embedding model
anchor_input = tf.keras.Input(shape=(100, 75, 3))
anchor_embeddings = embedding_layer(anchor_input)
embedding_model = models.Model(inputs=anchor_input, outputs=anchor_embeddings)

# Face detect with Haar Cascade
face_cascade = cv2.CascadeClassifier("face_recognition/haarcascade_frontalface_default.xml")
