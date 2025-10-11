# Semantic Search Functionality
from llm.get_voyage_embed import get_voyage_embedding
from llm.main import VECTOR_INDEX_FRAMES_SCALAR, VECTOR_INDEX_FRAMES_FULL, VECTOR_INDEX_TRANSCRIPT_SCALAR, \
    VECTOR_INDEX_TRANSCRIPT_FULL
from llm.mongo_client_1 import TRANSCRIPT_COLL, FRAME_INTELLIGENCE_METADATA, db, VIDEO_INTELLIGENCE_TRANSCRIPTS
from llm.retreival_2 import manual_hybrid_search


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
            "transcript_ids": 0,  # Remove IDs since we have the actual data
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
        top_n=5,
        vector_weight=0.4,
        text_weight=0.3,
        transcript_weight=0.3,
        search_type="text",
):
    vector_search_index_name = "vector_search_index_scalar",
    text_search_index_name = "frame_intelligence_index",
    transcript_index_name = "transcript_search_index",
    query_embedding = get_voyage_embedding(user_query, input_type="query")

    if query_embedding is None:
        print("Error: Failed to generate embedding for query")
        return []

    # Vector search pipeline for merged collection
    frames_vector_pipeline = [
        {
            "$vectorSearch": {
                "index": VECTOR_INDEX_FRAMES_FULL,  # Use full fidelity for better accuracy
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
                "video_id": 1,
                "vector_score": {"$meta": "vectorSearchScore"},

            }
        },
    ]

    try:
        frames_vector_results = list(db[VIDEO_INTELLIGENCE_TRANSCRIPTS].aggregate(frames_vector_pipeline))
    except Exception as e:
        print(f"Error in vector search: {e}")
        frames_vector_results = []

    # Vector search pipeline for merged collection
    transcript_vector_pipeline = [
        {
            "$vectorSearch": {
                "index": VECTOR_INDEX_TRANSCRIPT_FULL,  # Use full fidelity for better accuracy
                "path": "text_embedding",  # Different field name in merged collection
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": 20,
            }
        },
        {
            "$project": {
                "_id": 1,
                "text": 1,
                "video_id": 1,
                "t_start": 1,
                "vector_score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    try:
        transcript_vector_result = list(db[TRANSCRIPT_COLL].aggregate(transcript_vector_pipeline))
    except Exception as e:
        print(f"Error in vector search: {e}")
        transcript_vector_result = []

    # Text search pipeline for merged collection
    if search_type == "text":
        text_query = {"text": {"query": user_query, "path": "frame_description"}}
    else:
        text_query = {"phrase": {"query": user_query, "path": "frame_description"}}

    text_pipeline = [
        {"$search": {"index": 'frame_intelligence_index', **text_query}},
        {"$limit": 20},
        {
            "$project": {
                "_id": 1,
                "frame_number": 1,
                "frame_timestamp": 1,
                "frame_description": 1,
                "video_id": 1,
                "text_score": {"$meta": "searchScore"},
            }
        },
    ]

    try:
        text_results = list(db[VIDEO_INTELLIGENCE_TRANSCRIPTS].aggregate(text_pipeline))
    except Exception as e:
        print(f"Error in text search: {e}")
        text_results = []

    # Manual RRF scoring (same logic as original)
    from collections import defaultdict
    rrf_scores = defaultdict(lambda: {"score": 0, "doc": None, "details": []})

    # Process vector results
    for rank, doc in enumerate(frames_vector_results, start=1):
        doc_id = str(doc["_id"])
        rrf_contribution = vector_weight * (1 / (60 + rank))
        rrf_scores[doc_id]["score"] += rrf_contribution
        doc['des'] = doc['frame_description']
        doc['ts'] = doc['frame_timestamp']
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
        doc['des'] = doc['frame_description']
        doc['ts'] = doc['frame_timestamp']
        if rrf_scores[doc_id]["doc"] is None:
            rrf_scores[doc_id]["doc"] = doc
        rrf_scores[doc_id]["details"].append({
            "pipeline": "textPipeline",
            "rank": rank,
            "weight": text_weight,
            "contribution": rrf_contribution,
            "original_score": doc.get("text_score", 0),
        })

    # Process text results
    for rank, doc in enumerate(transcript_vector_result, start=1):
        doc_id = str(doc["_id"])
        rrf_contribution = transcript_weight * (1 / (60 + rank))
        rrf_scores[doc_id]["score"] += rrf_contribution
        doc['des'] = doc['text']
        doc['ts'] = doc['t_start']
        if rrf_scores[doc_id]["doc"] is None:
            rrf_scores[doc_id]["doc"] = doc
        rrf_scores[doc_id]["details"].append({
            "pipeline": "textPipeline",
            "rank": rank,
            "weight": transcript_weight,
            "contribution": rrf_contribution,
            "original_score": doc.get("text_score", 0),
        })

    # Sort and get top results
    sorted_results = sorted(
        rrf_scores.values(),
        key=lambda x: x["score"],
        reverse=True
    )[:top_n]

    print(f"Found {len(sorted_results)} results for query: '{user_query}'")

    res = [{'des':item['doc']['des'], 'ts':item['doc']['ts'], 'video':item['doc']['video_id']} for item in sorted_results]
    return res


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


if __name__ == "__main__":

    merged_hybrid_results = hybrid_search_with_transcripts(
        user_query="blue jersey",
        top_n=5,
        vector_weight=0.7,
        text_weight=0.3,
        transcript_weight=0.3,
        search_type="text",
    )

    print(merged_hybrid_results)

    exit()
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
            # include_transcripts = input("Include transcript data in results? (y/n): ").strip().lower()
            # show_transcripts = include_transcripts in ['y', 'yes']
            show_transcripts = 'y'

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
            # print("Searching with manual hybrid search (70% vector, 30% text)...")
            hybrid_results = []
            # hybrid_results = manual_hybrid_search(
            #     user_query=user_query,
            #     collection=db[FRAME_INTELLIGENCE_METADATA],
            #     top_n=5,
            #     vector_search_index_name="vector_search_index_scalar",
            #     text_search_index_name="text_search_index",
            #     vector_weight=0.7,
            #     text_weight=0.3,
            #     search_type="text",
            # )

            # NEW: Test with merged collection (includes transcript data)
            if show_transcripts:
                merged_semantic_results = []
                # print("Searching merged collection with transcript data...")
                # merged_semantic_results = semantic_search_with_transcripts(
                #     user_query=user_query,
                #     collection=db[VIDEO_INTELLIGENCE_TRANSCRIPTS],
                #     top_n=5,
                #     vector_search_index_name="vector_search_index_scalar",
                # )

                print("Searching merged collection with hybrid search + transcripts...")
                merged_hybrid_results = hybrid_search_with_transcripts(
                    user_query=user_query,
                    top_n=5,
                    vector_weight=0.7,
                    text_weight=0.3,
                    transcript_weight=0.3,
                    search_type="text",
                )

            # Display results
            display_search_results(scalar_results, "Scalar Quantization", 5, show_transcripts)
            display_search_results(full_fidelity_results, "Full Fidelity", 5, show_transcripts)
            display_search_results(hybrid_results, "Hybrid Search (70% vector, 30% text)", 5, show_transcripts)

            # Display merged collection results if transcripts were requested
            if show_transcripts:
                display_search_results(merged_semantic_results, "Merged Collection - Semantic Search", 5,
                                       show_transcripts)
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
                            print(
                                "Which result set? (1) Scalar, (2) Full Fidelity, (3) Hybrid, (4) Merged Semantic, (5) Merged Hybrid")
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
                                    print(
                                        f"    Rank: {detail['rank']}, Weight: {detail['weight']}, Contribution: {detail['contribution']:.6f}")

                            # Show transcript data if available
                            if 'transcript_data' in result and result['transcript_data']:
                                print(f"\n📝 Transcript Data ({len(result['transcript_data'])} segments):")
                                for i, transcript in enumerate(result['transcript_data'], 1):
                                    print(
                                        f"  {i}. Time: {transcript.get('t_start', 'N/A')}-{transcript.get('t_end', 'N/A')}s")
                                    print(f"     Text: {transcript.get('text', 'N/A')}")
                                    if i < len(result['transcript_data']):
                                        print()  # Add spacing between transcripts
                            elif result.get('transcript_count', 0) > 0:
                                print(
                                    f"\n📝 Transcripts: {result.get('transcript_count', 0)} segments available (use merged collection search to see details)")
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
