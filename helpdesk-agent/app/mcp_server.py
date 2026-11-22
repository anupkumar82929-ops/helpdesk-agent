"""MCP server exposing READ-ONLY employee data from Postgres.

Design: narrow, parameterised tools instead of a raw `query(sql)` tool, and the
connection uses the `mcp_reader` role, which has no access to salary/phone columns
and no write privileges. Even a fully hijacked agent cannot exfiltrate those.

Run over stdio:  python -m app.mcp_server
"""
import json
import os
import re

import psycopg2
from psycopg2.extras import RealDictCursor
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hr-it-postgres")
EMP_ID = re.compile(r"^E\d{3,4}$")


def _query(sql: str, params: tuple) -> list[dict]:
    conn = psycopg2.connect(os.environ["MCP_DATABASE_URL"])
    try:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def _validate(employee_id: str) -> str:
    eid = employee_id.strip().upper()
    if not EMP_ID.match(eid):
        raise ValueError("employee_id must look like E102")
    return eid


def _dump(obj) -> str:
    return json.dumps(obj, default=str)


@mcp.tool()
def get_employee_profile(employee_id: str) -> str:
    """Get basic non-sensitive profile (name, department, title, location, hire date, manager id) for an employee id like E102."""
    eid = _validate(employee_id)
    rows = _query(
        "SELECT employee_id, full_name, department, job_title, manager_id, location, hire_date "
        "FROM employees WHERE employee_id = %s",
        (eid,),
    )
    return _dump(rows[0]) if rows else _dump({"error": f"No employee {eid}"})


@mcp.tool()
def get_leave_balance(employee_id: str, leave_type: str = "") -> str:
    """Get leave balance for an employee id like E102. Optional leave_type: annual, casual or sick. Returns total, used and remaining days."""
    eid = _validate(employee_id)
    sql = ("SELECT leave_type, total_days, used_days, (total_days - used_days) AS remaining_days "
           "FROM leave_balances WHERE employee_id = %s")
    params: tuple = (eid,)
    if leave_type:
        sql += " AND leave_type = %s"
        params = (eid, leave_type.strip().lower())
    rows = _query(sql + " ORDER BY leave_type", params)
    return _dump(rows) if rows else _dump({"error": f"No leave data for {eid}"})


@mcp.tool()
def get_it_assets(employee_id: str) -> str:
    """List IT assets (laptop, monitor, phone) assigned to an employee id like E102, with warranty expiry and status."""
    eid = _validate(employee_id)
    rows = _query(
        "SELECT asset_id, asset_type, model, serial_number, assigned_on, warranty_expiry, status "
        "FROM it_assets WHERE employee_id = %s ORDER BY asset_id",
        (eid,),
    )
    return _dump(rows) if rows else _dump({"error": f"No assets for {eid}"})


@mcp.tool()
def get_manager(employee_id: str) -> str:
    """Get the name and department of the manager of an employee id like E102."""
    eid = _validate(employee_id)
    rows = _query(
        "SELECT m.employee_id, m.full_name, m.department, m.job_title "
        "FROM employees e JOIN employees m ON e.manager_id = m.employee_id "
        "WHERE e.employee_id = %s",
        (eid,),
    )
    return _dump(rows[0]) if rows else _dump({"error": f"No manager found for {eid}"})


if __name__ == "__main__":
    mcp.run(transport="stdio")
