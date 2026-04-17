# Script to configure Grafana alerts via API after startup (Windows PowerShell)
# This script creates alert rules for the IoT demo

$GRAFANA_URL = "http://localhost:3000"
$GRAFANA_USER = "admin"
$GRAFANA_PASSWORD = "admin123"
$BASE64_AUTH = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${GRAFANA_USER}:${GRAFANA_PASSWORD}"))
$HEADERS = @{
    "Authorization" = "Basic $BASE64_AUTH"
    "Content-Type" = "application/json"
}

Write-Host "Esperando a que Grafana este listo..." -ForegroundColor Yellow
do {
    try {
        $response = Invoke-WebRequest -Uri "${GRAFANA_URL}/api/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) { break }
    } catch { }
    Write-Host "." -NoNewline
    Start-Sleep -Seconds 3
} while ($true)

Write-Host "Grafana is ready" -ForegroundColor Green

# Get IoT folder UID (fallback to first folder)
Write-Host "Getting dashboard folder info..." -ForegroundColor Cyan
$folders = Invoke-RestMethod -Uri "${GRAFANA_URL}/api/folders" -Headers $HEADERS -Method Get
$iotFolder = $folders | Where-Object { $_.title -eq "IoT Demo" } | Select-Object -First 1
if ($iotFolder) {
    $FOLDER_UID = $iotFolder.uid
} else {
    $FOLDER_UID = $folders[0].uid
}
Write-Host "   Folder UID: ${FOLDER_UID}" -ForegroundColor Gray

# Get Redis datasource UID (strict)
Write-Host "Getting Redis datasource UID..." -ForegroundColor Cyan
$datasources = Invoke-RestMethod -Uri "${GRAFANA_URL}/api/datasources" -Headers $HEADERS -Method Get
$REDIS_DS = $datasources | Where-Object { $_.uid -eq "redis-datasource" -or ($_.name -eq "Redis" -and $_.type -eq "redis-datasource") } | Select-Object -First 1
if ($REDIS_DS) {
    $REDIS_DS_UID = $REDIS_DS.uid
} else {
    throw "Redis datasource not found. Ensure provisioning is loaded before creating alerts."
}
Write-Host "   Redis DS UID: ${REDIS_DS_UID}" -ForegroundColor Gray

# Remove existing rules with the same titles to avoid duplicates and stale datasource UIDs
$managedTitles = @("High Temperature Alert", "High Humidity Alert", "Gas Alarm Alert")
Write-Host "Cleaning previous managed alert rules..." -ForegroundColor Cyan
try {
    $existingRules = Invoke-RestMethod -Uri "${GRAFANA_URL}/api/v1/provisioning/alert-rules" -Headers $HEADERS -Method Get
    $rulesToDelete = $existingRules | Where-Object { $managedTitles -contains $_.title }
    foreach ($rule in $rulesToDelete) {
        Invoke-RestMethod -Uri "${GRAFANA_URL}/api/v1/provisioning/alert-rules/$($rule.uid)" -Headers $HEADERS -Method Delete | Out-Null
        Write-Host "   Removed: $($rule.title) [$($rule.uid)]" -ForegroundColor DarkGray
    }
} catch {
    Write-Host "   Warning: Could not cleanup previous rules, continuing..." -ForegroundColor Yellow
}

# Alert 1: High Temperature
Write-Host "Creating Alert Rule: High Temperature (>30C)..." -ForegroundColor Yellow
$tempAlert = @{
    title = "High Temperature Alert"
    condition = "C"
    data = @(
        @{
            refId = "A"
            relativeTimeRange = @{ from = 300; to = 0 }
            datasourceUid = $REDIS_DS_UID
            model = @{
                command = "hget"
                field = "value"
                keyName = "sensors:dht22_temperatura:latest"
                type = "command"
                refId = "A"
            }
        },
        @{
            refId = "C"
            relativeTimeRange = @{ from = 300; to = 0 }
            datasourceUid = "__expr__"
            model = @{
                type = "threshold"
                expression = "A"
                conditions = @(@{
                    evaluator = @{ params = @(30); type = "gt" }
                    operator = @{ type = "and" }
                    query = @{ params = @("A") }
                    reducer = @{ params = @(); type = "last" }
                    type = "query"
                })
                datasource = @{ type = "__expr__"; uid = "__expr__" }
                refId = "C"
            }
        }
    )
    folderUID = $FOLDER_UID
    noDataState = "NoData"
    execErrState = "Error"
    for = "10s"
    isPaused = $false
    notification_settings = @{ receiver = "Email Notifications" }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "${GRAFANA_URL}/api/v1/provisioning/alert-rules" -Headers $HEADERS -Method Post -Body $tempAlert | Out-Null
Write-Host "   Temperature alert created" -ForegroundColor Green

# Alert 2: High Humidity
Write-Host "Creating Alert Rule: High Humidity (>80%)..." -ForegroundColor Yellow
$humAlert = @{
    title = "High Humidity Alert"
    condition = "C"
    data = @(
        @{
            refId = "A"
            relativeTimeRange = @{ from = 300; to = 0 }
            datasourceUid = $REDIS_DS_UID
            model = @{
                command = "hget"
                field = "value"
                keyName = "sensors:dht22_humedad:latest"
                type = "command"
                refId = "A"
            }
        },
        @{
            refId = "C"
            relativeTimeRange = @{ from = 300; to = 0 }
            datasourceUid = "__expr__"
            model = @{
                type = "threshold"
                expression = "A"
                conditions = @(@{
                    evaluator = @{ params = @(80); type = "gt" }
                    operator = @{ type = "and" }
                    query = @{ params = @("A") }
                    reducer = @{ params = @(); type = "last" }
                    type = "query"
                })
                datasource = @{ type = "__expr__"; uid = "__expr__" }
                refId = "C"
            }
        }
    )
    folderUID = $FOLDER_UID
    noDataState = "NoData"
    execErrState = "Error"
    for = "10s"
    isPaused = $false
    notification_settings = @{ receiver = "Email Notifications" }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "${GRAFANA_URL}/api/v1/provisioning/alert-rules" -Headers $HEADERS -Method Post -Body $humAlert | Out-Null
Write-Host "   Humidity alert created" -ForegroundColor Green

# Alert 3: Gas Alarm
Write-Host "Creating Alert Rule: Gas Alarm Triggered..." -ForegroundColor Yellow
$gasAlert = @{
    title = "Gas Alarm Alert"
    condition = "C"
    data = @(
        @{
            refId = "A"
            relativeTimeRange = @{ from = 300; to = 0 }
            datasourceUid = $REDIS_DS_UID
            model = @{
                command = "hget"
                field = "value"
                keyName = "sensors:mq_gas_alarma:latest"
                type = "command"
                refId = "A"
            }
        },
        @{
            refId = "C"
            relativeTimeRange = @{ from = 300; to = 0 }
            datasourceUid = "__expr__"
            model = @{
                type = "threshold"
                expression = "A"
                conditions = @(@{
                    evaluator = @{ params = @(0.5); type = "gt" }
                    operator = @{ type = "and" }
                    query = @{ params = @("A") }
                    reducer = @{ params = @(); type = "last" }
                    type = "query"
                })
                datasource = @{ type = "__expr__"; uid = "__expr__" }
                refId = "C"
            }
        }
    )
    folderUID = $FOLDER_UID
    noDataState = "NoData"
    execErrState = "Error"
    for = "5s"
    isPaused = $false
    notification_settings = @{ receiver = "Email Notifications" }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "${GRAFANA_URL}/api/v1/provisioning/alert-rules" -Headers $HEADERS -Method Post -Body $gasAlert | Out-Null
Write-Host "   Gas alarm alert created" -ForegroundColor Green

Write-Host "`nAlert rules created successfully!" -ForegroundColor Green
Write-Host "Notification channel: Email Notifications (demo@iot-conference.com)" -ForegroundColor Cyan
Write-Host "`nAlert Rules Summary:" -ForegroundColor Magenta
Write-Host "   Temperature > 30C -> WARNING" -ForegroundColor Yellow
Write-Host "   Humidity > 80% -> WARNING" -ForegroundColor Yellow
Write-Host "   Gas Alarm = 1 -> CRITICAL" -ForegroundColor Red
