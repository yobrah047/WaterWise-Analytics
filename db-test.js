// Load environment variables from .env file
require("dotenv").config();

// Import the Pool class from the 'pg' module
const { Pool } = require("pg");

// Set up PostgreSQL connection using environment variables
const pool = new Pool({
  connectionString: process.env.DATABASE_URL, // Connection string from environment variable
  // Disable SSL if running on localhost, otherwise use SSL with rejectUnauthorized set to false
  ssl: process.env.DATABASE_URL.includes("localhost") ? false : { rejectUnauthorized: false },
});

async function testInsert() {
    const sampleData = {
        location: "Test River",
        test_date: new Date(),
        ph_level: 7.0,
        turbidity: 1.2,
        temperature: 23.5,
        electrical_conductivity: 400,
        dissolved_oxygen: 6.0,
        salinity: 0.2,
        total_dissolved_solids: 450,
        hardness: 120,
        alkalinity: 85,
        chlorine: 0.3, //
        coliform_bacteria: "No", //
        //
        water_source: "Spring",
        additional_notes: "Test insert via script"
    };

    const query = `
        INSERT INTO water_tests (
            location, test_date, ph_level, turbidity, temperature,
            electrical_conductivity, dissolved_oxygen, salinity,
            total_dissolved_solids, hardness, alkalinity, chlorine,
            coliform_bacteria, water_source, additional_notes
        )
        VALUES (
            $1, $2, $3, $4, $5,
            $6, $7, $8,
            $9, $10, $11, $12,
            $13, $14, $15
        ) RETURNING id;
    `;

    const values = [
        sampleData.location,
        sampleData.test_date,
        sampleData.ph_level,
        sampleData.turbidity,
        sampleData.temperature,
        sampleData.electrical_conductivity,
        sampleData.dissolved_oxygen,
        sampleData.salinity,
        sampleData.total_dissolved_solids,
        sampleData.hardness,
        sampleData.alkalinity,
        sampleData.chlorine,
        sampleData.coliform_bacteria,
        sampleData.water_source,
        sampleData.additional_notes
    ];

    // Execute the SQL query to insert data
    try {
        const result = await pool.query(query, values);
        // Log success message with the ID of the inserted row
        console.log("✅ Data inserted successfully. Test ID:", result.rows[0].id);
    } catch (err) {
        // Log any errors that occur during insertion
        console.error("❌ Error inserting test data:", err.message);
    } finally {
        await pool.end(); // Close the database connection pool
    }
}

testInsert();
