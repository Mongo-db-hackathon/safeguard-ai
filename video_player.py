from typing import Dict, List
from IPython.display import HTML, display
import base64
import os

def create_video_player_with_scenes(
    video_path: str,
    search_results: List[Dict],
    user_query: str = "",
    width: int = 800,
    height: int = 450,
) -> None:
    """
    Create an interactive video player with scene navigation for Jupyter notebooks.

    Args:
        video_path (str): Path to the video file
        search_results (List[Dict]): Search results with timestamps and descriptions
        user_query (str): The original search query that generated these results
        width (int): Video player width in pixels
        height (int): Video player height in pixels
    """

    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return

    if not search_results:
        print("❌ No search results provided")
        return

    # Convert video to base64 for embedding (for small videos)
    # For large videos, you might want to serve via a local server
    video_base64 = None
    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)

    if file_size_mb < 50:  # Only embed videos smaller than 50MB
        with open(video_path, "rb") as video_file:
            video_data = video_file.read()
            video_base64 = base64.b64encode(video_data).decode()

    # Get video file extension for MIME type
    file_ext = os.path.splitext(video_path)[1].lower()
    mime_types = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".ogg": "video/ogg",
        ".avi": "video/mp4",  # Fallback
        ".mov": "video/mp4",  # Fallback
    }
    video_mime = mime_types.get(file_ext, "video/mp4")

    # Sort search results by timestamp
    sorted_results = sorted(search_results, key=lambda x: x.get("frame_timestamp", 0))

    # Create HTML with embedded video player and controls
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: {width + 50}px;">
        <h3>🎬 Video Scene Navigator</h3>
        
        <!-- Search Query Display -->
        {f'''<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 18px;">🔍</span>
                <div>
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 5px;">Search Query:</div>
                    <div style="font-size: 16px; font-weight: bold;">"{user_query}"</div>
                    <div style="font-size: 12px; opacity: 0.8; margin-top: 5px;">Found {len(sorted_results)} matching scenes</div>
                </div>
            </div>
        </div>''' if user_query else ''}
        
        <!-- Video Player -->
        <div style="margin-bottom: 20px; border: 2px solid #ddd; border-radius: 8px; overflow: hidden;">
            <video id="videoPlayer" width="{width}" height="{height}" controls style="display: block;">
                {"<source src='data:" + video_mime + ";base64," + video_base64 + "' type='" + video_mime + "'>" if video_base64 else "<source src='" + video_path + "' type='" + video_mime + "'>" }
                Your browser does not support the video tag.
            </video>
        </div>
        
        <!-- Current Scene Info -->
        <div id="currentScene" style="background: #f0f8ff; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #4CAF50;">
            <h4 style="margin: 0 0 10px 0; color: #333;">📍 Current Scene</h4>
            <p id="sceneDescription" style="margin: 0; color: #666; font-style: italic;">Click a timestamp below to view scene details</p>
        </div>
        
        <!-- Scene Navigation Buttons -->
        <div style="background: #f9f9f9; padding: 20px; border-radius: 8px;">
            <h4 style="margin: 0 0 15px 0; color: #333;">🎯 Jump to Scenes</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px;">
"""

    # Add scene buttons
    for i, result in enumerate(sorted_results):
        timestamp = result.get("frame_timestamp", 0)
        description = result.get("frame_description", "No description")
        score = result.get("score", 0)
        frame_number = result.get("frame_number", 0)

        # Truncate description for button
        short_desc = description[:60] + "..." if len(description) > 60 else description

        html_content += f"""
                <button onclick="jumpToScene({timestamp}, `{description.replace('`', "'").replace('"', "'")}`, {score}, {frame_number})" 
                        style="padding: 10px; border: 1px solid #ddd; border-radius: 5px; background: white; cursor: pointer; text-align: left; transition: all 0.3s;"
                        onmouseover="this.style.background='#e3f2fd'; this.style.borderColor='#2196F3';"
                        onmouseout="this.style.background='white'; this.style.borderColor='#ddd';">
                    <div style="font-weight: bold; color: #1976D2; margin-bottom: 5px;">
                        ⏱️ {timestamp}s (Frame {frame_number}) | Score: {score:.3f}
                    </div>
                    <div style="font-size: 12px; color: #666;">
                        {short_desc}
                    </div>
                </button>
"""

    # Add JavaScript functionality
    html_content += """
            </div>
        </div>
        
        <!-- Video Controls Info -->
        <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
            <h4 style="margin: 0 0 10px 0; color: #856404;">💡 How to Use</h4>
            <ul style="margin: 0; color: #856404; font-size: 14px;">
                <li>Click any timestamp button to jump to that scene</li>
                <li>Use video controls to play, pause, and adjust volume</li>
                <li>Scene descriptions appear above when you select a timestamp</li>
            </ul>
        </div>
    </div>

    <script>
        function jumpToScene(timestamp, description, score, frameNumber) {
            const video = document.getElementById('videoPlayer');
            const sceneDesc = document.getElementById('sceneDescription');
            
            // Jump to timestamp
            video.currentTime = timestamp;
            
            // Update scene description
            sceneDesc.innerHTML = `
                <div style="margin-bottom: 10px;">
                    <strong>🎬 Frame ${frameNumber} at ${timestamp}s (Score: ${score.toFixed(3)})</strong>
                </div>
                <div style="line-height: 1.5;">
                    ${description}
                </div>
            `;
            
            // Auto-play if paused
            if (video.paused) {
                video.play().catch(e => console.log('Auto-play prevented by browser'));
            }
            
            // Scroll video into view
            video.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        
        // Add time update listener to show current time
        document.getElementById('videoPlayer').addEventListener('timeupdate', function() {
            const currentTime = this.currentTime;
            // You could add real-time scene detection here
        });
        
        // Add keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            const video = document.getElementById('videoPlayer');
            
            switch(e.key) {
                case ' ':  // Spacebar to play/pause
                    e.preventDefault();
                    if (video.paused) {
                        video.play();
                    } else {
                        video.pause();
                    }
                    break;
                case 'ArrowLeft':  // Left arrow to go back 10s
                    e.preventDefault();
                    video.currentTime = Math.max(0, video.currentTime - 10);
                    break;
                case 'ArrowRight':  // Right arrow to go forward 10s
                    e.preventDefault();
                    video.currentTime = Math.min(video.duration, video.currentTime + 10);
                    break;
            }
        });
    </script>
    """

    # Display the HTML
    display(HTML(html_content))

    print(f"🎬 Video player created with {len(sorted_results)} scenes")
    print(f"📁 Video: {os.path.basename(video_path)}")
    if file_size_mb >= 50:
        print("⚠️  Large video file - serving from local path")

# Example usage
video_path = "videos/video.mp4"  # Replace with your actual video path

print("🎬 Creating interactive video player...")
create_video_player_with_scenes(
    video_path,
    full_fidelity_results,
    user_query="Get me a scene where a player in red shirt doing front flip",
)