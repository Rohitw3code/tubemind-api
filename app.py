from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from youtube_transcript_api import YouTubeTranscriptApi
from groq_client import GroqClient

app = Flask(__name__)
CORS(app)

# Initialize Groq client
groq_client = GroqClient('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')

def extract_video_id(url: str) -> str:
    """
    Extract the video ID from a YouTube URL.
    Supports both standard and shortened URL formats.
    """
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11})"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid YouTube URL. Please check the URL and try again.")

def format_timestamp(seconds: float) -> str:
    """
    Convert seconds into a formatted timestamp string.
    Returns HH:MM:SS if hours > 0, otherwise MM:SS.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

@app.route('/api/transcript', methods=['POST'])
def get_transcript():
    try:
        data = request.get_json()
        video_url = data.get('url')
        
        if not video_url:
            return jsonify({'error': 'No URL provided'}), 400
            
        video_id = extract_video_id(video_url)
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Create a list of transcript lines with formatted timestamps
        transcript_lines = []
        transcript_data = ''
        for entry in transcript_list:
            start = entry["start"]
            text = entry["text"]
            transcript_data += text
            timestamp = format_timestamp(start)
            transcript_lines.append(f"[{timestamp}] {text}")
        
        full_transcript = "\n".join(transcript_lines)
        
        # Get AI summary using Groq
        summary = groq_client.summarize_transcript(transcript_data)
                
        return jsonify({
            'success': True,
            'transcript': {
                'full': full_transcript,
                'summary': summary,
                'ai_analysis': ''
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test')
def test():
    return jsonify({"return":"working"})

@app.route('/api/merge-transcripts', methods=['POST'])
def merge_transcripts():
    try:
        data = request.get_json()
        transcripts = data.get('transcripts', [])
        custom_prompt = data.get('customPrompt', '')
        
        if not transcripts:
            return jsonify({'error': 'No transcripts provided'}), 400
        
        # Combine all transcripts with section headers
        combined_transcript = ""
        for idx, transcript in enumerate(transcripts, 1):
            combined_transcript += f"\n\n## Video {idx}\n\n{transcript}"
            
        # Generate merged analysis using Groq
        merged_analysis = groq_client.summarize_transcript(
            combined_transcript + f"\n\nCustom Instructions: {custom_prompt}" if custom_prompt else combined_transcript
        )
        
        return jsonify({
            'success': True,
            'merged_analysis': merged_analysis
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)