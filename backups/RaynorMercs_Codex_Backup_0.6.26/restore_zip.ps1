$ErrorActionPreference = 'Stop'

$zipName = 'RaynorMercs_WoL_CCM.zip'
$destination = Join-Path $PSScriptRoot $zipName
$temporary = Join-Path $PSScriptRoot ('.restore-' + [guid]::NewGuid() + '.tmp')
$expectedHash = '833c92c252d49d621b477a53387e98d4e602b6fce41fc33ead3fc64151c9cd3e'

if ([IO.File]::Exists($destination)) {
    throw "Output already exists: $destination"
}

try {
    $output = [IO.File]::Open($temporary, [IO.FileMode]::CreateNew)
    try {
        foreach ($number in 1..14) {
            $partPath = Join-Path $PSScriptRoot ('{0}.part{1:00}' -f $zipName, $number)
            $inputStream = [IO.File]::OpenRead($partPath)
            try {
                $inputStream.CopyTo($output)
            } finally {
                $inputStream.Dispose()
            }
        }
    } finally {
        $output.Dispose()
    }

    if ((Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash -ne $expectedHash) {
        throw 'The restored ZIP did not match the original SHA-256.'
    }

    [IO.File]::Move($temporary, $destination)
    Write-Output $destination
} finally {
    if ([IO.File]::Exists($temporary)) {
        [IO.File]::Delete($temporary)
    }
}
