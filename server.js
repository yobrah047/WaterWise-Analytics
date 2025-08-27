// Import required Node.js modules
const express = require('express'); // Web framework for Node.js
const bodyParser = require('body-parser'); // Parse incoming request bodies
const { Pool } = require('pg'); // PostgreSQL client
const bcrypt = require('bcryptjs'); // Password hashing
const session = require('express-session'); // Session management
const pgSession = require('connect-pg-simple')(session); // Session store for PostgreSQL
const { spawn } = require('child_process'); // Spawn Python processes
const path = require('path'); // Handle file paths

// Initialize Express app
const app = express();
const port = 3000; // Server port

// Configure PostgreSQL connection pool
const pool = new Pool({
  user: "postgres", // Database user
  host: "localhost", // Database host
  database: "waterwise_analytics", // Database name
  password: "karani047", // Database password
  port: 5432, // Database port
});

// Middleware setup
app.use(bodyParser.json()); // Parse JSON request bodies
app.use(bodyParser.urlencoded({ extended: true })); // Parse URL-encoded form data
app.use(express.static('public')); // Serve static files (HTML, JS, CSS) from 'public' folder

// Configure session management with PostgreSQL store
app.use(
  session({
    store: new pgSession({ 
      pool, // Use the PostgreSQL pool
      tableName: 'user_sessions', // Table for storing sessions
      createTableIfMissing: true // Create table if it doesn't exist
    }),
    secret: "waterwise_secret", // Secret for signing session cookies
    resave: false, // Don't resave session if unmodified
    saveUninitialized: false, // Don't create session until something is stored
    cookie: { 
      maxAge: 30 * 24 * 60 * 60 * 1000, // Cookie expires after 30 days
      httpOnly: true, // Prevent client-side JS access to cookies
      sameSite: 'strict', // Mitigate CSRF attacks
      secure: process.env.NODE_ENV === 'production' // Use secure cookies in production
    },
    name: 'waterwise.sid' // Custom cookie name
  })
);

// 🧪 Route to clear user session
app.get("/clear-session", (req, res) => {
  req.session.destroy(() => { // Destroy the session
    res.send("Session cleared, please refresh the page.");
  });
});

// 🔐 Root route to serve authentication page
app.get("/", (req, res) => {
  console.log("Session Data:", req.session); // Debug session data
  res.sendFile(path.join(__dirname, "public", "auth.html")); // Serve auth.html
});

// Route to serve results page
app.get("/results", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "results.html")); // Serve results.html
});

// 🔐 User registration endpoint
app.post("/api/register", async (req, res, next) => {
  const { name, email, password, confirmPassword } = req.body;
  // Check if passwords match
  if (password !== confirmPassword) {
    const error = new Error("Passwords do not match");
    error.status = 400;
    return next(error);
  }

  try {
    // Hash password with bcrypt
    const hashedPassword = await bcrypt.hash(password, 10);
    // Insert user into database
    await pool.query(
      "INSERT INTO users (name, email, password) VALUES ($1, $2, $3)",
      [name, email, hashedPassword]
    );
    res.json({ success: true }); // Respond with success
  } catch (err) {
    next(err); // Pass errors to error handler
  }
});

// 🔐 User login endpoint
app.post("/api/login", async (req, res, next) => {
  const { email, password } = req.body;
  try {
    // Query user by email
    const result = await pool.query("SELECT * FROM users WHERE email = $1", [email]);
    const user = result.rows[0];

    // Check if user exists
    if (!user) {
      const error = new Error("User not found");
      error.status = 400;
      return next(error);
    }

    // Verify password
    const valid = await bcrypt.compare(password, user.password);
    if (!valid) {
      const error = new Error("Invalid password");
      error.status = 401;
      return next(error);
    }

    // Set user ID in session
    req.session.userId = user.id;
    res.json({
      success: true,
      redirectUrl: "/instructions.html" // Redirect to instructions page
    });
  } catch (err) {
    next(err); // Pass errors to error handler
  }
});

// 🔓 User logout endpoint
app.get("/api/logout", (req, res, next) => {
  req.session.destroy((err) => { // Destroy session
    if (err) {
      return next(err);
    }
    res.json({ success: true }); // Respond with success
  });
});

// 🧪 Water test submission endpoint (protected)
app.post("/submit", async (req, res, next) => {
  // Check if user is authenticated
  if (!req.session.userId) {
    const error = new Error("Unauthorized");
    error.status = 401;
    return next(error);
  }

  const data = req.body; // Get form data
  console.log("Received data for prediction:", data);

  // Define required fields for water test
  const requiredFields = [
    "ph", "turbidity", "temperature", "conductivity", "oxygen",
    "salinity", "tds", "hardness", "alkalinity", "chlorine",
    "total_coliforms", "e_coli"
  ];

  // Validate required fields
  for (const field of requiredFields) {
    if (data[field] === undefined || data[field] === null || data[field] === '') {
      const error = new Error(`Missing or empty required field: ${field}`);
      error.status = 400;
      return next(error);
    }
    // Ensure field is a valid number
    if (isNaN(parseFloat(data[field]))) {
      const error = new Error(`Invalid number for field: ${field}`);
      error.status = 400;
      return next(error);
    }
  }

  // Prepare data for Python prediction script
  const dataForPrediction = [
    '--pH', parseFloat(data.ph),
    '--turbidity', parseFloat(data.turbidity),
    '--temperature', parseFloat(data.temperature),
    '--conductivity', parseFloat(data.conductivity),
    '--dissolved_oxygen', parseFloat(data.oxygen),
    '--salinity', parseFloat(data.salinity),
    '--total_dissolved_solids', parseFloat(data.tds),
    '--hardness', parseFloat(data.hardness),
    '--alkalinity', parseFloat(data.alkalinity),
    '--chlorine', parseFloat(data.chlorine),
    '--total_coliforms', parseFloat(data.total_coliforms),
    '--e_coli', parseFloat(data.e_coli)
  ];

  // Spawn Python process for prediction
  console.log('Spawning Python process with args:', ['predict.py', ...dataForPrediction]);
  const pythonProcess = spawn('python', ['predict.py', ...dataForPrediction]);

  let pythonOutput = ''; // Store Python script output
  let pythonError = ''; // Store Python script errors

  // Capture Python script output
  pythonProcess.stdout.on('data', (data) => {
    pythonOutput += data.toString();
  });

  // Capture Python script errors
  pythonProcess.stderr.on('data', (data) => {
    pythonError += data.toString();
  });

  // Handle Python script completion
  pythonProcess.on('close', async (code) => {
    if (code !== 0) {
      // Log error if Python script fails
      console.error(`Python script exited with code ${code}, stdout: ${pythonOutput}, stderr: ${pythonError}`);
      return res.status(500).json({ error: 'Error during model prediction', details: pythonOutput });
    }

    try {
      // Parse Python script output
      const resultFromPython = JSON.parse(pythonOutput);

      // Send prediction result to client
      res.status(200).json(resultFromPython);

      // SQL query to insert water test data into database
      const query = `
        INSERT INTO water_tests (
            location, test_date, ph_level, turbidity, temperature,
            electrical_conductivity, dissolved_oxygen, salinity,
            total_dissolved_solids, hardness, alkalinity, chlorine,
            total_coliforms, e_coli, water_source, additional_notes
          ) VALUES (
            $1, $2, $3, $4, $5,
            $6, $7, $8,
            $9, $10, $11, $12,
            $13, $14, $15, $16
          ) RETURNING id;
        `;

      // Insert data into database
      const values = [...Object.values(data)];
      await pool.query(query, values);
    } catch (error) {
      console.error('Error:', error);
      next(error); // Pass errors to error handler
    }
  }); 
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack); // Log error stack
  const status = err.status || 500; // Default to 500 if no status
  res.status(status).json({ error: err.message || 'Internal Server Error' });
});

// Start the server
app.listen(port, () => {
  console.log(`🚀 Server running at http://localhost:${port}`);
});