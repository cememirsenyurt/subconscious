"""
Speech-to-Text transcription routes.

Handles audio file uploads and transcription using Google's free Speech Recognition.
"""

import os
import tempfile
from flask import Blueprint, request, jsonify
import speech_recognition as sr

transcribe_bp = Blueprint('transcribe', __name__)


@transcribe_bp.route("/api/transcribe", methods=["POST"])
def transcribe_audio():
    """
    Transcribe audio to text using Google's free Speech Recognition.
    
    Accepts audio file (webm, wav, etc.) and returns transcribed text.
    Uses the SpeechRecognition library with Google's free web API.
    """
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided", "text": ""}), 400
    
    audio_file = request.files["audio"]
    
    if not audio_file:
        return jsonify({"error": "Empty audio file", "text": ""}), 400
    
    recognizer = sr.Recognizer()
    
    try:
        # Save the uploaded audio to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_file:
            audio_file.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        # Convert webm to wav using pydub if available, otherwise try direct
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(tmp_path)
            wav_path = tmp_path.replace(".webm", ".wav")
            audio.export(wav_path, format="wav")
            audio_path = wav_path
        except ImportError:
            # If pydub not available, try to use the file directly
            audio_path = tmp_path
        except Exception as e:
            # If conversion fails, try direct approach
            print(f"Audio conversion warning: {e}")
            audio_path = tmp_path
        
        # Load and transcribe the audio
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
        
        # Use Google's free speech recognition (no API key needed)
        text = recognizer.recognize_google(audio_data)
        
        # Clean up temp files
        try:
            os.unlink(tmp_path)
            if audio_path != tmp_path:
                os.unlink(audio_path)
        except:
            pass
        
        return jsonify({
            "success": True,
            "text": text
        })
        
    except sr.UnknownValueError:
        return jsonify({
            "success": False,
            "error": "Could not understand audio",
            "text": ""
        })
    except sr.RequestError as e:
        return jsonify({
            "success": False,
            "error": f"Speech recognition service error: {str(e)}",
            "text": ""
        })
    except Exception as e:
        print(f"Transcription error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "text": ""
        })
