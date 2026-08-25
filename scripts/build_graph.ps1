# Windows Offline PowerShell Builder for Knowledge Graph & Search Index
$wikiFiles = Get-ChildItem -Path "wiki" -Recurse -Filter "*.md"
$nodes = @()
$edges = @()
$seenNodes = @{}
$nodeDegrees = @{}
$documentsIndex = @()

Write-Host "Scanning $($wikiFiles.Count) markdown files in wiki/..."

foreach ($file in $wikiFiles) {
    $docName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
    $cleanPath = $file.FullName.Replace("\", "/")
    
    $docType = "Document"
    if ($cleanPath -match "/concepts/") { $docType = "Concept" }
    elseif ($cleanPath -match "/entities/") { $docType = "Entity" }
    elseif ($cleanPath -match "/summaries/") { $docType = "Summary" }
    elseif ($cleanPath -match "/synthesis/") { $docType = "Synthesis" }

    if (-not $seenNodes.ContainsKey($docName)) {
        $seenNodes[$docName] = $true
        $nodes += [PSCustomObject]@{
            id = $docName
            label = $docName
            type = $docType
            path = $cleanPath
        }
    }
    
    $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
    $matches = [regex]::Matches($content, '\[\[(.*?)\]\]')
    $docLinks = @()

    foreach ($m in $matches) {
        $rawLink = $m.Groups[1].Value
        $cleanLink = ($rawLink.Split('|')[0].Split('#')[0]).Trim()
        if ($cleanLink.Length -gt 0 -and $cleanLink -ne $docName) {
            if (-not $seenNodes.ContainsKey($cleanLink)) {
                $seenNodes[$cleanLink] = $true
                $nodes += [PSCustomObject]@{
                    id = $cleanLink
                    label = $cleanLink
                    type = "Concept"
                }
            }
            $edges += [PSCustomObject]@{
                source = $docName
                target = $cleanLink
                relation = "links_to"
            }
            $docLinks += $cleanLink
            if (-not $nodeDegrees.ContainsKey($docName)) { $nodeDegrees[$docName] = 0 }
            if (-not $nodeDegrees.ContainsKey($cleanLink)) { $nodeDegrees[$cleanLink] = 0 }
            $nodeDegrees[$docName]++
            $nodeDegrees[$cleanLink]++
        }
    }

    # Extract snippet
    $cleanPreview = [regex]::Replace($content, '---[\s\S]*?---', '').Trim()
    $snippet = if ($cleanPreview.Length -gt 250) { $cleanPreview.Substring(0, 250).Replace("`n", " ") + "..." } else { $cleanPreview }

    $documentsIndex += [PSCustomObject]@{
        id = $docName
        path = $cleanPath
        type = $docType
        snippet = $snippet
        links = $docLinks
    }
}

if (-not (Test-Path "graph")) { New-Item -ItemType Directory -Path "graph" | Out-Null }

# 1. Save graph/graph.json
$graphObj = [PSCustomObject]@{
    metadata = [PSCustomObject]@{
        total_nodes = $nodes.Count
        total_edges = $edges.Count
    }
    nodes = $nodes
    edges = $edges
}
$graphJson = $graphObj | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText("graph/graph.json", $graphJson, [System.Text.Encoding]::UTF8)

# 2. Save graph/search_index.json
$searchObj = [PSCustomObject]@{
    metadata = [PSCustomObject]@{
        total_documents = $documentsIndex.Count
    }
    documents = $documentsIndex
}
$searchJson = $searchObj | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText("graph/search_index.json", $searchJson, [System.Text.Encoding]::UTF8)

$nodeCount = $nodes.Count
$edgeCount = $edges.Count
Write-Host "Generated graph/graph.json and graph/search_index.json successfully ($nodeCount nodes, $edgeCount edges)."
