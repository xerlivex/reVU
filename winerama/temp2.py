import os

os.chdir('D:/Users/Mykolas/winerama-recommender-tutorial/winerama')
os.getcwd()

os.environ['DJANGO_SETTINGS_MODULE'] = 'winerama.settings'

#import django

import django

django.setup()

from reviews.models import Review, Wine, Cluster, UserRating, Rating
from django.contrib.auth.models import User
from sklearn.cluster import KMeans
from scipy.sparse import dok_matrix, csr_matrix
import numpy as np
import pandas as pd
from scipy.spatial.distance import cosine

from django.template import RequestContext


num_reviews = Review.objects.count()
update_step = ((num_reviews/100)+1) * 5

if num_reviews % update_step == 3: # using some magic numbers here, sorry...
    # Create a sparse matrix from user reviews
    all_user_names = map(lambda x: x.username, User.objects.only("username"))
    all_wine_ids = set(map(lambda x: x.wine.id, Review.objects.only("wine")))
    num_users = len(all_user_names)
    ratings_m = dok_matrix((num_users, max(all_wine_ids)+1), dtype=np.float32)
    for i in range(num_users): # each user corresponds to a row, in the order of all_user_names
        user_reviews = Review.objects.filter(user_name=all_user_names[i])
        for user_review in user_reviews:
            ratings_m[i,user_review.wine.id] = user_review.rating
    
    # Perform kmeans clustering
    k = int(num_users / 10) + 2
    kmeans = KMeans(n_clusters=k)
    clustering = kmeans.fit(ratings_m.tocsr())
    
# Update clusters
    Cluster.objects.all().delete()
    new_clusters = {i: Cluster(name=i) for i in range(k)}
    for cluster in new_clusters.values(): # clusters need to be saved before referring to users
        cluster.save()
    for i,cluster_label in enumerate(clustering.labels_):
        new_clusters[cluster_label].users.add(User.objects.get(username=all_user_names[i]))
        
