# South African Languages Translation Management Script
Write-Host "=== South African Languages Translation Manager ==="

# Define all South African official languages with their locale codes
$saLanguages = @("af","en","nr","xh","zu","nso","st","tn","ss","ve","ts")

# Step 1: Create translation directory structure and files
Write-Host "Step 1: Creating translation structure..."
$createResult = python create_translations.py create 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Translation structure created successfully"
} else {
    Write-Host "Error creating translation structure"
    Write-Host $createResult
    exit 1
}

# Step 2: Generate summary report
Write-Host "Step 2: Generating summary report..."
Write-Host ""

$summary = @()
foreach ($locale in $saLanguages) {
    $poPath = "translations/$locale/LC_MESSAGES/messages.po"
    $moPath = "translations/$locale/LC_MESSAGES/messages.mo"
    
    $poExists = Test-Path $poPath
    $moExists = Test-Path $moPath
    
    $status = if ($poExists -and $moExists) { "Complete" } elseif ($poExists) { "PO only" } else { "Missing" }
    $summary += [PSCustomObject]@{
        Locale = $locale
        Status = $status
        PO_File = $poExists
        MO_File = $moExists
    }
}

# Display summary table
$summary | Format-Table -AutoSize

Write-Host ""
Write-Host "=== Next Steps ==="
Write-Host "1. Edit the .po files in the translations/[locale]/LC_MESSAGES/ directory"
Write-Host "2. Add translations for each message in the .po files"
Write-Host "3. Update your Flask app to include all languages in the LANGUAGES config"
Write-Host ""

Write-Host "=== Translation File Locations ==="
foreach ($locale in $saLanguages) {
    Write-Host ($locale + ": translations/" + $locale + "/LC_MESSAGES/messages.po")
}

Write-Host ""
Write-Host "=== Language Codes ==="
Write-Host "af - Afrikaans"
Write-Host "en - English"
Write-Host "nr - Southern Ndebele"
Write-Host "xh - Xhosa"
Write-Host "zu - Zulu"
Write-Host "nso - Northern Sotho"
Write-Host "st - Southern Sotho"
Write-Host "tn - Tswana"
Write-Host "ss - Swati"
Write-Host "ve - Venda"
Write-Host "ts - Tsonga"
Write-Host ""

Write-Host "=== Example Translation Entry ==="
Write-Host "In each .po file, add entries like:"
Write-Host "msgid ""Welcome to KasiKash Admin"""
Write-Host "msgstr ""Welcome to KasiKash Admin"""
Write-Host ""

Write-Host "Script completed successfully!"