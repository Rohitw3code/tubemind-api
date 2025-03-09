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

@app.route('/api/generate-script', methods=['POST'])
def generate_script():
    try:
        data = request.get_json()
        title = data.get('title')
        duration = data.get('duration')  # 'short', 'medium', 'long'
        custom_instructions = data.get('customInstructions', '')

        if not title or not duration:
            return jsonify({'error': 'Title and duration are required'}), 400

        # Map duration to actual time ranges
        duration_ranges = {
            'short': '1-3 minutes',
            'medium': '5-10 minutes',
            'long': '15-30 minutes'
        }

        # Create prompt for the AI
        prompt = f"""Generate a detailed video script for YouTube with the following specifications:

Title: {title}
Target Duration: {duration_ranges.get(duration, '5-10 minutes')}

{f'Additional Instructions: {custom_instructions}' if custom_instructions else ''}

Please provide a complete script including:
1. Introduction/Hook
2. Main Content Sections
3. Call to Action
4. Timestamps for each section
5. Approximate duration for each section
6. Key points to emphasize
7. Suggested B-roll/visual cues

Format the response as a structured script with clear sections and timing."""

        # Generate script using Groq
        generated_script = groq_client.generate_script(prompt)

        return jsonify({
            'success': True,
            'script': generated_script
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-hashtags', methods=['POST'])
def generate_hashtags():
    try:
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({'error': 'No content provided'}), 400

        # Create prompt for hashtag generation
        prompt = f"""Generate relevant, trending, and engaging hashtags for the following video content. 
        The hashtags should be optimized for YouTube and social media visibility.

Content: {content}

Please provide:
1. A mix of popular and niche hashtags
2. Relevant trending hashtags
3. Topic-specific hashtags
4. Industry-standard hashtags
5. Engagement-focused hashtags

Format: Return only the hashtags without '#' symbol, separated by commas."""

        # Generate hashtags using Groq
        response = groq_client.generate_hashtags(prompt)
        
        # Process the response to get a clean list of hashtags
        hashtags = [tag.strip() for tag in response.split(',') if tag.strip()]
        
        # Calculate trending score (example implementation)
        trending_score = min(len(hashtags) * 3, 100)  # Simple scoring based on number of relevant tags
        
        return jsonify({
            'success': True,
            'hashtags': hashtags,
            'stats': {
                'trending_score': trending_score,
                'relevance': 'High' if trending_score > 80 else 'Medium',
                'total_tags': len(hashtags)
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