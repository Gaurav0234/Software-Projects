from mcp_servers.server import list_files, scrape_url


def test_list_files_returns_employee_policy():
    result = list_files("./data/documents")

    assert result["success"] is True
    assert result["directory"] == "data\\documents"

    file_names = [item["name"] for item in result["items"]]
    assert "employee_policy.txt" in file_names


def test_list_files_blocks_access_outside_data():
    result = list_files(".")

    assert result["success"] is False
    assert result["error"] == "Access is allowed only inside the ./data directory."


def test_list_files_handles_missing_directory():
    result = list_files("./data/does_not_exist")

    assert result["success"] is False
    assert "Directory does not exist" in result["error"]


def test_scrape_url_rejects_invalid_url():
    result = scrape_url("not-a-valid-url")

    assert result["success"] is False
    assert result["error"] == "Please provide a valid HTTP or HTTPS URL."