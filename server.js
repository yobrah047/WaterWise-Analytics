const express = require('express');
const bodyParser = require('body-parser');
const { Pool } = require('pg');
const bcrypt = require('bcryptjs');
const session = require('express-session');
const pgSession = require('connect-pg-simple')(session);
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

// 🧪 Clear session route (make sure this is defined before the other routes)
app.get("/clear-session", (req, res) => {
  req.session.destroy(() => {
    res.send("Session cleared, please refresh the page.");
  });
});

// 🔐 Entry route
app.get("/", (req, res) => {
  console.log("Session Data:", req.session);  // Log the session data for debugging
    // Always serve auth.html for the root URL
    res.sendFile(path.join(__dirname, "public", "auth.html"));
});

// 🔐 Register endpoint
app.post("/api/register", async (req, res, next) => {
  const { name, email, password, confirmPassword } = req.body;
  if (password !== confirmPassword) {
    const error = new Error("Passwords do not match");
    error.status = 400;
    return next(error); // Pass error to the error handling middleware
  }

  try {
    const hashedPassword = await bcrypt.hash(password, 10);
    await pool.query(
      "INSERT INTO users (name, email, password) VALUES ($1, $2, $3)",
      [name, email, hashedPassword]
    );
    res.json({ success: true });
  } catch (err) {
    next(err); // Pass any error to the error handling middleware
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
      return next(error); // Pass error to the error handling middleware
    }

    const valid = await bcrypt.compare(password, user.password);
    if (!valid) {
      const error = new Error("Invalid password");
      error.status = 401;
      return next(error); // Pass error to the error handling middleware
    }

    req.session.userId = user.id;
    res.json({ success: true });
  } catch (err) {
    next(err); // Pass any error to the error handling middleware
  }
});

// 🔓 Logout endpoint
app.get("/api/logout", (req, res, next) => {
  req.session.destroy((err) => {
    if (err) {
      return next(err); // Pass logout errors to the error handling middleware
    }
    res.json({ success: true });
  });
});

// 🧪 Protected water test submission
app.post("/submit", async (req, res, next) => {
  if (!req.session.userId) {
    const error = new Error("Unauthorized");
    error.status = 401;
    return next(error); // Pass error to the error handling middleware
  }

  const data = req.body;
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

  const values = [
    data.location,
    data.date,
    data.ph,
    data.turbidity,
    data.temperature,
    data.conductivity,
    data.oxygen,
    data.salinity,
    data.tds,
    data.hardness,
    data.alkalinity,
    data.chlorine,
    data.total_coliforms,
    data.e_coli,
    data.water_source,
    data.notes,
  ];

  try {
    const result = await pool.query(query, values);
    res.status(200).json({ message: "Data inserted", testId: result.rows[0].id });
  } catch (error) {
    next(error); // Pass any error to the error handling middleware
  }
});

// Global Error Handler
app.use((err, req, res, next) => {
  console.error(err.stack);  // Log the error stack for debugging

  // If error has a status property, use it. Otherwise, set a 500 default.
  const status = err.status || 500;
  res.status(status).json({ error: err.message || 'Internal Server Error' });
});

app.listen(port, () => {
  console.log(`🚀 Server running at http://localhost:${port}`);
});
