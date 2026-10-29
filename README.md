# CloudOps Prototype

A student prototype for a unified cloud deployment dashboard. Current implementation includes a Flask web application, SQLite deployment history, health/API endpoints, and rule-based demo failure guidance.

## Current scope and limitations

- Local prototype only until cloud services are connected.
- The sample records are demo data.
- The diagnosis page uses predefined rules; it does not read live Kubernetes events or AWS logs.
- No authentication is implemented yet; do not expose this prototype publicly as-is.
- SQLite is suitable for this demonstration, not a multi-user production deployment.

## Run on Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

If PowerShell blocks activation, use the direct interpreter instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Run tests

```powershell
python -m unittest discover -s tests -v
```

## Run with Docker

After installing and starting Docker Desktop:

```powershell
docker build -t cloudops-prototype .
docker run --rm -p 5000:5000 cloudops-prototype
```

Open http://127.0.0.1:5000

## API endpoints

- `GET /api/health` - simple health check
- `GET /api/deployments` - deployment records as JSON

## CI

The GitHub Actions workflow in `.github/workflows/ci.yml` runs the unit tests on pushes and pull requests to main/master.
