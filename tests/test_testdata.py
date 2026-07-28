from itertools import islice

from cycling_overlay.testdata import generate_random_data


def test_generated_samples_have_expected_shape_and_ranges():
    gen = generate_random_data()
    samples = list(islice(gen, 5))

    assert len(samples) == 5
    for i, sample in enumerate(samples, start=1):
        assert len(sample) == 1
        row = sample[0]
        assert row["time"] == i
        assert 80 <= row["power"] <= 250
        assert 120 <= row["heartrate"] <= 180
        assert 70 <= row["cadence"] <= 100
        assert 20000 <= row["speed"] <= 35000
        assert row["distance"] >= 0
        assert row["tss"] >= 0
        assert row["calories"] >= 0


def test_distance_is_monotonically_increasing():
    gen = generate_random_data()
    samples = list(islice(gen, 10))
    distances = [s[0]["distance"] for s in samples]
    assert distances == sorted(distances)


def test_averages_are_bounded_by_instantaneous_range():
    gen = generate_random_data()
    samples = list(islice(gen, 20))
    for sample in samples:
        row = sample[0]
        assert 80 <= row["avgPower"] <= 250
        assert 120 <= row["avgHeartrate"] <= 180
        assert 70 <= row["avgCadence"] <= 100
