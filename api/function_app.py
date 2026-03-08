import json
import os
import azure.functions as func
from azure.data.tables import TableClient

app = func.FunctionApp()

CONN_STR = os.environ.get("CosmosDBConnectionString", "")
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "*")
TABLE_NAME = "visitorcount"
PARTITION_KEY = "counter"
ROW_KEY = "visitors"


def get_cors_headers():
    return {
        "Access-Control-Allow-Origin": CORS_ORIGIN,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


@app.function_name("GetVisitorCount")
@app.route(route="api/counter", methods=["GET", "POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def counter(req: func.HttpRequest) -> func.HttpResponse:
    headers = get_cors_headers()

    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=headers)

    try:
        table_client = TableClient.from_connection_string(CONN_STR, TABLE_NAME)

        try:
            entity = table_client.get_entity(partition_key=PARTITION_KEY, row_key=ROW_KEY)
            count = entity.get("count", 0) + 1
        except Exception:
            count = 1

        table_client.upsert_entity({
            "PartitionKey": PARTITION_KEY,
            "RowKey": ROW_KEY,
            "count": count,
        })

        return func.HttpResponse(
            body=json.dumps({"count": count}),
            status_code=200,
            headers={**headers, "Content-Type": "application/json"},
        )

    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            status_code=500,
            headers={**headers, "Content-Type": "application/json"},
        )
