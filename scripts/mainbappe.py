import tkinter as tk
from tkinter import messagebox, scrolledtext
import os
from pdf_viewer import PDFViewer
from image_analysis import ImageAnalysisService
import logging
import json

# Import our prompt definitions.
from prompts import single_page_prompt, chapter_prompt

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

class ChatWindow(tk.Toplevel):
    def __init__(self, parent, image_analysis_service, conversation):
        super().__init__(parent)
        self.title("Chat with API")
        self.geometry("600x400")
        self.image_analysis_service = image_analysis_service
        # Use the shared conversation chain from the main app.
        self.conversation = conversation
        
        # Create a scrolled text widget to display the conversation.
        self.chat_display = scrolledtext.ScrolledText(self, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_display.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Entry field for the user to type messages.
        self.message_entry = tk.Entry(self)
        self.message_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.message_entry.bind("<Return>", self.send_message)
        
        # Send button.
        self.send_button = tk.Button(self, text="Send", command=self.send_message)
        self.send_button.pack(pady=(0, 10))
        
        self.refresh_chat_display()
    
    def refresh_chat_display(self):
        """Clear and re-display the entire conversation."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        for msg in self.conversation:
            sender = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"]
            if isinstance(content, list):
                # If content is a list, display text parts and indicate images.
                display_text = ""
                for item in content:
                    if item.get("type") == "text":
                        display_text += item.get("text", "") + " "
                    elif item.get("type") == "image_url":
                        display_text += "[Image] "
                content_str = display_text.strip()
            else:
                content_str = content
            self.chat_display.insert(tk.END, f"{sender}: {content_str}\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def send_message(self, event=None):
        user_text = self.message_entry.get().strip()
        if not user_text:
            return
        # Append user's message as a simple text message.
        user_message = {"role": "user", "content": user_text}
        self.conversation.append(user_message)
        self.refresh_chat_display()
        self.message_entry.delete(0, tk.END)
        
        # Get assistant response using the full conversation history.
        response = self.image_analysis_service.chat_message(self.conversation)
        assistant_message = {"role": "assistant", "content": response}
        self.conversation.append(assistant_message)
        self.refresh_chat_display()

class ImageAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("800x600")
        
        # Load configuration.
        self.config = load_config()
        self.api_key = self.config.get("OPENROUTER_API_KEY")
        if not self.api_key:
            logging.error("API key not found in config.json. Please set OPENROUTER_API_KEY.")
            exit()
        
        # Initialize services.
        self.image_analysis_service = ImageAnalysisService(self.api_key)
        self.pdf_viewer = PDFViewer(root)
        
        # Conversation chain to store analysis and chat messages.
        self.conversation = []
        self.chat_window = None
        
        self.create_widgets()
        self.pdf_viewer.chapter_mode.trace("w", self.update_analyze_button_text)
        self.update_analyze_button_text()
    
    def create_widgets(self):
        # Analysis button – its text will change depending on the extraction mode.
        self.analyze_btn = tk.Button(self.root, 
                                     text="Analyze Chapter", 
                                     command=self.analyze_extraction)
        self.analyze_btn.pack(pady=10)
        
        # Chat button – opens the chat window for a conversation with the API.
        self.chat_btn = tk.Button(self.root,
                                  text="Chat with API",
                                  command=self.open_chat_window)
        self.chat_btn.pack(pady=10)
    
    def update_analyze_button_text(self, *args):
        if self.pdf_viewer.chapter_mode.get():
            self.analyze_btn.config(text="Analyze Chapter")
        else:
            self.analyze_btn.config(text="Analyze Image")
    
    def analyze_extraction(self):
        """
        Instead of requesting a description from the LLM (since the user already sees the image),
        add a context-only message to the conversation chain using the appropriate prompt.
        """
        images = self.pdf_viewer.extract_content()
        if not images:
            messagebox.showinfo("Info", "No images to analyze.")
            return
        try:
            base64_images = self.image_analysis_service.encode_images_to_base64(images)
            
            # Select the appropriate prompt based on extraction mode.
            prompt_text = chapter_prompt if self.pdf_viewer.chapter_mode.get() else single_page_prompt
            
            # Build a conversation message for the context.
            analysis_context_message = {
                "role": "user",
                "content": [{"type": "text", "text": prompt_text}]
            }
            for img_str in base64_images:
                analysis_context_message["content"].append({
                    "type": "image_url",
                    "image_url": {"url": img_str}
                })
            
            # Append the context message to the conversation chain.
            self.conversation.append(analysis_context_message)
            
            messagebox.showinfo("Context Updated", "Analysis context has been added to the conversation chain.")
            
            # Refresh the chat window (if open) to reflect the new context.
            if self.chat_window is not None:
                self.chat_window.refresh_chat_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed:\n{str(e)}")
            logging.error(f"Analysis error: {str(e)}")
    
    def open_chat_window(self):
        """Open (or raise) the chat window that shares the conversation chain."""
        if self.chat_window is None or not tk.Toplevel.winfo_exists(self.chat_window):
            self.chat_window = ChatWindow(self.root, self.image_analysis_service, self.conversation)
        else:
            self.chat_window.lift()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    root = tk.Tk()
    app = ImageAnalysisApp(root)
    root.mainloop()
