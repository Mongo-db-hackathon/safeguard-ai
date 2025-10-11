
from bson.objectid import ObjectId
from llm.mongo_client_1 import db, VIDEO_LIBRARY


def get_video_path(video_id: str) -> str | None:
    """
    Get the video path from the VIDEO_LIBRARY collection using video_id.
    
    Args:
        video_id (str): The MongoDB ObjectId of the video as a string
        
    Returns:
        str | None: The video path if found, None otherwise
    """
    if not video_id:
        return None
    coll = db[VIDEO_LIBRARY]
    doc = coll.find_one({"_id": ObjectId(video_id)}, {"_id": 0, "video_path": 1})
    return doc.get("video_path") if doc else None


def get_video_name(video_id: str) -> str | None:
    """
    Get the video name from the VIDEO_LIBRARY collection using video_id.
    
    Args:
        video_id (str): The MongoDB ObjectId of the video as a string
        
    Returns:
        str | None: The video name if found, None otherwise
    """
    coll = db[VIDEO_LIBRARY]
    doc = coll.find_one({"_id": ObjectId(video_id)}, {"_id": 0, "video_name": 1})
    return doc.get("video_name") if doc else None