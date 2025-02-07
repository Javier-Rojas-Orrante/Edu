import base64
import io
from openai import OpenAI
import logging

class ImageAnalysisService:
    def __init__(self, api_key):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.model = "google/gemini-2.0-flash-thinking-exp:free"
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def encode_images_to_base64(self, images):
        """
        Encode a list of images to Base64 format.

        Args:
            images (list): List of file-like objects (BytesIO) containing image data.

        Returns:
            list: A list of Base64-encoded strings.
        """
        base64_images = []
        for img in images:
            logging.debug("Encoding image to Base64")
            base64_encoded = base64.b64encode(img.getvalue()).decode('utf-8')
            # Add the prefix for a PNG image
            base64_images.append(f"data:image/png;base64,{base64_encoded}")
            logging.debug(f"Image encoded: {base64_images[-1][:50]}...")  # Log first 50 chars
        return base64_images

    def analyze_images(self, base64_images):
        """
        Analyze one or multiple images in a single API request.

        The prompt is adapted automatically:
          - Single image: "What's in this image?"
          - Multiple images: "What's in these images?"
        
        Args:
            base64_images (list): List of Base64-encoded image strings.
        
        Returns:
            str: Combined response for all images.
        """
        try:
            # Choose the prompt based on the number of images provided
            prompt_text = "What's in this image?" if len(base64_images) == 1 else "What's in these images?"
            
            content = [{"type": "text", "text": prompt_text}]
            
            # Append all images to the content array
            for image in base64_images:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": image}
                })
            
            messages = [{"role": "user", "content": content}]
            
            logging.debug(f"Sending batch message with {len(base64_images)} images")
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            logging.debug(f"Completion response object for image analysis: {completion}")
            
            # Safely extract response content
            if not completion.choices:
                return "Error: Empty response from API"

            first_choice = completion.choices[0]
            if not first_choice.message or not first_choice.message.content:
                return "Error: Malformed API response"

            return first_choice.message.content
        
        except Exception as e:
            logging.error(f"Error processing batch: {str(e)}")
            return f"Error: {str(e)}"

    def chat_message(self, conversation_history):
        """
        Send a conversation chain to the API and return the assistant's response.

        Args:
            conversation_history (list): List of messages (dict) in the conversation.

        Returns:
            str: Assistant's response.
        """
        try:
            logging.debug("Sending conversation history to API.")
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=conversation_history
            )
            logging.debug(f"Chat completion response: {completion}")
            if not completion.choices:
                return "Error: Empty response from API"
            first_choice = completion.choices[0]
            if not first_choice.message or not first_choice.message.content:
                return "Error: Malformed API response"
            return first_choice.message.content
        except Exception as e:
            logging.error(f"Error during chat: {str(e)}")
            return f"Error: {str(e)}"
