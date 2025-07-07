from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor
import re
from tkinter import *
import threading

# List of announcement pages to scrape
pages = [f"https://www.medipol.edu.tr/en/announcements?page={i}" for i in range(6)]
announcements_with_dates = []

# Scrape announcements from one page
def Get_Info(page_url):
    try:
        page = requests.get(page_url)
        soup = BeautifulSoup(page.text, "html.parser")
        announcements = soup.findAll("div", attrs={"class": "col-md-4 col-sm-6 list-card"})

        for announcement in announcements:
            text = announcement.text
            date_match = re.search(r'\d{2}\.\d{2}\.\d{4}', text)
            if date_match:
                date = date_match.group()
                clean_announcement = re.sub(r'\d{2}\.\d{2}\.\d{4}', '', text).strip()

                link_tag = announcement.find('a', href=True)
                announcement_url = link_tag['href'] if link_tag else None
                if announcement_url and not announcement_url.startswith('http'):
                    announcement_url = f"https://www.medipol.edu.tr{announcement_url}"

                announcements_with_dates.append((clean_announcement, date, announcement_url))
    except Exception as e:
        print(f"Error fetching {page_url}: {e}")

# Run all scrapes in parallel
def scrape_all_pages():
    with ThreadPoolExecutor() as executor:
        executor.map(Get_Info, pages)

# Helper: Check if text is English
def is_english(text):
    return bool(re.match(r"^[A-Za-z0-9 ,.'!?;:()&\[\]-]+$", text))

# Helper: Check if text contains a date
def contains_date(text):
    return bool(re.search(r'\b\d{2}[./]\d{2}[./]\d{4}\b', text))

# Fetch full announcement content
def Get_Details(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        justified_paragraphs = soup.find_all("p", attrs={"class": "text-align-justify"})

        details = []
        links = []

        for para in justified_paragraphs:
            text = para.text.strip()
            if contains_date(text) or not is_english(text):
                continue
            details.append(text)
            for link in para.find_all("a", href=True):
                href = link.get("href")
                if href:
                    links.append(href)

        return details, links
    except Exception as e:
        print(f"Error fetching details from {url}: {e}")
        return [], []

# Build the GUI
def GUI():
    window = Tk()
    window.title("Medipol University Announcements")
    window.geometry("1300x750")

    label = Label(window, text="Announcements")
    label.grid(row=0, column=0, columnspan=2, sticky=W)

    label1 = Label(window, text="Content of the Announcement")
    label1.grid(row=0, column=1, columnspan=2, sticky=W)

    label2 = Label(window, text="Date: ")
    label2.grid(row=0, column=1, sticky=E, padx=30)

    listbox1 = Listbox(window, height=50, width=150)
    listbox1.grid(row=1, column=1)

    listbox_frame = Frame(window)
    listbox_frame.grid(row=1, column=0)

    scrollbar = Scrollbar(listbox_frame, orient=VERTICAL)
    listbox = Listbox(listbox_frame, height=50, width=80, yscrollcommand=scrollbar.set)
    scrollbar.config(command=listbox.yview)

    scrollbar.pack(side=RIGHT, fill=Y)
    listbox.pack(side=LEFT, fill=BOTH, expand=1)

    def on_select(event):
        selected_index = listbox.curselection()
        if not selected_index:
            return
        index = selected_index[0]

        def fetch_and_display():
            selected_announcement, selected_date, selected_url = announcements_with_dates[index]
            window.title(f"Medipol University Announcements | {selected_announcement}")
            label2.config(text=f"Date: {selected_date}")
            listbox.itemconfig(index, bg='dark grey')
            listbox1.delete(0, END)

            if selected_url:
                details, links = Get_Details(selected_url)
                if details:
                    for detail in details:
                        listbox1.insert(END, detail)
                    if links:
                        listbox1.insert(END, "Links:")
                        for link in links:
                            listbox1.insert(END, link)
                else:
                    listbox1.insert(END, "No details available for this announcement.")
            else:
                listbox1.insert(END, "No details available for this announcement.")

        threading.Thread(target=fetch_and_display).start()

    listbox.bind("<<ListboxSelect>>", on_select)

    for announcement, date, url in announcements_with_dates:
        listbox.insert(END, announcement)

    mainloop()

# Start scraping and launch GUI
scrape_all_pages()
GUI()
