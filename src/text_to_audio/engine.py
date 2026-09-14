from io import BytesIO

from gtts import gTTS

# from dto import PublicationDTO
from .dto import PublicationDTO


class TextToAudio:
    def __init__(self, p: PublicationDTO):
        self.publication = p
        self.config = {
            "text": "",
            "lang": "pt-br",
            "tld": "com.br",
        }

    def convert(self) -> bytes:
        self.config["text"] = self.publication.to_start()

        g = gTTS(**self.config)
        audio = BytesIO()
        g.write_to_fp(audio)
        return audio.getvalue()


if __name__ == "__main__":
    t = TextToAudio(
        PublicationDTO(
            author_name="Self",
            date=None,  # "2021/02/2023",
            content="Olá, este é um pequeno teste de conversão de áudio para texto. Estou falando de forma natural, com algumas pausas e diferentes palavras para verificar a precisão da transcrição. O objetivo é descobrir se a biblioteca consegue reconhecer corretamente minha voz, a pontuação e a estrutura das frases.",
        )
    )
    t.convert()
