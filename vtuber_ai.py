import json
import shutil
import subprocess
from pathlib import Path

import requests
import speech_recognition as sr


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
CONFIG_EXAMPLE_PATH = ROOT / "config.example.json"
PERSONALITY_PATH = ROOT / "vtuber_personality.json"


class VTuberChat:
    def __init__(self) -> None:
        self.config = self._load_config()
        self.personality = self._load_personality()
        self.history = []

    def _load_config(self) -> dict:
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return json.loads(CONFIG_EXAMPLE_PATH.read_text(encoding="utf-8"))

    def _load_personality(self) -> dict:
        return json.loads(PERSONALITY_PATH.read_text(encoding="utf-8"))

    def _build_system_prompt(self) -> str:
        p = self.personality
        rules = "\n".join(f"- {r}" for r in p.get("persona_rules", []))
        goals = "\n".join(f"- {g}" for g in p.get("conversation_goals", []))
        guardrails = "\n".join(f"- {g}" for g in p.get("content_guardrails", []))
        style = p.get("style", {})

        return (
            f"Você é {p.get('name', 'uma VTuber')}.\n"
            f"Idioma principal: {p.get('language', 'pt-BR')}.\n"
            f"Tom: {style.get('tone', 'amigável')}.\n"
            f"Ritmo: {style.get('speaking_pace', 'médio')}.\n"
            f"Backstory: {p.get('backstory', '')}.\n\n"
            f"Regras de persona:\n{rules}\n\n"
            f"Metas de conversa:\n{goals}\n\n"
            f"Guardrails:\n{guardrails}\n"
        )

    def _ollama_chat(self, user_text: str) -> str:
        ollama_cfg = self.config["ollama"]
        url = f"{ollama_cfg['base_url'].rstrip('/')}/api/chat"

        messages = [{"role": "system", "content": self._build_system_prompt()}]
        messages.extend(self.history[-8:])
        messages.append({"role": "user", "content": user_text})

        payload = {
            "model": ollama_cfg["model"],
            "messages": messages,
            "stream": False,
            "options": {"temperature": ollama_cfg.get("temperature", 0.7)},
        }

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"].strip()

    def _speak(self, text: str) -> None:
        audio_cfg = self.config["audio"]
        tts_cmd = audio_cfg.get("tts_command", "soprano-tts")

        if not shutil.which(tts_cmd):
            print("[TTS] soprano-tts não encontrado no PATH. Pulando voz.")
            return

        cmd = [
            tts_cmd,
            "--voice",
            audio_cfg.get("tts_voice", "pt-BR"),
            "--speed",
            str(audio_cfg.get("tts_speed", 1.0)),
            "--text",
            text,
        ]

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            print(f"[TTS] Erro ao executar soprano-tts: {exc}")

    def _listen_once(self) -> str:
        recognizer = sr.Recognizer()
        with sr.Microphone(sample_rate=self.config["audio"].get("sample_rate", 16000)) as source:
            print("🎙️  Fale agora...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=20)

        model_path = self.config["audio"].get("vosk_model_path", "models/vosk")
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Modelo Vosk não encontrado em '{model_path}'. Configure em config.json"
            )

        text = recognizer.recognize_vosk(audio, language="pt-BR")
        parsed = json.loads(text)
        return parsed.get("text", "").strip()

    def chat_once(self, user_text: str, speak: bool = True) -> str:
        answer = self._ollama_chat(user_text)

        self.history.append({"role": "user", "content": user_text})
        self.history.append({"role": "assistant", "content": answer})

        if speak:
            self._speak(answer)
        return answer


def main() -> None:
    bot = VTuberChat()

    print("=== VTuber IA Local ===")
    print("1) Conversa por texto")
    print("2) Conversa por voz")
    print("q) Sair")

    while True:
        mode = input("\nEscolha o modo (1/2/q): ").strip().lower()
        if mode == "q":
            print("Até mais! ✨")
            break

        if mode == "1":
            user_text = input("Você: ").strip()
            if not user_text:
                continue
            try:
                answer = bot.chat_once(user_text, speak=True)
                print(f"{bot.personality.get('name', 'VTuber')}: {answer}")
            except Exception as exc:
                print(f"[Erro] {exc}")
            continue

        if mode == "2":
            try:
                user_text = bot._listen_once()
                if not user_text:
                    print("Não entendi sua fala. Tenta de novo.")
                    continue
                print(f"Você (voz): {user_text}")
                answer = bot.chat_once(user_text, speak=True)
                print(f"{bot.personality.get('name', 'VTuber')}: {answer}")
            except Exception as exc:
                print(f"[Erro voz] {exc}")
            continue

        print("Opção inválida.")


if __name__ == "__main__":
    main()
