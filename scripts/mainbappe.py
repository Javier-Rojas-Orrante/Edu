import tkinter as tk
from tkinter import messagebox
import os
from pdf_viewer import PDFViewer
from image_analysis import ImageAnalysisService
import logging
import json

def load_config(config_path="scripts/config.json"):
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

class ImageAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("800x600")
        
        # Load configuration
        self.config = load_config()
        self.api_key = self.config.get("OPENROUTER_API_KEY")
        
        if not self.api_key:
            logging.error("API key not found in config.json. Please set OPENROUTER_API_KEY.")
            exit()

        # Initialize services
        self.image_analysis_service = ImageAnalysisService(self.api_key)
        self.pdf_viewer = PDFViewer(root)
        
        # Create UI elements
        self.create_widgets()

    def create_widgets(self):
        # Analysis button
        self.analyze_btn = tk.Button(self.root, 
                                   text="Analyze Chapter", 
                                   command=self.analyze_chapter)
        self.analyze_btn.pack(pady=10)
        
        # Add PDF viewer components here as needed

    def analyze_chapter(self):
        """Handle image analysis workflow"""
        images = self.pdf_viewer.extract_current_chapter()
        
        if not images:
            messagebox.showinfo("Info", "No images to analyze.")
            return

        try:
            # Process images
            base64_images = self.image_analysis_service.encode_images_to_base64(images)
            analysis_response = self.image_analysis_service.analyze_images(base64_images)

            # Display results
            self.show_results(analysis_response)

        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed:\n{str(e)}")
            logging.error(f"Analysis error: {str(e)}")

    def show_results(self, response):
        """Display analysis results in a new window"""
        result_window = tk.Toplevel(self.root)
        result_window.title("Analysis Results")
        result_window.geometry("600x400")
        
        text_area = tk.Text(result_window, wrap=tk.WORD)
        text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Insert the raw response text
        text_area.insert(tk.END, response)
        text_area.config(state=tk.DISABLED)
        
        # Add copy to clipboard button
        copy_btn = tk.Button(result_window, 
                        text="Copy to Clipboard", 
                        command=lambda: self.copy_to_clipboard(response))
        copy_btn.pack(pady=5)

        def copy_to_clipboard(self, text):
            """Copy text to system clipboard"""
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("Info", "Analysis copied to clipboard!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    
    root = tk.Tk()
    app = ImageAnalysisApp(root)
    root.mainloop()