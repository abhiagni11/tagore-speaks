import uuid
from flask import Response, stream_with_context, Blueprint, request, jsonify  # type: ignore
from services.anthropic_service import generate_response
import json


# Create a Blueprint for chat routes
chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/api/stream", methods=["POST"])
def stream_message():
    data = request.json
    user_message = data.get("message")
    conversation_id = data.get("conversationId")

    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        print(f"Created new conversation ID: {conversation_id}")

    # Check if user_message is provided
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    def generate():
        for response in generate_response(user_message, conversation_id):
            # Now all responses will be of type "chunk", including tool calls
            if response["type"] == "chunk":
                yield f"data: {json.dumps({'chunk': response['content'], 'conversationId': conversation_id})}\n\n"
            elif response["type"] == "error":
                yield f"data: {json.dumps({'error': response['content'], 'conversationId': conversation_id})}\n\n"
            else:
                # Fallback for any unexpected response types
                yield f"data: {json.dumps({'error': 'Unexpected response type', 'conversationId': conversation_id})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")
