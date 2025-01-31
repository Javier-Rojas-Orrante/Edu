import os
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter import messagebox
import fitz
from PIL import Image, ImageTk

class PDFViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Teacher")
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.photo_image = None

        # Create menu
        menubar = tk.Menu(root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        root.config(menu=menubar)

        # Create main frame with scrollbars
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=1)

        # Create Canvas
        self.canvas = tk.Canvas(self.main_frame)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Create Scrollbars
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

        self.prev_btn = ttk.Button(nav_frame, text="Previous", command=self.prev_page)
        self.prev_btn.pack(side=tk.LEFT, padx=5, pady=2)

        self.next_btn = ttk.Button(nav_frame, text="Next", command=self.next_page)
        self.next_btn.pack(side=tk.LEFT, padx=5, pady=2)

        self.first_btn = ttk.Button(nav_frame, text="First", command=self.first_page)
        self.first_btn.pack(side=tk.LEFT, padx=5, pady=2)

        self.last_btn = ttk.Button(nav_frame, text="Last", command=self.last_page)
        self.last_btn.pack(side=tk.LEFT, padx=5, pady=2)

        self.page_label = ttk.Label(nav_frame, text="Page: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=10)

        # Bind canvas resize
        self.canvas.bind("<Configure>", self.render_page)

        self.extract_btn = ttk.Button(nav_frame, text="Extract Chapter Images", 
                                    command=self.extract_current_chapter_images)
        self.extract_btn.pack(side=tk.LEFT, padx=5, pady=2)

        # Initialize chapter tracking variables
        self.current_chapter = None
        self.chapters = []

    def open_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not file_path:
            return
        
        if self.doc:
            self.doc.close()
        
        self.doc = fitz.open(file_path)
        self.total_pages = len(self.doc)
        self.current_page = 0
        self.update_page_label()
        self.render_page()

    def render_page(self, event=None):
        if not self.doc:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 0 or canvas_height <= 0:
            return

        page = self.doc.load_page(self.current_page)
        zoom_x = canvas_width / page.rect.width
        zoom_y = canvas_height / page.rect.height
        zoom = min(zoom_x, zoom_y)

        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.photo_image = ImageTk.PhotoImage(img)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.photo_image, anchor=tk.NW)
        self.canvas.configure(scrollregion=self.canvas.bbox(tk.ALL))

    def update_page_label(self):
        self.page_label.config(text=f"Page: {self.current_page + 1}/{self.total_pages}")

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

    def first_page(self):
        self.current_page = 0
        self.update_page_label()
        self.render_page()

    def last_page(self):
        self.current_page = self.total_pages - 1
        self.update_page_label()
        self.render_page()
    
    def get_chapter_info(self):
        """Extract chapter information from PDF outline"""
        self.chapters = []
        if not self.doc:
            return

        toc = self.doc.get_toc()
        for level, title, page in toc:
            if level == 1:  # Assuming level 1 items are chapters
                self.chapters.append({
                    'title': title,
                    'start_page': page,
                    'end_page': len(self.doc) - 1  # Temporary value
                })

        # Set end pages for chapters
        for i in range(len(self.chapters)-1):
            self.chapters[i]['end_page'] = self.chapters[i+1]['start_page'] - 1
        if self.chapters:
            self.chapters[-1]['end_page'] = len(self.doc) - 1


    def get_current_chapter(self):
        """Determine which chapter contains the current page"""
        for chapter in self.chapters:
            if chapter['start_page'] <= self.current_page <= chapter['end_page']:
                return chapter
        return None

    def extract_current_chapter_images(self):
        """Extract all images from current chapter"""
        if not self.doc:
            messagebox.showerror("Error", "No PDF loaded")
            return

        chapter = self.get_current_chapter()
        if not chapter:
            messagebox.showinfo("Info", "No chapter structure detected")
            return

        # Create output directory
        output_dir = f"Chapter_Images_{chapter['title']}"
        os.makedirs(output_dir, exist_ok=True)

        # Extract images from chapter pages
        image_count = 0
        for page_num in range(chapter['start_page'], chapter['end_page'] + 1):
            page = self.doc.load_page(page_num)
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = self.doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Save image
                with open(f"{output_dir}/page{page_num+1}_img{img_index+1}.{base_image['ext']}", "wb") as f:
                    f.write(image_bytes)
                image_count += 1

        messagebox.showinfo("Success", 
            f"Extracted {image_count} images to {output_dir}/")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = PDFViewer(root)
    root.mainloop()