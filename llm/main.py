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
from mongo_client_1 import create_collections, db, FRAME_INTELLIGENCE_METADATA, TRANSCRIPT_COLL
from mongo_client_2 import create_vector_search_index, create_text_search_index
from mongo_client_3_insert import insert_frame_data_to_mongo

# Import retrieval functions
from get_voyage_embed import get_voyage_embedding
from retreival_2 import manual_hybrid_search

# Import train.py functions for merged collection
from train import create_merged_collection, VIDEO_INTELLIGENCE_TRANSCRIPTS
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

# Create merged collection with transcripts
print("\n=== Creating Merged Collection with Transcripts ===")
create_merged_collection()
merged_collection = db[VIDEO_INTELLIGENCE_TRANSCRIPTS]
print(f"Merged collection created: {VIDEO_INTELLIGENCE_TRANSCRIPTS}")

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

# New search functions for merged collection with transcript support
def semantic_search_with_transcripts(
    user_query, 
    collection, 
    top_n=5, 
    vector_search_index_name="vector_search_index_scalar"
):
    """
    Perform semantic search on the merged collection and include transcript data.
    
    Args:
        user_query (str): The user's query string.
        collection (MongoCollection): The merged MongoDB collection.
        top_n (int): The number of top results to return.
        vector_search_index_name (str): The name of the vector search index.
    
    Returns:
        list: A list of matching documents with transcript data.
    """
    
    # Get query embedding
    query_embedding = get_voyage_embedding(user_query, input_type="query")
    
    if query_embedding is None:
        return "Invalid query or embedding generation failed."
    
    # Vector search pipeline for merged collection
    vector_search_stage = {
        "$vectorSearch": {
            "index": vector_search_index_name,
            "queryVector": query_embedding,
            "path": "frame_embedding",  # Note: field name is different in merged collection
            "numCandidates": 100,
            "limit": top_n,
        }
    }
    
    # Lookup stage to get transcript data
    lookup_stage = {
        "$lookup": {
            "from": TRANSCRIPT_COLL,
            "localField": "transcript_ids",
            "foreignField": "_id",
            "as": "transcript_data"
        }
    }
    
    # Project stage to format results
    project_stage = {
        "$project": {
            "_id": 0,
            "frame_embedding": 0,  # Remove embedding from output
            "transcript_ids": 0,   # Remove IDs since we have the actual data
            "score": {
                "$meta": "vectorSearchScore"
            },
        }
    }
    
    # Combine stages
    pipeline = [vector_search_stage, lookup_stage, project_stage]
    
    # Execute pipeline
    results = list(collection.aggregate(pipeline))
    
    return results

def hybrid_search_with_transcripts(
    user_query,
    collection,
    top_n=5,
    vector_search_index_name="vector_search_index_scalar",
    text_search_index_name="text_search_index",
    vector_weight=0.7,
    text_weight=0.3,
    search_type="text",
):
    """
    Perform hybrid search on the merged collection with transcript data.
    This is a modified version of manual_hybrid_search for the merged collection.
    """
    
    # Get query embedding
    query_embedding = get_voyage_embedding(user_query, input_type="query")
    
    if query_embedding is None:
        print("Error: Failed to generate embedding for query")
        return []
    
    # Vector search pipeline for merged collection
    vector_pipeline = [
        {
            "$vectorSearch": {
                "index": vector_search_index_name,
                "path": "frame_embedding",  # Different field name in merged collection
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": 20,
            }
        },
        {
            "$project": {
                "_id": 1,
                "frame_number": 1,
                "frame_timestamp": 1,
                "frame_description": 1,
                "time_range": 1,
                "transcript_count": 1,
                "vector_score": {"$meta": "vectorSearchScore"},
            }
        },
    ]
    
    try:
        vector_results = list(collection.aggregate(vector_pipeline))
    except Exception as e:
        print(f"Error in vector search: {e}")
        vector_results = []
    
    # Text search pipeline for merged collection
    if search_type == "text":
        text_query = {"text": {"query": user_query, "path": "frame_description"}}
    else:
        text_query = {"phrase": {"query": user_query, "path": "frame_description"}}
    
    text_pipeline = [
        {"$search": {"index": text_search_index_name, **text_query}},
        {"$limit": 20},
        {
            "$project": {
                "_id": 1,
                "frame_number": 1,
                "frame_timestamp": 1,
                "frame_description": 1,
                "time_range": 1,
                "transcript_count": 1,
                "text_score": {"$meta": "searchScore"},
            }
        },
    ]
    
    try:
        text_results = list(collection.aggregate(text_pipeline))
    except Exception as e:
        print(f"Error in text search: {e}")
        text_results = []
    
    # Manual RRF scoring (same logic as original)
    from collections import defaultdict
    rrf_scores = defaultdict(lambda: {"score": 0, "doc": None, "details": []})
    
    # Process vector results
    for rank, doc in enumerate(vector_results, start=1):
        doc_id = str(doc["_id"])
        rrf_contribution = vector_weight * (1 / (60 + rank))
        rrf_scores[doc_id]["score"] += rrf_contribution
        rrf_scores[doc_id]["doc"] = doc
        rrf_scores[doc_id]["details"].append({
            "pipeline": "vectorPipeline",
            "rank": rank,
            "weight": vector_weight,
            "contribution": rrf_contribution,
            "original_score": doc.get("vector_score", 0),
        })
    
    # Process text results
    for rank, doc in enumerate(text_results, start=1):
        doc_id = str(doc["_id"])
        rrf_contribution = text_weight * (1 / (60 + rank))
        rrf_scores[doc_id]["score"] += rrf_contribution
        if rrf_scores[doc_id]["doc"] is None:
            rrf_scores[doc_id]["doc"] = doc
        rrf_scores[doc_id]["details"].append({
            "pipeline": "textPipeline",
            "rank": rank,
            "weight": text_weight,
            "contribution": rrf_contribution,
            "original_score": doc.get("text_score", 0),
        })
    
    # Sort and get top results
    sorted_results = sorted(
        rrf_scores.values(),
        key=lambda x: x["score"],
        reverse=True
    )[:top_n]
    
    # Format results and add transcript data
    final_results = []
    for item in sorted_results:
        doc = item["doc"].copy()
        doc["rrf_score"] = item["score"]
        doc["score_details"] = item["details"]
        
        # Remove internal scores
        doc.pop("vector_score", None)
        doc.pop("text_score", None)
        doc.pop("_id", None)
        
        # Add transcript data using lookup
        doc_id = item["doc"]["_id"]
        transcript_lookup_pipeline = [
            {"$match": {"_id": doc_id}},
            {"$lookup": {
                "from": TRANSCRIPT_COLL,
                "localField": "transcript_ids",
                "foreignField": "_id",
                "as": "transcript_data"
            }},
            {"$project": {"transcript_data": 1}}
        ]
        
        try:
            transcript_result = list(collection.aggregate(transcript_lookup_pipeline))
            if transcript_result:
                doc["transcript_data"] = transcript_result[0].get("transcript_data", [])
            else:
                doc["transcript_data"] = []
        except Exception as e:
            print(f"Error fetching transcript data: {e}")
            doc["transcript_data"] = []
        
        final_results.append(doc)
    
    print(f"Found {len(final_results)} results for query: '{user_query}'")
    print(f"Vector results: {len(vector_results)}, Text results: {len(text_results)}")
    
    return final_results

# Interactive Semantic Search
print("\n=== Interactive Semantic Search ===")
print("Enter your queries to search through video frames. Type 'quit' or 'exit' to stop.")

def display_search_results(results, search_type, top_n=3, show_transcripts=False):
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
        
        # Show transcript data if available and requested
        if show_transcripts and 'transcript_data' in result and result['transcript_data']:
            print(f"     📝 Transcripts ({len(result['transcript_data'])} segments):")
            for i, transcript in enumerate(result['transcript_data'][:3], 1):  # Show max 3 transcripts
                transcript_text = transcript.get('text', '')[:100]
                t_start = transcript.get('t_start', 'N/A')
                t_end = transcript.get('t_end', 'N/A')
                print(f"       {i}. [{t_start}-{t_end}s]: {transcript_text}...")
            if len(result['transcript_data']) > 3:
                print(f"       ... and {len(result['transcript_data']) - 3} more transcript segments")
        elif show_transcripts and result.get('transcript_count', 0) > 0:
            print(f"     📝 Transcripts: {result.get('transcript_count', 0)} segments available")
        elif show_transcripts:
            print(f"     📝 Transcripts: No transcript data available")
        
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
        
        # Ask user if they want to include transcript data
        include_transcripts = input("Include transcript data in results? (y/n): ").strip().lower()
        show_transcripts = include_transcripts in ['y', 'yes']
        
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
        
        # NEW: Test with merged collection (includes transcript data)
        if show_transcripts:
            print("Searching merged collection with transcript data...")
            merged_semantic_results = semantic_search_with_transcripts(
                user_query=user_query,
                collection=merged_collection,
                top_n=5,
                vector_search_index_name="vector_search_index_scalar",
            )
            
            print("Searching merged collection with hybrid search + transcripts...")
            merged_hybrid_results = hybrid_search_with_transcripts(
                user_query=user_query,
                collection=merged_collection,
                top_n=5,
                vector_search_index_name="vector_search_index_scalar",
                text_search_index_name="text_search_index",
                vector_weight=0.7,
                text_weight=0.3,
                search_type="text",
            )
        
        # Display results
        display_search_results(scalar_results, "Scalar Quantization", 5, show_transcripts)
        display_search_results(full_fidelity_results, "Full Fidelity", 5, show_transcripts)
        display_search_results(hybrid_results, "Hybrid Search (70% vector, 30% text)", 5, show_transcripts)
        
        # Display merged collection results if transcripts were requested
        if show_transcripts:
            display_search_results(merged_semantic_results, "Merged Collection - Semantic Search", 5, show_transcripts)
            display_search_results(merged_hybrid_results, "Merged Collection - Hybrid Search", 5, show_transcripts)
        
        # Ask if user wants to see more details
        all_results = [scalar_results, full_fidelity_results, hybrid_results]
        if show_transcripts:
            all_results.extend([merged_semantic_results, merged_hybrid_results])
        
        if any(all_results):
            show_details = input("\nWould you like to see more details for any result? (y/n): ").strip().lower()
            if show_details in ['y', 'yes']:
                try:
                    if show_transcripts:
                        print("Which result set? (1) Scalar, (2) Full Fidelity, (3) Hybrid, (4) Merged Semantic, (5) Merged Hybrid")
                        result_set = int(input("Enter choice (1-5): "))
                    else:
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
                    elif result_set == 4 and show_transcripts:
                        results = merged_semantic_results
                    elif result_set == 5 and show_transcripts:
                        results = merged_hybrid_results
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
                        
                        # Show transcript data if available
                        if 'transcript_data' in result and result['transcript_data']:
                            print(f"\n📝 Transcript Data ({len(result['transcript_data'])} segments):")
                            for i, transcript in enumerate(result['transcript_data'], 1):
                                print(f"  {i}. Time: {transcript.get('t_start', 'N/A')}-{transcript.get('t_end', 'N/A')}s")
                                print(f"     Text: {transcript.get('text', 'N/A')}")
                                if i < len(result['transcript_data']):
                                    print()  # Add spacing between transcripts
                        elif result.get('transcript_count', 0) > 0:
                            print(f"\n📝 Transcripts: {result.get('transcript_count', 0)} segments available (use merged collection search to see details)")
                        else:
                            print(f"\n📝 Transcripts: No transcript data available")
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
print("✅ Enhanced search capabilities:")
print("   - Original frame search (scalar, full fidelity, hybrid)")
print("   - Merged collection search with transcript data")
print("   - Semantic and hybrid search on video frames + transcripts")
print("   - Detailed transcript display with timestamps")


 