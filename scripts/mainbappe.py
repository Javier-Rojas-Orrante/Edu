import tkinter as tk
from tkinter import messagebox
import os
from pdf_viewer import PDFViewer
from image_analysis import ImageAnalysisService
import logging
import json

def load_config(config_path="config.json"):
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logging.error(f"Config file not found at {config_path}")
        return {}
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {config_path}")
        return {}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

    config = load_config()
    api_key = None
    #  TODO: THE FUCKING CONFIG LOAD IS BROKEN


    if not api_key:
        logging.error("API key not found in config.json. Please set OPENROUTER_API_KEY.")
        exit()

    root = tk.Tk()
    root.geometry("800x600")

    image_analysis_service = ImageAnalysisService(api_key)
    pdf_viewer = PDFViewer(root)

    def analyze_chapter():
        images = pdf_viewer.extract_current_chapter()
        if not images:
            messagebox.showinfo("Info", "No images to analyze.")
            return

        try:
            base64_images = image_analysis_service.encode_images_to_base64(images)
            responses = image_analysis_service.analyze_images(base64_images)

            response_text = "\n\n".join([f"Image {i+1}:\n{resp}" for i, resp in enumerate(responses)])
            messagebox.showinfo("Analysis Results", response_text)

        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed:\n{str(e)}")
            logging.error(f"Analysis error: {str(e)}")

    analyze_btn = tk.Button(root, text="Analyze Chapter", command=analyze_chapter)
    analyze_btn.pack()

    root.mainloop()