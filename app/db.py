# Importing MongoClient from pymongo library to connect to MongoDB
from pymongo import MongoClient

# Function to get the database connection
def get_db():
    # Connecting to MongoDB using a connection string (URL) with the credentials
    # Replace the placeholder with your actual username, password, and cluster details.
    client = MongoClient(
        "mongodb+srv://bharath:bharathsivanesh262005@cluste.5phjp.mongodb.net/study_planner?retryWrites=true&w=majority&appName=Cluste"
    )
    
    # Returning the 'study_planner' database from the connected MongoDB client
    return client["study_planner"]
