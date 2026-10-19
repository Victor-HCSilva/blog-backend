from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import TYPE_CHECKING, Any

from .dto import PublicationRepr, UserRepr

if TYPE_CHECKING:
    from publication.models import Publication


# ---------------------------------------------------------------------------
# Extração e normalização de texto e tags
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
    """Extrai o texto bruto de um documento no formato de blocos."""
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
    """Extrai tags candidatas de um texto usando frequência local de termos."""
    normalized = _normalize(text)
    tokens = re.findall(r"\b[a-z]{3,}\b", normalized)
    filtered = [t for t in tokens if t not in _STOPWORDS_PT]

    if not filtered:
        return []

    counts = Counter(filtered)
    return [token for token, _ in counts.most_common(top_n)]


def build_publication_repr(
    pub: Publication, tags: list[str] | None = None
) -> PublicationRepr:
    """Constrói um PublicationRepr a partir do objeto Publication."""
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
# Implementação própria de TF-IDF e Álgebra Vetorial
# ---------------------------------------------------------------------------

class SimpleTFIDF:
    """Implementação própria e leve de TF-IDF com vetores esparsos."""

    def __init__(
        self,
        min_df: int = 1,
        max_df: float = 0.95,
        ngram_range: tuple[int, int] = (1, 2),
    ) -> None:
        self.min_df = min_df
        self.max_df = max_df
        self.ngram_range = ngram_range
        self.idf_: dict[str, float] = {}

    def _tokenize(self, text: str) -> list[str]:
        normalized = _normalize(text)
        words = re.findall(r"\b[a-z]{2,}\b", normalized)
        words = [w for w in words if w not in _STOPWORDS_PT]

        tokens: list[str] = []
        min_n, max_n = self.ngram_range

        for n in range(min_n, max_n + 1):
            if n == 1:
                tokens.extend(words)
            else:
                tokens.extend(
                    " ".join(words[i : i + n])
                    for i in range(len(words) - n + 1)
                )
        return tokens

    def fit_transform(self, corpus: list[str]) -> list[dict[str, float]]:
        total_docs = len(corpus)
        tokenized_corpus = [self._tokenize(doc) for doc in corpus]

        # 1. Contagem de Document Frequency (DF)
        df_counts: Counter[str] = Counter()
        for doc_tokens in tokenized_corpus:
            df_counts.update(set(doc_tokens))

        # 2. Filtragem de vocabulário e cálculo de IDF
        max_doc_count = self.max_df * total_docs if isinstance(self.max_df, float) else self.max_df
        self.idf_ = {}
        for term, df in df_counts.items():
            if self.min_df <= df <= max_doc_count:
                # Fórmula padrão do scikit-learn: ln((1 + N) / (1 + DF)) + 1
                self.idf_[term] = math.log((1 + total_docs) / (1 + df)) + 1.0

        # 3. Vetorização do corpus
        return [self._vectorize(tokens) for tokens in tokenized_corpus]

    def transform(self, texts: list[str]) -> list[dict[str, float]]:
        return [self._vectorize(self._tokenize(text)) for text in texts]

    def _vectorize(self, tokens: list[str]) -> dict[str, float]:
        """Calcula TF com escala sublinear e normaliza por L2."""
        tf_counts = Counter(tokens)
        vector: dict[str, float] = {}

        for term, count in tf_counts.items():
            if term in self.idf_:
                # TF sublinear: 1 + ln(count)
                sublinear_tf = 1.0 + math.log(count)
                vector[term] = sublinear_tf * self.idf_[term]

        # Normalização L2 (norma Euclidiana)
        norm = math.sqrt(sum(val ** 2 for val in vector.values()))
        if norm > 0.0:
            return {k: v / norm for k, v in vector.items()}
        return {}


def cosine_similarity(v1: dict[str, float], v2: dict[str, float]) -> float:
    """Produto escalar entre vetores previamente normalizados em L2."""
    if not v1 or not v2:
        return 0.0

    # Itera sobre o menor dicionário para maior eficiência
    small, big = (v1, v2) if len(v1) < len(v2) else (v2, v1)
    return sum(weight * big[term] for term, weight in small.items() if term in big)


def average_vectors(vectors: list[dict[str, float]]) -> dict[str, float]:
    """Calcula o vetor médio ponderado e o re-normaliza para norma 1."""
    if not vectors:
        return {}

    acc: dict[str, float] = {}
    for vec in vectors:
        for term, val in vec.items():
            acc[term] = acc.get(term, 0.0) + val

    num_vecs = len(vectors)
    avg_vec = {k: v / num_vecs for k, v in acc.items()}

    norm = math.sqrt(sum(v ** 2 for v in avg_vec.values()))
    if norm > 0.0:
        return {k: v / norm for k, v in avg_vec.items()}
    return avg_vec


# ---------------------------------------------------------------------------
# Motor de recomendação
# ---------------------------------------------------------------------------

class TFIDFRecommender:
    def __init__(
        self,
        tag_boost: float = 0.25,
        min_df: int = 1,
        max_df: float = 0.95,
        ngram_range: tuple[int, int] = (1, 2),
    ) -> None:
        if not (0.0 <= tag_boost < 1.0):
            raise ValueError("`tag_boost` deve estar no intervalo [0, 1).")

        self._tag_boost = tag_boost
        self._vectorizer = SimpleTFIDF(
            min_df=min_df,
            max_df=max_df,
            ngram_range=ngram_range,
        )
        self._reprs: list[PublicationRepr] = []
        self._tfidf_matrix: list[dict[str, float]] = []
        self._slug_to_idx: dict[str, int] = {}
        self._is_fitted: bool = False

    def fit(self, publications: list[PublicationRepr]) -> "TFIDFRecommender":
        if not publications:
            raise ValueError("A lista de publicações não pode estar vazia.")

        self._reprs = publications
        self._slug_to_idx = {repr_.slug: idx for idx, repr_ in enumerate(publications)}

        corpus = [repr_.raw_text for repr_ in publications]
        self._tfidf_matrix = self._vectorizer.fit_transform(corpus)
        self._is_fitted = True
        return self

    def recommend(self, slug: str, top_n: int = 5) -> list[tuple[str, float]]:
        self._assert_fitted()
        if slug not in self._slug_to_idx:
            raise KeyError(f"Publicação com slug '{slug}' não encontrada no corpus.")

        ref_idx = self._slug_to_idx[slug]
        ref_repr = self._reprs[ref_idx]
        ref_vector = self._tfidf_matrix[ref_idx]
        ref_tags = set(ref_repr.tags)

        scored: list[tuple[str, float]] = []

        for idx, (target_repr, target_vec) in enumerate(zip(self._reprs, self._tfidf_matrix)):
            if idx == ref_idx:
                continue

            # Cosseno TF-IDF
            cosine_score = cosine_similarity(ref_vector, target_vec)

            # Similaridade de Jaccard para tags
            tag_score = 0.0
            if ref_tags:
                cand_tags = set(target_repr.tags)
                union = ref_tags | cand_tags
                if union:
                    tag_score = len(ref_tags & cand_tags) / len(union)

            final_score = (1.0 - self._tag_boost) * cosine_score + (self._tag_boost * tag_score)

            if final_score > 0.0:
                scored.append((target_repr.slug, final_score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_n]

    def recommend_for_history(self, read_slugs: list[str], top_n: int = 5) -> list[tuple[str, float]]:
        self._assert_fitted()
        indices = [self._slug_to_idx[s] for s in read_slugs if s in self._slug_to_idx]
        if not indices:
            return []

        user_vector = average_vectors([self._tfidf_matrix[i] for i in indices])
        read_set = set(indices)

        scored: list[tuple[str, float]] = []
        for idx, (target_repr, target_vec) in enumerate(zip(self._reprs, self._tfidf_matrix)):
            if idx in read_set:
                continue

            score = cosine_similarity(user_vector, target_vec)
            if score > 0.0:
                scored.append((target_repr.slug, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_n]

    def recommend_for_user(self, user: UserRepr, top_n: int = 5) -> list[tuple[str, float]]:
        self._assert_fitted()
        scores = self._preference_scores(user)

        scored = [(self._reprs[idx].slug, score) for idx, score in enumerate(scores) if score > 0.0]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_n]

    def recommend_for_profile(
        self,
        user: UserRepr,
        read_slugs: list[str],
        top_n: int = 5,
    ) -> list[tuple[str, float]]:
        self._assert_fitted()

        read_indices = {self._slug_to_idx[s] for s in read_slugs if s in self._slug_to_idx}
        has_preferences = any(p.strip() for p in user.preferences)

        if not read_indices and not has_preferences:
            return []

        pref_scores = self._preference_scores(user) if has_preferences else [0.0] * len(self._reprs)
        hist_scores = [0.0] * len(self._reprs)

        if read_indices:
            user_vector = average_vectors([self._tfidf_matrix[i] for i in read_indices])
            hist_scores = [
                cosine_similarity(user_vector, doc_vec)
                for doc_vec in self._tfidf_matrix
            ]

        final_scores: list[float] = []
        for idx in range(len(self._reprs)):
            if idx in read_indices:
                final_scores.append(-1.0)
            elif has_preferences and read_indices:
                final_scores.append(0.5 * pref_scores[idx] + 0.5 * hist_scores[idx])
            elif has_preferences:
                final_scores.append(pref_scores[idx])
            else:
                final_scores.append(hist_scores[idx])

        scored = [(self._reprs[i].slug, score) for i, score in enumerate(final_scores) if score > 0.0]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_n]

    def _preference_scores(self, user: UserRepr) -> list[float]:
        preferences = {_normalize(p).strip() for p in user.preferences if p.strip()}
        if not preferences:
            return [0.0] * len(self._reprs)

        pref_vec = self._vectorizer.transform([" ".join(sorted(preferences))])[0]
        scores: list[float] = []

        for target_repr, target_vec in zip(self._reprs, self._tfidf_matrix):
            cosine_score = cosine_similarity(pref_vec, target_vec)

            cand_tags = {_normalize(t).strip() for t in target_repr.tags if t.strip()}
            union = preferences | cand_tags
            tag_score = len(preferences & cand_tags) / len(union) if union else 0.0

            final = (1.0 - self._tag_boost) * cosine_score + (self._tag_boost * tag_score)
            scores.append(final)

        return scores

    def top_terms(self, slug: str, top_n: int = 10) -> list[tuple[str, float]]:
        self._assert_fitted()
        if slug not in self._slug_to_idx:
            raise KeyError(f"Publicação com slug '{slug}' não encontrada no corpus.")

        idx = self._slug_to_idx[slug]
        vec = self._tfidf_matrix[idx]
        sorted_terms = sorted(vec.items(), key=lambda item: item[1], reverse=True)
        return sorted_terms[:top_n]

    def get_tags(self, slug: str) -> list[str]:
        self._assert_fitted()
        if slug not in self._slug_to_idx:
            raise KeyError(f"Publicação com slug '{slug}' não encontrada no corpus.")
        return self._reprs[self._slug_to_idx[slug]].tags

    def _assert_fitted(self) -> None:
        if not self._is_fitted:
            raise RuntimeError("O recomendador ainda não foi treinado. Chame `.fit()` primeiro.")