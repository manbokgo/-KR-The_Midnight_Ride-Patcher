param(
    [Parameter(Mandatory=$true)][string]$TranslatorExe,
    [Parameter(Mandatory=$true)][string]$Database,
    [Parameter(Mandatory=$true)][string]$Output
)

$ErrorActionPreference = "Stop"

# Development-only converter for trusted local .mcmdb files.
# BinaryFormatter must never be used on untrusted downloads.
[Reflection.Assembly]::LoadFrom((Resolve-Path -LiteralPath $TranslatorExe)) | Out-Null

$stream = [IO.File]::OpenRead((Resolve-Path -LiteralPath $Database))
try {
    $formatter = New-Object Runtime.Serialization.Formatters.Binary.BinaryFormatter
    $db = $formatter.Deserialize($stream)
}
finally {
    $stream.Dispose()
}

$result = [ordered]@{}
foreach ($entry in $db.GetEnumerator()) {
    $translated = [string]$entry.Value.Translated
    $status = [string]$entry.Value.Status
    $result[[string]$entry.Key] = [ordered]@{
        translated = $translated
        status = $status
    }
}

$parent = Split-Path -Parent $Output
if ($parent) {
    [IO.Directory]::CreateDirectory($parent) | Out-Null
}
$json = $result | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText($Output, $json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
Write-Output ("exported {0} entries -> {1}" -f $result.Count, $Output)
