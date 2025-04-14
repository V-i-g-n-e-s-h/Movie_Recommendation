import streamlit as st
from py2neo import Graph
import pandas as pd
import math
from dotenv import load_dotenv
import os

load_dotenv()

sandbox_url = os.getenv("SANDBOX_URL")
sandbox_username = os.getenv("SANDBOX_USERNAME")
sandbox_password = os.getenv("SANDBOX_PASSWORD")

@st.cache_resource
def connect_to_neo4j():
    return Graph(sandbox_url, auth=(sandbox_username, sandbox_password))

graph = connect_to_neo4j()

def get_all_users():
    query = """
    MATCH (u:User) 
    RETURN u.name AS name 
    ORDER BY name
    """
    result = graph.run(query).data()
    return [user['name'] for user in result]

def get_all_movies():
    query = """
    MATCH (m:Movie) 
    RETURN m.title AS title 
    ORDER BY title
    """
    result = graph.run(query).data()
    return [movie['title'] for movie in result]

def get_all_genres():
    query = """
    MATCH (g:Genre) 
    RETURN g.name AS name 
    ORDER BY name
    """
    result = graph.run(query).data()
    return [genre['name'] for genre in result]

def get_all_directors():
    query = """
    MATCH (p:Person)-[:DIRECTED]->()
    RETURN DISTINCT p.name AS name
    ORDER BY name
    """
    result = graph.run(query).data()
    return [director['name'] for director in result]

def get_all_actors():
    query = """
    MATCH (p:Person)-[:ACTED_IN]->()
    RETURN DISTINCT p.name AS name
    ORDER BY name
    """
    result = graph.run(query).data()
    return [actor['name'] for actor in result]

def get_user_watched_movies(user_name):
    query = """
    MATCH (u:User {name: $user_name})-[:RATED]->(m:Movie)
    RETURN m.title AS title
    """
    result = graph.run(query, user_name=user_name).data()
    return [movie['title'] for movie in result]

def get_recommended_movies_from_movie(movie_title, user_name):
    query = """
    MATCH (:Movie {title: $movie_title})<-[:RATED]-(other_user:User)-[r:RATED]->(m:Movie)
    WHERE m.title <> $movie_title
    AND NOT EXISTS {
        MATCH (u:User {name: $user_name})-[:RATED]->(m)
    }
    RETURN m.title AS title, avg(r.rating) AS avg_rating, count(*) AS frequency
    ORDER BY frequency DESC, avg_rating DESC
    """
    return pd.DataFrame(graph.run(query, movie_title=movie_title, user_name=user_name).data())

def get_top_movies_by_genre(genre_name, user_name):
    query = """
    MATCH (m:Movie)-[:IN_GENRE]->(:Genre {name: $genre})
    MATCH (m)<-[r:RATED]-()
    WHERE NOT EXISTS {
        MATCH (u:User {name: $user_name})-[:RATED]->(m)
    }
    RETURN m.title AS title, avg(r.rating) AS avg_rating, count(r) AS ratings_count
    ORDER BY avg_rating DESC, ratings_count DESC
    """
    return pd.DataFrame(graph.run(query, genre=genre_name, user_name=user_name).data())

def get_movies_by_director(director_name, user_name):
    query = """
    MATCH (p:Person {name: $director_name})-[:DIRECTED]->(m:Movie)
    MATCH (m)<-[r:RATED]-()
    WHERE NOT EXISTS {
        MATCH (u:User {name: $user_name})-[:RATED]->(m)
    }
    RETURN m.title AS title, avg(r.rating) AS avg_rating, count(r) AS watch_count
    ORDER BY avg_rating DESC, watch_count DESC
    """
    return pd.DataFrame(graph.run(query, director_name=director_name, user_name=user_name).data())

def get_movies_by_actor(actor_name, user_name):
    query = """
    MATCH (p:Person {name: $actor_name})-[:ACTED_IN]->(m:Movie)
    MATCH (m)<-[r:RATED]-()
    WHERE NOT EXISTS {
        MATCH (u:User {name: $user_name})-[:RATED]->(m)
    }
    RETURN m.title AS title, avg(r.rating) AS avg_rating, count(r) AS watch_count
    ORDER BY avg_rating DESC, watch_count DESC
    """
    return pd.DataFrame(graph.run(query, actor_name=actor_name, user_name=user_name).data())

def get_user_top_movies(user_name):
    query = """
    MATCH (u:User {name: $user_name})-[r:RATED]->(m:Movie)
    RETURN m.title AS title, r.rating AS rating
    ORDER BY r.rating DESC
    """
    return pd.DataFrame(graph.run(query, user_name=user_name).data())

def paginate_dataframe(dataframe, page_size, page_num):
    total_pages = max(1, math.ceil(len(dataframe) / page_size))
    page_num = max(1, min(page_num, total_pages))
    start_idx = (page_num - 1) * page_size
    end_idx = min(start_idx + page_size, len(dataframe))
    
    return dataframe.iloc[start_idx:end_idx], total_pages, page_num

def display_paginated_results(df):
    if not df.empty:
        paginated_df, total_pages, current_page = paginate_dataframe(df, page_size, st.session_state['current_page'])
        col1, col2, col3, col4 = st.columns([1, 3, 3, 1])
        with col1:
            if st.button("◀️ Prev"):
                st.session_state['current_page'] = max(1, st.session_state['current_page'] - 1)
                st.rerun()
        
        with col2:
            st.write(f"Page {current_page} of {total_pages}")
        
        with col3:
            st.write(f"Showing {len(paginated_df)} of {len(df)} results")
            
        with col4:
            if st.button("Next ▶️"):
                st.session_state['current_page'] = min(total_pages, st.session_state['current_page'] + 1)
                st.rerun()
        st.dataframe(paginated_df)
        return True
    else:
        return False

st.title("Movie Recommender App")

if 'previous_option' not in st.session_state:
    st.session_state['previous_option'] = None

# setting side bar
users = get_all_users()
user_name = st.sidebar.selectbox("Select User:", users)

with st.sidebar.expander("Your Top Rated Movies", expanded=False):
    user_top_movies = get_user_top_movies(user_name)
    if not user_top_movies.empty:
        st.dataframe(user_top_movies, height=200)
    else:
        st.info("No rated movies found.")

# recommendation type
option = st.radio("Choose recommendation type:", ["By Movie", "By Genre", "By Director", "By Actor"])

if st.session_state['previous_option'] != option:
    if 'current_df' in st.session_state:
        del st.session_state['current_df']
    if 'current_page' in st.session_state:
        st.session_state['current_page'] = 1
    st.session_state['previous_option'] = option

page_size = st.sidebar.number_input("Results per page:", min_value=5, max_value=100, value=10)

if option == "By Movie":
    movies = get_all_movies()
    movie_name = st.selectbox("Select a movie:", movies)
    
    if st.button("Get Recommendations") and movie_name:
        with st.spinner(f"Finding similar movies to '{movie_name}' (excluding movies already watched by {user_name})..."):
            df = get_recommended_movies_from_movie(movie_name, user_name)
            st.session_state['current_df'] = df
            st.session_state['current_page'] = 1
            
    if 'current_df' in st.session_state and option == "By Movie":
        if not display_paginated_results(st.session_state['current_df']):
            st.info(f"No new recommendations found for '{movie_name}' that {user_name} hasn't watched yet.")

elif option == "By Genre":
    genres = get_all_genres()
    genre = st.selectbox("Select a genre:", genres)
    
    if st.button("Get Recommendations") and genre:
        with st.spinner(f"Finding top {genre} movies (excluding movies already watched by {user_name})..."):
            df = get_top_movies_by_genre(genre, user_name)
            st.session_state['current_df'] = df
            st.session_state['current_page'] = 1
            
    if 'current_df' in st.session_state and option == "By Genre":
        if not display_paginated_results(st.session_state['current_df']):
            st.info(f"No new {genre} movies found that {user_name} hasn't watched yet.")

elif option == "By Director":
    directors = get_all_directors()
    director_name = st.selectbox("Select a director:", directors)
    
    if st.button("Get Recommendations") and director_name:
        with st.spinner(f"Finding movies directed by {director_name} (excluding movies already watched by {user_name})..."):
            df = get_movies_by_director(director_name, user_name)
            st.session_state['current_df'] = df
            st.session_state['current_page'] = 1
            
    if 'current_df' in st.session_state and option == "By Director":
        if not display_paginated_results(st.session_state['current_df']):
            st.info(f"No new movies directed by {director_name} found that {user_name} hasn't watched yet.")

elif option == "By Actor":
    actors = get_all_actors()
    actor_name = st.selectbox("Select an actor:", actors)
    
    if st.button("Get Recommendations") and actor_name:
        with st.spinner(f"Finding movies starring {actor_name} (excluding movies already watched by {user_name})..."):
            df = get_movies_by_actor(actor_name, user_name)
            st.session_state['current_df'] = df
            st.session_state['current_page'] = 1
            
    if 'current_df' in st.session_state and option == "By Actor":
        if not display_paginated_results(st.session_state['current_df']):
            st.info(f"No new movies starring {actor_name} found that {user_name} hasn't watched yet.")