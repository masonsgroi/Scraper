# Scraper Design

## Purpose

Collect lift status and wait time data from Palisades Tahoe ski resort at regular intervals.

---

## What It Does

1. **Fetches** lift and trail data from Palisades Tahoe APIs
2. **Extracts** lift names, operational status, and wait times
3. **Writes** data to CSV files with timestamps
4. **Stores** CSV files in S3 for historical analysis

---

## Data Sources

### API Endpoints
- **Alpine Meadows**: `https://vicomap-cdn.resorts-interactive.com/api/maps/152`
- **Palisades Tahoe**: `https://vicomap-cdn.resorts-interactive.com/api/maps/1446`

### Data Format
Both APIs return JSON with a `lifts` array containing:
- `name` - Lift name (e.g., "KT-22", "Silverado")
- `status` - Operating status (e.g., "Open", "Closed", "On Hold")
- `waitTime` - Current wait time in minutes (or "N/A")

---

## Output

### Files Created
Each execution creates two timestamped CSV files:

**`status_{timestamp}.csv`**
```
Lift,Status
KT-22,Open
Silverado,Closed
Gold Coast,Open
```

**`wait_time_{timestamp}.csv`**
```
Lift,Wait Time
KT-22,5
Silverado,N/A
Gold Coast,10
```

### Timestamp Format
`YYYYMMDD_HHMMSS` (e.g., `20260101_143000`)

---

## Data Flow

```
Palisades APIs → Scraper → CSV Files → S3 Bucket
```

1. Scraper calls both API endpoints
2. Parses JSON responses
3. Combines data from both mountains
4. Generates two CSV files (status, wait times)
5. Uploads files to S3 with timestamp

---

## Error Handling

- **API unavailable**: Scraper logs error and exits
- **Invalid JSON**: Scraper logs error and exits
- **S3 upload fails**: Scraper logs error and exits

All errors are captured in CloudWatch Logs for troubleshooting.
