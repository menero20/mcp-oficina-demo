# mcp-oficina-demo — servidor MCP com acesso controlado

Exemplo de **servidor MCP (Model Context Protocol)** que conecta um LLM, como o Claude, ao sistema de uma
**oficina mecânica fictícia** (SQLite com dados inventados). O foco não é a oficina: são os padrões que
tornam seguro deixar um agente de IA **ler e gravar** em um sistema real.

## Padrões demonstrados

| Padrão | Como aparece aqui |
|---|---|
| Leitura separada de escrita | 4 ferramentas de consulta e 1 de escrita (`agendar_servico`) |
| Permissão decidida pelo servidor | `OFICINA_PERFIL=leitura` (padrão) ou `atendente`; o modelo não consegue se promover |
| Regra de negócio no servidor | expediente, dia útil, conflito de horário e cliente/serviço existentes são validados no código |
| Humano no circuito | sem `confirmar=True`, a escrita devolve só uma **prévia** para o usuário aprovar |
| Auditoria | toda gravação vai para `auditoria.log` com data, perfil e detalhes |
| Erro útil para o modelo | horário ocupado devolve a lista de horários livres, para o agente propor alternativa |

## Ferramentas

- `buscar_cliente(termo)` — por nome ou placa
- `agenda_do_dia(data)`
- `horarios_livres(data, servico)` — considera a duração de cada serviço
- `consultar_estoque(peca)` — marca o que precisa repor
- `agendar_servico(cliente_id, data, hora, servico, confirmar=False)`

## Rodar

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Windows
python teste_cliente.py      # teste ponta a ponta: sobe o servidor via stdio e chama as ferramentas
```

Conectar ao Claude Code:

```bash
claude mcp add oficina -e OFICINA_PERFIL=atendente -- python /caminho/server.py
```

Depois é só pedir em linguagem natural: *"tem horário amanhã para revisão de freios da Carla?"*.
O agente consulta, propõe, mostra a prévia e só grava quando você confirma.

---
Todos os nomes, telefones e placas são fictícios.
