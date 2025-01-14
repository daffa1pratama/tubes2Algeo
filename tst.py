import cv2
import numpy as np
import scipy 
from matplotlib.image import imread
import pickle as pickle
import random
import os
import matplotlib.pyplot as plt
from scipy import spatial

# Feature extractor
def extract_features(image_path, vector_size=32):
    image = imread(image_path)
    try:
        # Using KAZE, cause SIFT, ORB and other was moved to additional module
        # which is adding addtional pain during install
        alg = cv2.KAZE_create()
        # Dinding image keypoints
        kps = alg.detect(image)
        # Getting first 32 of them. 
        # Number of keypoints is varies depend on image size and color pallet
        # Sorting them based on keypoint response value(bigger is better)
        kps = sorted(kps, key=lambda x: -x.response)[:vector_size]
        # computing descriptors vector
        kps, dsc = alg.compute(image, kps)
        # Flatten all of them in one big vector - our feature vector
        dsc = dsc.flatten()
        # Making descriptor of same size
        # Descriptor vector size is 64
        needed_size = (vector_size * 64)
        if dsc.size < needed_size:
            # if we have less the 32 descriptors then just adding zeros at the
            # end of our feature vector
            dsc = np.concatenate([dsc, np.zeros(needed_size - dsc.size)])
    except cv2.error as e:
        #print ("Error: ", e)
        return None

    return dsc


def batch_extractor(images_path, pickled_db_path="referensi.pck"):
    files = [os.path.join(images_path, p) for p in sorted(os.listdir(images_path))]

    result = {}
    i=1
    for f in files:
        print ("Extracting features from image %s" % f)
        print (i)
        i+=1
        name = f.split('/')[-1].lower()
        result[name] = extract_features(f)
    
    # saving all our feature vectors in pickled file
    with open(pickled_db_path, 'wb') as fp:
        pickle.dump(result, fp)

class Matcher(object):

    def __init__(self, pickled_db_path="features.pck"):
        with open(pickled_db_path, 'rb') as fp:
            self.data = pickle.load(fp)
        self.names = []
        self.matrix = []
        for k, v in self.data.items():
            self.names.append(k)
            self.matrix.append(v)
        self.matrix = np.array(self.matrix)
        self.names = np.array(self.names)

    def cos_cdist(self, vector):
        # getting cosine distance between search image and images database
        v = vector.reshape(1, -1)
        return scipy.spatial.distance.cdist(self.matrix, v, "cosine").reshape(-1)

    def match(self, image_path, topn=5):
        features = extract_features(image_path)
        img_distances = self.cos_cdist(features)
        # getting top 5 records
        nearest_ids = np.argsort(img_distances)[:topn].tolist()
        print(nearest_ids)
        nearest_img_paths = self.names[nearest_ids].tolist()
        return nearest_img_paths, img_distances[nearest_ids].tolist()


def cosine_similarity(arrsample, arrextract):
    dot=0
    for i in range(len(arrsample)):
        dotopr = arrsample[i]*arrextract[i]
        dot += dotopr
    normsample = 0
    for i in range(len(arrsample)):
        x = arrsample[i]**2
        normsample += x
    normextract = 0
    for i in range(len(arrsample)):
        x = arrextract[i]**2
        normextract += x
    normsample = normsample**0.5
    normextract = normextract**0.5
    return(dot/(normextract*normsample))

def euclidean_distance(arrsample, arrextract):
    sum=0
    temp=0
    for i in range(len(arrsample)):
        temp = (arrsample[i] - arrextract[i])**2
        sum += temp
    return(sum**0.5)

def show_img(path):
    img = imread(path)
    kaze = cv2.KAZE_create()
    kp = kaze.detect(img,None)
    img2 = cv2.drawKeypoints(img,kp,outImage=None,flags=0,color=(0,255,0))
    plt.imshow(img2)
    plt.show()
    
def run():
    #images_path = "..\Database Tugas Besar\Data Referensi"
    images_path = "..\pins-face-recognition\PINS\pins_zendaya"
    files = [os.path.join(images_path, p) for p in sorted(os.listdir(images_path))]
    # getting 3 random images 
    sample = random.sample(files, 1)
    """
    print(sample)
    print(sample[0])
    """
    #batch_extractor(images_path)

    ma = Matcher("features.pck")
    
    #print(ma.matrix)
    #print(ma.names)

    # *** MATCHER ***#
    index = 0
    while(ma.names[index]!=sample[0].lower()):
        index += 1
    
    print(index)

    #cosine similarity
    cosine = [0 for i in range(len(ma.matrix))]
    for i in range(len(ma.matrix)):
        cosine[i] = 1-cosine_similarity(ma.matrix[index], ma.matrix[i])
    cosine = np.array(cosine)
    print(cosine)

    #euclidean distance
    dist = [0 for i in range(len(ma.matrix))]
    for i in range(len(ma.matrix)):
        dist[i] = euclidean_distance(ma.matrix[index], ma.matrix[i])
    dist = np.array(dist)
    print(dist)


    # *** ID *** #
    top = int(input("Masukkan banyak: "))
    ncosine = np.argsort(cosine)[:top].tolist()
    ndist = np.argsort(dist)[:top].tolist()
    print(ncosine)
    print(ndist)

    
    # *** SHOW RESULT *** #
    for s in sample:
        print("Random image ===========================")
        show_img(s)
        print("Result image ===========================")
        for i in range(top):
            j=0
            while(j!=ncosine[i]):
                j+=1
            show_img(os.path.join(ma.names[j]))
            print(cosine[ncosine[i]])
    
    #print(ma.matrix[index])
    #print(ma.names[index])
    """
    for s in sample:
        print ("Query image ==========================================")
        show_img(s)
        names, match = ma.match(s, topn=3)
        print(names)
        print(match)
        print ("Result images ========================================")
        for i in range(3):
            # we got cosine distance, less cosine distance between vectors
            # more they similar, thus we subtruct it from 1 to get match value
            print ("Match %s" % (1-match[i]))
            show_img(os.path.join(names[i]))
    """
run()