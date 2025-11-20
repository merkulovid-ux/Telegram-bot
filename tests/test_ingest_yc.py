import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from ingest_yc import (
    discover_local_files,
    extract_category_topic,
    infer_labels,
    upload_to_object_storage,
    create_search_index_with_sdk,
    main as ingest_main,
)



def test_discover_local_files(tmp_path):
    (tmp_path / "file1.pdf").touch()
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "file2.txt").touch()
    (tmp_path / "subdir" / "file3.md").touch()
    (tmp_path / "subdir" / "file4.jpg").touch()  # Should be ignored

    files = discover_local_files(tmp_path)
    assert len(files) == 3
    assert all(f.suffix in [".pdf", ".txt", ".md"] for f in files)

@patch('ingest_yc.PdfReader')
def test_extract_category_topic(mock_pdf_reader, tmp_path):
    mock_reader_instance = MagicMock()
    mock_pdf_reader.return_value = mock_reader_instance
    mock_reader_instance.pages = [MagicMock()]

    # Test with scrum in text
    mock_reader_instance.pages[0].extract_text.return_value = "This document is about Scrum framework."
    category, topic = extract_category_topic(tmp_path / "scrum.pdf")
    assert category == "Scrum"
    assert topic == "This document is about Scrum framework."

    # Test with coaching in text
    mock_reader_instance.pages[0].extract_text.return_value = "Coaching techniques."
    category, topic = extract_category_topic(tmp_path / "coaching.pdf")
    assert category == "Coaching"

    # Test with no specific keyword, fallback to file name
    mock_reader_instance.pages[0].extract_text.return_value = "General topic."
    category, topic = extract_category_topic(tmp_path / "general.txt")
    assert category == "Общее"
    assert topic == "General topic."

    # Test with empty text
    mock_reader_instance.pages[0].extract_text.return_value = ""
    category, topic = extract_category_topic(tmp_path / "empty.md")
    assert category == "Общее"
    assert topic == "empty"

def test_infer_labels(tmp_path):
    with patch('ingest_yc.extract_category_topic') as mock_extract:
        mock_extract.return_value = ("TestCategory", "TestTopic")
        labels = infer_labels(tmp_path / "test_file.pdf")
        assert labels == {
            "source": "test_file.pdf",
            "kb_category": "TestCategory",
            "kb_topic": "TestTopic",
        }

@patch('ingest_yc.boto3')
def test_upload_to_object_storage(mock_boto3, tmp_path):
    mock_s3_client = MagicMock()
    mock_boto3.client.return_value = mock_s3_client

    (tmp_path / "file1.pdf").touch()
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "file2.txt").touch()

    files = [tmp_path / "file1.pdf", tmp_path / "subdir" / "file2.txt"]
    upload_to_object_storage(files, tmp_path)

    assert mock_s3_client.upload_file.call_count == 2
    mock_s3_client.upload_file.assert_any_call(
        str(tmp_path / "file1.pdf"), "test-bucket", "knowledge-base/file1.pdf"
    )
    mock_s3_client.upload_file.assert_any_call(
        str(tmp_path / "subdir" / "file2.txt"), "test-bucket", "knowledge-base/subdir/file2.txt"
    )

@patch('ingest_yc.YCloudML')
def test_create_search_index_with_sdk(mock_ycloudml, tmp_path):
    mock_sdk_instance = MagicMock()
    mock_ycloudml.return_value = mock_sdk_instance
    mock_sdk_instance.files.upload.return_value = MagicMock(id="file-id")
    mock_sdk_instance.search_indexes.create_deferred.return_value.wait.return_value = MagicMock(id="search-index-id")

    (tmp_path / "file1.pdf").touch()
    files = [tmp_path / "file1.pdf"]
    
    index_id = create_search_index_with_sdk(files, tmp_path)
    assert index_id == "search-index-id"
    mock_sdk_instance.files.upload.assert_called_once()
    mock_sdk_instance.search_indexes.create_deferred.assert_called_once()

@patch('ingest_yc.discover_local_files')
@patch('ingest_yc.upload_to_object_storage')
@patch('ingest_yc.create_search_index_with_sdk')
@patch('ingest_yc.Path')
def test_ingest_main_flow(
    mock_path,
    mock_create_search_index_with_sdk,
    mock_upload_to_object_storage,
    mock_discover_local_files,
):
    mock_file_path = MagicMock()
    mock_discover_local_files.return_value = [mock_file_path]
    mock_create_search_index_with_sdk.return_value = "mock-index-id"
    
    mock_path_instance = MagicMock()
    mock_path.return_value = mock_path_instance
    mock_path_instance.parent = MagicMock(return_value=Path('/mock/dir'))
    mock_path_instance.__truediv__.return_value = Path('/mock/dir/data_pdfs')

    ingest_main()

    mock_discover_local_files.assert_called_once()
    mock_upload_to_object_storage.assert_called_once()
    mock_create_search_index_with_sdk.assert_called_once()
    mock_path_instance.write_text.assert_called_once_with("mock-index-id", encoding="utf-8")
