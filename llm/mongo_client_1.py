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

# Collection names
FRAME_INTELLIGENCE_METADATA = "video_intelligence"
TRANSCRIPT_COLL = "transcripts"
VIDEO_LIBRARY = "video_library"
PREVIOUS_FRAME_INCIDENTS = "previous_frame_incidents"
VIDEO_INTELLIGENCE_TRANSCRIPTS = "video_intelligence_transcripts"

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


# Create Indexes
from pymongo.operations import SearchIndexModel
import time


# Create vector search index if it doesn't exist
def create_vector_search_index(
        collection,
        vector_index_name,
        dimensions=1024,
        quantization="scalar",
        embedding_path="embedding",
):
    # Check if index already exists
    try:
        existing_indexes = collection.list_search_indexes()
        for index in existing_indexes:
            if index["name"] == vector_index_name:
                print(f"Vector search index '{vector_index_name}' already exists.")
                return
    except Exception as e:
        print(f"Could not list search indexes: {e}")
        return

    index_definition = {
        "fields": [
            {
                "type": "vector",
                "path": embedding_path,
                "numDimensions": dimensions,
                "similarity": "cosine",
            }
        ]
    }

    if quantization == "scalar":
        index_definition["fields"][0]["quantization"] = quantization

    if quantization == "binary":
        index_definition["fields"][0]["quantization"] = quantization

    # Create vector search index
    search_index_model = SearchIndexModel(
        definition=index_definition,
        name=vector_index_name,
        type="vectorSearch",
    )

    try:
        result = collection.create_search_index(model=search_index_model)
        print(f"New search index named '{result}' is building.")
    except Exception as e:
        print(f"Error creating vector search index: {e}")
        return

    # Wait for initial sync to complete
    print(
        f"Polling to check if the index '{result}' is ready. This may take up to a minute."
    )
    predicate = lambda index: index.get("queryable") is True

    while True:
        try:
            indices = list(collection.list_search_indexes(result))
            if indices and predicate(indices[0]):
                break
            time.sleep(5)
        except Exception as e:
            print(f"Error checking index readiness: {e}")
            time.sleep(5)

    print(f"{result} is ready for querying.")


create_vector_search_index(
    db[FRAME_INTELLIGENCE_METADATA], "vector_search_index_scalar", quantization="scalar"
)
create_vector_search_index(
    db[FRAME_INTELLIGENCE_METADATA],
    "vector_search_index_full_fidelity",
    quantization="full_fidelity",
)
create_vector_search_index(
    db[FRAME_INTELLIGENCE_METADATA],
    "vector_search_index_binary",
    quantization="binary",
)
create_vector_search_index(
    db[PREVIOUS_FRAME_INCIDENTS], "incident_vector_index_scalar", quantization="scalar"
)
create_vector_search_index(
    db[VIDEO_LIBRARY], "video_vector_index", quantization="full_fidelity"
)


def create_text_search_index(collection, index_definition, index_name):
    """
    Create a search index for a MongoDB Atlas collection.

    Args:
    collection: MongoDB collection object
    index_definition: Dictionary defining the index mappings
    index_name: String name for the index

    Returns:
    str: Result of the index creation operation
    """

    try:
        search_index_model = SearchIndexModel(
            definition=index_definition, name=index_name
        )

        result = collection.create_search_index(model=search_index_model)
        print(f"Search index '{index_name}' created successfully")
        return result
    except Exception as e:
        print(f"Error creating search index: {e!s}")
        return None


def insert_frame_data_to_mongo(frame_data_df):
    """Insert frame data DataFrame into MongoDB collection"""
    frame_intelligence_documents = frame_data_df.to_dict(orient="records")

    # Create a new collection for frame intelligence
    frame_intelligence_collection = db[FRAME_INTELLIGENCE_METADATA]

    # Insert the frame intelligence documents into the collection
    frame_intelligence_collection.insert_many(frame_intelligence_documents)

    print(f"Inserted {len(frame_intelligence_documents)} documents into {FRAME_INTELLIGENCE_METADATA}")
    print(f"Total documents in collection: {frame_intelligence_collection.count_documents({})}")

    return frame_intelligence_collection


if __name__ == "__main__":
    frame_intelligence_index_definition = {
        "mappings": {
            "dynamic": True,
            "fields": {
                # "video_id": {
                #     "type": "string",
                # },
                # "video_name": {
                #     "type": "string",
                # },
                # "video_url": {
                #     "type": "string",
                # },
                "frame_description": {
                    "type": "string",
                },
                "frame_number": {
                    "type": "number",
                },
                "frame_timestamp": {
                    "type": "date",
                },
            },
        }
    }

    print(create_text_search_index(
        db[FRAME_INTELLIGENCE_METADATA],
        frame_intelligence_index_definition,
        "frame_intelligence_index",
    ))

    # Ensure the collections are empty
    db[FRAME_INTELLIGENCE_METADATA].delete_many({})
    db[PREVIOUS_FRAME_INCIDENTS].delete_many({})
    db[VIDEO_LIBRARY].delete_many({})

    print(create_collections())
