import fitz  # PyMuPDF
import sys

class PDFReaderService:
    """
    A service to interact with PDF files, allowing users to retrieve the Table of Contents (TOC)
    and extract contents of specific chapters.
    """
    @staticmethod
    def get_table_of_contents(path):
        """
        Reads and prints the Table of Contents (TOC) of a PDF file with hierarchy.
        Adds an index to each chapter for easy reference.
        Returns the TOC as a list for further use.
        """
        # Open the PDF document
        with open(path, 'rb') as file:
            textbook = fitz.open(file)
            contents = textbook.get_toc()  # Get the Table of Contents

        # Display the TOC with hierarchy and keys
        print("Table of Contents:")
        for idx, chapter in enumerate(contents, start=1):
            level = chapter[0]  # Level in hierarchy
            title = chapter[1]  # Chapter title
            page = chapter[2]   # Starting page number
            print(f"[{idx}] {'  ' * (level - 1)}- {title} (Page {page})")
        
        return contents

    @staticmethod
    def get_chapter_start_and_end_pages(path, chapter_key):
        """
        Retrieves the start and end pages of a specific chapter based on its key in the TOC.
        Chapter key corresponds to the order in the TOC list (1-indexed).
        """
        # Open the PDF document
        with open(path, 'rb') as file:
            textbook = fitz.open(file)
            toc = textbook.get_toc()  # Get the TOC

        if chapter_key < 1 or chapter_key > len(toc):
            print(f"Chapter key {chapter_key} is out of range. The document has {len(toc)} chapters.")
            return None, None

        # Get the specified chapter
        chapter = toc[chapter_key - 1]
        start_page = chapter[2]  # Assume TOC page numbers are 1-based
        end_page = toc[chapter_key][2] - 1 if chapter_key < len(toc) else len(textbook)  # End page

        return start_page, end_page

    @staticmethod
    def get_chapter_contents(path, start_page, end_page):
        """
        Extracts the contents of a chapter given its start and end pages.
        Saves each page of the chapter as an image file.
        """
        # Open the PDF document
        with open(path, 'rb') as file:
            textbook = fitz.open(file)

            # Loop through the specified page range
            for page_number in range(start_page, end_page):
                page = textbook.load_page(page_number)  # Load the page
                image = page.get_pixmap()  # Render the page as an image
                image.save(f"chapter_page_{page_number + 1}.png")  # Save the image
