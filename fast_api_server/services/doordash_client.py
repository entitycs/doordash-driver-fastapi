
import logging
import sys
import base64
import time
import jwt
import requests
import psycopg
from psycopg.types.json import Jsonb
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from core.utils import add_query_field, Ref
from psycopg import sql
from psycopg.sql import Composed
from config.internal.internal_config import config
from core.logging.logger import logger

def generate_jwt_token() -> str:
    """Generate a short-lived JWT for DoorDash API authentication (5-minute expiry)"""
    issued_at = int(time.time())
    payload = {
        "aud": "doordash",
        "iss": config.DOORDASH_DEVELOPER_ID,
        "kid": config.DOORDASH_KEY_ID,
        "exp": issued_at + 300,
        "iat": issued_at,
    }
    headers = {"alg": "HS256", "dd-ver": "DD-JWT-V1"}

    # assert non-None secret
    assert config.DOORDASH_SIGNING_SECRET is not None, "SIGNING_SECRET is missing (should be validated at startup)"
    secret = config.DOORDASH_SIGNING_SECRET

    # Add padding if needed for base64url decoding
    missing_padding = len(secret) % 4
    if missing_padding:
        secret += "=" * (4 - missing_padding)

    key = base64.urlsafe_b64decode(secret)

    token = jwt.encode(
        payload,
        key=key,
        algorithm="HS256",
        headers=headers,
    )
    return token


def doordash_request(method: str, url: str, json_data: Optional[Dict] = None) -> Dict[str, Any]:
    """Centralized request handler with JWT auth and PostgreSQL logging"""
    token = generate_jwt_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    def insert_query(table : str, field_names : Composed, values : List[Any]) -> Composed:
        query = sql.SQL("INSERT INTO {} ({}) VALUES({}) RETURNING id").format(
            sql.Identifier(table),
            field_names,#.join(", ").as_string(conn),
            sql.SQL(', ').join(values)
        )
        return query

    # Initialize response variable
    response_data =  {}
    status_code = 500
    error_detail = None

    try:
        if json_data:
            with psycopg.connect(f"host=postgresql port=5432 dbname=doordash user=doordash password={config.DOORDASH_DB_PW} connect_timeout=10") as conn:
                with conn.cursor() as cur:
                    value = cur.execute("SELECT max(id) as delivery_id FROM deliveries").fetchone()
                    conn.commit()
                    if value:
                        json_data["external_delivery_id"] = time.strftime("%Y-%m-%d") + " - " + str(value[0] + 1) if value[0] else "*error*"
                    response = requests.request(method, url, json=json_data, headers=headers, timeout=30)
                    response.raise_for_status()
                    response_data = response.json()
                    status_code = response.status_code
        else:
            response = requests.request(method, url, headers=headers, timeout=30)
            response.raise_for_status()
            response_data = response.json()
            status_code = response.status_code
    except requests.HTTPError as e:
        status_code = getattr(e.response, "status_code", status_code)
        try:
            error_detail = e.response.json()
        except ValueError:
            error_detail = {"error": e.response.text}
    except requests.RequestException as e:
        status_code = 500
        error_detail = {"error": f"Request failed: {str(e)}"}

    finally:
        conn = None
        fields : Ref[Composed | None ]= Ref(None)
        try:
            conn = psycopg.connect(f"host=postgresql port=5432 dbname=doordash user=doordash password={config.DOORDASH_DB_PW} connect_timeout=10")
            with conn.cursor() as cur:
                field_values = []
                new_delivery_id : int | None = None
                # Log Delivery if applicable
                if json_data and json_data.get("external_delivery_id") and json_data.get("delivery_status"):
                    if json_data.get("delivery_status") == "created" or json_data.get("delivery_status") == "quote":
                        fields  = Ref(None)
                        field_values.clear()
                        field_values.append(add_query_field("store_id", {}, fields, 1))
                        field_values.append(add_query_field("order_data", {}, fields, Jsonb(json_data)))
                        field_values.append(add_query_field("dropoff_address", json_data, fields, None))
                        field_values.append(add_query_field("dropoff_phone", {}, fields, json_data["dropoff_phone_number"]))
                        if fields.value:
                            cur.execute(insert_query('deliveries', fields.value, field_values))
                                # "INSERT INTO <table(s) () VALUES () Returning id",
                                # eg. (1, Jsonb(json_data), dropoff_address, dropoff_phone)
                            conn.commit()
                            res = cur.fetchone()#
                            if res: 
                                res = res[0]
                                new_delivery_id = int(res)
                            logger.info("Request logged to PostgreSQL deliveries successfully")
                # Log Event(s) - #ticket: id13
                fields  = Ref(None)
                field_values.clear()
                field_values.append(add_query_field("status_code", {}, fields, status_code))
                field_values.append(add_query_field("store_id",{}, fields, 1))
                if new_delivery_id:
                    field_values.append(add_query_field("delivery_id", {}, fields, new_delivery_id))
                if status_code != 200:
                    field_values.append(add_query_field("message", {}, fields, Jsonb(error_detail)))
                else:
                    field_values.append(add_query_field("message", {}, fields, Jsonb(response_data)))
                if fields.value:
                    cur.execute(insert_query('events', fields.value, field_values))
                    conn.commit()
                    logger.info("Request logged to PostgreSQL events successfully")
        except Exception as db_error:
            if conn is not None:
                conn.rollback()
            logger.error(f"Failed to log request to PostgreSQL: {str(db_error)}")
            raise
        finally:
            if conn is not None:
                logger.info("Closing PostfreSQL connection")
                conn.close()

    # Handle the response after logging
    if error_detail:
        raise HTTPException(status_code=status_code, detail=error_detail)

    return response_data