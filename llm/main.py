from video_to_image import video_to_images
import voyageai
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
load_dotenv()
from gen_frame_desc import generate_frame_description
from encode_image_to_64 import encode_image_to_base64
from get_voyage_embed import get_voyage_embedding
from process_frames import process_frames_to_embeddings_with_descriptions
import os

# Import mongo client functions
from mongo_client_1 import create_collections, db, FRAME_INTELLIGENCE_METADATA
from mongo_client_2 import create_vector_search_index, create_text_search_index
from mongo_client_3_insert import insert_frame_data_to_mongo

# Import retrieval functions
from get_voyage_embed import get_voyage_embedding
from retreival_2 import manual_hybrid_search
video_title = "video"


# # Convert the video to images
# video_to_images(
#     video_path=f"videos/{video_title}.mp4", output_dir="frames", interval_seconds=2
# )

voyageai_client = voyageai.Client()
openai_client = OpenAI()


frame_data = process_frames_to_embeddings_with_descriptions(
    frames_dir="llm/frames", input_type="document", delay_seconds=0.5, cut_off_frame=500
)


# Convert frame data to a pandas dataframe
frame_data_df = pd.DataFrame.from_dict(frame_data, orient="index")

print("Frame data processed successfully!")
print(frame_data_df.head())

# MongoDB Integration
print("\n=== Setting up MongoDB ===")

# 1. Create collections (this will also establish connection)
print("Creating MongoDB collections...")
create_collections()

# 2. Create vector search indexes
print("Creating vector search indexes...")
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

# 3. Create text search index
print("Creating text search index...")
frame_intelligence_index_definition = {
    "mappings": {
        "dynamic": True,
        "fields": {
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

create_text_search_index(
    db[FRAME_INTELLIGENCE_METADATA],
    frame_intelligence_index_definition,
    "frame_intelligence_index",
)

# 4. Insert frame data into MongoDB
print("Inserting frame data into MongoDB...")
frame_intelligence_collection = insert_frame_data_to_mongo(frame_data_df)

print("\n=== MongoDB setup complete! ===")
print(f"Total frames processed and stored: {len(frame_data_df)}")
print(f"Collection name: {FRAME_INTELLIGENCE_METADATA}")

# Semantic Search Functionality
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

# Interactive Semantic Search
print("\n=== Interactive Semantic Search ===")
print("Enter your queries to search through video frames. Type 'quit' or 'exit' to stop.")

def display_search_results(results, search_type, top_n=3):
    """Helper function to display search results in a formatted way"""
    print(f"\n{search_type} results (top {top_n}): {len(results)} matches")
    for j, result in enumerate(results[:top_n], 1):
        # Handle both regular score and rrf_score (from hybrid search)
        score = result.get('score') or result.get('rrf_score', 'N/A')
        if isinstance(score, (int, float)):
            score_str = f"{score:.4f}"
        else:
            score_str = str(score)
        
        # Handle both timestamp formats
        timestamp = result.get('frame_timestamp') or result.get('timestamp', 'N/A')
        
        print(f"  {j}. Score: {score_str} - Frame: {result.get('frame_number', 'N/A')}")
        print(f"     Timestamp: {timestamp}")
        print(f"     Description: {result.get('frame_description', 'N/A')[:150]}...")
        if j < len(results):
            print()  # Add spacing between results

while True:
    try:
        # Get user input
        user_query = input("\nEnter your search query (or 'quit' to exit): ").strip()
        
        # Check for exit commands
        if user_query.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        # Skip empty queries
        if not user_query:
            print("Please enter a valid query.")
            continue
        
        print(f"\n--- Searching for: '{user_query}' ---")
        
        # Test with scalar quantization (faster, less precise)
        print("Searching with scalar quantization...")
        scalar_results = semantic_search_with_mongodb(
            user_query=user_query,
            collection=db[FRAME_INTELLIGENCE_METADATA],
            top_n=5,
            vector_search_index_name="vector_search_index_scalar",
        )
        
        # Test with full fidelity (slower, more precise)
        print("Searching with full fidelity...")
        full_fidelity_results = semantic_search_with_mongodb(
            user_query=user_query,
            collection=db[FRAME_INTELLIGENCE_METADATA],
            top_n=5,
            vector_search_index_name="vector_search_index_full_fidelity",
        )
        
        # Test with manual hybrid search (combines vector + text search)
        print("Searching with manual hybrid search (70% vector, 30% text)...")
        hybrid_results = manual_hybrid_search(
            user_query=user_query,
            collection=db[FRAME_INTELLIGENCE_METADATA],
            top_n=5,
            vector_search_index_name="vector_search_index_scalar",
            text_search_index_name="text_search_index",
            vector_weight=0.7,
            text_weight=0.3,
            search_type="text",
        )
        
        # Display results
        display_search_results(scalar_results, "Scalar Quantization", 5)
        display_search_results(full_fidelity_results, "Full Fidelity", 5)
        display_search_results(hybrid_results, "Hybrid Search (70% vector, 30% text)", 5)
        
        # Ask if user wants to see more details
        if scalar_results or full_fidelity_results or hybrid_results:
            show_details = input("\nWould you like to see more details for any result? (y/n): ").strip().lower()
            if show_details in ['y', 'yes']:
                try:
                    print("Which result set? (1) Scalar, (2) Full Fidelity, (3) Hybrid")
                    result_set = int(input("Enter choice (1-3): "))
                    result_num = int(input("Enter result number (1-5): ")) - 1
                    
                    # Select the appropriate result set
                    if result_set == 1:
                        results = scalar_results
                    elif result_set == 2:
                        results = full_fidelity_results
                    elif result_set == 3:
                        results = hybrid_results
                    else:
                        print("Invalid choice.")
                        continue
                    
                    if 0 <= result_num < len(results):
                        result = results[result_num]
                        print(f"\n--- Detailed Result {result_num + 1} ---")
                        print(f"Frame Number: {result.get('frame_number', 'N/A')}")
                        
                        # Handle both timestamp formats
                        timestamp = result.get('frame_timestamp') or result.get('timestamp', 'N/A')
                        print(f"Timestamp: {timestamp}")
                        
                        # Handle both score formats
                        score = result.get('score') or result.get('rrf_score', 'N/A')
                        if isinstance(score, (int, float)):
                            print(f"Score: {score:.4f}")
                        else:
                            print(f"Score: {score}")
                        
                        print(f"Full Description: {result.get('frame_description', 'N/A')}")
                        
                        # Handle both path formats
                        image_path = result.get('image_path') or result.get('frame_path', 'N/A')
                        print(f"Image Path: {image_path}")
                        
                        # Show score details for hybrid results
                        if 'score_details' in result:
                            print(f"\nScore Details (RRF breakdown):")
                            for detail in result['score_details']:
                                print(f"  - Pipeline: {detail['pipeline']}")
                                print(f"    Rank: {detail['rank']}, Weight: {detail['weight']}, Contribution: {detail['contribution']:.6f}")
                    else:
                        print("Invalid result number.")
                except ValueError:
                    print("Please enter a valid number.")
        
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        break
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please try again.")

print("\n=== Interactive Search Complete! ===")


 