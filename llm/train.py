import pymongo
import os
from dotenv import load_dotenv
from llm.mongo_client_1 import db, FRAME_INTELLIGENCE_METADATA, TRANSCRIPT_COLL, VIDEO_INTELLIGENCE_TRANSCRIPTS

load_dotenv()


# Collection names


def create_merged_collection(video_id=None):
    """
    Create a new collection that merges video_intelligence with transcripts
    based on timestamp mapping (30-second intervals) - EFFICIENT VERSION
    Stores only transcript IDs instead of duplicating transcript data
    Adds video_id to each merged document.
    """

    # Get the collections
    video_intelligence_collection = db[FRAME_INTELLIGENCE_METADATA]
    transcripts_collection = db[TRANSCRIPT_COLL]

    # Create the new merged collection
    merged_collection = db[VIDEO_INTELLIGENCE_TRANSCRIPTS]

    # Clear existing data if any
    merged_collection.delete_many({})
    print(f"Cleared existing data from {VIDEO_INTELLIGENCE_TRANSCRIPTS}")

    # Get all video intelligence frames
    video_frames = list(video_intelligence_collection.find())
    print(f"Found {len(video_frames)} video frames")

    # Get all transcripts
    transcripts = list(transcripts_collection.find())
    print(f"Found {len(transcripts)} transcript segments")

    if not video_frames or not transcripts:
        print("No data found in source collections")
        return

    # Create a mapping of time ranges to transcript IDs (EFFICIENT: only store IDs)
    transcript_time_mapping = {}

    for transcript in transcripts:
        t_start = transcript.get('t_start', 0)
        transcript_id = transcript.get('_id')

        # Create time range key (e.g., "0-30", "31-60", etc.)
        start_range = int(t_start // 30) * 30
        end_range = start_range + 30
        time_range_key = f"{start_range}-{end_range}"

        if time_range_key not in transcript_time_mapping:
            transcript_time_mapping[time_range_key] = []

        # Store only the transcript ID - no duplication of data!
        transcript_time_mapping[time_range_key] = transcript_id

    print(f"Created time range mapping: {list(transcript_time_mapping.keys())}")

    # Insert merged documents with video_id
    for frame in video_frames:
        frame_time = frame.get('frame_timestamp', 0)

        # Determine which time range this frame belongs to
        time_range = int(frame_time // 30) * 30
        time_range_key = f"{time_range}-{time_range+30}"

        # Create the merged document - EFFICIENT VERSION
        merged_doc = {
            # Video intelligence fields
            'frame_id': frame.get('_id'),
            'frame_embedding': frame.get('embedding', []),
            'frame_description': frame.get('frame_description', ''),
            'frame_number': frame.get('frame_number', 0),
            'frame_timestamp': frame_time,

            # Transcript reference - only store IDs!
            'transcript_ids': transcript_time_mapping.get(time_range_key),  # Array of ObjectIds

            # Metadata
            'time_range': time_range_key,
            'video_id': video_id
            # 'transcript_count': len(matching_transcript_ids)
        }

        merged_collection.insert_one(merged_doc)

    print(f"Inserted merged documents with video_id: {video_id}")


def query_merged_collection(frame_timestamp=None, time_range=None, limit=5):
    """
    Query the merged collection with various filters - EFFICIENT VERSION
    """
    merged_collection = db[VIDEO_INTELLIGENCE_TRANSCRIPTS]

    query = {}

    if frame_timestamp is not None:
        query['frame_timestamp'] = frame_timestamp

    if time_range is not None:
        query['time_range'] = time_range

    results = list(merged_collection.find(query).limit(limit))

    print(f"\n=== Query Results (Efficient Version) ===")
    print(f"Query: {query}")
    print(f"Found {len(results)} documents")

    for i, result in enumerate(results, 1):
        print(f"\n{i}. Frame {result.get('frame_number')} at {result.get('frame_timestamp')}s")
        print(f"   Time range: {result.get('time_range')}")
        print(f"   Transcript IDs: {result.get('transcript_ids', [])}")
        print(f"   Description: {result.get('frame_description', '')[:80]}...")

    return results


def get_frame_with_transcripts(frame_number=None, frame_timestamp=None):
    """
    Get a frame with its associated transcript data using aggregation
    This demonstrates how to efficiently retrieve transcript data when needed
    """
    merged_collection = db[VIDEO_INTELLIGENCE_TRANSCRIPTS]
    transcripts_collection = db[TRANSCRIPT_COLL]

    # Build match query
    match_query = {}
    if frame_number is not None:
        match_query['frame_number'] = frame_number
    if frame_timestamp is not None:
        match_query['frame_timestamp'] = frame_timestamp

    # Use aggregation to join with transcripts
    pipeline = [
        {"$match": match_query},
        {"$lookup": {
            "from": TRANSCRIPT_COLL,
            "localField": "transcript_ids",
            "foreignField": "_id",
            "as": "transcript_data"
        }},
        {"$limit": 1}
    ]

    result = list(merged_collection.aggregate(pipeline))

    if result:
        frame_data = result[0]
        print(f"\n=== Frame with Transcript Data ===")
        print(f"Frame {frame_data.get('frame_number')} at {frame_data.get('frame_timestamp')}s")
        print(f"Description: {frame_data.get('frame_description', '')}")
        print(f"Time range: {frame_data.get('time_range')}")

        if frame_data.get('transcript_data'):
            print(f"\nAssociated Transcripts:")
            for i, transcript in enumerate(frame_data['transcript_data'], 1):
                print(
                    f"  {i}. [{transcript.get('t_start')}-{transcript.get('t_end')}s]: {transcript.get('text', '')[:100]}...")
        else:
            print("No transcript data found")

        return frame_data
    else:
        print("No frame found matching criteria")
        return None


def search_frames_by_transcript_content(search_text, limit=5):
    """
    Search for frames based on transcript content
    This demonstrates how to search across both frame descriptions and transcript text
    """
    merged_collection = db[VIDEO_INTELLIGENCE_TRANSCRIPTS]
    transcripts_collection = db[TRANSCRIPT_COLL]

    # First, find transcripts that match the search text
    matching_transcripts = list(transcripts_collection.find({
        "text": {"$regex": search_text, "$options": "i"}
    }))

    if not matching_transcripts:
        print(f"No transcripts found containing '{search_text}'")
        return []

    # Get the IDs of matching transcripts
    matching_transcript_ids = [t['_id'] for t in matching_transcripts]

    # Find frames that reference these transcript IDs
    frames = list(merged_collection.find({
        "transcript_ids": {"$in": matching_transcript_ids}
    }).limit(limit))

    print(f"\n=== Frames with Transcripts containing '{search_text}' ===")
    print(f"Found {len(frames)} frames")

    for i, frame in enumerate(frames, 1):
        print(f"\n{i}. Frame {frame.get('frame_number')} at {frame.get('frame_timestamp')}s")
        print(f"   Description: {frame.get('frame_description', '')[:80]}...")
        print(f"   Transcript IDs: {frame.get('transcript_ids', [])}")

    return frames


# Execute the merge
if __name__ == "__main__":
    print("=== Starting Video Intelligence + Transcripts Merge (Efficient Version) ===")
    create_merged_collection()

    print("\n=== Testing Efficient Queries ===")

    # Test 1: Query by time range (shows only IDs)
    print("\n1. Query by time range (0-30 seconds):")
    query_merged_collection(time_range="0-30", limit=3)

    # Test 2: Query by specific timestamp
    print("\n2. Query by specific timestamp (15.0 seconds):")
    query_merged_collection(frame_timestamp=15.0, limit=2)

    # Test 3: Get frame with full transcript data (demonstrates efficient lookup)
    print("\n3. Get frame with full transcript data using aggregation:")
    get_frame_with_transcripts(frame_timestamp=15.0)

    # Test 4: Search frames by transcript content
    print("\n4. Search frames by transcript content:")
    search_frames_by_transcript_content("hello", limit=3)

    print("\n=== Efficiency Benefits ===")
    print("✅ No data duplication - transcript data stored only once")
    print("✅ Fast queries - smaller documents load quickly")
    print("✅ Easy updates - change transcript once, all frames automatically updated")
    print("✅ Scalable - works efficiently with thousands of frames")
    print("✅ Flexible - use aggregation when you need transcript details")
