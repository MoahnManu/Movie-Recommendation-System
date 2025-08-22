import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, render_template, request

# --- 1. Data Loading and Preprocessing ---
# This part is the same as the recommendation script, but it will be run once
# when the application starts.
df_ratings = pd.read_csv("C://Project//ratings.csv")
df_movies = pd.read_csv("C://Project//movies.csv")

# Create a user-movie matrix for collaborative filtering
user_movie_matrix = df_ratings.pivot_table(
    index='userId',
    columns='movieId',
    values='rating'
).fillna(0)

# Calculate user similarity matrix
user_similarity = cosine_similarity(user_movie_matrix)
user_similarity_df = pd.DataFrame(
    user_similarity,
    index=user_movie_matrix.index,
    columns=user_movie_matrix.index
)

# --- 2. Recommendation Logic Function ---
def recommend_movies(user_id, num_recommendations=5):
    """
    Recommends movies to a user based on similar users.
    """
    # Get the user's similarity scores with all other users
    similar_users = user_similarity_df[user_id].sort_values(ascending=False)
    similar_users = similar_users.drop(user_id) # Exclude the user themselves
    top_10_similar_users = similar_users.head(10)

    user_ratings = user_movie_matrix.loc[user_id]
    unseen_movies_ids = user_ratings[user_ratings == 0].index
    movie_scores = {}

    for similar_user, similarity_score in top_10_similar_users.items():
        similar_user_unseen_ratings = user_movie_matrix.loc[similar_user, unseen_movies_ids]
        for movie_id, rating in similar_user_unseen_ratings.items():
            if rating > 0:
                if movie_id not in movie_scores:
                    movie_scores[movie_id] = 0
                movie_scores[movie_id] += rating * similarity_score

    recommended_movies = sorted(movie_scores.items(), key=lambda x: x[1], reverse=True)
    top_recommendations = [movie_id for movie_id, score in recommended_movies[:num_recommendations]]

    # Look up movie titles
    recommended_titles = df_movies[df_movies['movieId'].isin(top_recommendations)]['title'].tolist()
    return recommended_titles

# --- 3. Flask Web Application ---
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    recommendations = []
    if request.method == 'POST':
        try:
            # Get user ID from the form
            user_id = int(request.form['user_id'])
            # Generate recommendations
            recommendations = recommend_movies(user_id)
        except (ValueError, KeyError) as e:
            recommendations = [f"Error: Invalid User ID or data. {e}"]
    return render_template('index.html', recommendations=recommendations)

if __name__ == '__main__':
    app.run(debug=True)