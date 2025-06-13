# 🧠 ZenithPlanner: Your Intelligent Task Manager

ZenithPlanner is a smart, AI-powered task management application that transforms how you organize your productivity. Built with Streamlit and powered by Google's Gemini AI, it understands natural language input and automatically organizes your tasks with intelligent prioritization.

## ✨ Key Features

### 🤖 AI-Powered Natural Language Processing
- **Intelligent Task Parsing**: Simply describe what you need to do in plain English
- **Smart Date Recognition**: Understands relative dates like "tomorrow", "next Friday", "in 2 weeks"
- **Automatic Categorization**: AI assigns appropriate categories (Work, Personal, Health, Finance, etc.)
- **Context-Aware Scheduling**: Considers current time and date for accurate deadline calculation

### 📊 Smart Task Organization
- **Priority-Based Dashboard**: Tasks are automatically sorted by urgency and due date
- **24-Hour Priority View**: Focus on what needs attention in the next day
- **Countdown Events**: Long-term tasks and events displayed separately with time remaining
- **Overdue Detection**: Clear visual indicators for overdue items

### 🔐 Secure Authentication & Data Management
- **Google OAuth Integration**: Secure login with your Google account
- **User Data Isolation**: Each user's tasks are completely private and secure
- **PostgreSQL Backend**: Robust data storage with Supabase integration
- **Session Management**: Secure cookie-based authentication with proper cleanup

### 📈 Productivity Analytics
- **AI-Generated Daily Summaries**: Get intelligent insights about your productivity
- **Completion Tracking**: Monitor what you've accomplished
- **Pending Task Analysis**: AI highlights what needs immediate attention
- **Motivational Insights**: Encouraging messages to keep you productive

### 🔄 Recurring Task Support
- **Flexible Recurrence Patterns**: Daily, weekly, monthly, and yearly recurring tasks
- **Birthday & Anniversary Tracking**: Special handling for annual events
- **Automatic Reset**: Completed recurring tasks automatically regenerate

### 🌍 Time Zone Aware
- **IST (Indian Standard Time) Optimized**: Designed for Indian users
- **Real-time Clock Integration**: Uses external time API for accuracy
- **Timezone Conversion**: Handles different timezone displays properly

## 🛠️ Technology Stack

- **Frontend**: [Streamlit](https://streamlit.io/) - Modern web application framework
- **AI Engine**: [Google Gemini AI](https://ai.google.dev/) - Advanced language understanding
- **Authentication**: [OAuth 2.0](https://oauth.net/2/) with Google
- **Database**: [PostgreSQL](https://www.postgresql.org/) with [Supabase](https://supabase.com/)
- **Backend**: [SQLAlchemy](https://www.sqlalchemy.org/) for database operations
- **AI Framework**: [LangChain](https://langchain.com/) for AI agent orchestration
- **Deployment**: [Streamlit Cloud](https://streamlit.io/cloud) ready

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Google Cloud Platform account (for Gemini AI API)
- Supabase account (for database)
- Google OAuth credentials

### Local Development Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/neon200/ZenithPlanner.git
   cd ZenithPlanner
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GOOGLE_CLIENT_ID=your_google_oauth_client_id
   GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
   DATABASE_URL=your_supabase_postgresql_url
   REDIRECT_URI=http://localhost:8501
   COOKIE_PASSWORD=your_secure_random_password_32_chars
   ```

4. **Run the Application**
   ```bash
   streamlit run streamlit_app.py
   ```

### Cloud Deployment (Streamlit Cloud)

1. **Fork this repository** to your GitHub account

2. **Configure Secrets** in Streamlit Cloud app settings:
   - `GEMINI_API_KEY`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `DATABASE_URL`
   - `REDIRECT_URI` (your deployed app URL)
   - `COOKIE_PASSWORD`

3. **Deploy** directly from your GitHub repository

## 🔧 Configuration Guide

### Google Cloud Setup
1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable the Gemini AI API
3. Create OAuth 2.0 credentials for web application
4. Add your redirect URIs (local and production)

### Supabase Database Setup
1. Create a new project on [Supabase](https://supabase.com)
2. Get your PostgreSQL connection string
3. The application will automatically create required tables

### OAuth Configuration
- **Local Development**: `http://localhost:8501`
- **Production**: Your deployed app URL
- Ensure both are added to Google OAuth settings

## 📖 How to Use

### Adding Tasks
Simply type natural language descriptions:
- "Submit project report by Friday 5 PM"
- "Call dentist tomorrow morning"
- "Mom's birthday next month on 15th"
- "Weekly team meeting every Monday 10 AM"

### Task Management
- **✔️ Complete**: Click the checkmark to mark tasks done
- **🗑️ Delete**: Remove tasks you no longer need
- **📋 Priority View**: Focus on urgent tasks (next 24 hours)
- **⏳ Countdown**: Track long-term events and deadlines

### AI Summary
Generate intelligent daily summaries that include:
- Tasks completed today
- Pending tasks in next 24 hours
- Motivational insights
- Productivity patterns

## 🏗️ Project Structure

```
ZenithPlanner/
├── streamlit_app.py      # Main application entry point
├── task_manager.py       # Core task management logic
├── config.py            # Configuration and environment handling
├── requirements.txt     # Python dependencies
├── db/
│   └── models.py       # Database models and operations
├── .env                # Local environment variables (create this)
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## 🔒 Security Features

- **OAuth 2.0 Authentication**: Industry-standard secure login
- **Encrypted Cookies**: Session data is encrypted
- **User Data Isolation**: Row-level security in database
- **Environment-based Configuration**: Secrets managed securely
- **Session Validation**: Proper token validation and cleanup

## 🌟 Advanced Features

### AI Agent System
- Uses LangChain framework for structured AI interactions
- Specialized tools for task creation and summarization
- Context-aware prompt engineering
- Error handling and fallback mechanisms

### Database Design
- PostgreSQL with full CRUD operations
- User isolation with foreign key constraints
- Timezone-aware datetime handling
- Optimized queries for performance

### Real-time Updates
- Live task status updates
- Automatic countdown calculations
- Dynamic time-based prioritization
- Instant AI feedback

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add comments for complex logic
- Test your changes thoroughly
- Update documentation as needed

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🐛 Issues & Support

- **Bug Reports**: [GitHub Issues](https://github.com/neon200/ZenithPlanner/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/neon200/ZenithPlanner/discussions)
- **Documentation**: Check this README and code comments

## 🎯 Roadmap

- [ ] Mobile app development
- [ ] Calendar integration (Google Calendar, Outlook)
- [ ] Team collaboration features
- [ ] Advanced analytics dashboard
- [ ] Multiple timezone support
- [ ] Voice input for task creation
- [ ] Integration with popular productivity tools

## 👨‍💻 About the Developer

Created by [neon200](https://github.com/neon200) - Building intelligent solutions for everyday productivity challenges.

---

⭐ **Star this repository** if you find ZenithPlanner helpful! Your support motivates continued development and improvements.