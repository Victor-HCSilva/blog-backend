import unittest

from engine_recommendation import PublicationRepr, TFIDFRecommender, UserRepr
from .fake_publication import data

TEST_USER = UserRepr(
    id=1,
    preferences=[
        "python",
        "programacao",
        "tecnologia",
        "desenvolvimento",
        "ia",
        "dados",
    ],
)


def load_test_publications() -> list[PublicationRepr]:
    return [
        PublicationRepr(
            id=publication["id"],
            slug=publication["slug"],
            title=publication["title"],
            raw_text=publication["raw_text"],
            tags=publication["tags"],
        )
        for publication in data
    ]


def get_test_recommendations() -> list[tuple[str, float]]:
    recommender = TFIDFRecommender().fit(load_test_publications())
    return recommender.recommend_for_user(TEST_USER, top_n=3)


class RecommendationTest(unittest.TestCase):
    def test_top_three_recommendations_match_test_user_profile(self) -> None:
        recommendations = get_test_recommendations()

        self.assertEqual(
            [slug for slug, _ in recommendations],
            [
                "introducao-ao-python-moderno",
                "machine-learning-por-onde-comecar",
                "por-que-voce-deve-aprender-sql",
            ],
        )
        self.assertEqual(len(recommendations), 3)
        self.assertGreater(recommendations[0][1], recommendations[1][1])
        self.assertGreater(recommendations[1][1], recommendations[2][1])

    def test_profile_recommendations_combine_preferences_and_exclude_read_posts(
        self,
    ) -> None:
        recommender = TFIDFRecommender().fit(load_test_publications())

        recommendations = recommender.recommend_for_profile(
            TEST_USER,
            read_slugs=["introducao-ao-python-moderno"],
            top_n=3,
        )

        recommended_slugs = [slug for slug, _ in recommendations]
        self.assertNotIn("introducao-ao-python-moderno", recommended_slugs)
        self.assertEqual(len(recommendations), 3)
        self.assertGreaterEqual(recommendations[0][1], recommendations[1][1])
        self.assertGreaterEqual(recommendations[1][1], recommendations[2][1])

    def test_profile_without_preferences_or_history_is_empty(self) -> None:
        recommender = TFIDFRecommender().fit(load_test_publications())

        self.assertEqual(
            recommender.recommend_for_profile(UserRepr(id=2), read_slugs=[]),
            [],
        )

    def test_history_recommendations_exclude_read_posts(self) -> None:
        recommender = TFIDFRecommender().fit(load_test_publications())

        recommendations = recommender.recommend_for_history(
            ["introducao-ao-python-moderno"], top_n=3
        )

        self.assertTrue(recommendations)
        self.assertNotIn(
            "introducao-ao-python-moderno",
            [slug for slug, _ in recommendations],
        )


def main() -> None:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RecommendationTest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    publications_by_slug = {
        publication.slug: publication for publication in load_test_publications()
    }

    print(f"Perfil do usuário de teste (id={TEST_USER.id}):")
    print(f"  Preferências: {', '.join(TEST_USER.preferences)}")
    print("\nTop 3 recomendações:")
    for rank, (slug, score) in enumerate(get_test_recommendations(), start=1):
        print(f"{rank}. {publications_by_slug[slug].title} [{slug}] — {score:.6f}")


if __name__ == "__main__":
    main()
