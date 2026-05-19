# Stage 1: Build React UI
FROM node:20-slim AS ui-build
WORKDIR /ui
COPY ui/package*.json ./
RUN npm install
COPY ui/ .
RUN npm run build

# Stage 2: Python API + serve static React files
FROM python:3.11-slim
WORKDIR /app
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api/app.py .
COPY --from=ui-build /ui/dist ./static
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
