# Backend Server Restart Required

The new investor endpoints (`/investors` and `/investors/relationships`) have been added to the code but the backend server needs to be restarted to load them.

## To Fix the 404 Error:

1. **Stop the current backend server** (Ctrl+C in the terminal where it's running)

2. **Restart the backend server**:
   ```bash
   cd backend
   python -m uvicorn main:app --reload --port 8000
   ```
   
   Or if you're using a different command:
   ```bash
   cd backend
   python main.py
   ```

3. **Verify the endpoints are available**:
   - Open http://localhost:8000/docs in your browser
   - Look for `/investors` and `/investors/relationships` in the API documentation
   - Or test directly: http://localhost:8000/investors

4. **Refresh the Graph View** in the frontend

The endpoints are already in the code at:
- `backend/main.py` line 1846: `@app.get("/investors")`
- `backend/main.py` line 1873: `@app.get("/investors/relationships")`

Once the server is restarted, the Graph View should work correctly.

