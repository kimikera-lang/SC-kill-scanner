# Star Citizen Log Scanner

A simple desktop application that monitors and displays the Star Citizen game log file in real-time.

## Requirements
- Python 3.x
- tkinter (usually comes with Python)
- watchdog package

## Installation

1. Install the required dependencies:
```
pip install -r requirements.txt
```

## Usage

1. Run the application:
```
python main.py
```

The application will automatically start monitoring the Star Citizen log file at:
`C:\Program Files\Roberts Space Industries\StarCitizen\LIVE\Game.log`

- The application will display any existing content in the log file
- New log entries will appear automatically as they are written to the file
- The text area will automatically scroll to show the newest entries

## Features
- Real-time log file monitoring
- Auto-scrolling text display
- Error handling for missing log file
- UTF-8 encoding support