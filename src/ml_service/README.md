# ML Service (Isolation Forest)

## 1) Install dependencies

```bash
pip install -r requirements.txt
```

## 2) Train model from MongoDB logs

The trainer reads from MongoDB collection `detection_results` (default).

```bash
python train_model.py
```

This creates:

- `model.pkl`

## 3) Run inference API

```bash
python app.py
```

Service runs on port `9000` and exposes:

- `GET /health`
- `POST /predict`

## Environment variables

- `MONGO_URI` (default: `mongodb://localhost:27017`)
- `MONGO_DB` (default: `detection_service`)
- `MONGO_COLLECTION` (default: `detection_results`)
