# Gem Search Frontend 💎

**React TypeScript frontend for the Gem Search application**

A modern, responsive web interface for searching and discovering web content with real-time full-text search capabilities.

## 🛠️ Tech Stack

- **React 18** - Modern React with hooks and functional components
- **TypeScript** - Type-safe JavaScript with enhanced developer experience  
- **Material-UI** - Comprehensive React component library
- **Create React App** - Zero-configuration build setup

## 🚀 Development

### Prerequisites
- **Node.js 18+**
- **npm** (comes with Node.js)

### Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm start
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

The development server features:
- 🔄 **Hot reload** - Automatic page refresh on code changes
- 🐛 **Error overlay** - Helpful error messages in the browser
- 🎯 **Fast refresh** - Preserve component state during edits

### Available Scripts

| Command | Description |
|---------|-------------|
| `npm start` | Start development server at http://localhost:3000 |
| `npm test` | Run tests in interactive watch mode |
| `npm run build` | Build optimized production bundle |
| `npm run eject` | Eject from Create React App (⚠️ irreversible) |

## 📁 Project Structure

```
frontend/src/
├── components/           # Reusable UI components
│   ├── SearchBar.tsx    # Search input component
│   └── SearchResults.tsx # Results display component
├── containers/          # Container components with business logic
│   └── SearchContainer.tsx # Main search orchestration
├── api/                # API integration layer
│   └── SearchAPI.ts    # Backend API communication
├── App.tsx             # Root application component
└── index.tsx           # Application entry point
```

## 🔌 API Integration

The frontend communicates with the FastAPI backend through a clean API layer:

```typescript
// Example API usage
import { searchContent } from './api/SearchAPI';

const results = await searchContent('artificial intelligence');
```

### Backend Connection
- **Development**: `http://localhost:8000` (FastAPI dev server)
- **Production**: Configure backend URL in deployment

## 🎨 UI Components

### SearchBar
- Real-time search input with debouncing
- Keyboard shortcuts and accessibility
- Loading states and error handling

### SearchResults  
- Paginated results display
- Relevance scoring visualization
- Responsive card-based layout

### SearchContainer
- Orchestrates search flow and state management
- Handles API communication and error states
- Manages search history and preferences

## 📱 Responsive Design

- **Mobile-first** approach with Material-UI breakpoints
- **Touch-friendly** interface with appropriate sizing
- **Accessible** design following WCAG guidelines

## 🧪 Testing

```bash
# Run tests in watch mode
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in CI mode  
npm test -- --watchAll=false
```

### Testing Strategy
- **Component tests** - Render and interaction testing
- **Integration tests** - API communication testing
- **Accessibility tests** - Screen reader and keyboard navigation

## 🚀 Production Build

```bash
# Create optimized production build
npm run build
```

This creates a `build/` directory with:
- ⚡ **Minified and optimized** JavaScript and CSS
- 📦 **Code splitting** for optimal loading performance  
- 🗜️ **Gzipped assets** for minimal transfer size
- 📄 **Static files** ready for deployment

### Deployment Options
- **Static hosting**: Vercel, Netlify, GitHub Pages
- **CDN**: AWS CloudFront, Cloudflare
- **Traditional hosting**: Apache, Nginx

## ⚙️ Configuration

### Environment Variables
Create `.env.local` for local development:
```bash
REACT_APP_API_URL=http://localhost:8000
```

### Build Optimization
The build process automatically:
- 🗜️ Minifies code for production
- 📦 Splits code into optimal chunks  
- 🖼️ Optimizes images and assets
- 📋 Generates service worker for caching

## 🔧 Development Tips

### Hot Reload
Changes to components trigger automatic browser refresh while preserving state.

### Error Handling  
Development mode shows helpful error overlays with:
- Stack traces with source mapping
- Compilation errors with file locations
- Runtime errors with component stack

### Debugging
Use React Developer Tools browser extension for:
- Component tree inspection
- Props and state debugging  
- Performance profiling

## 📚 Learn More

- [React Documentation](https://reactjs.org/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Material-UI Documentation](https://mui.com/)
- [Create React App Documentation](https://create-react-app.dev/)

## 🤝 Contributing

1. Follow existing code style and TypeScript patterns
2. Add tests for new components and features
3. Ensure responsive design works across devices
4. Test accessibility with screen readers

---

**Part of the Gem Search project** - Building modern web search experiences.