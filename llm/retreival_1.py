# Implementing vector search
from mongo_client_1 import FRAME_INTELLIGENCE_METADATA, db
from get_voyage_embed import get_voyage_embedding


def semantic_search_with_mongodb(
    user_query, collection, top_n=5, vector_search_index_name="vector_search_index"
):
    """
    Perform a vector search in the MongoDB collection based on the user query.

    Args:
    user_query (str): The user's query string.
    collection (MongoCollection): The MongoDB collection to search.
    top_n (int): The number of top results to return.
    vector_search_index_name (str): The name of the vector search index.

    Returns:
    list: A list of matching documents.
    """

    # Retrieve the pre-generated embedding for the query from our dictionary
    # This embedding represents the semantic meaning of the query as a vector
    query_embedding = get_voyage_embedding(user_query, input_type="query")

    # Check if we have a valid embedding for the query
    if query_embedding is None:
        return "Invalid query or embedding generation failed."

    # Define the vector search stage using MongoDB's $vectorSearch operator
    # This stage performs the semantic similarity search
    vector_search_stage = {
        "$vectorSearch": {
            "index": vector_search_index_name,  # The vector index we created earlier
            "queryVector": query_embedding,  # The numerical vector representing our query
            "path": "embedding",  # The field containing document embeddings
            "numCandidates": 100,  # Explore this many vectors for potential matches
            "limit": top_n,  # Return only the top N most similar results
        }
    }

    # Define which fields to include in the results and their format
    project_stage = {
        "$project": {
            "_id": 0,  # Exclude MongoDB's internal ID
            "embedding": 0,
            "score": {
                "$meta": "vectorSearchScore"  # Include similarity score from vector search
            },
        }
    }

    # Combine the search and projection stages into a complete pipeline
    pipeline = [vector_search_stage, project_stage]

    # Execute the pipeline against our collection and get results
    results = collection.aggregate(pipeline)

    # Convert cursor to a Python list for easier handling
    return list(results)



user_query = "Can you get me the frame with the red shirt player with front flip"


scalar_results = semantic_search_with_mongodb(
    user_query=user_query,
    collection=db[FRAME_INTELLIGENCE_METADATA],
    top_n=5,
    vector_search_index_name="vector_search_index_scalar",
)


full_fidelity_results = semantic_search_with_mongodb(
    user_query=user_query,
    collection=db[FRAME_INTELLIGENCE_METADATA],
    top_n=5,
    vector_search_index_name="vector_search_index_full_fidelity",
)

print(full_fidelity_results)




binary_results = semantic_search_with_mongodb(
    user_query=user_query,
    collection=db[FRAME_INTELLIGENCE_METADATA],
    top_n=5,
    vector_search_index_name="vector_search_index_binary",
)

print(binary_results)