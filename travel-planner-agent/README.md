# 🌍 AI Travel Itinerary Planner

A Streamlit web app that creates personalized travel itineraries using LangGraph AI agents.

## ✨ Features

* 🤖 AI-powered flight recommendations
* 🏨 Smart hotel selection
* 📅 Day-by-day itinerary planning
* 💰 Cost estimation
* 🔄 Real-time generation progress
* 📱 User-friendly web interface

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
Create a `.env` file:
```bash
OPENAI_API_KEY=your_openai_key
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_TRACING_V2=true
LANGSMITH_PROJECT="travel-planner"
TAVILY_API_KEY=your_tavily_key
SERPAPI_API_KEY=your_serpapi_key
```

### 3. Configure LangGraph API
Edit `streamlit_app.py`:
```python
URL = "http://127.0.0.1:2024"
client = get_client(url=URL)
assistant_id = "agent"
```

### 4. Run the App
```bash
streamlit run streamlit_app.py
```

## 📋 Usage

1. Enter travel details (origin, destination, dates)
2. Click "Plan My Trip" 
3. Watch real-time progress as LangGraph processes your request
4. Review and download your itinerary

## 📊 LangGraph Response Format

Your agent should return:
```python
{
    "origin": "BKK",
    "destination": "CNX", 
    "departure_date": "2025-09-20",
    "return_date": "2025-09-22",
    "flight_data": "Flight recommendations...",
    "hotel_data": "Hotel analysis...",
    "itinerary": "# Your Travel Plan..."
}
```

## 🛠️ Requirements

- LangGraph API server running
- Valid assistant/agent deployed