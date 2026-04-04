# VTuber IA (Texto + Voz) com Ollama (Phi-3) e Soprano TTS

Projeto base para rodar uma VTuber local, leve e personalizável:
- **LLM local** via **Ollama** (ex.: `phi3:mini`)
- **TTS leve** via **Soprano TTS** (CLI)
- Conversa por **texto** e por **voz** (STT opcional com Vosk)
- Personalidade em **JSON** (`vtuber_personality.json`)

## Requisitos

- Python 3.10+
- [Ollama](https://ollama.com/) rodando localmente
- Modelo leve puxado no Ollama, por exemplo:
  ```bash
  ollama pull phi3:mini
  ```
- (Opcional, voz de entrada) modelo Vosk em `./models/vosk`.
- (Opcional, voz de saída) `soprano-tts` no PATH.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.json config.json
```

## Como rodar

```bash
python vtuber_ai.py
```

No menu:
- `1` = conversar por texto
- `2` = conversar por voz (microfone)
- `q` = sair

## Observações

- Se `soprano-tts` não estiver instalado, o app continua em modo texto sem TTS.
- Se Vosk não estiver configurado, modo voz de entrada falha com mensagem amigável e você pode voltar ao texto.
- Para mudar personalidade, edite `vtuber_personality.json`.
