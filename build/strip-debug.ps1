# Paths are supplied by build-release.bat through the environment.
$ErrorActionPreference = 'Stop'
try {
    $source = $env:SOURCE_PATH
    $destination = $env:DESTINATION_PATH
    $prefix = if ([IO.Path]::GetExtension($source) -ieq '.py') { '#' } else { '//' }
    $marker = '^[\t ]*' + [regex]::Escape($prefix) + '\[DEBUG-(START|END)\]'

    # A one-byte encoding preserves original bytes, including UTF-8 and CRLF/LF.
    $encoding = [Text.Encoding]::GetEncoding(28591)
    $bytes = [IO.File]::ReadAllBytes($source)
    if ($bytes.Length -ge 2 -and (($bytes[0] -eq 255 -and $bytes[1] -eq 254) -or ($bytes[0] -eq 254 -and $bytes[1] -eq 255))) {
        throw 'UTF-16/UTF-32 source files are not supported.'
    }
    $text = $encoding.GetString($bytes)
    $output = New-Object Text.StringBuilder
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191) {
        [void]$output.Append($text.Substring(0, 3))
        $text = $text.Substring(3)
    }
    $depth = 0
    $lineNumber = 0
    foreach ($line in [regex]::Split($text, '(?<=\n)')) {
        $lineNumber++
        if ($line -match $marker) {
            if ($Matches[1] -eq 'START') {
                $depth++
            } else {
                if ($depth -eq 0) { throw "Unmatched DEBUG-END at line $lineNumber" }
                $depth--
            }
        } elseif ($depth -eq 0) {
            [void]$output.Append($line)
        }
    }
    if ($depth -ne 0) { throw 'Unmatched DEBUG-START: missing DEBUG-END' }
    # Validate all markers before overwriting the output file.
    [IO.File]::WriteAllBytes($destination, $encoding.GetBytes($output.ToString()))
    exit 0
} catch {
    [Console]::Error.WriteLine('[STRIP FAILED] {0}: {1}', $env:SOURCE_PATH, $_.Exception.Message)
    exit 1
}