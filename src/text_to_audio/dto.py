from dataclasses import dataclass


@dataclass
class PublicationDTO:
    author_name: str
    date: str | None
    content: str

    def to_start(self):
        return f"Publicação feita por {self.author_name} em {self.date if self.date else 'data não fornecida'}. Título: {self.content}"
