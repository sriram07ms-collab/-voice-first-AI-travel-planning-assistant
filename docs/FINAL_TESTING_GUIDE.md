# Final Testing Guide

Complete testing guide for the Voice-First Travel Assistant system.

## Table of Contents

1. [Pre-Testing Checklist](#pre-testing-checklist)
2. [Unit Tests](#unit-tests)
3. [Integration Tests](#integration-tests)
4. [End-to-End Tests](#end-to-end-tests)
5. [Performance Tests](#performance-tests)
6. [Security Tests](#security-tests)

---

## Pre-Testing Checklist

Before running tests, ensure:

- [ ] Backend server is running
- [ ] Frontend is accessible
- [ ] Environment variables are set
- [ ] API keys are configured
- [ ] Dependencies are installed
- [ ] Database/ChromaDB is accessible

---

## Unit Tests

### Running Unit Tests

```bash
# Run all unit tests
cd backend
pytest tests/test_feasibility.py -v
pytest tests/test_grounding.py -v
pytest tests/test_edits.py -v

# Run all unit tests at once
pytest tests/test_feasibility.py tests/test_grounding.py tests/test_edits.py -v
```

### Test Coverage

**Feasibility Tests (`test_feasibility.py`):**
- ✅ Feasible itinerary
- ✅ Infeasible daily duration
- ✅ Pace consistency
- ✅ Travel time limits

**Grounding Tests (`test_grounding.py`):**
- ✅ Well-grounded itinerary
- ✅ Missing source IDs
- ✅ Sources with URLs
- ✅ Explanation grounding

**Edit Correctness Tests (`test_edits.py`):**
- ✅ Correct single-day edit
- ✅ Incorrect multi-day edit
- ✅ Pace change edit

---

## Integration Tests

### Running Integration Tests

```bash
# Run integration tests
pytest tests/test_integration.py -v

# Run with coverage
pytest tests/test_integration.py --cov=src --cov-report=html
```

### Integration Test Scenarios

**1. Trip Planning Flow**
```python
# Test complete trip planning
- Create session
- Set preferences
- Plan trip
- Verify itinerary structure
- Check evaluation results
```

**2. Edit Flow**
```python
# Test complete edit flow
- Create session with itinerary
- Edit itinerary
- Verify only intended sections changed
- Check edit correctness evaluation
```

**3. Explanation Flow**
```python
# Test explanation flow
- Create session with itinerary
- Ask explanation question
- Verify explanation with sources
- Check grounding
```

**4. Evaluation Checks**
```python
# Test evaluation integration
- Run feasibility evaluation
- Run grounding evaluation
- Run edit correctness evaluation
- Verify all evaluations work together
```

---

## End-to-End Tests

### Manual E2E Testing

#### Test 1: Voice Input → Trip Planning

1. **Open frontend**
2. **Click microphone button**
3. **Say:** "Plan a 3-day trip to Jaipur. I like culture and history, relaxed pace."
4. **Verify:**
   - Voice input is captured
   - Transcript appears
   - Backend processes request
   - Itinerary is displayed
   - Sources are shown
   - Evaluation results are present

#### Test 2: Voice Edit → Itinerary Update

1. **With existing itinerary**
2. **Click microphone**
3. **Say:** "Make Day 2 more relaxed"
4. **Verify:**
   - Edit is processed
   - Only Day 2 changes
   - Day 1 remains unchanged
   - Evaluation shows edit correctness

#### Test 3: Explanation Questions

1. **With existing itinerary**
2. **Click "Explain Itinerary" button**
3. **Or say:** "Why did you pick Hawa Mahal?"
4. **Verify:**
   - Explanation is generated
   - Sources are cited
   - Explanation panel displays
   - Links are clickable

#### Test 4: PDF Generation

1. **With complete itinerary**
2. **Click "Generate PDF" (if implemented in frontend)**
3. **Or call API:**
   ```bash
   curl -X POST https://your-backend.com/api/generate-pdf \
     -H "Content-Type: application/json" \
     -d '{"session_id": "abc123", "email": "test@example.com"}'
   ```
4. **Verify:**
   - PDF is generated
   - Email is sent (if configured)
   - Response indicates success

#### Test 5: Evaluation Checks

1. **Check feasibility:**
   - Daily duration ≤ 13 hours
   - Travel times reasonable
   - Pace consistency

2. **Check grounding:**
   - All POIs have source IDs
   - All tips have citations
   - No hallucinations

3. **Check edit correctness:**
   - Only intended sections modified
   - Other sections unchanged

---

## Performance Tests

### API Response Times

```bash
# Test response times
time curl -X POST https://your-backend.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a trip to Jaipur"}'
```

**Expected:**
- Health check: < 100ms
- Chat endpoint: < 5s (LLM processing)
- Plan endpoint: < 10s (includes POI search)
- Edit endpoint: < 5s
- Explain endpoint: < 5s

### Load Testing (Optional)

Use tools like:
- **Apache Bench (ab)**
- **wrk**
- **k6**

Example:
```bash
# Install k6
brew install k6  # macOS
# or download from https://k6.io

# Run load test
k6 run load_test.js
```

---

## Security Tests

### 1. Input Validation

Test with malicious inputs:

```bash
# SQL injection attempt
curl -X POST https://your-backend.com/api/chat \
  -d '{"message": "'; DROP TABLE users; --"}'

# XSS attempt
curl -X POST https://your-backend.com/api/chat \
  -d '{"message": "<script>alert(\"XSS\")</script>"}'

# Verify: System handles gracefully, no errors
```

### 2. Rate Limiting

```bash
# Send many requests quickly
for i in {1..100}; do
  curl -X POST https://your-backend.com/api/chat \
    -d '{"message": "test"}'
done

# Verify: Rate limit kicks in after threshold
```

### 3. CORS

```bash
# Test from different origin
curl -X POST https://your-backend.com/api/chat \
  -H "Origin: https://malicious-site.com" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# Verify: CORS blocks unauthorized origins
```

### 4. Authentication (if implemented)

- Test with invalid tokens
- Test with expired tokens
- Test with missing tokens

---

## Test Scenarios from TEST_GUIDE.md

Refer to `TEST_GUIDE.md` for comprehensive test scenarios:

1. **Basic Trip Planning** (Scenario 1)
2. **Trip Planning with Preferences** (Scenario 2)
3. **Clarifying Questions** (Scenario 3)
4. **Edit: Change Pace** (Scenario 4)
5. **Edit: Swap Activity** (Scenario 5)
6. **Edit: Add Activity** (Scenario 6)
7. **Edit: Remove Activity** (Scenario 7)
8. **Explanation: Why POI** (Scenario 8)
9. **Explanation: Timing** (Scenario 9)
10. **Error Handling** (Scenarios 10-12)
11. **Evaluation Checks** (Scenarios 13-15)
12. **PDF Generation** (Scenario 16)

---

## Automated Testing Script

Create `tests/run_all_tests.sh`:

```bash
#!/bin/bash

echo "Running all tests..."

# Unit tests
echo "=== Unit Tests ==="
pytest tests/test_feasibility.py -v
pytest tests/test_grounding.py -v
pytest tests/test_edits.py -v

# Integration tests
echo "=== Integration Tests ==="
pytest tests/test_integration.py -v

# Phase tests
echo "=== Phase Tests ==="
python tests/test_phase2.py
python tests/test_phase3.py
python tests/test_phase4.py
python tests/test_phase5.py
python tests/test_phase6.py
python tests/test_phase8.py

echo "All tests completed!"
```

---

## Test Results Documentation

After running tests, document:

1. **Test Coverage:**
   ```bash
   pytest --cov=src --cov-report=html
   ```

2. **Test Results:**
   - Number of tests passed
   - Number of tests failed
   - Coverage percentage
   - Any known issues

3. **Performance Metrics:**
   - Average response times
   - Peak response times
   - Throughput

---

## Continuous Integration (CI)

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        cd backend
        pytest tests/ -v --cov=src
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## Test Checklist

Before considering testing complete:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All phase tests pass
- [ ] E2E manual tests completed
- [ ] Performance tests passed
- [ ] Security tests passed
- [ ] Test coverage > 70%
- [ ] All test scenarios from TEST_GUIDE.md verified
- [ ] Documentation updated
- [ ] Known issues documented

---

## Troubleshooting Test Failures

### Common Issues

**Problem: Import errors**
- Solution: Check `sys.path` in test files
- Verify backend is in Python path

**Problem: API key errors**
- Solution: Set `GROK_API_KEY` in environment
- Or use test key in test files

**Problem: Database errors**
- Solution: Use in-memory database for tests
- Or mock database calls

**Problem: Timeout errors**
- Solution: Increase timeout for API calls
- Mock external API calls in tests

---

## Next Steps

After testing:

1. **Fix any failing tests**
2. **Improve test coverage**
3. **Document test results**
4. **Set up CI/CD**
5. **Deploy to production**
6. **Monitor in production**

**Testing Status: Ready for Production!** ✅
