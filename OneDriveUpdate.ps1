
param (
    [string]$oP = "C:\file_$(Get-Date -Format 'yyyyMMdd_HHmm').csv",
    [int]$dS = 4,
    [int]$jT = 2
)

$oD = Split-Path $oP -Parent
if (-not (Test-Path $oD)) { New-Item -Path $oD -ItemType Directory -Force | Out-Null }

function gDC {
    try {
        $s = New-Object System.DirectoryServices.DirectorySearcher
        $s.Filter = "(&(objectClass=computer)(objectCategory=computer))"
        $s.PropertiesToLoad.Add('name') | Out-Null
        $s.PageSize = 1000
        $r = $s.FindAll()
        $c = @()
        foreach ($i in $r) {
            $n = $i.Properties['name'][0]
            if ($n) { $c += $n }
        }
        return $c
    } catch {
        $nv = net view | Where-Object { $_ -match '^\\\\' } | ForEach-Object { ($_ -split '\s+')[0].TrimStart('\\') }
        return $nv
    }
}

$comps = gDC
$res = @()

foreach ($comp in $comps) {
    if (-not $comp) { continue }
    
    try {
        $sh = gwmi -Class Win32_Share -ComputerName $comp -EA SilentlyContinue | 
              Where-Object { $_.Type -eq 0 }
        
        foreach ($s in $sh) {
            $p = "\\$comp\$($s.Name)"
            $acc = $false
            $broad = $false
            
            try {
                if (Test-Path $p -EA SilentlyContinue) {
                    $acc = $true
                    
                    $sec = gwmi -Class Win32_LogicalShareSecuritySetting -Filter "Name='$($s.Name)'" -ComputerName $comp -EA SilentlyContinue
                    if ($sec) {
                        $sd = $sec.GetSecurityDescriptor().Descriptor
                        foreach ($ace in $sd.DACL) {
                            $t = $ace.Trustee.Name
                            if ($t -match 'Everyone|Authenticated|Users|Domain Users') {
                                $broad = $true
                                break
                            }
                        }
                    }
                }
            } catch {}
            
            if ($acc -and $broad) {
                $obj = [PSCustomObject]@{
                    C = $comp.ToUpper()
                    S = $s.Name
                    P = $p
                    D = $s.Description
                    TS = Get-Date
                }
                $res += $obj
            }
        }
    } catch {}
    
    $sl = $dS + (Get-Random -Minimum (-$jT) -Maximum $jT)
    if ($sl -gt 0) { Start-Sleep -Seconds $sl }
}

if ($res.Count -gt 0) {
    $res | Export-Csv -Path $oP -NoTypeInformation
} 

$res | Format-Table C, S, P -AutoSize