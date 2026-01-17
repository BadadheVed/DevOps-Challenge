import express, { Request, Response, NextFunction } from 'express';
import client from 'prom-client';

const app = express();
const PORT = 3000;

// Create a Registry to register the metrics
const register = new client.Registry();

// Add a default label which can be used to identify metrics
register.setDefaultLabels({
  app: 'monitoring-app'
});

// Enable the collection of default metrics
client.collectDefaultMetrics({ register });

// Create custom metrics
const httpRequestDurationMicroseconds = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.1, 0.3, 0.5, 0.7, 1, 3, 5, 7, 10]
});

const httpRequestsTotal = new client.Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status_code']
});

// Register the custom metrics
register.registerMetric(httpRequestDurationMicroseconds);
register.registerMetric(httpRequestsTotal);

// Middleware to collect metrics
app.use((req: Request, res: Response, next: NextFunction) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    const route = req.route ? req.route.path : req.path;
    
    httpRequestsTotal
      .labels(req.method, route, res.statusCode.toString())
      .inc();
    
    httpRequestDurationMicroseconds
      .labels(req.method, route, res.statusCode.toString())
      .observe(duration);
  });
  
  next();
});

// Metrics endpoint
app.get('/metrics', async (req: Request, res: Response) => {
  try {
    res.set('Content-Type', register.contentType);
    res.end(await register.metrics());
  } catch (error) {
    res.status(500).end((error as Error).message);
  }
});

// Basic routes for testing
app.get('/', (req: Request, res: Response) => {
  res.json({ 
    message: 'Monitoring app is running!', 
    timestamp: new Date().toISOString() 
  });
});

app.get('/health', (req: Request, res: Response) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString() 
  });
});

app.get('/api/test', (req: Request, res: Response) => {
  // Simulate some processing time
  
    res.json({ 
      message: 'Test endpoint', 
      data: Math.random() 
    });
  
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
