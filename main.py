import os
import json
import functions_framework
from datetime import datetime
from google.cloud import secretmanager
from google.cloud import bigquery

@functions_framework.http
def ingest_linkedin_ads(request):
    # 1. Captura as variáveis de ambiente injetadas pelo Cloud Build
    project_id = os.environ.get("GCP_PROJECT")
    dataset_id = os.environ.get("BQ_DATASET")
    table_id = os.environ.get("BQ_TABLE")
    
    print(f"[INFO] Iniciando ingestão para o projeto {project_id}")

    try:
        # 2. Acessar o Secret Manager (Garante que o IAM está correto)
        client_secret = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/LINKEDIN_ADS_TOKEN/versions/latest"
        response = client_secret.access_secret_version(request={"name": name})
        token = response.payload.data.decode("UTF-8")
        print("[INFO] Token extraído do Secret Manager com sucesso.")
        
        # 3. Estratégia Sandbox (Mocking)
        # Em produção, aqui usariamos o módulo 'requests' passando o token no header
        mock_payload = {
            "campaign_name": "Campanha B2B - Teste Cloud Build",
            "impressions": 5430,
            "clicks": 125,
            "cost_usd": 45.50,
            "date": datetime.utcnow().strftime("%Y-%m-%d")
        }
        
        # 4. Ingestão na Camada Bronze (Raw) do BigQuery
        client_bq = bigquery.Client(project=project_id)
        table_ref = f"{project_id}.{dataset_id}.{table_id}"
        
        rows_to_insert = [
            {
                "ingestion_timestamp": datetime.utcnow().isoformat(),
                "payload_json": json.dumps(mock_payload)
            }
        ]
        
        errors = client_bq.insert_rows_json(table_ref, rows_to_insert)
        
        if errors:
            print(f"[ERROR] Falha na inserção BQ: {errors}")
            return ("Erro na ingestao BQ", 500)
            
        print("[SUCCESS] Mock ingerido com sucesso na camada Bronze.")
        return ("Ingestao concluida com sucesso", 200)

    except Exception as e:
        print(f"[CRITICAL] Falha no pipeline: {str(e)}")
        return (f"Erro interno: {str(e)}", 500)
