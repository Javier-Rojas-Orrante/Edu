import base64
import io
from openai import OpenAI

class ImageAnalysisService:
    def __init__(self, api_key):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )

        self.model = "google/gemini-2.0-flash-thinking-exp:free"

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
            # Read the image and encode it to Base64
            base64_encoded = base64.b64encode(img.getvalue()).decode('utf-8')
            # Add the prefix for a PNG image
            base64_images.append(f"data:image/png;base64,{base64_encoded}")
        return base64_images

    def analyze_images(self, base64_images):
        """
        Analyze a list of Base64-encoded images by making an API call to the LLM.

        Args:
            base64_images (list): List of Base64-encoded image strings.

        Returns:
            list: A list of responses from the API for each image.
        """
        responses = []

        for base64_image in base64_images:
            try:
                # Prepare the messages for the API
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What's in this image?"},
                            {"type": "image_base64", "image_base64": base64_image}
                        ]
                    }
                ]

                # Call the LLM API
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )

                # Extract the response
                response_content = completion.choices[0].message["content"]
                responses.append(response_content)

            except Exception as e:
                responses.append(f"Error processing image: {str(e)}")

        return responses