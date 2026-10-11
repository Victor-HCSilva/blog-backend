"""
Módulo de recomendação de publicações usando TF-IDF + Tags com scikit-learn.

Estratégia:
  1. Extrai o texto bruto de cada publicação (título + conteúdo dos blocos).
  2. Constrói um corpus TF-IDF sobre esse texto.
  3. Opcionalmente combina os scores de similaridade de texto com um boost
     de tags (quando as publicações compartilham tags em comum).
  4. Retorna as N publicações mais similares a uma publicação de referência.

Dependências extras necessárias:
    pip install scikit-learn
"""

from __future__ import annotations

import re
import unicodedata
from typing import TYPE_CHECKING, Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .dto import PublicationRepr, UserRepr


if TYPE_CHECKING:
    from publication.models import Publication


# ---------------------------------------------------------------------------
# Extração de texto e tags
# ---------------------------------------------------------------------------

_STOPWORDS_PT = {
    "a", "ao", "aos", "aquela", "aquelas", "aquele", "aqueles", "aquilo",
    "as", "ate", "com", "como", "da", "das", "de", "dela", "delas", "dele",
    "deles", "depois", "do", "dos", "e", "ela", "elas", "ele", "eles", "em",
    "entre", "era", "essa", "essas", "esse", "esses", "esta", "estas", "este",
    "estes", "eu", "foi", "for", "foram", "isso", "isto", "ja", "lhe", "lhes",
    "mais", "mas", "me", "mesmo", "meu", "minha", "muito", "na", "nao", "nas",
    "nem", "no", "nos", "num", "numa", "o", "os", "ou", "para", "pela",
    "pelas", "pelo", "pelos", "por", "qual", "quando", "que", "quem", "se",
    "sem", "ser", "seu", "seus", "so", "sua", "suas", "tambem", "te", "tem",
    "tendo", "ter", "teu", "teus", "tua", "tuas", "tudo", "um", "uma", "umas",
    "uns", "voce", "voces",
}


def _normalize(text: str) -> str:
    """Remove acentos e converte para minúsculas."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def _extract_text_from_document(document: dict[str, Any]) -> str:
    """
    Extrai o texto bruto de um documento no formato de blocos do blog.

    Suporta os tipos de bloco: paragraph, heading, quote, list, codeBlock.
    """
    parts: list[str] = []

    for block in document.get("blocks", []):
        block_type = block.get("type", "")

        if block_type in ("paragraph", "heading", "quote", "codeBlock"):
            for item in block.get("content", []):
                text = item.get("text", "").strip()
                if text:
                    parts.append(text)

        elif block_type == "list":
            for group in block.get("items", []):
                for item in group:
                    text = item.get("text", "").strip()
                    if text:
                        parts.append(text)

    return " ".join(parts)


def _extract_tags_from_text(text: str, top_n: int = 10) -> list[str]:
    """
    Extrai tags candidatas de um texto usando frequência de termos (TF local).

    Remove stopwords e retorna as `top_n` palavras mais relevantes.
    """
    normalized = _normalize(text)
    tokens = re.findall(r"\b[a-z]{3,}\b", normalized)
    filtered = [t for t in tokens if t not in _STOPWORDS_PT]

    if not filtered:
        return []

    freq: dict[str, int] = {}
    for token in filtered:
        freq[token] = freq.get(token, 0) + 1

    sorted_tokens = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [token for token, _ in sorted_tokens[:top_n]]


def build_publication_repr(
    pub: Publication, tags: list[str] | None = None
) -> PublicationRepr:
    """
    Constrói um `PublicationRepr` a partir de um objeto ORM `Publication`.

    O texto bruto é composto pelo título concatenado com o conteúdo dos blocos.
    As tags são extraídas automaticamente do texto completo.
    """
    body_text = _extract_text_from_document(pub.document)
    full_text = f"{pub.title} {body_text}".strip()
    extracted_tags = _extract_tags_from_text(full_text)
    if tags:
        extracted_tags = list(dict.fromkeys([*tags, *extracted_tags]))

    return PublicationRepr(
        id=pub.id,
        slug=pub.slug,
        title=pub.title,
        raw_text=full_text,
        tags=extracted_tags,
    )


# ---------------------------------------------------------------------------
# Motor de recomendação
# ---------------------------------------------------------------------------

class TFIDFRecommender:
    """
    Motor de recomendação baseado em TF-IDF + boost de tags compartilhadas.

    Exemplo de uso::

        pubs: list[Publication] = await list_publications_service(db=db)
        reprs = [build_publication_repr(p) for p in pubs]

        recommender = TFIDFRecommender(tag_boost=0.3)
        recommender.fit(reprs)

        similar = recommender.recommend(slug="meu-artigo", top_n=5)
        for slug, score in similar:
            print(slug, score)
    """

    def __init__(
        self,
        tag_boost: float = 0.25,
        min_df: int = 1,
        max_df: float = 0.95,
        ngram_range: tuple[int, int] = (1, 2),
    ) -> None:
        """
        Parâmetros
        ----------
        tag_boost:
            Peso (0-1) dado à sobreposição de tags na pontuação final.
            O restante (1 - tag_boost) é dado à similaridade TF-IDF.
        min_df:
            Ignora termos que aparecem em menos de `min_df` documentos.
        max_df:
            Ignora termos que aparecem em mais de `max_df` fração dos docs.
        ngram_range:
            Faixa de n-gramas considerada pelo TfidfVectorizer.
        """
        if not (0.0 <= tag_boost < 1.0):
            raise ValueError("`tag_boost` deve estar no intervalo [0, 1).")

        self._tag_boost = tag_boost
        self._vectorizer = TfidfVectorizer(
            min_df=min_df,
            max_df=max_df,
            ngram_range=ngram_range,
            strip_accents="unicode",
            analyzer="word",
            sublinear_tf=True,
        )

        self._reprs: list[PublicationRepr] = []
        self._tfidf_matrix: Any = None
        self._slug_to_idx: dict[str, int] = {}
        self._is_fitted: bool = False

    # ------------------------------------------------------------------
    # Treinamento
    # ------------------------------------------------------------------

    def fit(self, publications: list[PublicationRepr]) -> "TFIDFRecommender":
        """
        Ajusta o vectorizer e computa a matriz TF-IDF do corpus.

        Deve ser chamado antes de `recommend`.

        Parâmetros
        ----------
        publications:
            Lista de representações de publicações.
        """
        if not publications:
            raise ValueError("A lista de publicações não pode estar vazia.")

        self._reprs = publications
        self._slug_to_idx = {repr_.slug: idx for idx, repr_ in enumerate(publications)}

        corpus = [repr_.raw_text for repr_ in publications]
        self._tfidf_matrix = self._vectorizer.fit_transform(corpus)
        self._is_fitted = True
        return self

    # ------------------------------------------------------------------
    # Recomendação
    # ------------------------------------------------------------------

    def recommend(
        self,
        slug: str,
        top_n: int = 5,
    ) -> list[tuple[str, float]]:
        """
        Retorna as `top_n` publicações mais similares à publicação de referência.

        A pontuação final combina:
            score = (1 - tag_boost) * cosine_tfidf + tag_boost * jaccard_tags

        Parâmetros
        ----------
        slug:
            Slug da publicação de referência.
        top_n:
            Número máximo de recomendações a retornar.

        Retorno
        -------
        Lista de tuplas ``(slug, score)`` ordenadas por score decrescente,
        excluindo a própria publicação de referência.
        """
        self._assert_fitted()

        if slug not in self._slug_to_idx:
            raise KeyError(f"Publicação com slug '{slug}' não encontrada no corpus.")

        ref_idx = self._slug_to_idx[slug]
        ref_repr = self._reprs[ref_idx]

        # --- Similaridade TF-IDF (cosseno) ---
        ref_vector = self._tfidf_matrix[ref_idx]
        cosine_scores: np.ndarray = cosine_similarity(
            ref_vector, self._tfidf_matrix
        ).flatten()

        # --- Similaridade de tags (Jaccard) ---
        ref_tags = set(ref_repr.tags)
        tag_scores: np.ndarray = np.zeros(len(self._reprs), dtype=np.float64)

        if ref_tags:
            for idx, repr_ in enumerate(self._reprs):
                cand_tags = set(repr_.tags)
                union = ref_tags | cand_tags
                if union:
                    tag_scores[idx] = len(ref_tags & cand_tags) / len(union)

        # --- Pontuação final ponderada ---
        final_scores = (
            (1.0 - self._tag_boost) * cosine_scores
            + self._tag_boost * tag_scores
        )

        # Exclui a própria publicação
        final_scores[ref_idx] = -1.0

        top_indices = np.argsort(final_scores)[::-1][:top_n]

        return [
            (self._reprs[idx].slug, float(final_scores[idx]))
            for idx in top_indices
            if final_scores[idx] > 0.0
        ]

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def get_tags(self, slug: str) -> list[str]:
        """Retorna as tags extraídas de uma publicação específica."""
        self._assert_fitted()
        if slug not in self._slug_to_idx:
            raise KeyError(f"Publicação com slug '{slug}' não encontrada no corpus.")
        return self._reprs[self._slug_to_idx[slug]].tags

    def top_terms(self, slug: str, top_n: int = 10) -> list[tuple[str, float]]:
        """
        Retorna os `top_n` termos TF-IDF mais relevantes de uma publicação.

        Útil para depuração e auditoria do modelo.
        """
        self._assert_fitted()
        if slug not in self._slug_to_idx:
            raise KeyError(f"Publicação com slug '{slug}' não encontrada no corpus.")

        idx = self._slug_to_idx[slug]
        feature_names: list[str] = self._vectorizer.get_feature_names_out().tolist()
        tfidf_row = self._tfidf_matrix[idx].toarray().flatten()

        top_indices = np.argsort(tfidf_row)[::-1][:top_n]
        return [
            (feature_names[i], float(tfidf_row[i]))
            for i in top_indices
            if tfidf_row[i] > 0
        ]

    def _assert_fitted(self) -> None:
        if not self._is_fitted:
            raise RuntimeError(
                "O recomendador ainda não foi treinado. Chame `.fit()` primeiro."
            )


    def recommend_for_history(self, read_slugs: list[str], top_n: int = 5) -> list[tuple[str, float]]:
        self._assert_fitted()

        indices = [self._slug_to_idx[s] for s in read_slugs if s in self._slug_to_idx]
        if not indices:
            return []

        # Vetor de interesse = média dos vetores dos artigos que o leitor já consumiu
        user_vector = np.asarray(self._tfidf_matrix[indices].mean(axis=0))

        # Compara o perfil médio do usuário contra todo o catálogo do blog
        user_scores = cosine_similarity(user_vector, self._tfidf_matrix).flatten()

        # Zera o score dos artigos que ele já leu (para não recomendar repetido)
        for idx in indices:
            user_scores[idx] = -1.0

        top_indices = np.argsort(user_scores)[::-1][:top_n]
        return [(self._reprs[i].slug, float(user_scores[i])) for i in top_indices if user_scores[i] > 0]

    def recommend_for_user(
        self, user: UserRepr, top_n: int = 5
    ) -> list[tuple[str, float]]:
        """Recomenda publicações combinando as preferências declaradas do usuário."""
        self._assert_fitted()

        final_scores = self._preference_scores(user)
        top_indices = np.argsort(final_scores)[::-1][:top_n]

        return [
            (self._reprs[idx].slug, float(final_scores[idx]))
            for idx in top_indices
            if final_scores[idx] > 0.0
        ]

    def recommend_for_profile(
        self,
        user: UserRepr,
        read_slugs: list[str],
        top_n: int = 5,
    ) -> list[tuple[str, float]]:
        """Combina preferências explícitas com o histórico recente de leitura."""
        self._assert_fitted()

        read_indices = {
            self._slug_to_idx[slug] for slug in read_slugs if slug in self._slug_to_idx
        }
        has_preferences = any(preference.strip() for preference in user.preferences)
        if not read_indices and not has_preferences:
            return []

        preference_scores = (
            self._preference_scores(user)
            if has_preferences
            else np.zeros(len(self._reprs), dtype=np.float64)
        )
        history_scores = np.zeros(len(self._reprs), dtype=np.float64)
        if read_indices:
            user_vector = np.asarray(
                self._tfidf_matrix[sorted(read_indices)].mean(axis=0)
            )
            history_scores = cosine_similarity(
                user_vector, self._tfidf_matrix
            ).flatten()

        if has_preferences and read_indices:
            final_scores = 0.5 * preference_scores + 0.5 * history_scores
        elif has_preferences:
            final_scores = preference_scores
        else:
            final_scores = history_scores

        for idx in read_indices:
            final_scores[idx] = -1.0

        top_indices = np.argsort(final_scores)[::-1][:top_n]
        return [
            (self._reprs[idx].slug, float(final_scores[idx]))
            for idx in top_indices
            if final_scores[idx] > 0.0
        ]

    def _preference_scores(self, user: UserRepr) -> np.ndarray:
        preferences = {
            _normalize(preference).strip()
            for preference in user.preferences
            if preference.strip()
        }
        if not preferences:
            return np.zeros(len(self._reprs), dtype=np.float64)

        user_vector = self._vectorizer.transform([" ".join(sorted(preferences))])
        cosine_scores = cosine_similarity(user_vector, self._tfidf_matrix).flatten()

        tag_scores = np.zeros(len(self._reprs), dtype=np.float64)
        for idx, publication in enumerate(self._reprs):
            publication_tags = {_normalize(tag).strip() for tag in publication.tags}
            publication_tags.discard("")
            union = preferences | publication_tags
            if union:
                tag_scores[idx] = len(preferences & publication_tags) / len(union)

        return (
            (1.0 - self._tag_boost) * cosine_scores + self._tag_boost * tag_scores
        )
