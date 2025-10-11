# Implementing hybrid search with RankFusion and manual RRF fallback
from mongo_client_1 import FRAME_INTELLIGENCE_METADATA, db
from get_voyage_embed import get_voyage_embedding
from collections import defaultdict


def manual_hybrid_search(
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
    Manual hybrid search that works on ANY MongoDB version (including pre-8.0).
    
    This function manually implements the Reciprocal Rank Fusion (RRF) algorithm:
    RRF_score = sum(weight * (1 / (60 + rank))) across all input pipelines
    
    Instead of using $rankFusion, we:
    1. Run vector search and text search separately
    2. Manually combine and rank results using RRF formula
    3. Return top N results
    
    Args:
        user_query (str): The user's query or search term.
        collection (Collection): MongoDB collection object.
        top_n (int): Number of results to return.
        vector_search_index_name (str): Name of the vector search index.
        text_search_index_name (str): Name of the text search index.
        vector_weight (float): Weight for vector search results.
        text_weight (float): Weight for text search results.
        search_type (str): Type of text search - "text" or "phrase".
        
    Returns:
        List[Dict]: List of search results with RRF scores.
    """
    
    # Convert user query to embedding for vector search
    query_embedding = get_voyage_embedding(user_query, input_type="query")
    
    if query_embedding is None:
        print("Error: Failed to generate embedding for query")
        return []
    
    # ========================================================================
    # STEP 1: Run Vector Search
    # ========================================================================
    vector_pipeline = [
        {
            "$vectorSearch": {
                "index": vector_search_index_name,
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": 20,
            }
        },
        {
            "$project": {
                "_id": 1,
                "frame_number": 1,
                "timestamp": 1,
                "frame_description": 1,
                "frame_path": 1,
                "video_id": 1,
                "vector_score": {"$meta": "vectorSearchScore"},
            }
        },
    ]
    
    try:
        vector_results = list(collection.aggregate(vector_pipeline))
    except Exception as e:
        print(f"Error in vector search: {e}")
        vector_results = []
    
    # ========================================================================
    # STEP 2: Run Text Search
    # ========================================================================
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
                "timestamp": 1,
                "frame_description": 1,
                "frame_path": 1,
                "video_id": 1,
                "text_score": {"$meta": "searchScore"},
            }
        },
    ]
    
    try:
        text_results = list(collection.aggregate(text_pipeline))
    except Exception as e:
        print(f"Error in text search: {e}")
        text_results = []
    
    # ========================================================================
    # STEP 3: Manually Compute RRF Scores
    # ========================================================================
    # Dictionary to store RRF scores: doc_id -> {score, doc_data, details}
    rrf_scores = defaultdict(lambda: {"score": 0, "doc": None, "details": []})
    
    # Process vector search results
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
    
    # Process text search results
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
    
    # ========================================================================
    # STEP 4: Sort by RRF Score and Return Top N
    # ========================================================================
    sorted_results = sorted(
        rrf_scores.values(),
        key=lambda x: x["score"],
        reverse=True
    )[:top_n]
    
    # Format results
    final_results = []
    for item in sorted_results:
        doc = item["doc"].copy()
        doc["rrf_score"] = item["score"]
        doc["score_details"] = item["details"]
        # Remove internal scores from output
        doc.pop("vector_score", None)
        doc.pop("text_score", None)
        doc.pop("_id", None)
        final_results.append(doc)
    
    print(f"Found {len(final_results)} results for query: '{user_query}'")
    print(f"Vector results: {len(vector_results)}, Text results: {len(text_results)}")
    
    return final_results


def hybrid_search(
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
    Perform hybrid search using both vector and text search with MongoDB RankFusion.
    
    RankFusion uses the Reciprocal Rank Fusion (RRF) algorithm to combine results from
    multiple pipelines. The RRF score is calculated as:
    
    RRF_score = sum(weight * (1 / (60 + rank))) across all input pipelines
    
    Documents that appear in multiple pipelines with high rankings will receive
    higher final scores.

    Args:
        user_query (str): The user's query or search term.
        collection (Collection): MongoDB collection object.
        top_n (int): Number of results to return.
        vector_search_index_name (str): Name of the vector search index.
        text_search_index_name (str): Name of the text search index.
        vector_weight (float): Weight for vector search results (non-negative number).
        text_weight (float): Weight for text search results (non-negative number).
        search_type (str): Type of text search - "text" for fuzzy matching or "phrase" for exact phrase.

    Returns:
        List[Dict]: List of search results with scores and details.
    """

    # Convert user query to embedding for vector search
    query_embedding = get_voyage_embedding(user_query, input_type="query")
    
    # Check if embedding generation was successful
    if query_embedding is None:
        print("Error: Failed to generate embedding for query")
        return []

    # Build the text search query based on search_type
    # "text" provides fuzzy matching and is more flexible
    # "phrase" provides exact phrase matching for precise queries
    if search_type == "text":
        text_search_query = {
            "text": {
                "query": user_query,
                "path": "frame_description",
            }
        }
    else:  # phrase
        text_search_query = {
            "phrase": {
                "query": user_query,
                "path": "frame_description",
            }
        }
    
    # Build the RankFusion aggregation pipeline according to MongoDB 8.0+ specification
    # RankFusion executes all input pipelines independently, then combines results
    # using the Reciprocal Rank Fusion (RRF) algorithm
    rank_fusion_stage = {
        "$rankFusion": {
            "input": {
                "pipelines": {
                    # Vector search pipeline: semantic similarity search using embeddings
                    "vectorPipeline": [
                        {
                            "$vectorSearch": {
                                "index": vector_search_index_name,
                                "path": "embedding",
                                "queryVector": query_embedding,
                                "numCandidates": 100,  # Number of candidates to consider
                                "limit": 20,  # Return top 20 from vector search
                            }
                        }
                    ],
                    # Text search pipeline: keyword/phrase-based search
                    "textPipeline": [
                        {
                            "$search": {
                                "index": text_search_index_name,
                                **text_search_query,
                            }
                        },
                        {"$limit": 20},  # Return top 20 from text search
                    ],
                }
            },
            # Combination strategy: weight each pipeline's contribution to final ranking
            "combination": {
                "weights": {
                    "vectorPipeline": vector_weight,
                    "textPipeline": text_weight,
                }
            },
            # Include detailed scoring information for transparency
            "scoreDetails": True,
        }
    }

    # Project stage to select desired fields and include score details
    project_stage = {
        "$project": {
            "_id": 0,
            "embedding": 0,
            "scoreDetails": {"$meta": "scoreDetails"},
        }
    }

    # Final limit stage
    limit_stage = {"$limit": top_n}

    # Combine all stages into the complete aggregation pipeline
    pipeline = [rank_fusion_stage, project_stage, limit_stage]

    try:
        # Execute the pipeline against the collection
        results = list(collection.aggregate(pipeline))

        print(f"Found {len(results)} results for query: '{user_query}'")

        return results

    except Exception as e:
        print(f"Error executing hybrid search: {e}")
        return []


# ============================================================================
# Test hybrid search with different configurations
# Using manual_hybrid_search() - works on ANY MongoDB version
# ============================================================================

# user_query = "Can you get me the frame with the red shirt player with front flip"

# print("\n" + "=" * 80)
# print("TEST 1: Scalar Index with TEXT search (70% vector, 30% text)")
# print("=" * 80)

# scalar_text_results = manual_hybrid_search(
#     user_query=user_query,
#     collection=db[FRAME_INTELLIGENCE_METADATA],
#     top_n=5,
#     vector_search_index_name="vector_search_index_scalar",
#     text_search_index_name="text_search_index",
#     vector_weight=0.7,
#     text_weight=0.3,
#     search_type="text",  # Fuzzy text matching
# )

# print(scalar_text_results)
# print("\n")

# print("=" * 80)
# print("TEST 2: Scalar Index with PHRASE search (70% vector, 30% text)")
# print("=" * 80)

# scalar_phrase_results = manual_hybrid_search(
#     user_query=user_query,
#     collection=db[FRAME_INTELLIGENCE_METADATA],
#     top_n=5,
#     vector_search_index_name="vector_search_index_scalar",
#     text_search_index_name="text_search_index",
#     vector_weight=0.7,
#     text_weight=0.3,
#     search_type="phrase",  # Exact phrase matching
# )

# print(scalar_phrase_results)
# print("\n")

# print("=" * 80)
# print("TEST 3: Full Fidelity Index (60% vector, 40% text)")
# print("=" * 80)

# full_fidelity_results = manual_hybrid_search(
#     user_query=user_query,
#     collection=db[FRAME_INTELLIGENCE_METADATA],
#     top_n=5,
#     vector_search_index_name="vector_search_index_full_fidelity",
#     text_search_index_name="text_search_index",
#     vector_weight=0.6,
#     text_weight=0.4,
#     search_type="text",
# )

# print(full_fidelity_results)
# print("\n")

# print("=" * 80)
# print("TEST 4: Binary Index (50% vector, 50% text - Equal Weights)")
# print("=" * 80)

# binary_equal_weight_results = manual_hybrid_search(
#     user_query=user_query,
#     collection=db[FRAME_INTELLIGENCE_METADATA],
#     top_n=5,
#     vector_search_index_name="vector_search_index_binary",
#     text_search_index_name="text_search_index",
#     vector_weight=0.5,
#     text_weight=0.5,
#     search_type="text",
# )

# print(binary_equal_weight_results)
# print("\n")

# print("=" * 80)
# print("TEST 5: Binary Index (90% vector, 10% text - Vector Dominant)")
# print("=" * 80)

# binary_vector_dominant_results = manual_hybrid_search(
#     user_query=user_query,
#     collection=db[FRAME_INTELLIGENCE_METADATA],
#     top_n=5,
#     vector_search_index_name="vector_search_index_binary",
#     text_search_index_name="text_search_index",
#     vector_weight=0.9,
#     text_weight=0.1,
#     search_type="text",
# )

# print(binary_vector_dominant_results)
# print("\n")

# print("=" * 80)
# print("Summary: Manual RRF implementation - Works on ANY MongoDB version!")
# print("Different weights and search types produce different ranking results")
# print("=" * 80)


# # ============================================================================
# # QUICK START EXAMPLE - Simple usage you can copy and modify
# # ============================================================================

# print("\n\n" + "=" * 80)
# print("QUICK START EXAMPLE - Equal Weights (50% vector, 50% text)")
# print("=" * 80)

# # Simple example with equal weights
# scalar_hybrid_search_results = manual_hybrid_search(
#     user_query=user_query,
#     collection=db[FRAME_INTELLIGENCE_METADATA],
#     top_n=5,
#     vector_search_index_name="vector_search_index_scalar",
#     text_search_index_name="text_search_index",
#     vector_weight=0.5,
#     text_weight=0.5,
# )

# print(scalar_hybrid_search_results)

# print("\n" + "=" * 80)
# print("✅ Using manual_hybrid_search() - works on ANY MongoDB version")
# print("To modify: Change weights, index names, or search_type parameter")
# print("=" * 80)