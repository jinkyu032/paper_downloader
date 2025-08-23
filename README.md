# Paper Downloader 📄

**Stop manually downloading for research papers one by one!** 


## 💡 Motivation
- I built this application because I was tired of the tedious, repetitive process of finding a paper online, copying the title, downloading the PDF, and then manually renaming and saving it to the correct folder. This tool automates that entire workflow.

## 🎯 Why You'll Love This Tool

- **Save Hours of Time**: Download dozens of papers in minutes instead of searching individually
- **Zero Manual Work**: Just paste paper titles and let the app do the rest.


---

## ✨ Key Features

🚀 **Batch Processing** - Queue up multiple paper titles and download them all simultaneously  
📁 **Smart Organization** - Automatically saves papers with clean, readable filenames  
💾 **Custom Download Folders** - Save and manage multiple download locations. You can bookmark multiple folders and easily switch between them for different projects.
🔍 **Intelligent Search** - Finds the best PDF versions using Google Scholar's ranking  
⚡ **Live Updates** - Add new papers while downloads are running   

---

## � Quick Start (Ready to Use!)

### Option 1: Download the App (Recommended)
1. **Download** the latest version from [Releases](https://github.com/jinkyu032/paper-downloader.git/releases)
2. **Unzip** and move `Paper Downloader.app` to your Applications folder
3. **Launch** and start downloading papers immediately!

### Option 2: Run from Source
```bash
# Clone the repository
git clone https://github.com/jinkyu032/paper-downloader.git
cd paper-downloader

# Install dependencies
pip install -r requirements.txt

# Run the app
python paper_downloader.py
```

---

## 📖 How to Use (30 seconds to master!)

![Paper Downloader Interface](https://via.placeholder.com/800x500/007aff/ffffff?text=Paper+Downloader+Interface)

### Step 1: Add Paper Titles
```
Deep Learning for Computer Vision
Attention Is All You Need
BERT: Pre-training of Deep Bidirectional Transformers
```
Type or paste paper titles in the left panel (one per line). **Pro tip**: Use keyboard shortcut `Cmd+Return` (Mac) or `Ctrl+Return` (Windows/Linux) to start downloads instantly!

### Step 2: Choose Download Location
- Select a folder from the dropdown menu
- Click **"Manage"** to add new folders or **"Open"** to view the current one
- Your settings are automatically saved for next time

### Step 3: Configure & Go
- Set **"Max Downloads"** (how many papers per title to find)
- Click **"Start"** or use the **'Cmd+Return'** shorcut!
- Papers appear in real-time in the Download Queue on the right

### That's it! 🎉
The app handles everything else: finding papers, downloading PDFs, organizing files with clean names, and updating you on progress.

---

## � Pro Tips & Best Practices

**🎯 For Best Results:**
- Use specific, complete paper titles rather than keywords
- Include author names when titles are ambiguous (e.g., "Attention Is All You Need Vaswani")
- Start with 1-2 papers to test, then batch larger collections

**⚡ Power User Features:**
- **Keyboard Shortcuts**: `Cmd+Return` (Mac) or `Ctrl+Return` (Windows/Linux) to start downloads
- **Live Queue**: Add more papers while current downloads are running
- **Smart Retry**: Failed downloads can be restarted individually

**🛡️ Reliability:**
- Uses persistent browser profiles to reduce CAPTCHA triggers
- Automatically handles Google Scholar's anti-bot measures
- Clean, sanitized filenames that work across all operating systems
- **Note**: You may occasionally need to solve CAPTCHAs in the browser window - this is normal and helps maintain reliable access

---

## 🔧 Technical Details

**Built with:**
- **Python 3.8+** with Tkinter for cross-platform GUI
- **Selenium WebDriver** for reliable Google Scholar access
- **BeautifulSoup** for intelligent PDF link extraction
- **Requests** for fast, concurrent downloads

**System Requirements:**
- **macOS 10.14+**, **Windows 10+**, or **Ubuntu 18.04+**
- **Chrome browser** (automatically managed by the app)
- **50MB free space** minimum

---

## � Troubleshooting

**App won't close?** 
- This is fixed in the latest version! The app now properly terminates all background processes.

**Downloads failing with "Error: Blocked"?**
- Wait a few minutes and try again - Google Scholar has rate limits
- Reduce the number of simultaneous downloads
- The app automatically handles most blocking scenarios

**Can't find a paper?**
- Try a more specific title or include author names
- Some papers may not be freely available
- Check if the paper exists on Google Scholar manually

---

## 🛠️ For Developers

### Building from Source
```bash
# Install build dependencies
pip install pyinstaller selenium webdriver-manager

# Create standalone app
pyinstaller --windowed --name "Paper Downloader" paper_downloader.py

# Find your app in the dist/ folder
```

## 🤝 Support & Community

- **Feature Requests?** We'd love to hear them!
- **Questions?** Check existing issues or start a discussion

⭐ **If this tool saves you time, please star the repository!** It helps other researchers discover it.

---

## 📜 License

MIT License - feel free to use, modify, and distribute. See [LICENSE](LICENSE) for details.

---

**Made with ❤️ for the research community**

*Tired of manually hunting down papers? Let automation handle the tedious work so you can focus on what matters: your research.*