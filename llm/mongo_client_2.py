# Create Indexes
from pymongo.operations import SearchIndexModel
import time

from mongo_client_1 import FRAME_INTELLIGENCE_METADATA, PREVIOUS_FRAME_INCIDENTS, VIDEO_LIBRARY
from mongo_client_1 import db

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