# 🎓 University Data Visualization Dashboard

Django REST Framework + Next.js 14 기반 대학교 데이터 시각화 대시보드

[![Django](https://img.shields.io/badge/Django-5.0.7-green.svg)](https://www.djangoproject.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2.5-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-blue.svg)](https://www.typescriptlang.org/)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](./backend/dashboard/tests/)

Excel 파일을 업로드하여 데이터를 시각화하고 분석하는 대시보드입니다.

## Tech Stack

### Backend
- Django 5.0.7 + Django REST Framework
- PostgreSQL (Railway)
- Python 3.11.9

### Frontend
- Next.js 14 (App Router)
- TypeScript
- TanStack Table (테이블 관리)
- TanStack Form (폼 관리)
- Recharts (차트 시각화)
- Tailwind CSS (스타일링)

### Deployment
- Railway (Backend + Frontend + Database)

## Project Structure

```
Final/
├── backend/          # Django REST API
│   ├── config/      # Django settings
│   ├── dashboard/   # Main app
│   ├── manage.py
│   └── requirements.txt
├── frontend/        # Next.js application
│   ├── app/         # App Router pages
│   ├── components/  # React components
│   ├── lib/         # Utilities
│   └── package.json
├── docs/            # Documentation
├── .moai/           # MoAI-ADK configuration
└── README.md
```

## Getting Started

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Environment Variables

### Backend (.env)

```env
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)

```env
API_URL=http://localhost:8000
```

## ✨ Features

### 📤 데이터 업로드
- Excel 파일 (.xlsx, .xls) 업로드
- 드래그 앤 드롭 지원
- 파일 유효성 검사 (형식, 크기)
- 자동 데이터 파싱 및 저장

### 📊 데이터 관리
- TanStack Table로 강력한 테이블 기능
- 정렬, 필터링, 검색
- 페이지네이션 (10/20/50/100개씩 보기)
- 동적 컬럼 생성

### 📈 데이터 시각화
- 4가지 차트 타입: 막대, 선, 영역, 파이
- Recharts 기반 인터랙티브 차트
- 필드 매핑 및 데이터 집계
- 반응형 차트 디자인

### 🎨 UI/UX
- Next.js 14 App Router
- Tailwind CSS 스타일링
- 완전 반응형 디자인
- 로딩/에러 상태 관리

### 🔒 백엔드 API
- Django REST Framework
- RESTful API 설계
- PostgreSQL 데이터베이스
- CORS 설정

### ✅ 테스팅
- Backend: pytest (16개 테스트, 100% 통과)
- Frontend: vitest (유틸리티 함수 테스트)
- 모델, API, 파일 업로드 테스트

## 📸 Screenshots

### 대시보드 홈
통계 카드, 카테고리 분포, 최근 업로드 데이터셋

### 데이터셋 목록
TanStack Table로 정렬, 검색, 페이지네이션

### 데이터 분석
Recharts로 막대/선/영역/파이 차트

### 파일 업로드
드래그 앤 드롭, 파일 미리보기, 진행률 표시

## 🚀 Deployment

자세한 배포 가이드는 [DEPLOYMENT.md](./DEPLOYMENT.md)를 참조하세요.

### Railway (백엔드)

```bash
# 1. Railway 프로젝트 생성
# 2. PostgreSQL 데이터베이스 추가
# 3. 환경 변수 설정
# 4. Git push로 자동 배포
```

### Vercel (프론트엔드)

```bash
# 1. Vercel 프로젝트 생성
# 2. GitHub 저장소 연결
# 3. 환경 변수 설정 (NEXT_PUBLIC_API_URL)
# 4. 자동 배포
```

## 📝 Testing

### Backend Tests

```bash
cd backend
pytest dashboard/tests/ -v
# 16 passed in 3.54s
```

### Frontend Tests

```bash
cd frontend
npm run test
# All utility tests passing
```

## 📚 API Documentation

### Endpoints

- `GET /api/datasets/` - 데이터셋 목록
- `POST /api/datasets/` - 데이터셋 생성 (파일 업로드)
- `GET /api/datasets/{id}/` - 데이터셋 상세
- `DELETE /api/datasets/{id}/` - 데이터셋 삭제
- `GET /api/datasets/{id}/records/` - 레코드 조회
- `GET /api/records/` - 전체 레코드
- `GET /api/statistics/overview/` - 대시보드 통계

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details

## 👨‍💻 Author

Built with MoAI-ADK Alfred SuperAgent

---

**⭐ If you like this project, please give it a star!**
