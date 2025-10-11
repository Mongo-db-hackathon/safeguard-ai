from mongo_client_1 import FRAME_INTELLIGENCE_METADATA, db

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