"""Servidor MCP de exemplo: dá a um LLM (ex.: Claude) acesso CONTROLADO ao sistema de uma oficina fictícia.

Mostra os padrões que importam em produção:
- ferramentas de leitura separadas das de escrita;
- perfil de acesso (OFICINA_PERFIL=leitura | atendente) decidido pelo servidor, não pelo modelo;
- validação de regra de negócio no servidor (expediente, conflito de horário, cliente existente);
- humano no circuito: escrita só com confirmar=True, senão devolve uma prévia;
- trilha de auditoria de toda escrita.
"""
import json
import os
import sqlite3
from datetime import date, datetime, time, timedelta
from pathlib import Path

from mcp.server import MCPServer

import dados

PERFIL = os.environ.get("OFICINA_PERFIL", "leitura")
AUDITORIA = Path(__file__).with_name("auditoria.log")
EXPEDIENTE = (time(8), time(18))

if not dados.BANCO.exists():
    dados.criar()

app = MCPServer("oficina-demo", instructions=(
    "Sistema de uma oficina mecânica FICTÍCIA. Use as ferramentas para consultar clientes, agenda e estoque. "
    "Para agendar, chame agendar_servico primeiro sem confirmar, mostre a prévia ao usuário e só então confirme."))


def _db():
    db = sqlite3.connect(dados.BANCO)
    db.row_factory = sqlite3.Row
    return db


def _auditar(acao: str, detalhe: dict) -> None:
    with AUDITORIA.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"quando": datetime.now().isoformat(timespec="seconds"), "perfil": PERFIL,
                            "acao": acao, **detalhe}, ensure_ascii=False) + "\n")


def _data(texto: str) -> date:
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise ValueError("data deve estar no formato AAAA-MM-DD")


def _ocupado(db, dia: str) -> list[tuple[time, time]]:
    linhas = db.execute("SELECT a.hora, s.minutos FROM agenda a JOIN servicos s ON s.codigo = a.servico "
                        "WHERE a.data = ?", (dia,)).fetchall()
    out = []
    for r in linhas:
        ini = datetime.combine(date.min, time.fromisoformat(r["hora"]))
        out.append((ini.time(), (ini + timedelta(minutes=r["minutos"])).time()))
    return out


@app.tool()
def buscar_cliente(termo: str) -> list[dict]:
    """Busca clientes por parte do nome ou da placa do veículo."""
    with _db() as db:
        rows = db.execute("""SELECT c.id, c.nome, c.telefone, v.modelo, v.placa FROM clientes c
                             LEFT JOIN veiculos v ON v.cliente_id = c.id
                             WHERE c.nome LIKE ? OR v.placa LIKE ?""", (f"%{termo}%", f"%{termo}%")).fetchall()
    return [dict(r) for r in rows]


@app.tool()
def agenda_do_dia(data: str) -> list[dict]:
    """Lista os serviços agendados numa data (AAAA-MM-DD)."""
    dia = _data(data).isoformat()
    with _db() as db:
        rows = db.execute("""SELECT a.hora, c.nome AS cliente, s.nome AS servico, s.minutos FROM agenda a
                             JOIN clientes c ON c.id = a.cliente_id JOIN servicos s ON s.codigo = a.servico
                             WHERE a.data = ? ORDER BY a.hora""", (dia,)).fetchall()
    return [dict(r) for r in rows]


@app.tool()
def horarios_livres(data: str, servico: str) -> list[str]:
    """Horários de início livres para um serviço (código: OLEO, FREIO, ALINH, REV) numa data."""
    dia = _data(data)
    if dia.weekday() >= 5:
        return []
    with _db() as db:
        s = db.execute("SELECT minutos FROM servicos WHERE codigo = ?", (servico,)).fetchone()
        if not s:
            raise ValueError(f"serviço desconhecido: {servico}")
        ocupado = _ocupado(db, dia.isoformat())
    livres, t = [], datetime.combine(dia, EXPEDIENTE[0])
    while (fim := t + timedelta(minutes=s["minutos"])).time() <= EXPEDIENTE[1] and fim.date() == dia:
        if all(fim.time() <= a or t.time() >= b for a, b in ocupado):
            livres.append(t.strftime("%H:%M"))
        t += timedelta(minutes=30)
    return livres


@app.tool()
def consultar_estoque(peca: str = "") -> list[dict]:
    """Estoque de peças (filtra por nome); marca o que está abaixo do mínimo."""
    with _db() as db:
        rows = db.execute("SELECT * FROM estoque WHERE peca LIKE ?", (f"%{peca}%",)).fetchall()
    return [{**dict(r), "repor": r["quantidade"] < r["minimo"]} for r in rows]


@app.tool()
def agendar_servico(cliente_id: int, data: str, hora: str, servico: str, confirmar: bool = False) -> dict:
    """Agenda um serviço. Sem confirmar=True devolve só a prévia (nada é gravado)."""
    if PERFIL != "atendente":
        return {"ok": False, "erro": "perfil sem permissão de escrita (OFICINA_PERFIL=atendente)"}
    dia = _data(data)
    with _db() as db:
        cliente = db.execute("SELECT nome FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
        s = db.execute("SELECT nome FROM servicos WHERE codigo = ?", (servico,)).fetchone()
        if not cliente or not s:
            return {"ok": False, "erro": "cliente ou serviço inexistente"}
        if hora not in horarios_livres(dia.isoformat(), servico):
            return {"ok": False, "erro": "horário indisponível", "livres": horarios_livres(dia.isoformat(), servico)}
        previa = {"cliente": cliente["nome"], "servico": s["nome"], "data": dia.isoformat(), "hora": hora}
        if not confirmar:
            return {"ok": True, "previa": previa, "aviso": "nada gravado: confirme com o usuário e chame com confirmar=True"}
        db.execute("INSERT INTO agenda (data, hora, cliente_id, servico) VALUES (?,?,?,?)",
                   (dia.isoformat(), hora, cliente_id, servico))
    _auditar("agendar_servico", previa)
    return {"ok": True, "agendado": previa}


if __name__ == "__main__":
    app.run()
