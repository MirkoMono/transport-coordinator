from transport_api.services.manifest import ManifestRoute, ManifestStop, generate_manifest_pdf


def test_generate_manifest_pdf():
    pdf = generate_manifest_pdf(
        [
            ManifestRoute(
                vehicle_name="Van 1",
                driver_name="Driver A",
                total_distance=12_500,
                stops=[
                    ManifestStop(
                        sequence=0,
                        person_name="Anna Berg",
                        address="Södermalm Stockholm",
                        eta_minutes=8,
                    )
                ],
            )
        ],
        production_name="Test Production",
    )
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 500
