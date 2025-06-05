from gpt4v_image_labeler import generate_classification_summary


def test_generate_summary_all_failed(tmp_path):
    results = [{"error": "fail"} for _ in range(3)]
    output_file = tmp_path / "labels.jsonl"

    generate_classification_summary(results, str(output_file))

    summary_file = output_file.with_name(output_file.stem + "_summary.md")
    assert summary_file.exists()

    content = summary_file.read_text()
    assert "- Successfully Classified: 0" in content
    assert "- Failed: 3" in content
    assert "- Success Rate: 0.0%" in content

