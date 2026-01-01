# Scraper Development Plan

Step-by-step guide to building the scraper functionality incrementally.

---

## Phase 1: Fetch Data from One API

**Goal**: Successfully retrieve JSON data from one Palisades API endpoint.

### Step 1.1: Create Basic Script

Create `scraper.py` with:
- `fetch_json_from_url(url)` function
- User-Agent header for requests
- Test with `https://vicomap-cdn.resorts-interactive.com/api/maps/152`

### Step 1.2: Test

```bash
python scraper.py
```

**Expected**: JSON data printed to console

✅ **Phase 1 Complete**: Successfully fetching API data

---

## Phase 2: Extract Lift Information

**Goal**: Parse JSON and extract lift names, status, and wait times.

### Step 2.1: Add Parsing Logic

Add `extract_lift_data(json_data)` function:
- Loop through `lifts` array in JSON
- Extract: `name`, `status`, `waitTime`
- Create two data structures: status_data and wait_time_data
- Return both lists

### Step 2.2: Test

```bash
python scraper.py
```

**Expected**: Lift names, statuses, and wait times printed to console

✅ **Phase 2 Complete**: Successfully parsing lift data

---

## Phase 3: Add Second API

**Goal**: Fetch and combine data from both Palisades API endpoints.

### Step 3.1: Fetch from Both APIs

Add `scrape_all_lifts()` function:
- Define URLs list with both endpoints (152 and 1446)
- Loop through URLs
- Combine results from both APIs
- Return combined data

**API endpoints**:
- Alpine Meadows: `https://vicomap-cdn.resorts-interactive.com/api/maps/152`
- Palisades Tahoe: `https://vicomap-cdn.resorts-interactive.com/api/maps/1446`

### Step 3.2: Test

```bash
python scraper.py
```

**Expected**: Data from both mountains printed to console

✅ **Phase 3 Complete**: Successfully fetching from multiple APIs

---

## Phase 4: Write to CSV Files

**Goal**: Save extracted data to CSV files locally.

### Step 4.1: Add CSV Output

Add `save_to_csv(status_data, wait_time_data)` function:
- Import: `pandas`, `datetime`
- Generate timestamp: `datetime.utcnow().strftime('%Y%m%d_%H%M%S')`
- Create DataFrames from status and wait_time data
- Save to CSV files with timestamp in filename

### Step 4.2: Create requirements.txt

```
requests
pandas
```

### Step 4.3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4.4: Test

```bash
python scraper.py
```

**Expected**: Two CSV files created with timestamp in filename

✅ **Phase 4 Complete**: Successfully writing to CSV files

---

## Phase 5: Add Error Handling

**Goal**: Handle errors gracefully and log them.

### Step 5.1: Add Try-Except Blocks

**Update `fetch_json_from_url()`**:
- Wrap requests in try-except
- Catch `requests.exceptions.RequestException`
- Print error and re-raise

**Update `scrape_all_lifts()`**:
- Wrap each URL fetch in try-except
- Continue to next URL on failure
- Raise exception if no data scraped

**Update `save_to_csv()`**:
- Wrap DataFrame operations in try-except
- Print error and re-raise

**Add `main()` function**:
- Wrap entire execution in try-except
- Print success/failure messages
- Exit with code 1 on failure

### Step 5.2: Test

```bash
python scraper.py
```

**Expected**: Scraper runs with proper error handling and logging

✅ **Phase 5 Complete**: Scraper with error handling implemented
