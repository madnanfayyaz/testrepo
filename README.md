# 🛡️ GRC Platform - Complete Django Application

**Enterprise Governance, Risk & Compliance Management Platform**

[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Overview

A comprehensive, multi-tenant GRC (Governance, Risk & Compliance) platform built with Django and Django REST Framework. Manage compliance across multiple standards (ISO 27001, NIST, SOC 2, etc.), conduct assessments, track findings, and generate compliance reports.

## ✨ Features

### 🏢 Multi-Tenancy
- Complete tenant isolation
- Organization & department hierarchies
- Cross-tenant data protection

### 👤 Identity & Access Management
- Custom user model with extended profile
- Role-based access control (RBAC)
- Permission system with 30+ granular permissions
- JWT authentication ready

### 📚 Standards Management
- Support for multiple compliance frameworks
- Hierarchical control structure (domains → controls → sub-controls)
- ISO 27001:2022, NIST CSF, SOC 2, CIS Controls support
- Version control for standards

### ❓ Question Bank
- Reusable question library
- Map questions to multiple controls across standards
- Likert scale, Yes/No, Text, and File upload question types
- Evidence tagging and guidance

### ✅ Assessment Management
- Create assessments based on compliance standards
- Assign questions to users/departments
- Track assessment progress
- Materialization of questions from standards

### 📊 Response Collection
- Collect responses with evidence attachments
- Response workflow (Draft → Submitted → Approved)
- Response versioning
- Comments and collaboration

### 🔍 Findings Management
- Track compliance gaps and issues
- Risk scoring and prioritization
- Remediation planning and tracking
- Finding lifecycle management

### 📈 Reporting & Analytics
- Compliance dashboards
- Real-time metrics and KPIs
- Trend analysis
- Executive summaries

## 🏗️ Architecture

```
grc_platform/
├── grc_platform/          # Django project settings
├── tenancy/               # Multi-tenant foundation
├── iam/                   # Identity & Access Management
├── standards/             # Compliance standards
├── question_bank/         # Question library
├── assessments/           # Assessment management
├── responses/             # Response collection
├── findings/              # Finding tracking
├── reporting/             # Dashboards & reports
├── orgs/                  # Organizations
├── evidence/              # Evidence management
├── policy/                # Policy management
├── notifications/         # Email notifications
└── auditlog/              # Audit trail
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ (for production)
- Git

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/grc-platform.git
   cd grc-platform
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server:**
   ```bash
   python manage.py runserver
   ```

8. **Access the application:**
   - Admin: http://localhost:8000/admin/
   - API: http://localhost:8000/api/

### Seed Initial Data (Optional)

```bash
python manage.py seed_initial_data
```

## 🎯 Core Modules

### 1. Tenancy Module (7 Models)
- **Tenant** - Multi-tenant foundation
- **Organization** - Organizations within tenant
- **BusinessUnit** - Business units/departments
- **SystemAsset** - IT assets and systems
- **Region** - Geographic regions
- **ScopeMapping** - Compliance scope definitions
- **ChangeLog** - Change tracking

### 2. IAM Module (5 Models)
- **AppUser** - Custom user model (extends AbstractUser)
- **Role** - User roles
- **Permission** - Granular permissions
- **RolePermission** - Role-permission mappings
- **UserRole** - User-role assignments

### 3. Standards Module (6 Models)
- **Standard** - Compliance standards (ISO 27001, NIST, etc.)
- **StandardVersion** - Version control
- **ControlNode** - Hierarchical control structure
- **ControlEvidence** - Evidence requirements
- **ControlRelationship** - Control dependencies
- **ControlSnapshot** - Historical versions

### 4. Question Bank Module (4 Models)
- **QuestionBank** - Reusable questions
- **QuestionBankOption** - Answer options
- **ControlQuestionMap** - Question-control mappings
- **QuestionApplicabilityRule** - Conditional logic

### 5. Assessments Module (8 Models)
- **Assessment** - Assessment instances
- **AssessmentScope** - Assessment scope
- **AssessmentQuestion** - Materialized questions
- **Assignment** - User assignments
- **AssessmentProgress** - Progress tracking
- **AssessmentEvidence** - Evidence collection
- **AssessmentComment** - Collaboration
- **AssessmentSnapshot** - Point-in-time capture

### 6. Responses Module (8 Models)
- **Response** - Answer submissions
- **ResponseEvidence** - Evidence attachments
- **ResponseComment** - Discussion threads
- **ResponseVersion** - Version history
- **ResponseApproval** - Approval workflow
- **EvidenceFile** - File storage
- **ResponseReview** - Review tracking
- **ResponseMetadata** - Additional data

### 7. Findings Module (6 Models)
- **Finding** - Compliance gaps
- **FindingSeverity** - Severity levels
- **RemediationPlan** - Fix plans
- **RemediationTask** - Action items
- **FindingComment** - Discussions
- **FindingHistory** - Audit trail

### 8. Reporting Module (4 Models)
- **Dashboard** - Custom dashboards
- **Report** - Generated reports
- **ReportSchedule** - Automated reports
- **Metric** - KPI tracking

## 🔌 API Endpoints

### Tenancy
- `GET/POST /api/tenancy/` - List/create tenants
- `GET/PUT/PATCH/DELETE /api/tenancy/{id}/` - Tenant detail

### IAM
- `POST /api/iam/register/` - User registration
- `POST /api/iam/login/` - User login
- `GET/POST /api/iam/users/` - User management
- `GET/POST /api/iam/roles/` - Role management
- `GET/POST /api/iam/permissions/` - Permission management

### Standards
- `GET/POST /api/standards/` - List/create standards
- `GET /api/standards/{id}/controls/` - Get controls for standard
- `POST /api/standards/import/` - Import standards from CSV

### Question Bank
- `GET/POST /api/question-bank/` - Question library
- `GET /api/question-bank/{id}/controls/` - Mapped controls
- `POST /api/question-bank/bulk-import/` - Bulk import

### Assessments
- `GET/POST /api/assessments/` - Assessment management
- `POST /api/assessments/{id}/materialize/` - Generate questions
- `GET /api/assessments/{id}/progress/` - Progress tracking

### Responses
- `GET/POST /api/responses/` - Response management
- `POST /api/responses/{id}/submit/` - Submit response
- `POST /api/responses/{id}/approve/` - Approve response

### Findings
- `GET/POST /api/findings/` - Finding management
- `POST /api/findings/{id}/remediate/` - Create remediation plan
- `PATCH /api/findings/{id}/close/` - Close finding

### Reporting
- `GET/POST /api/reporting/dashboards/` - Dashboard management
- `GET /api/reporting/metrics/` - Real-time metrics
- `POST /api/reporting/generate/` - Generate reports

## 🔐 Authentication

The platform supports multiple authentication methods:

1. **Session Authentication** (Django default)
   ```python
   # Login via admin or form
   ```

2. **JWT Authentication** (REST API)
   ```bash
   # Get token
   curl -X POST http://localhost:8000/api/iam/token/ \
     -d "username=admin&password=password"
   
   # Use token
   curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/assessments/
   ```

## 🎨 Technology Stack

- **Backend:** Django 4.2+
- **API:** Django REST Framework 3.14+
- **Database:** PostgreSQL 14+ (SQLite for development)
- **Authentication:** Django Auth + JWT
- **Filtering:** django-filter
- **CORS:** django-cors-headers
- **Web Server:** Gunicorn (production)
- **Static Files:** WhiteNoise

## 📦 Dependencies

```
Django>=4.2.0
djangorestframework>=3.14.0
django-filter>=23.0
django-cors-headers>=4.0.0
djangorestframework-simplejwt>=5.3.0
dj-database-url>=2.0.0
psycopg2-binary>=2.9.0
gunicorn>=21.0.0
whitenoise>=6.5.0
python-decouple>=3.8
```

## 🚂 Railway Deployment

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for complete deployment guide.

### Quick Deploy to Railway:

1. Push code to GitHub
2. Connect Railway to GitHub repository
3. Add PostgreSQL database
4. Configure environment variables
5. Deploy!

```bash
# Via Railway CLI
railway link
railway up
railway run python manage.py migrate
railway run python manage.py createsuperuser
```

## 🧪 Testing

### Run Tests

```bash
# All tests
python manage.py test

# Specific app
python manage.py test tenancy

# With coverage
coverage run --source='.' manage.py test
coverage report
```

### Smoke Tests

See [SMOKE_TEST.md](SMOKE_TEST.md) for comprehensive smoke testing guide.

```bash
# Quick smoke test
python manage.py check
python manage.py check --deploy
```

## 📚 Documentation

- [Railway Deployment Guide](RAILWAY_DEPLOYMENT.md)
- [Smoke Test Guide](SMOKE_TEST.md)
- [API Documentation](#) (Coming soon)
- [User Guide](#) (Coming soon)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🛠️ Development Roadmap

- [ ] API documentation with Swagger/ReDoc
- [ ] Frontend dashboard (React/Vue)
- [ ] Email notifications
- [ ] PDF report generation
- [ ] Advanced analytics
- [ ] Integration with SIEM tools
- [ ] Mobile app
- [ ] Automated compliance mapping

## 💡 Use Cases

- **Compliance Management** - Track compliance across ISO 27001, NIST, SOC 2
- **Risk Assessment** - Identify and mitigate security risks
- **Audit Preparation** - Prepare for external audits
- **Gap Analysis** - Find compliance gaps
- **Continuous Monitoring** - Track compliance over time
- **Evidence Management** - Centralize compliance evidence
- **Remediation Tracking** - Track remediation efforts

## 📊 System Requirements

### Minimum (Development):
- 2 CPU cores
- 4 GB RAM
- 10 GB storage
- Python 3.10+

### Recommended (Production):
- 4 CPU cores
- 8 GB RAM
- 50 GB storage
- PostgreSQL 14+
- Redis (for caching)

## 🔧 Configuration

### Environment Variables

```bash
# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=localhost,yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com

# Email (Optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password
```

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/YOUR_USERNAME/grc-platform/issues)
- **Discussions:** [GitHub Discussions](https://github.com/YOUR_USERNAME/grc-platform/discussions)
- **Email:** support@yourdomain.com

## 🙏 Acknowledgments

- Django Software Foundation
- Django REST Framework
- Railway.app
- All contributors

---

**Built with ❤️ for compliance professionals**

**⭐ Star this repo if you find it useful!**
