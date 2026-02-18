#!/usr/bin/env python3
from __future__ import annotations

import argparse

from not_mainstreet.database import EngineDatabases
from not_mainstreet.portal_server import PortalServerConfig, run_portal_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Run NotMainStreet portal interface server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--inside-db", default="data/inside_ivi.db")
    parser.add_argument("--outside-db", default="data/outside_portal.db")
    args = parser.parse_args()

    cfg = PortalServerConfig(
        host=args.host,
        port=args.port,
        databases=EngineDatabases(inside_path=args.inside_db, outside_path=args.outside_db),
    )
    server = run_portal_server(cfg)
    print(f"Portal running on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
