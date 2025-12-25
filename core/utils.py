from typing import Any, List, Dict, Generic, TypeVar
from psycopg import sql
from psycopg.sql import Composed

TValue = TypeVar("TValue")
class Ref(Generic[TValue]):
    def __init__(self, value: TValue):
        self.value = value

ColType = TypeVar("ColType")
def add_query_field(
    col_name: str,
    source: Dict[str, ColType],
    target: Ref[Composed| None],
    default: ColType
) -> ColType:

    if target.value:
        target.value = target.value + sql.SQL(", ") + sql.Identifier(col_name)
    else:
        target.value =  Composed([sql.Identifier(col_name)])
    return getattr(source,col_name,default)

def insert_query(table : str, field_names : Composed, values : List[Any]) -> Composed:
    """
         
    """
    query = sql.SQL("INSERT INTO {} ({}) VALUES({}) RETURNING id").format(
        sql.Identifier(table),
        field_names,#.join(", ").as_string(conn),
        sql.SQL(', ').join(values)
    )
    return query