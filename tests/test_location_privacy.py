import unittest

from not_mainstreet import build_density_certificate, quantize_location


class LocationPrivacyTests(unittest.TestCase):
    def test_quantize_validation(self) -> None:
        with self.assertRaises(ValueError):
            quantize_location(91, 0)

    def test_density_certificate_k_anon(self) -> None:
        peers = [
            (37.7749, -122.4194),
            (37.7750, -122.4195),
            (37.7751, -122.4196),
            (37.7748, -122.4192),
        ]
        cert = build_density_certificate(
            37.77495,
            -122.41945,
            peers,
            min_k=3,
            cell_size_m=500,
            epoch_salt="epoch-2026-02-18",
        )
        self.assertTrue(cert.verified)
        self.assertEqual(len(cert.cell_commitment), 64)
        self.assertIn(cert.density_band, {"sparse", "moderate", "dense"})

    def test_density_certificate_fails_if_too_sparse(self) -> None:
        cert = build_density_certificate(
            40.0,
            -70.0,
            [],
            min_k=2,
            cell_size_m=500,
            epoch_salt="epoch-2026-02-18",
        )
        self.assertFalse(cert.verified)
        self.assertEqual(cert.population_floor, 1)


if __name__ == "__main__":
    unittest.main()
