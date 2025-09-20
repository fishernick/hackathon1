# PurdueAI - Campus Assistant

A ChatGPT-powered assistant specifically designed for Purdue University students, faculty, and staff. PurdueAI can help with campus locations, dining options, transportation, events, and more!

## Features

- 🏫 **Campus Locations**: Find addresses and directions to any campus building
- 🍽️ **Dining Information**: Get information about dining courts and food options
- 🚌 **Transportation**: Get directions and travel times between locations
- 📍 **Google Maps Integration**: Real-time location data and directions
- 🎯 **Purdue-Focused**: Only answers questions relevant to Purdue University
- 💬 **Web Interface**: Clean, modern chat interface with Purdue's color theme

## Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up API Keys

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

### 3. Run the Application

#### Option 1: Web Interface (Recommended)
```bash
python app.py
```
Then open your browser and go to: http://localhost:5001

#### Option 2: Command Line Interface
```bash
python main.py
```

## Usage

### Web Interface
1. Open http://localhost:5001 in your browser
2. Type your question in the chat input
3. Press Enter or click Send
4. Get instant responses from PurdueAI!

### Example Questions
- "Where is Tarkington Hall?"
- "How do I get to the Memorial Union?"
- "What's the distance from Hawkins Hall to the library?"
- "Tell me about dining options on campus"
- "How far is it from Purdue to Indianapolis Airport?"

## API Endpoints

- `GET /` - Main chat interface
- `POST /api/chat` - Send a message to PurdueAI
- `GET /api/health` - Health check

## Architecture

- **Backend**: Python Flask server with OpenAI and Google Maps integration
- **Frontend**: HTML/CSS/JavaScript with responsive design
- **AI**: OpenAI GPT-3.5-turbo for natural language processing
- **Maps**: Google Maps API for location data and directions

## Color Theme

The interface uses Purdue University's official colors:
- **Primary Gold**: #C28E0E
- **Primary Red**: #8B0000
- **Clean white background** with subtle gradients

## Testing

Run the test suite to verify everything is working:

```bash
python test_purdue_ai.py
```

## Troubleshooting

### Common Issues

1. **Port 5000 in use**: The app will automatically use port 5001
2. **API Key errors**: Make sure your `.env` file is in the project root
3. **Google Maps errors**: Verify your Google Maps API key has the necessary permissions

### Getting Help

If you encounter any issues:
1. Check that all dependencies are installed
2. Verify your API keys are correct
3. Make sure the virtual environment is activated
4. Check the console output for error messages

## License

This project is for educational purposes. Make sure to follow OpenAI's usage policies and Google Maps API terms of service.

---

**Boiler Up! 🚂**
