import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import logging
import io

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

class PDFViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Learnicius Jr")
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.photo_image = None
        self.chapters = []
        self.MAX_CHAPTER_PAGES = 100  # Safety limit

        # Set a default zoom factor (for higher quality rendering)
        self.zoom_factor = 2.0

        # Create menu
        menubar = tk.Menu(root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        root.config(menu=menubar)

        # Main frame with scrollbars
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=1)

        self.canvas = tk.Canvas(self.main_frame)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Scrollbars
        v_scroll = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll = ttk.Scrollbar(self.main_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")

        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Navigation controls
        nav_frame = ttk.Frame(root)
        nav_frame.pack(fill=tk.X)

        self.prev_btn = ttk.Button(nav_frame, text="Previous", command=self.prev_page, state=tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT, padx=5, pady=2)

        self.next_btn = ttk.Button(nav_frame, text="Next", command=self.next_page, state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT, padx=5, pady=2)

        self.page_label = ttk.Label(nav_frame, text="Page: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=10)

        self.page_entry = ttk.Entry(nav_frame, width=5, state=tk.DISABLED)
        self.page_entry.pack(side=tk.LEFT, padx=5)
        self.go_btn = ttk.Button(nav_frame, text="Go", command=self.go_to_page, state=tk.DISABLED)
        self.go_btn.pack(side=tk.LEFT, padx=5)
        
        # Extraction mode toggle: Checked = Chapter mode; Unchecked = Single page (image) mode
        self.chapter_mode = tk.BooleanVar(value=True)
        self.mode_toggle = ttk.Checkbutton(nav_frame, text="Chapter Mode", variable=self.chapter_mode, command=self.update_extract_button_text)
        self.mode_toggle.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Extraction button – its text (and function) will update based on the mode
        self.extract_btn = ttk.Button(nav_frame, text="Extract Chapter", command=self.extract_content, state=tk.DISABLED)
        self.extract_btn.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Zoom controls
        self.zoom_out_btn = ttk.Button(nav_frame, text="Zoom Out", command=self.zoom_out, state=tk.DISABLED)
        self.zoom_out_btn.pack(side=tk.LEFT, padx=5, pady=2)
        self.zoom_in_btn = ttk.Button(nav_frame, text="Zoom In", command=self.zoom_in, state=tk.DISABLED)
        self.zoom_in_btn.pack(side=tk.LEFT, padx=5, pady=2)

        self.canvas.bind("<Configure>", self.render_page)

    def open_pdf(self):
        try:
            file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
            if not file_path: 
                return

            if self.doc:
                self.doc.close()

            self.doc = fitz.open(file_path)
            self.total_pages = len(self.doc)
            self.current_page = 0
            self.chapters = self.get_chapter_info()
            
            # Enable controls
            self.prev_btn['state'] = tk.NORMAL
            self.next_btn['state'] = tk.NORMAL
            self.extract_btn['state'] = tk.NORMAL
            self.go_btn['state'] = tk.NORMAL
            self.page_entry['state'] = tk.NORMAL
            self.zoom_in_btn['state'] = tk.NORMAL
            self.zoom_out_btn['state'] = tk.NORMAL
            
            self.update_page_label()
            self.render_page()
            logging.info(f"Loaded PDF with {self.total_pages} pages")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load PDF:\n{str(e)}")
            # Reset controls if open failed
            self.prev_btn['state'] = tk.DISABLED
            self.next_btn['state'] = tk.DISABLED
            self.extract_btn['state'] = tk.DISABLED
            self.go_btn['state'] = tk.DISABLED
            self.page_entry['state'] = tk.DISABLED
            self.zoom_in_btn['state'] = tk.DISABLED
            self.zoom_out_btn['state'] = tk.DISABLED

    def get_chapter_info(self):
        """Extract hierarchical chapter information with deepest subdivisions"""
        chapters = []
        try:
            toc = self.doc.get_toc()
            
            # Handle case with no TOC entries
            if not toc:
                return [{
                    'title': 'Full Document',
                    'start': 0,
                    'end': self.total_pages - 1
                }]

            # Identify deepest hierarchical subdivisions
            leaf_entries = []
            for i, entry in enumerate(toc):
                level, title, page = entry
                is_leaf = True
                
                # Check if any subsequent entries are children of this entry
                for j in range(i+1, len(toc)):
                    next_level = toc[j][0]
                    if next_level > level:  # Found a deeper subdivision
                        is_leaf = False
                        break
                    if next_level <= level:  # Sibling or parent level reached
                        break
                        
                if is_leaf:
                    leaf_entries.append(entry)

            # Fallback to top-level chapters if no subdivisions found
            if not leaf_entries:
                leaf_entries = [e for e in toc if e[0] == 1]
                if not leaf_entries:  # If no chapters, treat whole document as one
                    return [{
                        'title': 'Full Document',
                        'start': 0,
                        'end': self.total_pages - 1
                    }]

            # Create chapter ranges with boundary checks
            for i, (level, title, page) in enumerate(leaf_entries):
                start = max(0, page - 1)  # Convert to 0-based index
                end = self.total_pages - 1
                
                # Calculate end page using next subdivision's start
                if i < len(leaf_entries) - 1:
                    next_start = max(0, leaf_entries[i+1][2] - 1)
                    end = min(next_start - 1, self.total_pages - 1)
                    
                # Ensure valid page range
                start = min(start, self.total_pages - 1)
                end = max(start, min(end, self.total_pages - 1))

                chapters.append({
                    'title': self.clean_title(title),
                    'start': start,
                    'end': end
                })
                logging.info(f"Subdivision: {title} (pages {start+1}-{end+1})")

            return chapters

        except Exception as e:
            logging.warning(f"Chapter detection failed: {str(e)}")
            return [{
                'title': 'Full Document',
                'start': 0,
                'end': self.total_pages - 1
            }]

    def clean_title(self, title):
        return "".join(c if c.isalnum() else "_" for c in title.strip())

    def render_page(self, event=None):
        if not self.doc:
            return
        
        try:
            page = self.doc.load_page(self.current_page)
            # Use the fixed zoom factor for rendering.
            matrix = fitz.Matrix(self.zoom_factor, self.zoom_factor)
            pix = page.get_pixmap(matrix=matrix)
            self.photo_image = ImageTk.PhotoImage(
                Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            )
            
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, image=self.photo_image, anchor=tk.NW)
            self.canvas.configure(scrollregion=(0, 0, pix.width, pix.height))
            
        except Exception as e:
            logging.error(f"Render error: {str(e)}")

    def update_page_label(self):
        self.page_label.config(text=f"Page: {self.current_page+1}/{self.total_pages}")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page_label()
            self.render_page()

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_page_label()
            self.render_page()

    def go_to_page(self):
        if not self.doc:
            messagebox.showinfo("Info", "No PDF loaded")
            return
        try:
            page_num = int(self.page_entry.get())
            if 1 <= page_num <= self.total_pages:
                self.current_page = page_num - 1  # Convert to 0-based index
                self.update_page_label()
                self.render_page()
            else:
                messagebox.showerror("Error", f"Invalid page number. Please enter between 1 and {self.total_pages}")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")

    def zoom_in(self):
        self.zoom_factor *= 1.25
        self.render_page()

    def zoom_out(self):
        self.zoom_factor /= 1.25
        self.render_page()

    def extract_current_chapter(self):
        try:
            if not self.doc:
                messagebox.showinfo("Info", "No PDF loaded")
                return []

            current_chapter = next(
                (ch for ch in self.chapters 
                 if ch['start'] <= self.current_page <= ch['end']), None
            )

            if not current_chapter:
                messagebox.showinfo("Info", "Current page not in any chapter")
                return []

            # Validate chapter boundaries
            if not (0 <= current_chapter['start'] <= current_chapter['end'] < self.total_pages):
                messagebox.showerror("Error", "Invalid chapter boundaries")
                return []

            # Check page count safety limit
            page_count = current_chapter['end'] - current_chapter['start'] + 1
            if page_count > self.MAX_CHAPTER_PAGES:
                messagebox.showerror("Limit Exceeded", 
                    f"Chapter too large ({page_count} pages). Max allowed: {self.MAX_CHAPTER_PAGES}")
                return []

            # Extract pages
            images = []
            for page_num in range(current_chapter['start'], current_chapter['end'] + 1):
                if page_num >= self.total_pages:
                    break

                page = self.doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = io.BytesIO(pix.tobytes("png"))
                images.append(img_data)
                logging.info(f"Processed page {page_num+1}")

            messagebox.showinfo("Success", 
                f"Extracted chapter: {current_chapter['title']}\n"
                f"Pages: {current_chapter['start']+1}-{current_chapter['end']+1}\n"
                f"Images saved in memory: {len(images)}")

            return images

        except Exception as e:
            messagebox.showerror("Error", f"Extraction failed:\n{str(e)}")
            logging.error(f"Extraction error: {str(e)}")
            return []
        
    def extract_current_page(self):
        """Extracts the current page as an image."""
        try:
            if not self.doc:
                messagebox.showinfo("Info", "No PDF loaded")
                return []

            page = self.doc.load_page(self.current_page)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = io.BytesIO(pix.tobytes("png"))

            messagebox.showinfo("Success", f"Extracted page {self.current_page + 1}")
            logging.info(f"Extracted page {self.current_page + 1}")
            return [img_data]

        except Exception as e:
            messagebox.showerror("Error", f"Page extraction failed:\n{str(e)}")
            logging.error(f"Page extraction error: {str(e)}")
            return []

    def extract_content(self):
        """Extracts content based on the current extraction mode."""
        if self.chapter_mode.get():
            return self.extract_current_chapter()
        else:
            return self.extract_current_page()

    def update_extract_button_text(self):
        if self.chapter_mode.get():
            self.extract_btn.config(text="Extract Chapter")
        else:
            self.extract_btn.config(text="Extract Page")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = PDFViewer(root)
    root.mainloop()
