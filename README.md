# Sonicus - Therapeutic Sound Healing Platform 🎵

A comprehensive B2C therapeutic sound healing platform built with React (Frontend) and FastAPI (Backend), supporting **all 26 EU languages** for a truly global wellness experience.

## 🌟 Features

### 🎧 Core Functionality
- **Therapeutic Sound Library**: Professional-grade audio therapy content
- **Personalized Sessions**: AI-powered sound recommendations
- **Multi-tier Subscriptions**: Starter (Free), Premium, and Pro plans
- **Real-time Analytics**: Track wellness progress and listening habits
- **Cross-platform Access**: Web, mobile-responsive design

### 🌍 Internationalization
- **26 EU Languages**: Complete support for all European Union languages plus regional variants
- **Geographical Organization**: Languages sorted by proximity for intuitive selection
- **Auto-detection**: Intelligent browser language detection with fallbacks
- **Cultural Adaptation**: Localized pricing, therapeutic terminology, wellness concepts

### 🔐 Security & Authentication
- **Advanced Auth**: Multi-factor authentication with Authentik integration
- **Session Management**: Secure user sessions with advanced monitoring
- **Multi-tenant Architecture**: Isolated user data and personalized experiences
- **Privacy-first**: GDPR compliant with comprehensive data protection

## 🏗️ Architecture

```
sonicus/
├── backend/                 # FastAPI Python Backend
│   ├── app/
│   │   ├── core/           # Authentication, security, config
│   │   ├── db/             # Database models and sessions
│   │   ├── models/         # Pydantic models
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # Business logic
│   │   └── schemas/        # Data schemas
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # React.js Frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── context/        # React context providers
│   │   ├── i18n/           # Internationalization
│   │   │   └── locales/    # 26 language translation files
│   │   ├── styles/         # CSS stylesheets
│   │   └── utils/          # Utility functions
│   ├── public/             # Static assets
│   └── package.json        # Node.js dependencies
│
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** (for backend)
- **Node.js 16+** (for frontend)
- **PostgreSQL** (for database)
- **Redis** (for caching)

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/Akkadian-delphi/sonicus.git
cd sonicus

# Set up Python virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database and API keys

# Run database migrations
python -m app.db.migrations

# Start the backend server
python run.py
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm start

# Build for production
npm run build
```

## 🌐 Supported Languages

### Complete EU Language Support (26 Languages) - Organized Geographically

#### North America & Americas
| Language | Code | Native Name | Status |
|----------|------|-------------|---------|
| 🇺🇸 English (US) | `en-US` | English (United States) | ✅ Default |
| 🇷 Portuguese (BR) | `pt-BR` | Português (Brasil) | ✅ Complete |

#### Western Europe (Atlantic Coast)
| Language | Code | Native Name | Status |
|----------|------|-------------|---------|
| 🇵🇹 Portuguese (PT) | `pt-PT` | Português (Portugal) | ✅ Complete |
| 🇪🇸 Spanish | `es` | Español | ✅ Complete |
| 🇫🇷 French | `fr` | Français | ✅ Complete |

#### British Isles
| Language | Code | Native Name | Status |
|----------|------|-------------|---------|
| �� English (UK) | `en-GB` | English (United Kingdom) | ✅ Complete |
| �🇪 Irish | `ga` | Gaeilge | ✅ Complete |

#### Low Countries & Central Europe
| Language | Code | Native Name | Status |
|----------|------|-------------|---------|
| 🇳🇱 Dutch | `nl` | Nederlands | ✅ Complete |
| �� German | `de` | Deutsch | ✅ Complete |

#### Alpine Region
| Language | Code | Native Name | Status |
|----------|------|-------------|---------|
| 🇮🇹 Italian | `it` | Italiano | ✅ Complete |

#### Nordic Countries
| Language | Code | Native Name | Status |
|----------|------|-------------|---------|
| �� Danish | `da` | Dansk | ✅ Complete |
| 🇸🇪 Swedish | `sv` | Svenska | ✅ Complete |
| �� Finnish | `fi` | Suomi | ✅ Complete |

#### Baltic States
| Language | Code | Native Name | Status |
|----------|------|-------------|---------|
| 🇪🇪 Estonian | `et` | Eesti keel | ✅ Complete |
| �� Latvian | `lv` | Latviešu valoda | ✅ Complete |
| 🇱🇹 Lithuanian | `lt` | Lietuvių kalba | ✅ Complete |

#### Central Europe
| Language | Code | Native Name | Status |
|----------|------|-------------|---------|
| 🇨🇿 Czech | `cs` | Čeština | ✅ Complete |
| 🇸🇰 Slovak | `sk` | Slovenčina | ✅ Complete |
| 🇵🇱 Polish | `pl` | Polski | ✅ Complete |
| 🇭🇺 Hungarian | `hu` | Magyar | ✅ Complete |

#### Southeast Europe
| Language | Code | Native Name | Status |
|----------|------|-------------|---------|
| 🇸� Slovene | `sl` | Slovenščina | ✅ Complete |
| 🇭🇷 Croatian | `hr` | Hrvatski | ✅ Complete |
| �🇷🇴 Romanian | `ro` | Română | ✅ Complete |
| 🇧🇬 Bulgarian | `bg` | Български | ✅ Complete |

#### Mediterranean
| Language | Code | Native Name | Status |
|----------|------|-------------|---------|
| 🇬🇷 Greek | `el` | Ελληνικά | ✅ Complete |
| 🇲🇹 Maltese | `mt` | Malti | ✅ Complete |

**Total**: 26 languages covering 100% of EU official languages plus regional variants

## 🔧 Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Authentik OAuth2/OIDC
- **Caching**: Redis
- **Task Queue**: Celery
- **Testing**: pytest
- **API Documentation**: OpenAPI/Swagger

### Frontend
- **Framework**: React 18
- **Language**: JavaScript/JSX
- **Styling**: CSS3 with modern features
- **Internationalization**: react-i18next
- **State Management**: React Context
- **Build Tool**: Create React App
- **Testing**: Jest & React Testing Library

### DevOps & Deployment
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions
- **Monitoring**: Structured logging
- **Security**: Environment-based configuration

## 📊 Subscription Tiers

| Feature | Starter (Free) | Premium (€9.99/mo) | Pro (€19.99/mo) |
|---------|----------------|-------------------|------------------|
| Daily Sessions | 3 | 10 | Unlimited |
| Session Length | 15 minutes | 60 minutes | Unlimited |
| Content Library | Basic | Full | Premium + Exclusive |
| Analytics | Personal | Advanced | Advanced + Insights |
| Support | Community | Email | Priority |

*Pricing automatically adapts to local currencies for EU markets*

## 🔐 Security Features

- **Multi-Factor Authentication**: SMS, Email, TOTP support
- **Session Security**: Advanced session monitoring and management
- **Data Privacy**: GDPR-compliant multi-tenant architecture
- **API Security**: Rate limiting, request validation, CORS protection
- **Encryption**: End-to-end data encryption for sensitive information

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

## 📈 Performance

- **Frontend**: Optimized React build with code splitting
- **Backend**: FastAPI with async/await for high concurrency
- **Caching**: Redis for session management and frequently accessed data
- **Database**: Optimized PostgreSQL queries with connection pooling
- **CDN Ready**: Static assets optimized for CDN delivery

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software. All rights reserved. Unauthorized copying, modification, distribution, or use of this software is strictly prohibited without explicit written permission from the copyright holder.

## 🆘 Support

- **Documentation**: Check the `docs/` folder for detailed guides
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join community discussions in GitHub Discussions
- **Contact**: [support@sonicus.com](mailto:support@sonicus.com)

## 🗺️ Roadmap

### Phase 1 ✅ (Current)
- [x] Core therapeutic sound platform
- [x] Complete EU language support
- [x] Advanced authentication system
- [x] Subscription management

### Phase 2 🚧 (In Progress)
- [ ] Mobile app (React Native)
- [ ] AI-powered sound recommendations
- [ ] Community features
- [ ] Advanced analytics dashboard

### Phase 3 🔮 (Planned)
- [ ] IoT device integration
- [ ] Therapist portal
- [ ] API for third-party integrations
- [ ] Advanced biometric tracking

---

**🎵 Sonicus - Transforming wellness through the healing power of sound**

*Built with ❤️ by [Elefefe](https://github.com/Akkadian-delphi)*
