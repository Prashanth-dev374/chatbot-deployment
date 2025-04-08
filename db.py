from pymongo import MongoClient

# Your connection string
MONGO_URI = "mongodb+srv://atlas-sample-dataset-load-67f4bffca7af2e32f0af104c:prashanth6224@cluster0.mbfzyjv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI)

# Choose your database name
db = client.chatbotDB
