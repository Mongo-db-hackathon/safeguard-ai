from transcripts.audio import ingest_transcripts
import voyageai
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
from llm.process_frames import process_frames_to_embeddings_with_descriptions
import os

# Import mongo client functions
from llm.mongo_client_1 import create_collections, db, FRAME_INTELLIGENCE_METADATA, TRANSCRIPT_COLL, \
    create_vector_search_index, create_text_search_index, insert_frame_data_to_mongo, insert_video_metadata

# Import retrieval functions
from llm.get_voyage_embed import get_voyage_embedding
from llm.retreival_2 import manual_hybrid_search
from llm.get_video_path import get_video_name, get_video_path

# Import train.py functions for merged collection
from llm.train import create_merged_collection, VIDEO_INTELLIGENCE_TRANSCRIPTS


def work(video_path):
    # # Convert the video to images
    # video_to_images(
    #     video_path=video_path, output_dir="frames", interval_seconds=2
    # )

    voyageai_client = voyageai.Client()
    openai_client = OpenAI()

    video_title = os.path.splitext(os.path.basename(video_path))[0]

    # Insert video metadata and get video_id
    video_id = insert_video_metadata(video_title, video_path)
    print(f"Inserted video metadata. Video ID: {video_id}")


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

    # 4. Insert frame data into MongoDB with video_id
    print("Inserting frame data into MongoDB...")
    frame_intelligence_collection = insert_frame_data_to_mongo(frame_data_df, video_id=video_id)

    ingest_transcripts(video_path, video_id)
    print(f"Ingested transcripts for video ID: {video_path}")

    print("\n=== MongoDB setup complete! ===")
    print(f"Total frames processed and stored: {len(frame_data_df)}")
    print(f"Collection name: {FRAME_INTELLIGENCE_METADATA}")

    # Create merged collection with transcripts
    print("\n=== Creating Merged Collection with Transcripts ===")
    create_merged_collection(video_id)
    merged_collection = db[VIDEO_INTELLIGENCE_TRANSCRIPTS]
    print(f"Merged collection created: {VIDEO_INTELLIGENCE_TRANSCRIPTS}")

    create_search_incides()


VECTOR_INDEX_FRAMES_SCALAR = "vector_search_index_frames_scalar"
VECTOR_INDEX_FRAMES_FULL = "vector_search_index_frames_full_fidelity"
VECTOR_INDEX_TRANSCRIPT_SCALAR = "vector_search_transcript_index_scalar1"
VECTOR_INDEX_TRANSCRIPT_FULL = "vector_search_transcript_index_full_fidelity1"


def create_search_incides():
    # 2. Create vector search indexes

    # 1) pick consistent names

    # 2) target collections
    transcript_coll = db[TRANSCRIPT_COLL]  # frames-only collection
    merged_coll = db[VIDEO_INTELLIGENCE_TRANSCRIPTS]  # merged frames+transcripts collection

    # 3) create scalar-quantized index on frame_embedding (fast, smaller)
    create_vector_search_index(
        collection=merged_coll,  # or frames_coll if that’s where you search
        vector_index_name=VECTOR_INDEX_FRAMES_SCALAR,
        dimensions=1024,
        quantization="scalar",
        embedding_path="frame_embedding",
    )

    # 4) create full-fidelity index on frame_embedding (slower, most precise)
    #    pass a value that does NOT trigger the quantization block in your function.
    create_vector_search_index(
        collection=merged_coll,
        vector_index_name=VECTOR_INDEX_FRAMES_FULL,
        dimensions=1024,
        quantization=None,  # leaves quantization unset = full fidelity
        embedding_path="frame_embedding",
    )


    # 3) create scalar-quantized index on frame_embedding (fast, smaller)
    create_vector_search_index(
        collection=transcript_coll,  # or frames_coll if that’s where you search
        vector_index_name=VECTOR_INDEX_TRANSCRIPT_SCALAR,
        dimensions=1024,
        quantization="scalar",
        embedding_path="text_embedding",
    )

    # 4) create full-fidelity index on frame_embedding (slower, most precise)
    #    pass a value that does NOT trigger the quantization block in your function.
    create_vector_search_index(
        collection=transcript_coll,
        vector_index_name=VECTOR_INDEX_TRANSCRIPT_FULL,
        dimensions=1024,
        quantization=None,  # leaves quantization unset = full fidelity
        embedding_path="text_embedding",
    )

    # PyMongo
    # db.command({
    #     "createSearchIndexes": VIDEO_INTELLIGENCE_TRANSCRIPTS,  # collection name
    #     "indexes": [{
    #         "name": "frame_intelligence_index",  # text_search_index_name
    #         "definition": {
    #             "mappings": {
    #                 "dynamic": True,
    #                 "fields": {
    #                     "frame_description": {"type": "string", "analyzer": "lucene.standard"},
    #                     "frame_number": {"type": "number"},
    #                     "frame_timestamp": {"type": "number"},
    #                     "video_id": {"type": "string"}  # include if you filter/sort by it
    #                 }
    #             }
    #         }
    #     }]
    # })

    # print("Creating vector search indexes...")
    # create_vector_search_index(
    #     db[VIDEO_INTELLIGENCE_TRANSCRIPTS], "vector_search_index_scalar", quantization="scalar"
    # )
    # create_vector_search_index(
    #     db[VIDEO_INTELLIGENCE_TRANSCRIPTS],
    #     "vector_search_index_full_fidelity",
    #     quantization="full_fidelity",
    # )
    # create_vector_search_index(
    #     db[VIDEO_INTELLIGENCE_TRANSCRIPTS],
    #     "vector_search_index_binary",
    #     quantization="binary",
    # )
    #
    # # 3. Create text search index
    # print("Creating text search index...")
    # frame_intelligence_index_definition = {
    #     "mappings": {
    #         "dynamic": True,
    #         "fields": {
    #             "frame_description": {
    #                 "type": "string",
    #             },
    #             "frame_number": {
    #                 "type": "number",
    #             },
    #             "frame_timestamp": {
    #                 "type": "date",
    #             },
    #             "video_id": {
    #                 "type": "string",
    #             },
    #         },
    #     }
    # }
    #
    # create_text_search_index(
    #     db[FRAME_INTELLIGENCE_METADATA],
    #     frame_intelligence_index_definition,
    #     "frame_intelligence_index",
    # )


if __name__ == "__main__":
    create_search_incides()

    # video_path = "videos/video.mp4"
    # work(video_path)
