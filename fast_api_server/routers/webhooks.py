import base64
import psycopg
from psycopg.sql import Composed
from psycopg.types.json import Jsonb
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi import Depends
from config.internal.internal_config import config
from core.utils import add_query_field, insert_query, Ref
from core.logging.logger import logger


router = APIRouter(prefix="/webhooks", tags=["DoorDash Webhooks"])

WEBHOOK_USER = config.DOORDASH_WEBHOOK_ID
WEBHOOK_PASS = config.DOORDASH_WEBHOOK_SECRET

def verify_basic_auth(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    encoded = authorization.split(" ")[1]
    decoded = base64.b64decode(encoded).decode()
    username, password = decoded.split(":")

    if username != WEBHOOK_USER or password != WEBHOOK_PASS:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return True

@router.post("/doordash")
async def doordash_webhook(
    request: Request,
    _auth=Depends(verify_basic_auth)
):
    if _auth is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    payload = await request.json()
    conn = None
    fields : Ref[Composed | None ]= Ref(None)
    field_values = []
    new_delivery_id : int | None = payload.get("external_delivery_id")
    try:
        conn = psycopg.connect(f"host=postgresql port=5432 dbname=doordash user=doordash password={config.DOORDASH_DB_PW} connect_timeout=10")
        with conn.cursor() as cur:
            field_values.append(add_query_field("status_code", {}, fields, 200))
            field_values.append(add_query_field("store_id",{}, fields, 1))
            if new_delivery_id:
                cur.execute(
                    """
                    SELECT id
                    FROM deliveries
                    WHERE order_data->>'external_delivery_id' = %s
                    LIMIT 1;
                    """,
                    (new_delivery_id,)
                )
                result = cur.fetchone()
                if result:
                    new_delivery_id = result[0]
                else:
                    raise
                field_values.append(add_query_field("delivery_id", {}, fields, new_delivery_id))
            field_values.append(add_query_field("message", {}, fields, Jsonb(payload)))
            if fields.value:
                cur.execute(insert_query('events', fields.value, field_values))
                conn.commit()
                logger.info("Request logged to PostgreSQL events successfully")

    except Exception as db_error:
        if conn is not None:
            conn.rollback()
        logger.info(f"Failed to log request to PostgreSQL: {str(db_error)}")
        return JSONResponse({"status": "ok"})
        #raise
    finally:
        if conn is not None:
            logger.info("Closing PostfreSQL connection")
            conn.close()
    logger.info("Received DoorDash webhook:", payload)
    return JSONResponse({"status": "ok"})
