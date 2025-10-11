import pymongo
import os
from dotenv import load_dotenv
load_dotenv()


def get_mongo_client(mongo_uri):
    """Establish and validate connection to the MongoDB."""

    client = pymongo.MongoClient(
        mongo_uri, appname="devrel.showcase.agents.video_intelligence.python"
    )

    # Validate the connection
    ping_result = client.admin.command("ping")
    if ping_result.get("ok") == 1.0:
        # Connection successful
        print("Connection to MongoDB successful")
        return client
    else:
        print("Connection to MongoDB failed")
    return None

DB_NAME = "video_intelligence"
db_client = get_mongo_client(os.environ.get("MONGODB_URI"))
db = db_client[DB_NAME]
print(db)





# Collection names
FRAME_INTELLIGENCE_METADATA = "video_intelligence"
VIDEO_LIBRARY = "video_library"
PREVIOUS_FRAME_INCIDENTS = "previous_frame_incidents"


# Embedding dimensions
EMBEDDING_DIMENSIONS = 1024

# Create collections


def create_collections():
    existing_collections = db.list_collection_names()
    print(f"Existing collections: {existing_collections}")

    # If the collection does not exist, create it
    if FRAME_INTELLIGENCE_METADATA not in existing_collections:
        db.create_collection(FRAME_INTELLIGENCE_METADATA)
        print(f"Created collection: {FRAME_INTELLIGENCE_METADATA}")
    else:
        print(f"Collection {FRAME_INTELLIGENCE_METADATA} already exists")

    if VIDEO_LIBRARY not in existing_collections:
        db.create_collection(VIDEO_LIBRARY)
        print(f"Created collection: {VIDEO_LIBRARY}")
    else:
        print(f"Collection {VIDEO_LIBRARY} already exists")

    if PREVIOUS_FRAME_INCIDENTS not in existing_collections:
        db.create_collection(PREVIOUS_FRAME_INCIDENTS)
        print(f"Created collection: {PREVIOUS_FRAME_INCIDENTS}")
    else:
        print(f"Collection {PREVIOUS_FRAME_INCIDENTS} already exists")


print(create_collections()) 


