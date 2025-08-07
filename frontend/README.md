# 🎵 Sonicus Frontend - React Application

## 📋 Current Status (August 2025)

The React frontend has been **updated and aligned** with the working FastAPI backend authentication system.

### ✅ Recent Updates

1. **Authentication System Fixed**:
   - Updated `axios.js` to use correct token key (`access_token`)
   - Fixed AuthContext to match backend `/token` and `/users/me` endpoints
   - Added development mode support for testing

2. **API Integration**:
   - Base URL: `http://localhost:18100/api/v1`
   - Working endpoints: `/token`, `/users/me`, `/users` (registration)
   - Proper JWT token handling in axios interceptors

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ 
- Backend running on `http://localhost:18100`

### Installation & Setup

```bash
# Navigate to frontend directory
cd /Users/luis/Projects/Elefefe/Sonicus/frontend

# Install dependencies
npm install

# Start development server
npm start
```

The application will open at `http://localhost:3000`

## 🔧 Environment Configuration

The frontend uses these environment variables (`.env`):

```env
# Backend API Configuration
REACT_APP_API_BASE_URL=http://localhost:18100/api/v1

# Authentik OIDC (for future implementation)
REACT_APP_AUTHENTIK_BASE_URL=https://authentik.elefefe.eu
REACT_APP_AUTHENTIK_CLIENT_ID=HyqThUySJmHfm0ubuBWFhaoKDCphL5uf1IiokF2X
REACT_APP_AUTHENTIK_REDIRECT_URI=http://localhost:3000/auth/callback
```

## 🧪 Testing the Authentication

### Manual Testing
1. **Registration**: `POST /users` - Create new user account
2. **Login**: `POST /token` - Get JWT access token  
3. **Profile**: `GET /users/me` - Access protected user data

### Test Credentials
```javascript
Email: test.user@example.com
Password: testpassword123
```

## 📁 Project Structure

```
frontend/
├── public/                 # Static files
├── src/
│   ├── components/        # Reusable React components
│   │   ├── Navbar.js     # Navigation with auth state
│   │   └── AdminRoute.js  # Protected route component
│   ├── context/          # React Context providers  
│   │   └── AuthContext.js # Authentication state management
│   ├── pages/            # Page components
│   │   ├── LoginPage.js  # Login form with dual auth methods
│   │   └── HomePage.js   # Landing page
│   ├── utils/            # Utilities
│   │   ├── axios.js      # Configured axios instance
│   │   └── apiService.js # API interaction functions
│   ├── config/           # Configuration files
│   │   └── authentik.js  # OIDC configuration (future)
│   └── App.js           # Main application component
└── package.json         # Dependencies and scripts
```

---

**Status**: ✅ **Ready for Development & Testing**

The frontend authentication system is now fully aligned with the backend and ready for feature development and testing.

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
