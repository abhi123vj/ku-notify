# KU Notifications

An automated notification system that monitors Kerala University announcements and sends email alerts for relevant updates.

## Features

- 🔄 **Automated Monitoring**: Runs every 5 hours to check for new notifications
- 📧 **Email Alerts**: Sends filtered notifications via email using Resend API
- 🎯 **Keyword Filtering**: Only sends notifications containing specified keywords
- 📅 **Year-based Filtering**: Filter notifications by academic year
- 🗄️ **MongoDB Integration**: Stores notification data to prevent duplicates
- ☁️ **GitHub Actions**: Fully automated deployment and execution

## How It Works

1. The system fetches notifications from Kerala University's website
2. Filters notifications based on configured keywords and year
3. Checks against MongoDB to avoid sending duplicate notifications
4. Sends email alerts for new, relevant notifications
5. Stores processed notifications in the database

## Setup

### Prerequisites

- GitHub account (for Actions)
- MongoDB database
- Resend API account for email services

### Configuration

Set up the following secrets in your GitHub repository settings:

| Secret | Description | Example |
|--------|-------------|---------|
| `BASE_URL` | Kerala University notifications URL | `https://www.keralauniversity.ac.in` |
| `MONGO_URI` | MongoDB connection string | `mongodb+srv://user:pass@cluster.mongodb.net/db` |
| `RESEND_API_KEY` | Resend API key for sending emails | `re_xxxxxxxxxxxxx` |
| `EMAIL_FROM` | Sender email address | `notifications@yourdomain.com` |
| `EMAIL_TO` | Recipient email address | `your-email@gmail.com` |
| `NOTIFY_KEYWORDS` | Keywords to filter notifications | `exam,result,admission,fee` |
| `NOTIFY_YEAR` | Academic year to monitor | `2024,2025` |

### Installation

1. **Fork/Clone this repository**
   ```bash
   git clone https://github.com/yourusername/ku-notifications.git
   cd ku-notifications
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   - For local development, create a `.env` file with the required variables
   - For GitHub Actions, add them as repository secrets

4. **Run locally (optional)**
   ```bash
   python app.py
   ```

## GitHub Actions Workflow

The workflow automatically:
- Runs every 5 hours (00:00, 05:00, 10:00, 15:00, 20:00 UTC)
- Can be triggered manually via workflow dispatch
- Uses Python 3.12 for compatibility
- Includes pip caching for faster builds
- Provides failure notifications

### Manual Trigger

You can manually trigger the workflow from the GitHub Actions tab in your repository.

## Project Structure

```
ku-notifications/
├── .github/
│   └── workflows/
│       └── notifications.yml    # GitHub Actions workflow
├── app.py                       # Main application script
├── requirements.txt             # Python dependencies
├── README.md                   # This file
└── .env.example               # Environment variables template
```

## Dependencies

- `requests` - HTTP requests to fetch notifications
- `pymongo` - MongoDB database operations
- `python-dotenv` - Environment variable management
- `resend` - Email service integration
- `beautifulsoup4` - HTML parsing (if needed)

## Usage

### Keyword Configuration

Configure `NOTIFY_KEYWORDS` with comma-separated keywords:
```
exam,result,admission,fee,timetable,syllabus
```

### Year Configuration

Set `NOTIFY_YEAR` for specific academic years:
```
2024,2025
```

## Troubleshooting

### Common Issues

1. **Workflow failing**: Check if all secrets are properly configured
2. **No notifications received**: Verify keyword filters and email settings
3. **Database connection issues**: Ensure MongoDB URI is correct and accessible
4. **Email delivery problems**: Check Resend API key and email addresses

### Debugging

- Check GitHub Actions logs for detailed error messages
- Verify environment variables are set correctly
- Test MongoDB connection separately
- Validate Resend API credentials

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational purposes. Please respect Kerala University's terms of service and rate limits when using this system.

---

**Note**: Make sure to keep your API keys and database credentials secure. Never commit sensitive information to your repository.