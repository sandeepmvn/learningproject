# Team Trip Expense Tracker

A full-stack expense tracking and splitting application for team trips, built with FastAPI (Python) backend and designed for React frontend.

## 🌟 Features

- **Trip Management**: Create and manage team trips with dates, destinations, and currency
- **Participant Management**: Add team members to trips
- **Expense Tracking**: Record expenses with flexible splitting options
- **Smart Splitting**: 
  - Equal split among all participants
  - Equal split among selected participants
  - Custom split with specific amounts per person
- **Settlement Calculation**: Automatic calculation of who owes whom
- **Balance Tracking**: View individual balances (paid vs. owed)
- **RESTful API**: Well-documented API with Swagger UI

## 🏗️ Architecture

### Backend
- **Framework**: FastAPI 0.115.12
- **Database**: SQLite (development) / PostgreSQL (production recommended)
- **ORM**: SQLAlchemy 2.0.40
- **Testing**: pytest 8.3.5
- **Server**: uvicorn 0.34.0

### Frontend (Planned)
- **Framework**: React with Vite
- **Styling**: Tailwind CSS
- See `frontend/README.md` for detailed frontend instructions

## 📋 Prerequisites

- Python 3.12+
- pip package manager
- Docker (optional, for containerized deployment)
- Azure subscription (for cloud deployment)

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```powershell
   git clone <repository-url>
   cd learningproject
   ```

2. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Run the backend**
   ```powershell
   uvicorn app.main:app --reload
   ```

4. **Access the API**
   - API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Using Docker

1. **Build and run with Docker Compose**
   ```powershell
   docker-compose up --build -d
   ```

2. **View logs**
   ```powershell
   docker-compose logs -f
   ```

3. **Stop services**
   ```powershell
   docker-compose down
   ```

See `DOCKER_DEPLOYMENT.md` for detailed Docker instructions.

## 📚 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/trips` | List all trips |
| POST | `/trips` | Create a trip |
| GET | `/trips/{trip_id}` | Get trip details with participants and expenses |
| GET | `/trips/{trip_id}/participants` | List trip participants |
| POST | `/trips/{trip_id}/participants` | Add a participant |
| GET | `/trips/{trip_id}/expenses` | List trip expenses |
| POST | `/trips/{trip_id}/expenses` | Create an expense |
| GET | `/trips/{trip_id}/summary` | Get balances and settlements |

### Example Usage

#### Create a Trip
```bash
POST /trips
{
  "name": "Goa Team Trip",
  "description": "Engineering offsite",
  "destination": "Goa",
  "start_date": "2026-05-10",
  "end_date": "2026-05-14",
  "currency": "INR"
}
```

#### Add a Participant
```bash
POST /trips/1/participants
{
  "name": "Alice",
  "email": "alice@example.com"
}
```

#### Create an Expense (Equal Split)
```bash
POST /trips/1/expenses
{
  "title": "Team Dinner",
  "amount": 3000,
  "paid_by_participant_id": 1,
  "category": "Food",
  "spent_on": "2026-05-10"
}
```

#### Get Settlement Summary
```bash
GET /trips/1/summary
```

Response:
```json
{
  "trip_id": 1,
  "trip_name": "Goa Team Trip",
  "total_expenses": 3900.0,
  "balances": [
    {
      "participant_id": 1,
      "participant_name": "Alice",
      "paid": 3000.0,
      "owes": 1000.0,
      "balance": 2000.0
    }
  ],
  "settlements": [
    {
      "from_participant_id": 2,
      "from_participant_name": "Bob",
      "to_participant_id": 1,
      "to_participant_name": "Alice",
      "amount": 550.0
    }
  ]
}
```

## 🧪 Testing

Run the test suite:

```powershell
pytest
```

Run with coverage:

```powershell
pytest --cov=app --cov-report=html
```

View coverage report:
```powershell
# Open htmlcov/index.html in your browser
```

## 📁 Project Structure

```
learningproject/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application and routes
│   ├── models.py         # SQLAlchemy database models
│   ├── schemas.py        # Pydantic request/response models
│   ├── services.py       # Business logic and calculations
│   └── database.py       # Database configuration
├── tests/
│   └── test_api.py       # API endpoint tests
├── frontend/
│   └── README.md         # Frontend development guide
├── .azure/
│   └── config.json       # Azure App Service configuration
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Docker orchestration
├── azure-pipelines.yml   # Azure DevOps CI/CD pipeline
├── startup.sh            # Azure App Service startup script
├── DOCKER_DEPLOYMENT.md  # Docker deployment guide
├── AZURE_DEPLOYMENT.md   # Azure deployment guide
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./expense_tracker.db` |

### Database

The application uses SQLite by default for development. For production, consider using PostgreSQL.

To switch to PostgreSQL:

1. Update `DATABASE_URL`:
   ```
   postgresql://user:password@host:5432/dbname
   ```

2. Install PostgreSQL driver:
   ```powershell
   pip install psycopg2-binary
   ```

## 🚢 Deployment

### Docker Deployment

See `DOCKER_DEPLOYMENT.md` for complete Docker deployment instructions.

### Azure App Service Deployment

See `AZURE_DEPLOYMENT.md` for complete Azure DevOps CI/CD and App Service deployment guide.

Quick Azure deployment:

```powershell
# Install Azure CLI
# Login
az login

# Create resources
az group create --name expense-tracker-rg --location eastus
az appservice plan create --name expense-plan --resource-group expense-tracker-rg --sku B1 --is-linux
az webapp create --resource-group expense-tracker-rg --plan expense-plan --name expense-tracker-api --runtime "PYTHON:3.12"

# Deploy
az webapp up --name expense-tracker-api --resource-group expense-tracker-rg
```

## 📖 Additional Documentation

- **Frontend Development**: `frontend/README.md` - React frontend setup and API integration guide
- **Docker Deployment**: `DOCKER_DEPLOYMENT.md` - Containerization and Docker Compose setup
- **Azure Deployment**: `AZURE_DEPLOYMENT.md` - Azure DevOps pipelines and App Service deployment

## 🛠️ Development

### Adding New Features

1. Create database models in `app/models.py`
2. Define Pydantic schemas in `app/schemas.py`
3. Implement business logic in `app/services.py`
4. Add API routes in `app/main.py`
5. Write tests in `tests/`

### Code Quality

The project follows Python best practices:
- Type hints throughout
- Pydantic validation for all inputs
- Proper error handling with HTTP status codes
- Comprehensive test coverage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📝 License

This project is for educational and demonstration purposes.

## 🆘 Support

For issues and questions:
1. Check the documentation in `frontend/`, `DOCKER_DEPLOYMENT.md`, and `AZURE_DEPLOYMENT.md`
2. Review API docs at `/docs` endpoint
3. Check application logs

## 🎯 Roadmap

- [ ] Complete React frontend implementation
- [ ] Add user authentication
- [ ] Support for multiple currencies with conversion
- [ ] Export trip summary as PDF
- [ ] Mobile responsive design
- [ ] Email notifications for settlements
- [ ] Integration with payment platforms
- [ ] Multi-language support

---

**Built with ❤️ using FastAPI and Python**
