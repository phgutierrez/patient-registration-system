FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY web/package.json web/package-lock.json* ./
RUN npm install
COPY web ./
RUN npm run build

FROM python:3.12-slim AS backend
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend-builder /frontend/dist ./web/dist
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
