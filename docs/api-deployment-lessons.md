# API Deployment Lessons Learned

## Context
This document captures lessons learned from troubleshooting and fixing backend API deployment issues for the PharmaKG project. These issues occurred on 2026-02-12 during Cross-Domain Query Builder page development.

---

## Key Issues and Solutions

### Issue 1: `AdvancedQueryService` Import Error

#### Problem
```
ImportError: cannot import name 'AdvancedQueryService' from 'api.services.advanced_queries'
```

#### Root Causes
1. **Missing `__init__.py` file**: The `api/services/` directory was missing an `__init__.py` file
2. **File corruption**: The `advanced_queries.py` file had 0 lines (all content on one giant line)
3. **Missing pydantic imports**: Added `ShortestPathRequest` class without importing `BaseModel` and `Field`
4. **Missing typing imports**: Added `Optional` and `List` without importing from `typing`

#### Solutions
1. **Create `__init__.py`**:
   ```bash
   # Create api/services/__init__.py
   echo "# Services module" > api/services/__init__.py
   ```

2. **Restore corrupted file from git**:
   ```bash
   git restore api/services/advanced_queries.py
   ```

3. **Add required imports in `api/main.py`**:
   ```python
   from typing import Optional, List
   from pydantic import BaseModel, Field
   ```

---

### Issue 2: Python Environment Path Issues

#### Problem
When running `python3 -m uvicorn api.main:app`, the import failed. But when running `uvicorn.run("api.main:app")` directly in Python, it worked.

#### Root Cause
Using system `python3` instead of conda environment `python3` caused path resolution issues.

#### Solution
Always use the full path to the conda environment Python:
```bash
/root/miniconda3/envs/pharmakg-api/bin/python3
```

Or activate the conda environment before running:
```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate pharmakg-api
```

---

### Issue 3: Neo4j Cypher Query Syntax Errors

#### Problem 1: Double bracket in variable-length pattern
```cypher
MATCH path = (start)-[:RELATED_TO*1..$max_length]]->(end)  # WRONG - extra ]
```
**Solution**: Remove the extra bracket
```cypher
MATCH path = (start)-[:RELATED_TO*1..$max_length]->(end)  # CORRECT
```

#### Problem 2: Parameter in variable-length pattern (not supported)
```cypher
MATCH path = (start)-[:RELATED_TO*1..$max_length]->(end)  # WRONG
```
**Solution**: Use a literal value instead
```cypher
MATCH path = (start)-[:RELATED_TO*1..{max_length}]->(end)  # CORRECT
```

#### Problem 3: WHERE clause for relationship types doesn't work with variable-length paths
```cypher
MATCH path = (start)-[:RELATED_TO*1..3]->(end)
WHERE type(r) IN $rel_types  # WRONG - 'r' is not defined for variable-length paths
```
**Solution**: Build relationship pattern dynamically
```python
if relationship_types:
    rel_pattern = "|".join(relationship_types)  # e.g., "RELATED_TO|CONNECTED_TO"
else:
    rel_pattern = "RELATED_TO"

query = f"MATCH path = (start)-[:{rel_pattern}*1..{max_length}]->(end)"
```

---

### Issue 4: QueryResult Attribute Error

#### Problem
```python
return result.records if result.success else []
# AttributeError: 'QueryResult' object has no attribute 'success'
```

#### Root Cause
The `QueryResult` class in `database.py` doesn't have a `success` attribute. It only has `records`.

#### Solution
```python
return result.records if result.records else []
```

Or simply:
```python
return result.records or []
```

---

## Working Startup Method

### Method 1: Python Script (Recommended)

Create `/tmp/start_api.py`:
```python
#!/root/miniconda3/envs/pharmakg-api/bin/python3
import uvicorn
import sys
import os

os.chdir('/root/autodl-tmp/pj-pharmaKG')
sys.path.insert(0, '/root/autodl-tmp/pj-pharmaKG')

if __name__ == "__main__":
    print("Starting PharmaKG API server...")
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, log_level="info")
```

Run with:
```bash
chmod +x /tmp/start_api.py
/tmp/start_api.py
```

### Method 2: Background Heredoc

```bash
/root/miniconda3/envs/pharmakg-api/bin/python3 << 'EOF' &
import uvicorn
import sys
import os

os.chdir('/root/autodl-tmp/pj-pharmaKG')
sys.path.insert(0, '/root/autodl-tmp/pj-pharmaKG')

uvicorn.run("api.main:app", host="0.0.0.0", port=8000, log_level="info")
EOF
```

### Method 3: Direct Command (Only works with proper environment)

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate pharmakg-api
cd /root/autodl-tmp/pj-pharmaKG
/root/miniconda3/envs/pharmakg-api/bin/python3 << 'EOF'
import uvicorn
import sys
import os

os.chdir('/root/autodl-tmp/pj-pharmaKG')
sys.path.insert(0, '/root/autodl-tmp/pj-pharmaKG')

uvicorn.run("api.main:app", host="0.0.0.0", port=8000)
EOF
```

---

## Common Commands

### Start Backend Service
```bash
# Kill any existing uvicorn processes
pkill -9 -f "uvicorn" 2>/dev/null

# Start new service
/root/miniconda3/envs/pharmakg-api/bin/python3 << 'EOF'
import uvicorn, sys, os
os.chdir('/root/autodl-tmp/pj-pharmaKG')
sys.path.insert(0, '/root/autodl-tmp/pj-pharmaKG')
uvicorn.run("api.main:app", host="0.0.0.0", port=8000)
EOF &
```

### Test Backend Health
```bash
curl -s http://127.0.0.1:8000/health
```

### Stop Backend Service
```bash
pkill -9 -f "uvicorn"
```

### View Logs
```bash
tail -f /tmp/api.log
```

---

## Cross-Domain Query Builder POST Endpoint

### Endpoint
```
POST /advanced/path/shortest
```

### Request Body
```json
{
  "start_id": "CHEMBL25",
  "end_id": "CHEMBL210",
  "max_length": 3,
  "rel_types": ["RELATED_TO"]
}
```

### Response
```json
{
  "start_entity": "CHEMBL25",
  "end_entity": "CHEMBL210",
  "paths": [],
  "count": 0
}
```

---

## Summary of Fixes Applied

1. ✅ Added `api/services/__init__.py`
2. ✅ Restored corrupted `advanced_queries.py` from git
3. ✅ Added `from typing import Optional, List` to `api/main.py`
4. ✅ Added `from pydantic import BaseModel, Field` to `api/main.py`
5. ✅ Fixed Cypher query syntax (removed extra `]`)
6. ✅ Changed `*1..$max_length` to `*1..{max_length}` (literal value)
7. ✅ Built relationship pattern dynamically instead of using WHERE clause
8. ✅ Changed `result.success` to `result.records` (attribute doesn't exist)

---

## Prevention Checklist

Before deploying or restarting the API service:

- [ ] Verify `api/services/__init__.py` exists
- [ ] Verify all required imports are present in `api/main.py`
- [ ] Verify Python files have proper line endings (use `wc -l` to check)
- [ ] Test import with: `python3 -c "from api.services.advanced_queries import AdvancedQueryService"`
- [ ] Always use the conda environment Python: `/root/miniconda3/envs/pharmakg-api/bin/python3`
- [ ] Ensure working directory is `/root/autodl-tmp/pj-pharmaKG`
- [ ] Ensure project root is in `sys.path`
