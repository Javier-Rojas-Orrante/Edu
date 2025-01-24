import fitz  # PyMuPDF

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
    def get_chapter_contents(path, chapter_key):
        """
        Retrieves the contents of a specific chapter based on its key in the TOC.
        Chapter key corresponds to the order in the TOC list (1-indexed).
        """
        # Open the PDF document
        with open(path, 'rb') as file:
            textbook = fitz.open(file)
            toc = textbook.get_toc()  # Get the TOC

        if chapter_key < 1 or chapter_key > len(toc):
            print(f"Chapter key {chapter_key} is out of range. The document has {len(toc)} chapters.")
            return None

        # Get the specified chapter
        chapter = toc[chapter_key - 1]
        title = chapter[1]
        start_page = chapter[2] - 1  # Convert to 0-based index
        end_page = toc[chapter_key][2] - 1 if chapter_key < len(toc) else len(textbook)  # End page

        print(f"Chapter '{title}' starts on page {start_page + 1}.")

        # Extract text from all pages in the chapter
        chapter_text = ""
        for page_num in range(start_page, end_page):
            page = textbook[page_num]
            chapter_text += page.get_text()

        return chapter_text