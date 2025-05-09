const express = require('express');
const bodyParser = require('body-parser');
const { Pool } = require('pg');
const bcrypt = require('bcryptjs');
const session = require('express-session');
const pgSession = require('connect-pg-simple')(session);
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const port = 3000;

// PostgreSQL connection
const pool = new Pool({
  user: "postgres",
  host: "localhost",
  database: "waterwise_analytics",
  password: "karani047",
  port: 5432,
});

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true })); // for form submissions
app.use(express.static('public')); // serve auth.html, index.html, form.js, etc.

app.use(
  session({
    store: new pgSession({ 
      pool,
      tableName: 'user_sessions',
      createTableIfMissing: true
    }),
    secret: "waterwise_secret",
    resave: false,
    saveUninitialized: false,
    cookie: { 
      maxAge: 30 * 24 * 60 * 60 * 1000, // 30 days
      httpOnly: true,
      sameSite: 'strict',
      secure: process.env.NODE_ENV === 'production'
    },
    name: 'waterwise.sid'
  })
);

// 🧪 Clear session route
app.get("/clear-session", (req, res) => {
  req.session.destroy(() => {
    res.send("Session cleared, please refresh the page.");
  });
});

// 🔐 Entry route
app.get("/", (req, res) => {
  console.log("Session Data:", req.session);  // Log the session data for debugging
  res.sendFile(path.join(__dirname, "public", "auth.html"));
});

// Route to serve results.html
app.get("/results", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "results.html"));
});

// 🔐 Register endpoint
app.post("/api/register", async (req, res, next) => {
  const { name, email, password, confirmPassword } = req.body;
  if (password !== confirmPassword) {
    const error = new Error("Passwords do not match");
    error.status = 400;
    return next(error);
  }

  try {
    const hashedPassword = await bcrypt.hash(password, 10);
    await pool.query(
      "INSERT INTO users (name, email, password) VALUES ($1, $2, $3)",
      [name, email, hashedPassword]
    );
    res.json({ success: true });
  } catch (err) {
    next(err);
  }
});

// 🔐 Login endpoint
app.post("/api/login", async (req, res, next) => {
  const { email, password } = req.body;
  try {
    const result = await pool.query("SELECT * FROM users WHERE email = $1", [email]);
    const user = result.rows[0];

    if (!user) {
      const error = new Error("User not found");
      error.status = 400;
      return next(error);
    }

    const valid = await bcrypt.compare(password, user.password);
    if (!valid) {
      const error = new Error("Invalid password");
      error.status = 401;
      return next(error);
    }

    req.session.userId = user.id;
    res.json({ success: true });
  } catch (err) {
    next(err);
  }
});

// 🔓 Logout endpoint
app.get("/api/logout", (req, res, next) => {
  req.session.destroy((err) => {
    if (err) {
      return next(err);
    }
    res.json({ success: true });
  });
});






// 🧪 Protected water test submission
app.post("/submit", async (req, res, next) => {
  if (!req.session.userId) {
    const error = new Error("Unauthorized");
    error.status = 401;
    return next(error);
  }

  const data = req.body; // Get form data
  console.log("Received data for prediction:", data);

  // Validate required fields
  const requiredFields = [
    "ph",
    "turbidity",
    "temperature",
    "conductivity",
    "oxygen",
    "salinity",
    "tds",
    "hardness",
    "alkalinity",
    "chlorine",
    "total_coliforms",
    "e_coli"
  ];

  for (const field of requiredFields) {
    if (data[field] === undefined || data[field] === null || data[field] === '') {
      const error = new Error(`Missing or empty required field: ${field}`);
      error.status = 400;
      return next(error);
    }
    // Validate that the field can be converted to a float
    if (isNaN(parseFloat(data[field]))) {
      const error = new Error(`Invalid number for field: ${field}`);
      error.status = 400;
      return next(error);
    }
  }

 // Prepare data for Python script
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


  // Spawn Python process
  console.log('Spawning Python process with args:', ['predict.py', ...dataForPrediction]);
  const pythonProcess = spawn('python', ['predict.py', ...dataForPrediction]);

  let pythonOutput = '';
  let pythonError = '';

  pythonProcess.stdout.on('data', (data) => {
    pythonOutput += data.toString();
  });

  pythonProcess.stderr.on('data', (data) => {
    pythonError += data.toString();
  });

  pythonProcess.on('close', async (code) => {
    if (code !== 0) {
      console.error(`Python script exited with code ${code}, stdout: ${pythonOutput}, stderr: ${pythonError}`);
      return res.status(500).json({ error: 'Error during model prediction', details: pythonOutput });
    }

    try {
      const resultFromPython = JSON.parse(pythonOutput);

      // Send result back to the front end
      res.status(200).json(resultFromPython);

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

      const values = [...Object.values(data)];
      await pool.query(query, values);
    } catch (error) {
      console.error('Error:', error);
      next(error);
    }
  }); 
});

app.use((err, req, res, next) => {
  console.error(err.stack);
  const status = err.status || 500;
  res.status(status).json({ error: err.message || 'Internal Server Error' });
});

app.listen(port, () => {
  console.log(`🚀 Server running at http://localhost:${port}`);
});
