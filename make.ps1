<#
.Synopsis
Makefile script in PowerShell that contains commands useful during development for Red.

.Description
Available commands:
   run              Run the bot in the subset mode.
   scp              Transfer files to VPS
   commit           Commit to github

.Parameter Command
Command to execute. See Cmdlet's description for more information.

#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $false)]
    [ArgumentCompleter({
            param (
                $commandName,
                $parameterName,
                $wordToComplete,
                $commandAst,
                $fakeBoundParameters
            )
            $script:availableCommands = @("draft", "run", "commit", "scp")
            return $script:availableCommands | Where-Object { $_ -like "$wordToComplete*" }
        })]
    [String]
    $command,
    [String]
    $m = "😴 update(lazy): Various fixes and updates",
    [switch]
    $help = $false
)

# get-content .env | Foreach-Object {
#     if ($_.contains("#")) {
#         return;
#     }
#     else {
#         $name, $value = $_.split('=')
#         Write-Host $name, $value
#         Set-Content env:\$name $values
#     }
# }

function draft {
    Write-Host($m)
}

function run() {
    uv run src/main.py --subset-mode
}

function commit() {
    Set-Location src/shared
    git add .
    git commit -a -m "$m"
    git push
    Set-Location ..
    Set-Location ..
    git add .
    git commit -a -m "$m"
    git push
}

function scp() {
    # Write-Host $env:SSH_USERNAME
    # Write-Host [Environment]::GetEnvironmentVariable($SSH_PRIVATE_KEY)
    # scp -i "$Env:SSH_PRIVATE_KEY" ".\.env" $Env:SSH_USERNAME@$Env:SSH_HOST:~/IreBot/.env
}

$script:availableCommands = $MyInvocation.MyCommand.ParameterSets[0].Parameters[0].Attributes[0].ScriptBlock.Invoke()

if ($help -or !$command) {
    Get-Help $MyInvocation.InvocationName
    exit
}

switch ($command) {
    { $script:availableCommands -contains $_ } {
        & $command
        break
    }
    default {
        Write-Host (
            """$command"" is not a valid command.",
            "To see available commands, type: ""$($MyInvocation.InvocationName) -help"""
        )
        break
    }
}