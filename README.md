# Paper Downloader 📄

A sleek, modern desktop application for finding and downloading academic papers. This tool streamlines your research workflow by allowing you to batch-download multiple papers from Google Scholar directly to your chosen folder.

---

## ✨ Features

* **Batch Downloads**: Add multiple paper titles to the queue and download them all at once.
* **Live Queue**: Add new papers to the queue while downloads are in progress without interruption.
* **Smart Search**: Uses Google Scholar to find the most relevant PDF versions of your queried papers.
* **Custom Download Folders**: Save and manage multiple download locations with a built-in bookmarking system.
* **Modern UI**: A clean, minimalist interface inspired by modern design principles for a seamless user experience.
* **Cross-Platform**: Built with Python and Tkinter, with a build process that works on macOS.

---

## 📖 How to Use

![App Screenshot](https://i.imgur.com/your-screenshot-url.png)
_Note: You will need to replace the link above with a URL to your own screenshot._

1.  **Enter Paper Titles**: Type or paste the titles of the papers you want to find into the text box on the left, with one title per line.
2.  **Select a Download Folder**: Use the dropdown menu to choose a saved location. You can add or remove folders using the **Manage...** button, or click **Open** to view the currently selected folder in your file explorer.
3.  **Configure and Start**: Adjust the **Max Downloads** to control how many relevant papers are downloaded for each query. When ready, click the **Start** button to add the papers to the download queue and begin the process.
4.  **Monitor Your Downloads**: Watch the progress in the **Download Queue** on the right. The application will show the status of each query and list the files it successfully downloads, sorted by relevance.


---

## 🚀 Getting Started (for Users)

You can download the latest pre-built version of the application from the **[Releases](https://github.com/your-username/your-repo-name/releases)** page.

1.  Go to the latest release.
2.  Download the `Paper.Downloader.zip` file.
3.  Unzip the file and move the `Paper Downloader.app` to your Applications folder.

---

## 🛠️ For Developers (Running from Source)

If you want to run or modify the application from the source code, follow these steps.

### 1. Clone the Repository


git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name


### 2. Install Dependencies

Make sure you have Python 3 installed. Then, install the required libraries:


pip3 install -r requirements.txt


*(You will need to create a `requirements.txt` file. See below.)*

### 3. Run the Application


python3 paper_downloader.py


---

## 📦 How to Build the App

This project uses **pyinstaller** to create a standalone desktop application.

1.  Install pyinstaller:
    ```
    pip3 install pyinstaller
    ```
2.  Run the build command from the project's root directory:
    ```
    pyinstaller --windowed --name "Paper Downloader" paper_downloader.py
    ```
3.  The final `Paper Downloader.app` will be located in the `dist` folder.

---

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
