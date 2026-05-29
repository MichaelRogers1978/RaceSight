param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$Reload
)

$python = Join-Path $PSScriptRoot ".venv/Scripts/python.exe"
if (-not (Test-Path $python)) {
    throw "Python virtual environment not found at $python"
}

$args = @("-m", "uvicorn", "ai.orchestrator.granite_client:app", "--host", $Host, "--port", "$Port")
if ($Reload) {
    $args += "--reload"
}

& $python @args
