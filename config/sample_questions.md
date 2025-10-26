# Sample Questions for Automotive Manufacturing Database

This file contains sample questions that can be asked of the agenticbot system. These questions are derived from the database schema and example SQL queries in the systemcontext.md file.

## Primary Example Questions

### 1. Vehicle Inventory & Status
- "Get me all the vehicles that are unshipped at my plant with associated status"
- "Generate a list of vehicles (vin) that are still in the plant inventory with their associated status information"
- "Show me all vehicles with missing collection points"
- "List all vehicles with freight verification data"
- "Show me vehicles by plant location and status"

### 2. Quality Control & Defects
- "Get all quality concerns / defects filed on the vehicle (vin) as well as the repairs done on it"
- "What quality concerns are unresolved for vehicles?"
- "Show me vehicles with repair status and time to repair"

### 3. Campaign Management
- "Get the campaigns that the vehicle has been put on and the associated details"
- "Get campaign details for specific vehicles"
- "Show me vehicles on active campaigns"

### 4. Connected Vehicle Data
- "Get connected vehicle (cv) details for individual vins that are still in inventory as stored in the unit_master table"
- "Show me vehicle tire pressure and battery information"
- "What vehicles have GPS location data?"
- "Get vehicle telematics data including fuel level and engine status"

### 5. Diagnostics & Maintenance
- "Get the DTCs that are reported by the vehicle through the connected vehicle data"
- "Find vehicles with diagnostic trouble codes (DTCs)"
- "What vehicles have charge and hold test results?"
- "Show me OTA (Over-The-Air) update status for vehicles"

## Additional Natural Language Variations

### Simple Queries
- "How many vehicles are in inventory?"
- "Show me all Ford vehicles"
- "What plants have unshipped vehicles?"
- "List vehicles by model year"

### Complex Queries
- "Find vehicles with low tire pressure and their current location"
- "Show me vehicles with quality concerns that haven't been repaired"
- "Get all electric vehicles with battery status below 50%"
- "Find vehicles with failed campaigns in the last 30 days"

### Analytical Queries
- "What's the average time to repair quality concerns by plant?"
- "Which plant has the most unshipped vehicles?"
- "Show me campaign success rates by vehicle model"
- "What are the most common DTCs across all vehicles?"

## Query Categories by Difficulty

### Easy (Single table, basic filtering)
- "Show me all vehicles from plant WAP"
- "List vehicles produced in 2024"
- "Get all Ford F-150 vehicles"

### Medium (Joins, aggregations)
- "Show me vehicles with their connected vehicle data"
- "Get quality concerns by plant"
- "List vehicles with campaign status"

### Hard (Complex joins, analytics)
- "Get comprehensive vehicle inventory with all status information"
- "Show me vehicle journey from production to shipping"
- "Analyze quality trends by plant and model"

## Use Cases by Department

### Manufacturing
- Vehicle production tracking
- Plant inventory management
- Quality control monitoring

### Quality Assurance
- Defect tracking and resolution
- Campaign management
- Repair time analysis

### Engineering
- Connected vehicle diagnostics
- OTA update monitoring
- DTC analysis

### Logistics
- Shipping status tracking
- Freight verification
- Location management

---
*Generated from systemcontext.md schema and example queries*
*Last updated: October 23, 2025*
