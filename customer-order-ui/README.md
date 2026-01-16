# Customer Order UI

A modern, responsive web application for customers to design and order custom products in the Universal Factory Simulation Platform. This Angular-based frontend provides an intuitive interface for product customization with AI-powered design generation.

## 🎯 Purpose

The Customer Order UI serves as the customer-facing interface for the factory simulation platform, allowing users to:

- **Design Custom Products**: Describe desired products using natural language
- **AI-Powered Design Generation**: Automatically generate product designs using AI image generation
- **Real-time Order Placement**: Submit orders that integrate with the factory's production workflow
- **Factory Monitoring**: View live production status and machine operations

## 🚀 Features

### Core Functionality
- **Product Description Input**: Text-based product specification
- **AI Image Generation**: Integration with Pollinations.ai for design creation
- **Order Management**: Submit orders to the factory production system
- **Live Factory Monitoring**: Direct access to machine observation interface

### Technical Features
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Material UI Components**: Professional Angular Material design system
- **Real-time Updates**: Live status indicators and progress tracking
- **Error Handling**: Comprehensive error states and user feedback
- **Rate Limiting**: Built-in handling for API limits with retry logic

## 🏗️ Architecture

### Frontend (Angular)
- **Framework**: Angular 19 with standalone components
- **UI Library**: Angular Material + Tailwind CSS
- **State Management**: Component-based state with RxJS
- **API Communication**: HTTP client with RESTful backend integration

### Backend Integration
- **Flask API**: Python backend for order processing and AI proxy
- **MQTT Integration**: Real-time communication with factory orchestrator
- **Database**: PostgreSQL/TimescaleDB for order and telemetry persistence

### Deployment
- **Development**: Angular CLI development server
- **Production**: Docker container with Nginx serving static files
- **Environment Configuration**: Runtime environment variable injection

## 📋 Prerequisites

- Node.js 20+
- npm or yarn
- Docker (for containerized deployment)
- Access to factory simulation backend API

## 🛠️ Installation & Setup

### Local Development

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Environment Configuration**
   Create/update `src/environments/environment.ts`:
   ```typescript
   export const environment = {
     production: false,
     apiUrl: 'http://localhost:5001' // Backend API URL
   };
   ```

3. **Start Development Server**
   ```bash
   npm start
   ```
   Navigate to `http://localhost:4200/`

### Docker Deployment

1. **Build and Run**
   ```bash
   # Set API_URL environment variable
   export API_URL=http://your-backend-api:5001

   # Build and run with Docker Compose
   docker-compose up --build
   ```

2. **Access Application**
   Open `http://localhost:4200` in your browser

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_URL` | Backend API endpoint URL | `localhost:5001` |

### Build Configuration

The application supports multiple build configurations:

- **Development**: `ng build --configuration development`
- **Production**: `ng build --configuration production`

## 📖 Usage Guide

### Designing a Product

1. **Access the Application**
   Open the Customer Order UI in your web browser

2. **Describe Your Product**
   Enter a detailed description of your desired product in the text field

3. **Generate Design**
   Click "Generate AI Design" to create a visual representation using AI

4. **Review and Place Order**
   - Review the generated design
   - Click "Place Order" to submit to the factory
   - Monitor production progress if desired

### Monitoring Production

- Click "Observe Machines" to access the live factory monitoring interface
- View real-time machine status, sensor data, and production progress

## 🔌 API Integration

### Backend Endpoints

The UI communicates with the following backend services:

- `GET /factory-config` - Retrieve factory configuration
- `POST /proxy-image` - Generate AI images via proxy
- `POST /order` - Place production orders

### MQTT Topics

Orders are published to MQTT topics for factory processing:
- `factory/{site_id}/production/request` - Production order requests

## 🧪 Testing

### Unit Tests
```bash
npm test
```

### End-to-End Tests
```bash
npm run e2e
```

## 🐳 Docker Configuration

### Container Structure

- **Build Stage**: Node.js container compiles Angular application
- **Runtime Stage**: Nginx serves static files with environment injection
- **Entry Point**: Runtime script sets environment variables

### Docker Compose Services

```yaml
services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "4200:80"
    environment:
      - API_URL=localhost:5001
```

## 🔒 Security Considerations

- API requests include proper CORS handling
- Environment variables prevent hardcoded sensitive data
- Rate limiting implemented for AI generation requests
- Input validation on all user-submitted data

## 🚨 Error Handling

The application includes comprehensive error handling for:

- **API Rate Limits**: Automatic retry with exponential backoff
- **Network Failures**: User-friendly error messages
- **Image Loading**: Fallback states for failed image generation
- **Invalid Input**: Form validation with immediate feedback

## 📊 Performance

- **Lazy Loading**: Components loaded on demand
- **Image Optimization**: AI-generated images cached and optimized
- **Bundle Splitting**: Angular's built-in code splitting
- **Caching**: HTTP interceptors for request caching

## 🤝 Contributing

1. Follow Angular style guide and best practices
2. Use conventional commit messages
3. Include unit tests for new features
4. Update documentation for API changes

## 📝 License

This project is part of the Universal Factory Simulation Platform. See root project LICENSE for details.

## 🆘 Troubleshooting

### Common Issues

**Application won't load**
- Check API_URL environment variable
- Verify backend service is running
- Check browser console for errors

**AI image generation fails**
- Backend proxy service may be unavailable
- Check API rate limits
- Verify internet connectivity

**Orders not processing**
- Check MQTT broker connectivity
- Verify factory orchestrator is running
- Check backend logs for errors

### Debug Mode

Enable debug logging by setting:
```typescript
// In environment.ts
export const environment = {
  production: false,
  debug: true
};
```

## 📚 Related Documentation

- [Universal Factory Platform README](../README.md)
- [Factory Configuration Guide](../docs/CREATE_NEW_FACTORY.md)
- [API Documentation](../docs/ARCHITECTURE.md)
- [How to Use Guide](../docs/HOW_TO_USE.md)

```bash
ng e2e
```

Angular CLI does not come with an end-to-end testing framework by default. You can choose one that suits your needs.

## Additional Resources

For more information on using the Angular CLI, including detailed command references, visit the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.
