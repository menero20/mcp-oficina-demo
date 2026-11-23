"""Teste ponta a ponta: sobe o servidor por stdio, lista as ferramentas e chama algumas."""
import asyncio
import os
import sys
from datetime import date, timedelta

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def dia_util():
    d = date.today() + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d.isoformat()


async def main():
    params = StdioServerParameters(command=sys.executable, args=["server.py"],
                                   env={**os.environ, "OFICINA_PERFIL": "atendente"})
    async with stdio_client(params) as (r, w), ClientSession(r, w) as s:
        await s.initialize()
        print("ferramentas:", [t.name for t in (await s.list_tools()).tools])
        d = dia_util()
        for nome, args in [("buscar_cliente", {"termo": "Carla"}),
                           ("horarios_livres", {"data": d, "servico": "FREIO"}),
                           ("agendar_servico", {"cliente_id": 4, "data": d, "hora": "08:00", "servico": "OLEO"}),
                           ("agendar_servico", {"cliente_id": 4, "data": d, "hora": "15:00", "servico": "OLEO"}),
                           ("agendar_servico", {"cliente_id": 4, "data": d, "hora": "15:00", "servico": "OLEO", "confirmar": True}),
                           ("consultar_estoque", {})]:
            res = await s.call_tool(nome, args)
            print(f"\n{nome} {args}\n ->", " | ".join(c.text for c in res.content)[:400])


asyncio.run(main())
