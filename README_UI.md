# SRM AI Doc Assist - Modern UI

A modern, responsive web interface for the SRM AI Document Assistant, inspired by Google Gemini's design principles.

## Features

### 🎨 Modern Design
- **Clean, professional interface** with subtle shadows and blue accents
- **Responsive layout** that works on desktop, tablet, and mobile devices
- **Dark/Light theme support** with system preference detection
- **Smooth animations** and hover effects

### 📱 Responsive Layout
- **Collapsible sidebar** that automatically adapts to screen size
- **Mobile-first design** with touch-friendly controls
- **Adaptive grid system** for feature cards and content

### 🔧 Interactive Features
- **Collapsible sidebar** with navigation and tools
- **Settings modal** for theme and model preferences
- **Chat history** with persistent storage
- **Real-time chat interface** with loading indicators
- **Auto-resizing text input** for better user experience

### 🚀 Smart Functionality
- **New chat button** to start fresh conversations
- **Recent chats list** for quick access to previous conversations
- **Source citations** showing where answers come from
- **Confidence scoring** for answer quality
- **Model selection** for different AI capabilities

## Getting Started

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)
- Ollama running with Llama models

### Installation

1. **Clone and setup the project:**
   ```bash
   cd SRM_RAG
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Start the application:**
   ```bash
   python app.py --host 127.0.0.1 --port 8000
   ```

3. **Open your browser:**
   Navigate to `http://127.0.0.1:8000`

## UI Components

### Sidebar
- **Header**: Logo and toggle button
- **New Chat**: Start fresh conversations
- **Recent Chats**: List of previous conversations
- **Tools**: Quick access to features
- **Settings**: Theme and model preferences

### Main Content
- **Header**: Mobile menu and user profile
- **Content Area**: Chat messages and welcome screen
- **Feature Cards**: Highlight key capabilities
- **Chat Input**: Modern input field with action buttons

### Chat Interface
- **User Messages**: Blue bubbles on the right
- **AI Responses**: Gray bubbles on the left
- **Sources**: Clickable source citations
- **Loading States**: Visual feedback during processing

## Usage

### Starting a Chat
1. Type your question in the input field
2. Press Enter or click the send button
3. View the AI response with source citations
4. Continue the conversation naturally

### Managing Chats
- **New Chat**: Click the "New Chat" button to start fresh
- **Recent Chats**: Click on any chat in the sidebar to reload it
- **Chat History**: All conversations are automatically saved

### Customization
- **Theme**: Choose between Light, Dark, or System preference
- **Model**: Select different Llama models for various capabilities
- **Settings**: Access via the gear icon in the sidebar footer

## Responsive Breakpoints

- **Desktop** (>1024px): Full sidebar always visible
- **Tablet** (768px-1024px): Collapsible sidebar with overlay
- **Mobile** (<768px): Sidebar hidden by default, accessible via menu

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development

### File Structure
```
templates/
├── index.html          # Main HTML template
└── static/
    ├── css/
    │   └── style.css   # Main stylesheet
    └── js/
        └── app.js      # JavaScript functionality
```

### Key Features
- **CSS Grid & Flexbox** for responsive layouts
- **CSS Custom Properties** for theming
- **ES6 Classes** for organized JavaScript
- **Local Storage** for persistent data
- **Fetch API** for server communication

### Customization
- **Colors**: Modify CSS custom properties in `style.css`
- **Layout**: Adjust breakpoints and grid systems
- **Functionality**: Extend the `SRMAIApp` class in `app.js`

## Troubleshooting

### Common Issues
1. **Sidebar not working**: Check JavaScript console for errors
2. **Styling issues**: Ensure CSS file is loading correctly
3. **Chat not working**: Verify API endpoint is accessible
4. **Mobile issues**: Test responsive breakpoints

### Debug Mode
Open browser developer tools to see:
- Console logs for JavaScript errors
- Network tab for API calls
- Elements tab for DOM structure

## Contributing

To improve the UI:
1. Test on multiple devices and screen sizes
2. Ensure accessibility standards are met
3. Maintain consistent design language
4. Add new features incrementally

## License

This project follows the same license as the main SRM RAG system.

