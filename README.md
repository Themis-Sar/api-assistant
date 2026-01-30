# api-assistant
# School IoT Chatbot

A Flask-based web application that integrates Claude AI with a school IoT API to provide an intelligent chatbot interface for querying schools, rooms, sensors, and real-time sensor data.

## Features

- 🤖 **AI-Powered Chat Interface**: Natural language interaction powered by Claude Sonnet 4
- 🏫 **School Data Access**: Query information about schools in the system
- 🚪 **Room Management**: View rooms within specific schools
- 📊 **Sensor Monitoring**: Access sensor data and real-time readings
- 💬 **Conversation Memory**: Maintains chat history for context-aware responses
- 🎨 **Modern UI**: Clean, responsive interface built with Tailwind CSS

## Prerequisites

- Python 3.8 or higher
- An Anthropic API key ([Get one here](https://console.anthropic.com/))
- Access credentials for your school IoT API

## Installation

1. **Clone or download the repository**

2. **Install required dependencies**

```bash
pip install flask anthropic requests python-dotenv
```

3. **Set up environment variables**

Create a `.env` file in the project root with the following variables:

```env
# Anthropic API
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# School IoT API Credentials
API_USERNAME=your_api_username
API_PASSWORD=your_api_password
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret

# API Endpoints
TOKEN_URL=https://your-api-domain.com/oauth/token
API_URL=https://your-api-domain.com/api

# Flask Configuration
SECRET_KEY=your_secret_key_here
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key for Claude | Yes |
| `API_USERNAME` | Username for IoT API authentication | Yes |
| `API_PASSWORD` | Password for IoT API authentication | Yes |
| `CLIENT_ID` | OAuth client ID for the IoT API | Yes |
| `CLIENT_SECRET` | OAuth client secret for the IoT API | Yes |
| `TOKEN_URL` | OAuth token endpoint URL | Yes |
| `API_URL` | Base URL for the IoT API | Yes |
| `SECRET_KEY` | Flask secret key for sessions | No (defaults to 'dev-secret-key') |

## Usage

1. **Start the application**

```bash
python app.py
```

2. **Access the chatbot**

Open your browser and navigate to:
```
http://localhost:5000
```

3. **Interact with the chatbot**

Try these example queries:
- "Show me all schools"
- "What rooms are in [school name]?"
- "List sensors in [room name]"
- "What's the current temperature in [room name]?"
- "Show me the latest sensor readings"

## API Architecture

The application uses a hierarchical API structure:

```
Schools (Main Groups)
  └── Rooms (Subgroups - Type 3)
      └── Sensors (Resources)
          └── Sensor Values (Latest readings)
```

### API Endpoints Used

- `GET /group/main` - Fetch all schools
- `GET /group/{school_uuid}/subgroup/3` - Fetch rooms in a school
- `GET /group/{room_uuid}/resource` - Fetch sensors in a room
- `GET /resource/{sensor_uuid}/latest` - Fetch latest sensor value

## How It Works

1. **User Input**: User sends a message through the web interface
2. **Claude Processing**: Claude AI analyzes the message to determine if API data is needed
3. **API Integration**: If needed, the system fetches relevant data from the IoT API
4. **Response Formatting**: Claude formats the API data into a clear, readable response
5. **Display**: The formatted response is displayed in the chat interface

## Code Structure

```
app.py
├── API Client Functions
│   ├── get_access_token()
│   ├── get_schools()
│   ├── get_school_rooms()
│   ├── get_room_sensors()
│   └── get_sensor_latest_value()
│
├── ExternalAPIClient Class
│   └── Manages all API interactions
│
├── ClaudeChatbot Class
│   ├── call_claude_api() - Handles Claude AI requests
│   ├── process_message() - Main message processing logic
│   └── fetch_external_data() - Fetches data based on request type
│
└── Flask Routes
    ├── / - Main chat interface
    ├── /api/chat - Message processing endpoint
    └── /api/clear - Clear conversation history
```

## Customization

### Modifying the System Prompt

Edit the `system_prompt` in the `call_claude_api()` method to customize Claude's behavior:

```python
system_prompt = """You are a helpful assistant for a school IoT API.
[Your custom instructions here]
"""
```

### Adding New API Endpoints

1. Add a new function in the API client section
2. Update the `ExternalAPIClient` class with a new method
3. Add a new case in `fetch_external_data()` method
4. Update the system prompt to inform Claude about the new capability

### Styling

The UI uses Tailwind CSS. Modify the `HTML_TEMPLATE` variable to customize the appearance.

## Troubleshooting

### Common Issues

**Claude API Error**
- Verify your `ANTHROPIC_API_KEY` is correct
- Check your API usage limits

**OAuth Authentication Failed**
- Confirm `CLIENT_ID`, `CLIENT_SECRET`, `API_USERNAME`, and `API_PASSWORD` are correct
- Verify the `TOKEN_URL` is accessible

**API Connection Error**
- Check that `API_URL` is correct and accessible
- Ensure your network allows connections to the API

**No Response from Chatbot**
- Check the console/logs for error messages
- Verify all environment variables are set
- Ensure the Flask server is running

### Logging

The application includes logging. Check the console output for detailed error messages:

```python
logging.basicConfig(level=logging.INFO)
```

Change to `logging.DEBUG` for more verbose output.

## Security Considerations

⚠️ **Important Security Notes:**

- Never commit your `.env` file to version control
- Use strong, unique values for `SECRET_KEY` in production
- Keep your API credentials secure
- Consider implementing rate limiting for production use
- Use HTTPS in production environments
- Implement proper authentication if deploying publicly

## Production Deployment

For production deployment:

1. Set `debug=False` in `app.run()`
2. Use a production WSGI server (e.g., Gunicorn):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```
3. Set up proper environment variables (don't use `.env` file)
4. Implement HTTPS/SSL
5. Add authentication and authorization
6. Set up monitoring and logging

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is provided as-is for educational and development purposes.

## Support

For issues related to:
- **Claude AI**: Visit [Anthropic Documentation](https://docs.anthropic.com/)
- **Flask**: Visit [Flask Documentation](https://flask.palletsprojects.com/)
- **This Application**: Check the troubleshooting section or review the code comments

