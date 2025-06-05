from unittest.mock import AsyncMock, patch

import pytest

from ocrdlp import OCRDLPCli


@pytest.fixture(autouse=True)
def api_keys(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "test" )
    monkeypatch.setenv("OPENAI_API_KEY", "test" )
    yield

def create_image_dir(tmp_path):
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    # create a dummy file to satisfy directory existence
    (image_dir / "dummy.jpg").touch()
    return image_dir


def test_search_command_writes_file(tmp_path):
    output_file = tmp_path / "urls.txt"
    mock_urls = ["https://example.com/a.jpg"]

    with patch("ocrdlp.search_images", new=AsyncMock(return_value=mock_urls)):
        cli = OCRDLPCli()
        exit_code = cli.run(["search", "invoice", "--engine", "serper", "--limit", "1", "--output", str(output_file)])

    assert exit_code == 0
    assert output_file.read_text().strip() == mock_urls[0]


def test_download_command_with_query(tmp_path):
    mock_urls = ["https://example.com/a.jpg"]
    mock_result = {mock_urls[0]: str(tmp_path / "img.jpg")}

    with (
        patch("ocrdlp.search_images", new=AsyncMock(return_value=mock_urls)) as mock_search,
        patch("ocrdlp.download_images", new=AsyncMock(return_value=mock_result)) as mock_download,
    ):
        cli = OCRDLPCli()
        exit_code = cli.run([
            "download",
            "--query",
            "invoice",
            "--output-dir",
            str(tmp_path),
            "--limit",
            "1",
        ])

    assert exit_code == 0
    mock_search.assert_awaited_once()
    mock_download.assert_awaited_once_with(mock_urls, output_dir=str(tmp_path))


def test_classify_command_with_validation(tmp_path):
    input_dir = create_image_dir(tmp_path)
    output_file = tmp_path / "labels.jsonl"
    mock_results = [{"document_category": "Invoice"}]
    validation_summary = {"total_records": 1, "valid_classifications": 1, "field_completeness": {}}

    with patch("ocrdlp.classify_images_batch", new=AsyncMock(return_value=mock_results)) as mock_classify, \
         patch("ocrdlp.validate_classification_labels", return_value=validation_summary) as mock_validate:
        cli = OCRDLPCli()
        exit_code = cli.run([
            "classify",
            str(input_dir),
            "--output",
            str(output_file),
            "--validate",
        ])

    assert exit_code == 0
    mock_classify.assert_awaited_once_with(image_dir=str(input_dir), output_file=str(output_file))
    mock_validate.assert_called_once_with(str(output_file))


def test_pipeline_command(tmp_path):
    mock_urls = ["https://example.com/a.jpg"]
    mock_download = {mock_urls[0]: str(tmp_path / "img.jpg")}
    mock_classify_results = [{"document_category": "Invoice"}]

    with patch("ocrdlp.search_images", new=AsyncMock(return_value=mock_urls)) as mock_search, \
         patch("ocrdlp.download_images", new=AsyncMock(return_value=mock_download)) as mock_download_fn, \
         patch("ocrdlp.classify_images_batch", new=AsyncMock(return_value=mock_classify_results)) as mock_classify:
        cli = OCRDLPCli()
        exit_code = cli.run([
            "pipeline",
            "invoice",
            "--output-dir",
            str(tmp_path),
            "--limit",
            "1",
        ])

    assert exit_code == 0
    mock_search.assert_awaited_once()
    mock_download_fn.assert_awaited_once_with(mock_urls, output_dir=str(tmp_path / "images"))
    mock_classify.assert_awaited_once()


def test_validate_command(tmp_path):
    file_path = tmp_path / "labels.jsonl"
    file_path.write_text("{}\n")
    summary = {"total_records": 1, "valid_classifications": 1, "field_completeness": {}}

    with patch("ocrdlp.validate_classification_labels", return_value=summary) as mock_validate:
        cli = OCRDLPCli()
        exit_code = cli.run(["validate", str(file_path)])

    assert exit_code == 0
    mock_validate.assert_called_once_with(str(file_path))
