import express from 'express';
import bodyParser from 'body-parser';
import cors from 'cors';
import dotenv from 'dotenv';

import chatRoutes from './routes/chatRoutes.js';
import tekmetricsRoutes from './routes/tekmetricsRoutes.js';

dotenv.config();

const app = express();

// Configure CORS options
const corsOptions = {
  origin: 'http://veteranvehiclerepair.com', // Replace with your actual WordPress domain
  optionsSuccessStatus: 200
};

app.use(cors(corsOptions));
app.use(bodyParser.json());

app.use('/api/chat', chatRoutes);
app.use('/api/tekmetrics', tekmetricsRoutes);

// Add a root route to verify the server is running
app.get('/', (req, res) => {
  res.send('Server is running');
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
