"""Cria o banco de exemplo (SQLite) com dados 100% fictícios de uma oficina mecânica."""
import sqlite3
from datetime import date, timedelta
from pathlib import Path

BANCO = Path(__file__).with_name("oficina.db")


def proximo_dia_util(d: date, n: int) -> date:
    while n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def criar(caminho: Path = BANCO) -> None:
    caminho.unlink(missing_ok=True)
    db = sqlite3.connect(caminho)
    db.executescript("""
        CREATE TABLE clientes (id INTEGER PRIMARY KEY, nome TEXT, telefone TEXT);
        CREATE TABLE veiculos (id INTEGER PRIMARY KEY, cliente_id INTEGER REFERENCES clientes, modelo TEXT, placa TEXT);
        CREATE TABLE servicos (codigo TEXT PRIMARY KEY, nome TEXT, minutos INTEGER, preco REAL);
        CREATE TABLE estoque (peca TEXT PRIMARY KEY, quantidade INTEGER, minimo INTEGER);
        CREATE TABLE agenda (id INTEGER PRIMARY KEY, data TEXT, hora TEXT, cliente_id INTEGER, servico TEXT);
    """)
    db.executemany("INSERT INTO clientes VALUES (?,?,?)", [
        (1, "Ana Exemplo", "(00) 90000-0001"),
        (2, "Bruno Fictício", "(00) 90000-0002"),
        (3, "Carla Teste", "(00) 90000-0003"),
        (4, "Diego Modelo", "(00) 90000-0004"),
    ])
    db.executemany("INSERT INTO veiculos VALUES (?,?,?,?)", [
        (1, 1, "Hatch 1.0 2018", "AAA0A00"), (2, 2, "Sedan 2.0 2021", "BBB1B11"),
        (3, 3, "Picape 2.8 2016", "CCC2C22"), (4, 4, "SUV 1.5 2023", "DDD3D33"),
    ])
    db.executemany("INSERT INTO servicos VALUES (?,?,?,?)", [
        ("OLEO", "Troca de óleo e filtro", 60, 180.0),
        ("FREIO", "Revisão de freios", 120, 350.0),
        ("ALINH", "Alinhamento e balanceamento", 60, 150.0),
        ("REV", "Revisão completa", 240, 690.0),
    ])
    db.executemany("INSERT INTO estoque VALUES (?,?,?)", [
        ("Filtro de óleo", 12, 5), ("Pastilha de freio", 3, 4),
        ("Óleo 5W30 (litro)", 40, 20), ("Palheta", 0, 2),
    ])
    d1 = proximo_dia_util(date.today(), 1).isoformat()
    db.executemany("INSERT INTO agenda (data, hora, cliente_id, servico) VALUES (?,?,?,?)", [
        (d1, "08:00", 1, "OLEO"), (d1, "10:00", 3, "FREIO"), (d1, "14:00", 2, "ALINH"),
    ])
    db.commit()
    db.close()


if __name__ == "__main__":
    criar()
    print(f"banco de exemplo criado em {BANCO}")
